#!/usr/bin/env bash
# check-release-drift.sh — the marketplace manifests must match the latest release.
#
#   bash scripts/check-release-drift.sh              # repo from origin
#   bash scripts/check-release-drift.sh tapway/tapway-superpowers
#
# `claude plugin update` reads the version in .claude-plugin/*.json and
# hermes/plugin/plugin.yaml, not git tags. The Auto Release workflow writes those
# files after tagging; when that write silently failed (bot push rejected by the
# branch ruleset, step marked continue-on-error) the tags ran ahead and every
# client kept seeing the old version. Nothing detected it. This does.
#
# Exit 0 = GREEN, 1 = RED.
set -uo pipefail

REPO="${1:-}"
exec python3 - "$REPO" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

fail = 0


def ok(msg):
    print(f"PASS  {msg}")


def bad(msg):
    global fail
    print(f"FAIL  {msg}")
    fail = 1


def sh(args):
    p = subprocess.run(args, capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def repo_from_git():
    out = sh(["git", "remote", "get-url", "origin"]).strip()
    m = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", out)
    return m.group(1) if m else ""


def vkey(tag):
    core = tag.lstrip("v").split("-", 1)[0]
    return tuple(int(p) for p in core.split("."))


repo = sys.argv[1] or repo_from_git()
print(f"== release drift: {repo or '(local)'} ==")

names = []
for line in sh(["git", "ls-remote", "--tags", "--refs", "origin"]).splitlines():
    if "refs/tags/" in line:
        names.append(line.rsplit("refs/tags/", 1)[1])
if not names:
    names = sh(["git", "tag", "-l"]).splitlines()
# Production releases are `-prod`; tags cut before the suffix convention are
# plain `vX.Y.Z`. Accept both, newest core wins, so the first -prod release
# supersedes the legacy line without making the check flap during transition.
prod = [n for n in names if re.fullmatch(r"v\d+\.\d+\.\d+(?:-prod)?", n)]
if not prod:
    bad("no production release tag found (vX.Y.Z-prod)")
    print("== RED ==")
    raise SystemExit(1)
latest = max(prod, key=vkey)
expected = latest.lstrip("v")
ok(f"latest production tag is {latest}")

root = Path.cwd()
yaml_path = root / "hermes" / "plugin" / "plugin.yaml"
plugin_path = root / ".claude-plugin" / "plugin.json"
market_path = root / ".claude-plugin" / "marketplace.json"

found = {}
m = re.search(r"^version:\s*(\S+)", yaml_path.read_text(encoding="utf-8"), re.MULTILINE) \
    if yaml_path.is_file() else None
found["hermes/plugin/plugin.yaml"] = m.group(1) if m else "(missing)"

def jget(path, *keys):
    if not path.is_file():
        return "(missing)"
    data = json.loads(path.read_text(encoding="utf-8"))
    for k in keys:
        if isinstance(k, int):
            data = data[k]
        else:
            data = data.get(k)
        if data is None:
            return "(missing)"
    return str(data)


found[".claude-plugin/plugin.json"] = jget(plugin_path, "version")
found[".claude-plugin/marketplace.json (metadata)"] = jget(market_path, "metadata", "version")
found[".claude-plugin/marketplace.json (plugins[0])"] = jget(market_path, "plugins", 0, "version")
changelog = root / "CHANGELOG.md"
m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog.read_text(encoding="utf-8"), re.MULTILINE) \
    if changelog.is_file() else None
found["CHANGELOG.md (top released heading)"] = m.group(1) if m else "(no released heading)"

for surface, version in found.items():
    if version == expected:
        ok(f"{surface} = {version}")
    else:
        bad(f"{surface} = {version} (want {expected})")

if fail:
    print("\nFix: merge the open `chore(release): sync plugin manifests` PR, or run")
    print("     `bash scripts/next_version.sh -prod` + update all five fields in one PR.")
print(f"== {'GREEN' if fail == 0 else 'RED'} ==")
raise SystemExit(1 if fail else 0)
PY