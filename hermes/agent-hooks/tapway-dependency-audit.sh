#!/usr/bin/env bash
# Hermes shell hook — pre_tool_call dependency audit for `git commit`.
# Spawned by Hermes on `terminal` tool calls; returns a JSON block decision on
# stdout if critical/high vulnerabilities are found in lockfiles.
#
# READ stdin JSON: {"tool_input":{"command":"git commit ..."}, ...}

payload="$(cat -)"
cmd=$(printf '%s' "$payload" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$cmd" in
  git\ commit*|git\ cm*) ;;
  *) printf '{}\n'; exit 0 ;;
esac

FAILED=0
LOCKFILES=$(git ls-files 2>/dev/null | grep -E "\.lock$|package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|poetry\.lock$|Pipfile\.lock$|uv\.lock$|go\.sum$|Cargo\.lock$")

# Python
if echo "$LOCKFILES" | grep -qE "requirements.*\.txt$|pyproject\.toml$|poetry\.lock$|uv\.lock$" && command -v pip-audit >/dev/null 2>&1; then
  pip-audit 2>/dev/null | grep -qiE "critical|high" && FAILED=1
fi

# Node
if echo "$LOCKFILES" | grep -qE "package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$" && [ -f package.json ] && command -v npm >/dev/null 2>&1; then
  npm audit --audit-level=high 2>/dev/null | grep -qi "severity: high\|severity: critical" && FAILED=1
fi

# osv-scanner (all ecosystems)
if command -v osv-scanner >/dev/null 2>&1 && [ -n "$LOCKFILES" ]; then
  osv-scanner --format json . 2>/dev/null | grep -qi '"isVulnerable": true' && FAILED=1
fi

if [ "$FAILED" = "1" ]; then
  printf '{"decision":"block","reason":"Dependency audit found critical/high vulnerabilities - run osv-scanner / npm audit fix / pip-audit fix, then re-commit"}\n'
  exit 0
fi

printf '{}\n'
exit 0