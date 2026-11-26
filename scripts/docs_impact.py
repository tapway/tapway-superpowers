#!/usr/bin/env python3
"""Check a PR's docs disposition against the event's merge-base diff."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_audit import routine  # noqa: E402  (same exemptions as the audit)

SHA = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?")
DOCS_LINE = re.compile(r" {0,3}Docs[ \t]*:", re.IGNORECASE)
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
DOCS_ONLY_FILES = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    ".github/pull_request_template.md",
}
NON_PROOF_PREFIXES = (
    "docs/plans/",
    "docs/brainstorming/",
    "docs/checklists/",
    "docs/specs/",
    "docs/post-mortems/",
    "docs/superpowers/specs/",
)

CONFIG = ".docs-impact.json"
SCOPED = re.compile(r"Docs: no impact \(([^)]*)\) — (.+)")
NOT_SOURCE = re.compile(r"(^|/)(tests?|__tests__|fixtures|examples|node_modules)/|^docs/|^\.github/")
CODE_EXT = r"\.(py|ts|tsx|js|go|rs|java|kt)$"
# Which changed paths ask for which document. "block" fails the check; otherwise
# it warns, because paths alone cannot tell a design change from a small edit.
RULES = {
    "schema": {
        "doc": "docs/DB_SCHEMA.md",
        "block": True,
        "paths": [
            r"(^|/)(alembic|migrations)/.+\.(py|sql|ts|js)$",
            r"\.sql$",
            r"(^|/)schema\.prisma$",
            r"(^|/)models(/.+)?\.py$",
        ],
    },
    "deployment": {
        "doc": "docs/DEPLOYMENT.md",
        "block": True,
        "paths": [
            r"(^|/)Dockerfile[^/]*$",
            r"(^|/)(docker-)?compose[^/]*\.ya?ml$",
            r"(^|/)(deploy|k8s|helm|terraform|infra)/",
            r"(^|/)\.env[^/]*(example|sample|template)$",
            r"(^|/)nginx[^/]*\.conf$",
        ],
    },
    "architecture": {
        "doc": "docs/ARCHITECTURE.md",
        "block": False,
        "new_directory": True,
        "paths": [
            r"(^|/)(package\.json|pyproject\.toml|requirements[^/]*\.txt|go\.mod|Cargo\.toml)$",
            r"(^|/)(docker-)?compose[^/]*\.ya?ml$",
        ],
    },
    "workflows": {
        "doc": "docs/WORKFLOWS.md",
        "block": False,
        "paths": [
            r"(^|/)(api|routes|routers|workers|consumers|jobs|schedulers|adapters)/.+" + CODE_EXT,
            r"(^|/)[^/]*_(worker|consumer|scheduler)" + CODE_EXT,
        ],
    },
}


def load_rules(base: str) -> dict:
    """The rules, adjusted by .docs-impact.json as it is on the target branch."""
    rules = {name: dict(rule) for name, rule in RULES.items()}
    shown = subprocess.run(["git", "show", f"{base}:{CONFIG}"], capture_output=True, timeout=20)
    if shown.returncode:
        return rules
    config = json.loads(shown.stdout.decode("utf-8-sig"))
    for name, override in config.get("rules", {}).items():
        rules[name].update(override)
    if config.get("database") is False:
        del rules["schema"]
    return rules


def new_directories(base: str, changes: list[tuple[bytes, str]]) -> set[str]:
    """Added source files whose folder did not exist before this PR."""
    listed = subprocess.run(
        ["git", "ls-tree", "-r", "-d", "--name-only", "-z", base],
        capture_output=True, check=True, timeout=20,
    ).stdout.decode("utf-8", errors="surrogateescape")
    existing = set(listed.split("\0"))
    return {
        path for status, path in changes
        if status == b"A" and "/" in path and re.search(CODE_EXT, path)
        and path.rsplit("/", 1)[0] not in existing
    }


def unmet_rules(rules: dict, base: str, changes: list[tuple[bytes, str]], reasons: set[str]):
    """(name, rule, example path) for each triggered rule with no doc and no reason."""
    touched = {path for status, path in changes if status in (b"A", b"M")}
    added_dirs = new_directories(base, changes)
    for name, rule in rules.items():
        if name in reasons or rule["doc"] in touched:
            continue
        for _, path in changes:
            if NOT_SOURCE.search(path):
                continue
            if any(re.search(p, path) for p in rule["paths"]) or (
                rule.get("new_directory") and path in added_dirs
            ):
                yield name, rule, path
                break


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(2, "Docs impact: expected an event path and optional --advisory.\n")


def read_event(path: Path) -> tuple[str, str, str]:
    pr = json.loads(path.read_text(encoding="utf-8"))["pull_request"]
    base, head, body = pr["base"]["sha"], pr["head"]["sha"], pr["body"]
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in (base, head)):
        raise ValueError("Invalid commit IDs")
    if body is not None and not isinstance(body, str):
        raise ValueError("Invalid PR body")
    return base, head, body or ""


def changed_paths(base: str, head: str) -> list[tuple[bytes, str]]:
    diff = subprocess.run(
        [
            "git", "diff", "--no-ext-diff", "--name-status", "--no-renames", "-z",
            f"{base}...{head}", "--",
        ],
        capture_output=True,
        check=True,
        timeout=20,
    ).stdout
    # With renames disabled, Git emits exactly one status and one path per record.
    *fields, end = diff.split(b"\0")
    if end or len(fields) % 2 or not all(fields):
        raise ValueError("Malformed Git diff")
    return [
        (status, path.decode("utf-8", errors="surrogateescape"))
        for status, path in zip(fields[::2], fields[1::2])
    ]


def docs_markdown(path: str) -> bool:
    return path.startswith("docs/") and path.endswith(".md")


def declarations(body: str) -> Iterator[str]:
    in_comment = False
    fence = ""
    for line in re.split(r"\r\n?|\n", body):
        marker = FENCE.fullmatch(line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
            continue
        if not in_comment and marker and (marker[1][0] == "~" or "`" not in marker[2]):
            fence = marker[1]
            continue

        visible = ""
        while line:
            if in_comment:
                _, close, line = line.partition("-->")
                if not close:
                    break
                in_comment = False
            else:
                text, start, line = line.partition("<!--")
                visible += text
                in_comment = bool(start)
        if DOCS_LINE.match(visible):
            yield visible.strip()


def split_declarations(body: str) -> tuple[list[str], set[str], str | None]:
    """General lines, the rules given their own reason, and any scoping error."""
    general, scoped = [], set()
    for line in declarations(body):
        match = SCOPED.fullmatch(line)
        if not match:
            general.append(line)
            continue
        name, reason = match[1].strip(), match[2].strip()
        if name not in RULES or re.fullmatch(r"<[^<>]*>", reason):
            return general, scoped, f"Use 'Docs: no impact (<rule>) — reason' with a rule from: {', '.join(RULES)}."
        if name in scoped:
            return general, scoped, f"Give the {name} reason once."
        scoped.add(name)
    return general, scoped, None


def finding(body: str, changes: list[tuple[bytes, str]]) -> str | None:
    lines, scoped, error = split_declarations(body)
    if error:
        return error
    if not lines and scoped:
        return None
    if not lines:
        return "Add one plain Docs: line with 'updated' or 'no impact' followed by an em dash and details."
    if len(lines) != 1:
        return "Keep exactly one plain Docs: declaration."

    disposition, _, details = lines[0].partition(" — ")
    details = details.strip()
    if disposition == "Docs: no impact" and details and not re.fullmatch(r"<[^<>]*>", details):
        return None
    if disposition == "Docs: updated" and details:
        eligible = {
            path for status, path in changes
            if status in (b"A", b"M")
            and (path == "README.md" or (docs_markdown(path) and not path.startswith(NON_PROOF_PREFIXES)))
        }
        if all(path.strip() in eligible for path in details.split(",")):
            return None
        return "List only added or modified maintained docs in Docs: updated, separated by commas."
    return "Use 'Docs: updated' or 'Docs: no impact' followed by an em dash and changed doc paths or a specific reason."


def main() -> int:
    parser = ArgumentParser(prog="docs_impact.py", description=__doc__, allow_abbrev=False)
    parser.add_argument("event_path", type=Path)
    parser.add_argument("--advisory", action="store_true")
    args = parser.parse_args()

    try:
        base, head, body = read_event(args.event_path)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print("Docs impact: expected a readable UTF-8 PR event with commit IDs and a string or null body.", file=sys.stderr)
        return 2
    event = json.loads(args.event_path.read_text(encoding="utf-8"))
    try:
        reason = routine(event["pull_request"], event["repository"]["full_name"])
    except (KeyError, TypeError):
        reason = None
    if reason:
        print(f"Docs impact: not applicable ({reason}).")
        return 0
    try:
        changes = changed_paths(base, head)
        rules = load_rules(base)
        missing = list(unmet_rules(rules, base, changes, split_declarations(body)[1]))
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, AttributeError, re.error):
        print("Docs impact: could not read the PR diff. Check Git and ensure both commits and their history are available.", file=sys.stderr)
        return 2

    if all(path in DOCS_ONLY_FILES or docs_markdown(path) for _, path in changes):
        print("Docs impact: not applicable (no non-docs changes).")
        return 0
    errors, warnings = [], []
    message = finding(body, changes)
    if message:
        errors.append(message)
    for name, rule, path in missing:
        text = (
            f"{path} looks like a {name} change. Update {rule['doc']}, or add "
            f"'Docs: no impact ({name}) — reason' to the PR description."
        )
        (errors if rule["block"] else warnings).append(text)
    if args.advisory:
        warnings, errors = errors + warnings, []

    for text in warnings:
        print(f"::warning::Docs impact: {text}")
    for text in errors:
        print(f"Docs impact: {text}", file=sys.stderr)
    if errors:
        return 1
    if not message:
        print("Docs impact: declaration accepted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
