#!/bin/bash
# Pre-commit quality gate — blocks commits when lint / format / typecheck /
# coverage fail. Uses exit 2 so Codex BLOCKS the commit tool call.
# Codex sends the Bash payload as JSON on stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

echo "$COMMAND" | grep -qE "git commit" || exit 0

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

# --- Backend: ruff lint + format, mypy typecheck, pytest ---
if [ "$HAS_BACKEND" = "1" ]; then
  BACKEND_DIR="."
  if [ -d backend ]; then
    BACKEND_DIR="backend"
  fi
  cd "$BACKEND_DIR" 2>/dev/null || true

  if command -v ruff >/dev/null 2>&1; then
    echo "→ backend lint (ruff)"
    ruff check . || { echo "❌ Lint failed"; FAILED=1; }
    ruff format --check . || { echo "❌ Format check failed"; FAILED=1; }
  fi

  if command -v mypy >/dev/null 2>&1 && [ -d src ]; then
    echo "→ backend typecheck (mypy)"
    mypy src/ --ignore-missing-imports || { echo "❌ Typecheck failed"; FAILED=1; }
  elif command -v mypy >/dev/null 2>&1 && [ -n "$(find . -maxdepth 2 -name '*.py' -print -quit 2>/dev/null)" ]; then
    echo "→ backend typecheck (mypy, no src/ — scanning root)"
    mypy . --ignore-missing-imports || { echo "❌ Typecheck failed"; FAILED=1; }
  fi

  if command -v pytest >/dev/null 2>&1; then
    echo "→ backend tests (pytest)"
    # Detect coverage config either via addopts --cov-fail-under OR [tool.coverage] fail_under
    if grep -qE "cov-fail-under|fail_under" pyproject.toml 2>/dev/null; then
      pytest --cov=src --cov-report=term-missing -q || { echo "❌ Tests/coverage failed"; FAILED=1; }
    else
      if [ -d tests ] || [ -n "$(find . -maxdepth 3 -name 'test_*.py' -o -name '*_test.py' -print -quit 2>/dev/null)" ]; then
        pytest -q || { echo "❌ Tests failed"; FAILED=1; }
      else
        echo "→ No test directory found — skipping pytest"
      fi
    fi
  fi

  cd - >/dev/null 2>&1 || true
fi

# --- Frontend: lint, prettier, tsc strict, test ---
if [ "$HAS_FRONTEND" = "1" ] && [ -d frontend ] && [ -f frontend/package.json ]; then
  (
    cd frontend 2>/dev/null || exit 0
    if [ -f package-lock.json ]; then
      echo "→ frontend lint + typecheck + test"
      npm run lint || { echo "❌ Frontend lint failed"; exit 1; }
      npx prettier --check . || { echo "❌ Frontend format failed"; exit 1; }
      npx tsc --noEmit || { echo "❌ Frontend typecheck failed"; exit 1; }
      npm test -- --watchAll=false || { echo "❌ Frontend tests failed"; exit 1; }
    fi
  ) || FAILED=1
fi

# --- Result ---
if [ "$FAILED" = "1" ]; then
  echo "❌ Pre-commit quality gate FAILED — commit blocked." >&2
  echo "   Fix the failures above, stage the fixes, and re-commit." >&2
  exit 2   # BLOCK
fi

echo "✅ Pre-commit quality gate passed."
exit 0