#!/usr/bin/env python3
"""Write descriptive release notes from the descriptions of the merged PRs.

    python3 release_notes.py --tag v1.2.0-prod --previous v1.1.0-prod > notes.md

GitHub's generated notes decide WHICH pull requests are in the release; each one
is then described by its own "## Release note" section, falling back to
"## Summary", "## Problem" or the first paragraph. Needs GH_TOKEN and
GITHUB_REPOSITORY. Reading PR descriptions in a private repo needs
`pull-requests: read`; without it the notes carry titles only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

MAX_FALLBACK_CHARS = 400
MAX_BULLETS = 5
PR_LINE = re.compile(r"^\* (.+) by @(\S+) in https://\S+/pull/(\d+)\s*$", re.M)
TITLE = re.compile(r"^(\w+)(?:\(([^)]*)\))?(!)?:\s*(.+)$")
SKIPPED_TITLES = ("chore(release)", "chore(staging)")
GROUPS = ("Breaking changes", "Features", "Fixes", "Other changes")


def _sections(body):
    parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.M)
    named = {parts[i].lower().rstrip("s"): parts[i + 1] for i in range(1, len(parts), 2)}
    return parts[0], named


def _blocks(text):
    """Prose paragraphs (joined to one line) and bullets; everything else dropped."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    blocks = []
    for para in re.split(r"\n\s*\n", text.strip()):
        lines = [
            line.strip()
            for line in para.split("\n")
            if line.strip() and not line.strip().startswith(("Docs:", "\U0001F916", "|", "#", "- [", "---"))
        ]
        if not lines:
            continue
        if lines[0].startswith(("- ", "* ")):
            blocks += ["- " + line[2:] for line in lines if line.startswith(("- ", "* "))]
        else:
            blocks.append(" ".join(lines))
    return blocks


def _truncate(text):
    if len(text) <= MAX_FALLBACK_CHARS:
        return text
    return text[:MAX_FALLBACK_CHARS].rsplit(" ", 1)[0] + "…"


def describe(body):
    """The lines that explain one PR to a reader of the release."""
    body = re.sub(r"<!--.*?-->", "", (body or "").replace("\r", ""), flags=re.S)
    preamble, named = _sections(body)

    written = _blocks(named.get("release note", ""))
    if written:
        return [] if written[0].strip(" .").lower() in ("none", "n/a") else written

    for text in (named.get("summary", ""), named.get("problem", ""), preamble):
        blocks = _blocks(text)
        if not blocks:
            continue
        if blocks[0].startswith("- "):
            return [_truncate(b) for b in blocks[:MAX_BULLETS] if b.startswith("- ")]
        return [_truncate(blocks[0])]
    return []


def _quiet(text):
    """Backtick @names so release notes never notify anyone."""
    return re.sub(r"(?<![\w`/])@([A-Za-z0-9][\w./-]*[\w-]|[A-Za-z0-9])", r"`@\1`", text)


def build_notes(generated, fetch_body):
    """Turn GitHub's generated notes into grouped, described notes."""
    groups = {name: [] for name in GROUPS}
    for title, author, number in PR_LINE.findall(generated):
        if title.startswith(SKIPPED_TITLES):
            continue
        match = TITLE.match(title)
        kind, scope, breaking, subject = match.groups() if match else ("", None, None, title)
        if breaking:
            group = "Breaking changes"
        else:
            group = {"feat": "Features", "fix": "Fixes"}.get(kind, "Other changes")

        heading = f"**{scope}:** {subject}" if scope else subject
        by = "" if author.endswith("[bot]") else f", by `@{author}`"
        entry = [f"- {_quiet(heading)} (#{number}{by})"]
        try:
            entry += ["  " + _quiet(line) for line in describe(fetch_body(int(number)))]
        except Exception as error:  # one unreadable PR must not lose the release notes
            print(f"::warning::no description for #{number}: {error}", file=sys.stderr)
        groups[group].append("\n".join(entry))

    out = [f"## {name}\n\n" + "\n".join(items) for name, items in groups.items() if items]
    if not out:
        out = ["No user-facing changes."]
    compare = re.search(r"^\*\*Full Changelog\*\*.*$", generated, flags=re.M)
    if compare:
        out.append(compare.group(0))
    return "\n\n".join(out) + "\n"


def _gh_json(*args):
    result = subprocess.run(["gh", "api", *args], capture_output=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "gh api failed")
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tag", required=True, help="the tag being released")
    parser.add_argument("--previous", help="previous tag of the same stream")
    args = parser.parse_args()
    repo = os.environ["GITHUB_REPOSITORY"]

    request = [f"repos/{repo}/releases/generate-notes", "-f", f"tag_name={args.tag}"]
    if args.previous:
        request += ["-f", f"previous_tag_name={args.previous}"]
    generated = _gh_json(*request)["body"]

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(build_notes(generated, lambda n: _gh_json(f"repos/{repo}/pulls/{n}")["body"]))


if __name__ == "__main__":
    main()
