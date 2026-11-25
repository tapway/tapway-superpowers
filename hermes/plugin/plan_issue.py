"""Plan → GitHub issue (C2), executed automatically after a plan is written.

The issue is the unit CodeMAX's kanban mirrors, so it has to exist the moment
the plan does — not when someone remembers to run a script. This module is the
single implementation behind all three entry points:

- Claude Code / Codex: ``hooks/post-plan-issue/post-plan-issue.sh`` (PostToolUse)
- Hermes: the plugin's ``post_tool_call`` hook

It is stdlib-only on purpose: it runs inside a hook process, before the repo's
dependencies are guaranteed, and inside Hermes' bundled interpreter which ships
no PyYAML.

Readability is part of the contract. Every issue opens with a Summary, then
What changes (the plan's tasks as checkboxes), Acceptance criteria, Test plan,
Files and Links, with the full plan collapsed underneath. A plan whose shape the
parser does not recognise still gets those sections, just with thinner content.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

LABEL = "codemax"
PROTECTED_BRANCHES = {"master", "main", "staging", "prod"}
MAX_BODY = 60000  # GitHub rejects >65536; leave room for the call site's own edits

PLAN_RE = re.compile(r"(^|/)docs/plans/[^/\\]+\.md$")
BRAINSTORM_RE = re.compile(r"(^|/)docs/brainstorming/[^/\\]+\.md$")
STATUS_RE = re.compile(r"^status:\s*[\"']?([A-Za-z][\w-]*)", re.MULTILINE)
ACCEPTED_STATUSES = {"accepted", "approved"}
BRAINSTORM_LINK_RE = re.compile(r"brainstorming/([^)\s`]+\.md)")
TITLE_PREFIX_RE = re.compile(r"^(brainstorm|design|rfc)\s*:\s*", re.IGNORECASE)
ISSUE_RE = re.compile(r"^issue:\s*(\d+)\s*$", re.MULTILINE)
ISSUE_SCAN_LIMIT = 100  # newest labelled issues; bodies are needed for exact match
BRANCH_MARKER_RE = re.compile(r"^\s*[-*]\s*\*\*Branch:\*\*\s*`?([^`\s]+)`?\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
BOILERPLATE_RE = re.compile(r"\s*[—–-]\s*(implementation\s+)?plan\s*$", re.IGNORECASE)
BRANCH_TYPES = {
    "feat": "feat",
    "feature": "feat",
    "fix": "fix",
    "bugfix": "fix",
    "hotfix": "fix",
    "chore": "chore",
    "docs": "docs",
    "doc": "docs",
    "refactor": "refactor",
    "test": "test",
    "perf": "perf",
}

Runner = Callable[..., Any]


@dataclass
class IssueResult:
    number: int | None = None
    url: str | None = None
    created: bool = False
    skipped: str | None = None
    error: str | None = None
    message: str | None = None


# --------------------------------------------------------------------------- #
# plan files
# --------------------------------------------------------------------------- #
def is_plan_path(path: str | os.PathLike[str]) -> bool:
    return bool(PLAN_RE.search(str(path).replace("\\", "/")))


def is_brainstorm_path(path: str | os.PathLike[str]) -> bool:
    return bool(BRAINSTORM_RE.search(str(path).replace("\\", "/")))


def doc_kind(path: str | os.PathLike[str]) -> str | None:
    """Return "plan", "brainstorm", or None — by path only."""
    if is_plan_path(path):
        return "plan"
    if is_brainstorm_path(path):
        return "brainstorm"
    return None


def doc_status(text: str) -> str:
    block, _ = split_frontmatter(text)
    match = STATUS_RE.search(block)
    return match.group(1).lower() if match else ""


def is_accepted_brainstorm(text: str) -> bool:
    return doc_status(text) in ACCEPTED_STATUSES


def is_issue_doc(path: str | os.PathLike[str]) -> bool:
    """A plan, or a design doc whose frontmatter marks it accepted."""
    kind = doc_kind(path)
    if kind == "plan":
        return True
    if kind != "brainstorm":
        return False
    try:
        return is_accepted_brainstorm(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return False


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter block without the fences, body)."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4 :]


def issue_number(text: str) -> int | None:
    block, _ = split_frontmatter(text)
    match = ISSUE_RE.search(block)
    return int(match.group(1)) if match else None


def record_issue_text(text: str, number: int) -> str:
    """Put ``issue: <n>`` in the frontmatter, creating one when absent."""
    block, body = split_frontmatter(text)
    if text.startswith("---") and block:
        if ISSUE_RE.search(block):
            block = ISSUE_RE.sub(f"issue: {number}", block, count=1)
        else:
            block = f"\nissue: {number}" + block
        return _rejoin(block, text)
    return f"---\nissue: {number}\n---\n\n{text}"


def _rejoin(block: str, text: str) -> str:
    end = text.find("\n---", 3)
    return f"---{block}{text[end:]}"


def record_issue(path: Path | str, number: int) -> None:
    plan = Path(path)
    plan.write_text(record_issue_text(plan.read_text(encoding="utf-8"), number), encoding="utf-8")


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _slug_words(branch: str) -> str:
    tail = branch.split("/", 1)[1] if "/" in branch else branch
    return " ".join(w for w in re.split(r"[-_]+", tail) if w)


def render_title(plan_text: str, branch: str) -> str:
    _, body = split_frontmatter(plan_text)
    match = H1_RE.search(body)
    title = match.group(1).strip() if match else ""
    title = BOILERPLATE_RE.sub("", title).strip()
    title = TITLE_PREFIX_RE.sub("", title).strip()
    if not title:
        title = _slug_words(branch)
    prefix = BRANCH_TYPES.get(branch.split("/", 1)[0].lower())
    if prefix and not re.match(r"^(feat|fix|chore|docs|refactor|test|perf)(\(|:)", title):
        title = f"{prefix}: {title}"
    return title[:200]


def _sections(body: str) -> list[tuple[str, str]]:
    """(heading, section text) for every H2, in order."""
    heads = list(H2_RE.finditer(body))
    out: list[tuple[str, str]] = []
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(body)
        out.append((match.group(1).strip(), body[match.end() : end]))
    return out


def _bullets(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        match = re.match(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+?)\s*$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def _labelled(block: str, *names: str) -> str:
    for name in names:
        match = re.search(rf"^\*\*{name}:\*\*\s*(.+?)\s*$", block, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _first_paragraph(block: str) -> str:
    for chunk in re.split(r"\n\s*\n", block):
        text = chunk.strip()
        if not text or text.startswith(("#", "|", "```", "**")):
            continue
        return " ".join(text.split())
    return ""


def _pick(sections: list[tuple[str, str]], pattern: str) -> str:
    for heading, block in sections:
        if re.search(pattern, heading, re.IGNORECASE):
            return block
    return ""


def _acceptance(body: str, sections: list[tuple[str, str]]) -> list[str]:
    """Bullets from a top-level acceptance section, else each task's AC block."""
    section = _pick(sections, r"acceptance|definition of done|done when|success criteria")
    items = _bullets(section) if section else []
    if not items:
        for match in re.finditer(r"^\*\*Acceptance criteria:?\*\*\s*$", body, re.MULTILINE | re.IGNORECASE):
            tail = re.split(r"\n#{2,3}\s", body[match.end() :])[0]
            items.extend(_bullets(tail))
    return items


def _files(body: str) -> list[str]:
    found: list[tuple[str, str]] = []
    for line in body.splitlines():
        match = re.match(r"^\s*[-*]\s+\*{0,2}(Create|Modify|Edit|Test|Delete)\*{0,2}:\s*(.+)$",
                         line, re.IGNORECASE)
        if not match:
            continue
        disposition = match.group(1).lower()
        for path in re.findall(r"`([^`]+)`", match.group(2)):
            if any(path == seen for seen, _ in found):
                continue
            found.append((path, "create" if disposition == "create" else disposition))
    return [f"- `{path}` — {disposition}" for path, disposition in found[:40]]


def render_body(plan_text: str, *, plan_path: str, branch: str, repo: str,
                kind: str = "plan") -> str:
    _meta, body = split_frontmatter(plan_text)
    sections = _sections(body)
    h1 = H1_RE.search(body)
    top = body[: h1.end()] if h1 else ""
    after_h1 = body[h1.end() :] if h1 else body

    summary = _labelled(after_h1, "Goal", "Purpose", "Objective") or _first_paragraph(after_h1)
    problem = _labelled(after_h1, "Problem", "Motivation", "Why", "Context")
    if not problem:
        problem = _first_paragraph(_pick(sections, r"problem|motivation|why|background"))
    out_of_scope = _labelled(after_h1, "Out of scope", "Not in scope", "Non-goals")
    summary = summary or (h1.group(1).strip() if h1 else "") or "Plan written."
    if len(summary) > 1200:
        summary = summary[:1200].rsplit(" ", 1)[0] + " …"

    preferred = (
        [s for s in sections if re.search(r"recommendation|chosen design|decision|approach|architecture", s[0], re.IGNORECASE)]
        if kind == "brainstorm" else []
    )
    changes: list[str] = []
    for heading, block in (preferred or sections):
        if re.search(r"test|acceptance|verif|out of scope|testing", heading, re.IGNORECASE):
            continue
        tasks = [m.group(1).strip() for m in H3_RE.finditer(block)]
        if tasks:
            changes.append(f"- **{heading}**")
            changes.extend(f"  - [ ] {task}" for task in tasks)
        else:
            bullets = _bullets(block)[:6]
            if bullets:
                changes.append(f"- **{heading}**")
                changes.extend(f"  - [ ] {item}" for item in bullets)
    if not changes and kind == "brainstorm":
        changes = ["- [ ] Implement the design (no recommendation bullets found — see the collapsed doc)"]
    if not changes:
        changes = ["- [ ] Implement the plan (no task headings found — see the collapsed plan)"]

    acceptance = _acceptance(body, sections)[:20]
    if not acceptance:
        acceptance = ["All tasks in the plan are implemented and reviewed", "CI is green on the PR"]
    acceptance_md = "\n".join(
        f"- [ ] {item}" if not item.startswith("[") else f"- [ ] {item}" for item in acceptance
    )

    testing = _pick(sections, r"test|verification|verif")
    test_items = [line.strip() for line in testing.splitlines() if line.strip().startswith(("`", "-", "*"))][:12]
    if not test_items:
        test_items = ["- Run the repo's test gate and lint; CI must be green."]
    test_md = "\n".join(
        f"- {item.lstrip('-* ').strip()}" for item in test_items
    )

    files_md = "\n".join(_files(body)) or (
        "- (no file list in the design doc)" if kind == "brainstorm" else "- (no file list in the plan)"
    )
    links = [f"- **Plan:** `{plan_path}`", f"- **Branch:** `{branch}`", f"- **Repo:** `{repo}`"]

    head = "\n\n".join(
        [
            "## Summary",
            summary,
            *(["## Why", problem] if problem else []),
            *(["## Out of scope", out_of_scope] if out_of_scope else []),
            "## What changes",
            "\n".join(changes),
            "## Acceptance criteria",
            acceptance_md,
            "## Test plan",
            test_md,
            "## Files",
            files_md,
            "## Links",
            "\n".join(links),
        ]
    )

    source = "design doc" if kind == "brainstorm" else "plan"
    summary_word = "Full design" if kind == "brainstorm" else "Full plan"
    footer = f"\n\n---\n\n_Auto-created from the {source} by tapway-superpowers (plan → issue contract)._"
    budget = MAX_BODY - len(head) - len(footer) - 80
    if budget < 200:
        return head[:MAX_BODY]
    plan_block = plan_text.strip()
    if len(plan_block) > budget:
        plan_block = plan_block[:budget].rsplit("\n", 1)[0] + "\n\n… (truncated)"
    return (
        f"{head}\n\n<details><summary>{summary_word}</summary>\n\n{plan_block}\n\n</details>{footer}"
    )


# --------------------------------------------------------------------------- #
# git + gh
# --------------------------------------------------------------------------- #
def _default_runner(args: list[str], cwd: Path | None = None):
    return subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def repo_from_git(directory: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(directory), "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    match = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", out.stdout.strip())
    return match.group(1) if match else None


def branch_from_git(directory: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    )
    return out.stdout.strip() if out.returncode == 0 else ""


def linked_brainstorm_issue(plan_path: Path | str, text: str) -> int | None:
    """Issue number of a design doc this plan links to, when it already has one."""
    plan = Path(plan_path)
    for match in BRAINSTORM_LINK_RE.finditer(text):
        name = match.group(1)
        for base in plan.parents:
            candidate = base / "docs" / "brainstorming" / name
            if candidate.is_file():
                try:
                    return issue_number(candidate.read_text(encoding="utf-8"))
                except OSError:
                    return None
    return None


def issue_branch(body: str) -> str:
    """The branch recorded in an issue body by ``render_body``, if any."""
    match = BRANCH_MARKER_RE.search(body or "")
    return match.group(1).strip() if match else ""


def issues_on_branch(listed, branch: str) -> list[int]:
    """Numbers from ``gh issue list --json number,body`` whose marker is exact."""
    if getattr(listed, "returncode", 1) != 0:
        return []
    try:
        data = json.loads(listed.stdout or "[]")
    except (ValueError, TypeError):
        return []
    numbers: list[int] = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict) or issue_branch(item.get("body") or "") != branch:
            continue
        number = item.get("number")
        if isinstance(number, int):
            numbers.append(number)
        elif isinstance(number, str) and number.isdigit():
            numbers.append(int(number))
    return numbers


def ensure_issue(
    plan_path: Path | str,
    *,
    repo: str,
    branch: str,
    label: str = LABEL,
    runner: Runner | None = None,
    cwd: Path | None = None,
) -> IssueResult:
    """Create (or adopt) the issue for this plan and record its number."""
    run = runner or _default_runner
    plan = Path(plan_path)
    kind = doc_kind(plan)
    if kind is None:
        return IssueResult(skipped="not-an-issue-doc")
    text = plan.read_text(encoding="utf-8")

    if kind == "brainstorm" and not is_accepted_brainstorm(text):
        return IssueResult(
            skipped="not-accepted",
            message=f"design doc status is {doc_status(text) or 'unset'}; only an accepted design opens an issue",
        )

    existing = issue_number(text)
    if existing is not None:
        source = "design doc" if kind == "brainstorm" else "plan"
        return IssueResult(number=existing, message=f"{source} already records issue #{existing}")

    if kind == "plan":
        inherited = linked_brainstorm_issue(plan, text)
        if inherited is not None:
            record_issue(plan, inherited)
            return IssueResult(
                number=inherited,
                url=f"https://github.com/{repo}/issues/{inherited}" if repo else None,
                message=f"reused issue #{inherited} from the linked design doc",
            )

    if not branch or branch in PROTECTED_BRANCHES:
        return IssueResult(skipped="protected-branch",
                           message=f"{branch or 'detached'} is not a feature branch")
    if not repo:
        return IssueResult(skipped="no-repo", message="no GitHub origin remote")

    # Do not use `gh --search` here: it is tokenised ("feat/a-b" matches
    # "feat/a-b-c") and its index lags creation (a seconds-old issue is still
    # invisible), so it both adopts another branch's issue and misses its own.
    # List the label's newest issues and match the branch marker exactly.
    listed = run(
        [
            "gh", "issue", "list", "--repo", repo, "--label", label, "--state", "all",
            "--limit", str(ISSUE_SCAN_LIMIT), "--json", "number,body",
        ],
        cwd,
    )
    for number in issues_on_branch(listed, branch):
        record_issue(plan, number)
        return IssueResult(number=number, url=f"https://github.com/{repo}/issues/{number}",
                           message=f"reused existing issue #{number} on this branch")

    title = render_title(text, branch)
    body = render_body(text, plan_path=str(plan).replace(os.sep, "/"), branch=branch, repo=repo,
                       kind=kind)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(body)
        body_file = handle.name
    try:
        created = run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--label", label,
             "--body-file", body_file],
            cwd,
        )
    finally:
        try:
            os.unlink(body_file)
        except OSError:
            pass

    url = (created.stdout or "").strip().splitlines()[-1] if created.stdout else ""
    match = re.search(r"/issues/(\d+)", url)
    if created.returncode != 0 or not match:
        detail = (created.stderr or created.stdout or "").strip().splitlines()
        return IssueResult(error=f"gh issue create failed: {detail[-1] if detail else 'no output'}")

    number = int(match.group(1))
    record_issue(plan, number)
    return IssueResult(number=number, url=url, created=True,
                       message=f"created issue #{number}: {url}")


def codemax_repo(directory: Path) -> bool:
    """CodeMAX-only behaviour: an explicit switch, or a `.codemax.yml` in the repo."""
    if os.environ.get("CODEMAX_WORKFLOW") == "1" or os.environ.get("CODEMAX_ENABLED") == "1":
        return True
    return (directory / ".codemax.yml").is_file()


WRITE_TOOLS = {"write_file", "patch", "edit", "apply_patch", "Write", "Edit", "MultiEdit"}


def on_post_tool_call(
    tool_name: str = "",
    args: dict[str, Any] | None = None,
    runner: Runner | None = None,
    **_: Any,
) -> None:
    """Hermes ``post_tool_call``: run the same flow in-process.

    Returns ``None`` always — a post hook cannot deny the call, and a plan that
    failed to get an issue must not fail the write that produced it.
    """
    try:
        if tool_name not in WRITE_TOOLS or not isinstance(args, dict):
            return None
        if os.environ.get("TAPWAY_ISSUE_AUTOCREATE") == "0":
            return None
        path = args.get("file_path") or args.get("path")
        if not isinstance(path, str) or doc_kind(path) is None:
            return None
        if not os.path.isabs(path):
            base = args.get("workdir") or os.getcwd()
            path = os.path.join(str(base), path)
        result = handle_plan_write(path, runner=runner)
        if result.message:
            import logging

            logging.getLogger(__name__).info("plan_issue: %s", result.message)
        return None
    except Exception as exc:  # noqa: BLE001 - never fail the tool call
        import logging

        logging.getLogger(__name__).warning("plan_issue: %s", exc)
        return None


def handle_plan_write(path: Path | str, runner: Runner | None = None) -> IssueResult:
    """Entry point for both hook surfaces. Never raises."""
    plan = Path(path)
    if not plan.is_file() or not is_issue_doc(plan):
        return IssueResult(skipped="not-an-issue-doc")
    directory = plan.resolve().parent
    try:
        top = subprocess.run(["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True)
        root = Path(top.stdout.strip()) if top.returncode == 0 else directory
    except OSError:
        root = directory
    if not codemax_repo(root):
        return IssueResult(skipped="not-a-codemax-repo")
    try:
        return ensure_issue(
            plan,
            repo=repo_from_git(root) or "",
            branch=branch_from_git(root),
            runner=runner,
        )
    except Exception as exc:  # noqa: BLE001 - a hook must never break the tool call
        return IssueResult(error=f"{type(exc).__name__}: {exc}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: plan_issue.py <plan-or-design-file>", flush=True)
        return 2
    result = handle_plan_write(argv[1])
    if result.error:
        print(f"tapway-superpowers: {result.error}", flush=True)
        return 0  # never fail the write that triggered us
    if result.message:
        print(f"tapway-superpowers: {result.message}", flush=True)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv))