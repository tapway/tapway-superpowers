#!/bin/bash
# Pre-commit quality gate — blocks commits when lint / format / typecheck /
# coverage fail. Uses exit 2 so Claude Code BLOCKS the commit tool call
# (exit 1 is treated as a non-blocking error and would let the commit through).
#
# Detection: only runs checks relevant to the project's stack, so a backend-only
# repo doesn't run Node checks (and vice versa). Failures anywhere → exit 2.

CHANGED=$(git diff --cached --name-only 2>/dev/null)

# --- Detect stack from staged files / project layout (no assumptions) ---
HAS_BACKEND=0
HAS_FRONTEND=0
if [ -d backend ] || [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  HAS_BACKEND=1
fi
if [ -d frontend ] || [ -f package.json ]; then
  HAS_FRONTEND=1
fi
for f in $CHANGED; do
  case "$f" in
    *.py|**/backend/**|**/api/**) HAS_BACKEND=1 ;;
    *.tsx|*.ts|*.jsx|*.js|*.css|*.scss|**/frontend/**) HAS_FRONTEND=1 ;;
  esac
done

FAILED=0

echo "→ Running pre-commit quality gate..."

# --- Backend: ruff lint + format, mypy typecheck, pytest-cov ---
if [ "$HAS_BACKEND" = "1" ]; then
  cd backend 2>/dev/null || cd . 2>/dev/null

  if command -v ruff >/dev/null 2>&1; then
    echo "→ backend lint (ruff)"
    ruff check . || { echo "❌ Lint failed"; FAILED=1; }
    ruff format --check . || { echo "❌ Format check failed"; FAILED=1; }
  fi

  if command -v mypy >/dev/null 2>&1; then
    echo "→ backend typecheck (mypy)"
    mypy src/ --ignore-missing-imports || { echo "❌ Typecheck failed"; FAILED=1; }
  fi

  if command -v pytest >/dev/null 2>&1; then
    echo "→ backend coverage gate (pytest-cov)"
    if grep -q "cov-fail-under" pyproject.toml 2>/dev/null; then
      pytest --cov=src --cov-report=term-missing -q || { echo "❌ Tests/coverage failed"; FAILED=1; }
    else
      pytest -q || { echo "❌ Tests failed"; FAILED=1; }
    fi
  fi

  cd - >/dev/null 2>&1 || true
fi

# --- Frontend: lint, prettier, tsc strict, coverage ---
if [ "$HAS_FRONTEND" = "1" ] && [ -f frontend/package.json ]; then
  cd frontend || exit 0

  if [ -f package-lock.json ]; then
    echo "→ frontend lint + typecheck + test"
    npm run lint || { echo "❌ Frontend lint failed"; FAILED=1; }
    npx prettier --check . || { echo "❌ Frontend format failed"; FAILED=1; }
    npx tsc --noEmit || { echo "❌ Frontend typecheck failed"; FAILED=1; }
    npm test -- --coverage --watchAll=false || { echo "❌ Frontend tests failed"; FAILED=1; }
  fi

  cd - >/dev/null 2>&1 || true
fi

# --- Result ---
if [ "$FAILED" = "1" ]; then
  echo "❌ Pre-commit quality gate FAILED — commit blocked." >&2
  echo "   Fix the failures above, stage the fixes, and re-commit." >&2
  exit 2   # BLOCK (Claude Code: exit 2 blocks the tool call)
fi

echo "✅ Pre-commit quality gate passed."
exit 0