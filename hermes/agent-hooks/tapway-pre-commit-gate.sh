#!/usr/bin/env bash
# Hermes shell hook — pre_tool_call blocker for `git commit` quality gate.
# Spawned by Hermes when the `terminal` tool runs; receives JSON on stdin,
# returns {"decision":"block", "reason": "..."} on stdout to veto the commit.
#
# READ stdin JSON: {"hook_event_name":"pre_tool_call","tool_name":"terminal",
#                   "tool_input":{"command":"git commit -m ..."}, ...}

payload="$(cat -)"
# Extract the command from stdin JSON. Prefer jq (lighter, more likely installed);
# fall back to python3 if jq is unavailable.
if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1; then
  cmd=$(printf '%s' "$payload" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
else
  # No JSON parser available — can't inspect the command, so allow (don't block blindly)
  printf '{}\n'
  exit 0
fi

# Only gate `git commit` invocations
case "$cmd" in
  git\ commit*|git\ cm*) ;;
  *) printf '{}\n'; exit 0 ;;
esac

# --- Same checks as hooks/pre-commit-gate.sh (Claude Code side) ---
FAILED=0
CHANGED=$(git diff --cached --name-only 2>/dev/null)

HAS_BACKEND=0; HAS_FRONTEND=0
# Fix: use separate if statements (&&/|| precedence bug: A || B || C && D
# parses as A || B || (C && D), so if A is true, D is never set)
if [ -d backend ] || [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  HAS_BACKEND=1
fi
if [ -d frontend ] || [ -f package.json ]; then
  HAS_FRONTEND=1
fi
for f in $CHANGED; do
  case "$f" in
    *.py|*backend*|*api*) HAS_BACKEND=1 ;;
    *.tsx|*.ts|*.jsx|*.js|*frontend*) HAS_FRONTEND=1 ;;
  esac
done

BACKEND_DIR="."
[ -d backend ] && BACKEND_DIR="backend"

if [ "$HAS_BACKEND" = "1" ] && command -v ruff >/dev/null 2>&1; then
  (cd "$BACKEND_DIR" 2>/dev/null && ruff check . && ruff format --check .) || FAILED=1
fi
if [ "$HAS_BACKEND" = "1" ] && command -v mypy >/dev/null 2>&1 && [ -d "$BACKEND_DIR/src" ]; then
  (cd "$BACKEND_DIR" 2>/dev/null && mypy src/ --ignore-missing-imports) || FAILED=1
fi
if [ "$HAS_BACKEND" = "1" ] && command -v pytest >/dev/null 2>&1; then
  if [ -d "$BACKEND_DIR/tests" ] || [ -n "$(find "$BACKEND_DIR" -maxdepth 3 -name 'test_*.py' -print -quit 2>/dev/null)" ]; then
    (cd "$BACKEND_DIR" 2>/dev/null && pytest -q) || FAILED=1
  fi
fi
if [ "$HAS_FRONTEND" = "1" ] && [ -d frontend ] && [ -f frontend/package.json ] && command -v npx >/dev/null 2>&1; then
  (cd frontend 2>/dev/null && npm run lint && npx tsc --noEmit) || FAILED=1
fi

if [ "$FAILED" = "1" ]; then
  printf '{"decision":"block","reason":"Pre-commit quality gate failed - run lint/format/typecheck/tests, fix issues, then re-commit"}\n'
  exit 0
fi

printf '{}\n'
exit 0