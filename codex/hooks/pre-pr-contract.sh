#!/usr/bin/env bash
# pre-pr-contract.sh (Codex) — block `gh pr create` when the branch's docs break
# the contracts. Self-contained: Codex installs hooks one file at a time, so it
# cannot rely on hooks/lib/ or scripts/workflow_gate.py being present.
#
#   C1  docs/brainstorming/*.md — every option section cites the brain.
#   C2  docs/plans/*.md        — frontmatter carries `issue: <number>`.
#
# Output: {"decision":"block","reason":"…"} or {}.

set -uo pipefail

payload="$(cat)"
python3 - "$payload" <<'PY'
import json
import os
import re
import subprocess
import sys

try:
    data = json.loads(sys.argv[1])
except (json.JSONDecodeError, IndexError):
    print("{}")
    raise SystemExit(0)

tool_input = data.get("tool_input")
if not isinstance(tool_input, dict):
    tool_input = data.get("args") if isinstance(data.get("args"), dict) else data
command = str(tool_input.get("command") or "")
if "gh pr create" not in command:
    print("{}")
    raise SystemExit(0)
if os.environ.get("TAPWAY_PR_GATE", "1") != "1":
    print("{}")
    raise SystemExit(0)

base = os.environ.get("TAPWAY_PR_BASE", "origin/staging")
diff = subprocess.run(
    ["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True
)
if diff.returncode != 0:
    print("{}")
    raise SystemExit(0)

OPTION_RE = re.compile(r"^#{2,3}\s+(?:Option|Approach|Alternative|Proposal)\b.*$", re.MULTILINE | re.IGNORECASE)
GROUNDING_RE = re.compile(r"Grounding:\s*\S|UNKNOWN \(not retrieved", re.IGNORECASE)
ISSUE_RE = re.compile(r"^issue:\s*(\d+)\s*$", re.MULTILINE)

findings = []
for path in [line.strip() for line in diff.stdout.splitlines() if line.strip().endswith(".md")]:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        continue
    if path.startswith("docs/plans/"):
        frontmatter = ""
        if text.startswith("---"):
            end = text.find("\n---", 3)
            frontmatter = text[3:end] if end != -1 else ""
        if not ISSUE_RE.search(frontmatter):
            findings.append(f"{path}: plan has no 'issue: <number>' frontmatter")
    elif path.startswith("docs/brainstorming/"):
        options = list(OPTION_RE.finditer(text))
        if not options:
            findings.append(f"{path}: no option section — a brainstorm needs at least one")
            continue
        for index, match in enumerate(options):
            end = options[index + 1].start() if index + 1 < len(options) else len(text)
            if not GROUNDING_RE.search(text[match.end() : end]):
                findings.append(f"{path}: {match.group(0).strip()} has no 'Grounding:' line")

if findings:
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": "tapway-superpowers refused `gh pr create`: "
                + "; ".join(findings[:5])
                + " — fix the docs, or set TAPWAY_PR_GATE=0 for one run.",
            }
        )
    )
else:
    print("{}")
PY