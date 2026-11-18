"""Hermes pre_tool_call gates (B6).

Runs in-process, so it works even when the shell hooks are not installed. It
mirrors hooks/pre-brainstorm-ground: a write to ``docs/brainstorming/*.md`` must
carry a ``Grounding:`` line for every option section, or an explicit
``UNKNOWN (not retrieved: …)`` row.

Returning ``{"action": "block", "message": …}`` is the Hermes hook contract;
returning ``None`` lets the tool run.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

BRAINSTORM_PREFIX = "docs/brainstorming/"
WRITE_TOOLS = {
    "write_file",
    "patch",
    "edit",
    "apply_patch",
    "Write",
    "Edit",
    "MultiEdit",
}
OPTION_RE = re.compile(r"^#{2,3}\s+(?:Option|Approach|Alternative|Proposal)\b.*$", re.MULTILINE | re.IGNORECASE)
GROUNDING_RE = re.compile(r"Grounding:\s*\S|UNKNOWN \(not retrieved", re.IGNORECASE)


def enabled() -> bool:
    """Explicit env wins; otherwise on under CodeMAX, off elsewhere (public repo).

    ``CODEMAX_ENABLED`` is the switch the team guide tells people to export, and
    ``plan_issue.codemax_repo`` already honoured it — the gate did not, so the
    documented setup left the PR gate off.
    """
    value = os.environ.get("TAPWAY_BRAINSTORM_GATE")
    if value is not None:
        return value == "1"
    codemax = (
        os.environ.get("CODEMAX_WORKFLOW") == "1"
        or os.environ.get("CODEMAX_ENABLED") == "1"
        or Path(".codemax.yml").is_file()
    )
    return codemax


def _target(args: dict[str, Any]) -> tuple[str, str]:
    path = ""
    for key in ("file_path", "path"):
        if isinstance(args.get(key), str):
            path = args[key]
            break
    text = ""
    for key in ("content", "new_string"):
        if isinstance(args.get(key), str):
            text = args[key]
            break
    return path, text


def _normalise(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def check_doc(path: str, text: str) -> list[str]:
    """Return one finding per ungrounded option section (empty = allowed)."""
    if not _normalise(path).startswith(BRAINSTORM_PREFIX):
        return []
    if not text.strip():
        return []

    matches = list(OPTION_RE.finditer(text))
    if not matches:
        return ["no '## Option / Approach / Alternative / Proposal' section — a brainstorm needs at least one"]

    findings: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.end() : end]
        if not GROUNDING_RE.search(section):
            findings.append(f"{match.group(0).strip()} has no 'Grounding:' line")
    return findings


def on_pre_tool_call(tool_name: str = "", args: Any = None, **_: Any) -> dict[str, str] | None:
    if not enabled():
        return None
    if not isinstance(args, dict):
        return None

    pr_verdict = _pr_contract_gate(tool_name, args)
    if pr_verdict is not None:
        return pr_verdict

    if tool_name not in WRITE_TOOLS:
        return None

    path, text = _target(args)
    if not path:
        return None

    findings = check_doc(path, text)
    if not findings:
        return None
    return {
        "action": "block",
        "message": (
            "tapway-superpowers refused this brainstorm write — every option must cite "
            "the brain with a 'Grounding: <wiki/...>' line (or an explicit "
            "'UNKNOWN (not retrieved: <reason>)').\n\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\nTo override for one run, set TAPWAY_BRAINSTORM_GATE=0."
        ),
    }


# --------------------------------------------------------------------------- #
# PR contract (C2) — the same rule the Claude/Codex pre-pr-contract hook applies
# --------------------------------------------------------------------------- #
SHELL_TOOLS = {"terminal", "bash", "Bash", "shell", "run_command"}
PR_CREATE_RE = re.compile(r"\bgh\s+pr\s+create\b")


def _pr_contract_gate(tool_name: str, args: dict[str, Any]) -> dict[str, str] | None:
    if tool_name not in SHELL_TOOLS:
        return None
    if os.environ.get("TAPWAY_PR_GATE") == "0":
        return None
    command = args.get("command") or args.get("cmd") or ""
    if not isinstance(command, str) or not PR_CREATE_RE.search(command):
        return None

    workdir = args.get("workdir") or args.get("cwd") or os.getcwd()
    try:
        root = Path(str(workdir))
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
    except OSError:
        return None
    if top.returncode != 0:
        return None
    repo_root = Path(top.stdout.strip())

    def git(*git_args: str) -> str:
        out = subprocess.run(
            ["git", "-C", str(repo_root), *git_args], capture_output=True, text=True
        )
        return out.stdout if out.returncode == 0 else ""

    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "master":  # staging<-master sync: the base is stale by definition
        return None

    base = os.environ.get("TAPWAY_PR_BASE") or ""
    if not base:
        for candidate in ("origin/staging", "origin/main", "origin/master"):
            if git("rev-parse", "--verify", "--quiet", candidate).strip():
                base = candidate
                break
    if not base:
        return None

    changed = [line for line in git("diff", "--name-only", f"{base}...HEAD").splitlines() if line]
    if not changed:
        return None  # nothing committed against the base — refuse to guess

    findings: list[str] = []
    for rel in changed:
        if not rel.endswith(".md"):
            continue
        try:
            text = (repo_root / rel).read_text(encoding="utf-8")
        except OSError:
            continue
        if rel.startswith("docs/plans/"):
            from .plan_issue import issue_number

            if issue_number(text) is None:
                findings.append(
                    f"{rel}: plan has no 'issue: <number>' frontmatter "
                    "(create the GitHub issue first)"
                )
        elif rel.startswith("docs/brainstorming/"):
            findings.extend(f"{rel}: {finding}" for finding in check_doc(rel, text))
    if not findings:
        return None
    return {
        "action": "block",
        "message": (
            "tapway-superpowers refused `gh pr create`:\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\nCreate the GitHub issue (it is auto-created when you save the plan), "
            "add `issue: <n>` to the plan frontmatter, or set TAPWAY_PR_GATE=0 for one run."
        ),
    }