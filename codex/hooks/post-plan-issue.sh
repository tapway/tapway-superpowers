#!/bin/bash
# post-plan-issue.sh (Codex port) — create the GitHub issue after a plan write.
#
# Codex installs hooks one file at a time, so this hook ships its own copy of the
# renderer next to it (.codex/hooks/plan_issue.py, copied from
# hermes/plugin/plan_issue.py by codex/install.sh). Self-contained otherwise:
# no hooks/lib, no scripts/.
#
# Never blocks: PostToolUse cannot deny, and a failure here must not fail the
# edit. The PR contract gate is the backstop.

set -uo pipefail

INPUT="$(cat)"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ "${TAPWAY_ISSUE_AUTOCREATE:-1}" = "1" ] || exit 0

FILE_PATH="$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    raw = json.load(sys.stdin)
except Exception:
    raw = {}
tool_input = raw.get("tool_input") if isinstance(raw.get("tool_input"), dict) else {}
print(tool_input.get("file_path") or tool_input.get("path") or raw.get("file_path") or raw.get("path") or "")
' 2>/dev/null)"

[ -n "$FILE_PATH" ] || exit 0
case "$FILE_PATH" in
  *docs/plans/*.md) ;;
  *) exit 0 ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$TOP" ] && [ -f "$TOP/$FILE_PATH" ] && FILE_PATH="$TOP/$FILE_PATH"
fi
[ -f "$FILE_PATH" ] || exit 0

if ! command -v gh >/dev/null 2>&1; then
  echo "tapway-superpowers: gh CLI not found — skipped issue creation" >&2
  exit 0
fi

python3 - "$HOOK_DIR" "$FILE_PATH" <<'PY' || true
import sys

sys.path.insert(0, sys.argv[1])
from plan_issue import handle_plan_write  # noqa: E402

result = handle_plan_write(sys.argv[2])
if result.message:
    print(f"tapway-superpowers: {result.message}")
if result.error:
    print(f"tapway-superpowers: issue not created — {result.error}", file=sys.stderr)
PY

exit 0