#!/bin/bash
# PreToolUse entry point for tool_guard.py. Claude Code sends the tool call as
# JSON on stdin; it reaches the script unchanged. Fails closed: Claude Code
# only blocks on exit 2 and treats any other failure as "carry on", so a
# missing python3 or a crashed interpreter must be turned into exit 2 here.
if ! command -v python3 >/dev/null 2>&1; then
  echo "Blocked by tool-guard: python3 is required (hooks/tool-guard/tool_guard.py)" >&2
  exit 2
fi
python3 "$(dirname "$0")/tool_guard.py"
rc=$?
if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  echo "Blocked by tool-guard: the guard failed (exit $rc); refusing to run unguarded" >&2
  exit 2
fi
exit "$rc"
