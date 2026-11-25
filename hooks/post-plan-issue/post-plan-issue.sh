#!/usr/bin/env bash
# post-plan-issue.sh — create the GitHub issue the moment a plan is written.
#
# PostToolUse on Write|Edit|MultiEdit. It never blocks the write (PostToolUse
# cannot), and it never fails the tool call: any error is reported on stderr and
# the edit stands. The PR-side contract gate is the backstop if this cannot run.
#
#   docs/plans/*.md  →  gh issue create --label codemax  →  `issue: <n>` written
#                       back into the plan frontmatter
#   docs/brainstorming/*.md  →  same, but only when frontmatter says status:
#                               accepted (or approved); drafts stay silent.
#
# Off switch: TAPWAY_ISSUE_AUTOCREATE=0. It only runs in a CodeMAX repo
# (CODEMAX_ENABLED/CODEMAX_WORKFLOW=1, or a .codemax.yml in the repo root).

set -uo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
HOOK_LIB="$ROOT/hooks/lib"
# shellcheck source=../lib/hook_payload.sh
[ -f "$HOOK_LIB/hook_payload.sh" ] && . "$HOOK_LIB/hook_payload.sh"

payload="$(cat | normalize_payload)"

FILE_PATH="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin).get("tool_input", {}) or {}
except Exception:
    data = {}
print(data.get("file_path") or data.get("path") or data.get("filename") or "")
' 2>/dev/null)"

[ -n "$FILE_PATH" ] || exit 0
# Windows harnesses send backslash paths; route on a forward-slash copy.
case "${FILE_PATH//\\//}" in
  *docs/plans/*.md) ;;
  *docs/brainstorming/*.md) ;;
  *) exit 0 ;;
esac
[ "${TAPWAY_ISSUE_AUTOCREATE:-1}" = "1" ] || exit 0

# The payload path is usually relative to the project root; resolve it before
# handing it to the renderer.
if [ ! -f "$FILE_PATH" ]; then
  TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$TOP" ] && [ -f "$TOP/$FILE_PATH" ] && FILE_PATH="$TOP/$FILE_PATH"
fi
[ -f "$FILE_PATH" ] || exit 0

if ! command -v gh >/dev/null 2>&1; then
  echo "tapway-superpowers: gh CLI not found — skipped issue creation for $FILE_PATH" >&2
  exit 0
fi

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 - "$FILE_PATH" <<'PY' || true
import sys

from hermes.plugin.plan_issue import handle_plan_write

result = handle_plan_write(sys.argv[1])
if result.message:
    print(f"tapway-superpowers: {result.message}")
if result.error:
    print(f"tapway-superpowers: issue not created — {result.error}", file=sys.stderr)
PY

exit 0