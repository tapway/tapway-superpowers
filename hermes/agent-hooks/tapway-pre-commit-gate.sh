#!/usr/bin/env bash
# Hermes shell hook — pre_tool_call blocker for `git commit` quality gate.
# Spawned by Hermes when the `terminal` tool runs; receives JSON on stdin,
# returns {"decision":"block", "reason": "..."} on stdout to veto the commit.
#
# READ stdin JSON: {"hook_event_name":"pre_tool_call","tool_name":"terminal",
#                   "tool_input":{"command":"git commit -m ..."}, ...}

payload="$(cat -)"
cmd=$(printf '%s' "$payload" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only gate `git commit` invocations
case "$cmd" in
  git\ commit*|git\ cm*) ;;
  *) printf '{}\n'; exit 0 ;;
esac

# --- Same checks as hooks/pre-commit-gate.sh (Claude Code side) ---
FAILED=0
CHANGED=$(git diff --cached --name-only 2>/dev/null)

HAS_BACKEND=0; HAS_FRONTEND=0
[ -d backend ] || [ -f pyproject.toml ] || [ -f requirements.txt ] && HAS_BACKEND=1
[ -d frontend ] || [ -f package.json ] && HAS_FRONTEND=1
for f in $CHANGED; do
  case "$f" in
    *.py|*backend*|*api*) HAS_BACKEND=1 ;;
    *.tsx|*.ts|*.jsx|*.js|*frontend*) HAS_FRONTEND=1 ;;
  esac
done

if [ "$HAS_BACKEND" = "1" ] && command -v ruff >/dev/null 2>&1; then
  (cd backend 2>/dev/null && ruff check . && ruff format --check .) || FAILED=1
fi
if [ "$HAS_BACKEND" = "1" ] && command -v pytest >/dev/null 2>&1; then
  (cd backend 2>/dev/null && pytest -q) || FAILED=1
fi
if [ "$HAS_FRONTEND" = "1" ] && [ -f frontend/package.json ] && command -v npx >/dev/null 2>&1; then
  (cd frontend 2>/dev/null && npm run lint && npx tsc --noEmit) || FAILED=1
fi

if [ "$FAILED" = "1" ]; then
  printf '{"decision":"block","reason":"Pre-commit quality gate failed - run lint/format/typecheck/tests, fix issues, then re-commit"}\n'
  exit 0
fi

printf '{}\n'
exit 0