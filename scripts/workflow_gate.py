#!/usr/bin/env python3
"""CI/pre-PR contract gate (B4/B5/B10).

Checks only the documents a change touches:

- ``docs/plans/*.md`` must carry ``issue: <number>`` in frontmatter (C2).
- ``docs/brainstorming/*.md`` must ground every option section (C1).

Exit 1 with one line per finding; exit 0 when clean. No network, no gbrain —
the authoritative citation check stays in CodeMAX CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hermes.plugin.gates import check_doc  # noqa: E402

ISSUE_RE = re.compile(r"^issue:\s*(\d+)\s*$", re.MULTILINE)


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def check_file(path: str, text: str) -> list[str]:
    if path.startswith("docs/plans/"):
        if not ISSUE_RE.search(frontmatter(text)):
            return [f"{path}: plan has no 'issue: <number>' frontmatter (create the GitHub issue first)"]
        return []
    if path.startswith("docs/brainstorming/"):
        return [f"{path}: {finding}" for finding in check_doc(path, text)]
    return []


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        print("usage: workflow_gate.py <file> [file ...]", file=sys.stderr)
        return 2

    findings: list[str] = []
    for raw in paths:
        path = raw.strip()
        if not path or not path.endswith(".md"):
            continue
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError:
            continue
        findings.extend(check_file(path.replace("\\", "/"), text))

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))