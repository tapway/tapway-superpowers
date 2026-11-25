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


def finding(body: str, changes: list[tuple[bytes, str]]) -> str | None:
    lines = list(declarations(body))
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
    try:
        changes = changed_paths(base, head)
    except (OSError, subprocess.SubprocessError, ValueError):
        print("Docs impact: could not read the PR diff. Check Git and ensure both commits and their history are available.", file=sys.stderr)
        return 2

    if all(path in DOCS_ONLY_FILES or docs_markdown(path) for _, path in changes):
        print("Docs impact: not applicable (no non-docs changes).")
        return 0
    message = finding(body, changes)
    if message is None:
        print("Docs impact: declaration accepted.")
        return 0
    if args.advisory:
        print(f"::warning::Docs impact: {message}")
        return 0
    print(f"Docs impact: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
