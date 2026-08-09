#!/bin/bash
# Platform-agnostic git pre-commit backstop — blocks commits from ANY agent or
# human when quality gates fail. This is the safety net beneath the agent-native
# hooks (Claude PreToolUse exit-2 / Hermes shell hooks).
#
# NOTE: git hooks block with exit 1 (unlike Claude Code's exit 2). Exit 1 here
# is correct and expected — git treats any non-zero exit as "reject the commit".
#
# Installed by setup-project / install.sh into .git/hooks/pre-commit:
#   ln -sf ../../hooks/pre-commit/git-pre-commit.sh .git/hooks/pre-commit
#   chmod +x hooks/pre-commit/git-pre-commit.sh

# Only run on staged changes of code files (skip docs/config-only commits)
STAGED=$(git diff --cached --name-only)
[ -z "$STAGED" ] && exit 0

HAS_CODE=0
for f in $STAGED; do
  case "$f" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.css|*.scss) HAS_CODE=1 ;;
  esac
done
[ "$HAS_CODE" = "0" ] && exit 0

echo "→ git pre-commit backstop: running quality checks"

# Lint & format (ruff for Python, eslint/prettier for JS/TS)
if command -v ruff >/dev/null 2>&1; then
  ruff check . || { echo "❌ git pre-commit: ruff lint failed" >&2; exit 1; }
  ruff format --check . 2>/dev/null || { echo "❌ git pre-commit: ruff format failed" >&2; exit 1; }
fi

if [ -f package.json ] && command -v npx >/dev/null 2>&1; then
  npx eslint . --quiet 2>/dev/null || { echo "❌ git pre-commit: eslint failed" >&2; exit 1; }
fi

# Typecheck
if [ -f tsconfig.json ] && command -v npx >/dev/null 2>&1; then
  npx tsc --noEmit 2>/dev/null || { echo "❌ git pre-commit: tsc failed" >&2; exit 1; }
fi

echo "✅ git pre-commit backstop passed."
exit 0