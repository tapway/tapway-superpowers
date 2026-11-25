#!/usr/bin/env python3
"""Extract the POST-write text from a shell command (heredoc / echo redirect).

Usage: extract-post-text.py <command-string on stdin>
Prints the extracted document text (empty if none found).
"""
import re
import sys


def extract(cmd: str) -> str:
    m = re.search(
        r">\s*([\"\']?)([A-Za-z0-9._/-]*docs/brainstorming/[A-Za-z0-9._/-]+\.md)\1"
        r"\s*<<\s*([\"\']?)(\w+)\3\s*\n(.*)\n?\4\s*$",
        cmd,
        re.S,
    )
    if m:
        return m.group(5)
    m = re.search(
        r"(?:echo|printf)(?:\s+-[eE])?\s+([\"\'])(.*?)\1\s*>\s*"
        r"([A-Za-z0-9._/-]*docs/brainstorming/[A-Za-z0-9._/-]+\.md)",
        cmd,
        re.S,
    )
    if m:
        return m.group(2)
    return ""


if __name__ == "__main__":
    sys.stdout.write(extract(sys.stdin.read()))
