#!/bin/bash
# Post-write auto-lint — runs after Claude writes or edits a file

FILE="$1"

if [[ -z "$FILE" ]]; then
  exit 0
fi

# TypeScript/JavaScript files
if [[ "$FILE" =~ \.(ts|tsx|js|jsx)$ ]]; then
  cd frontend 2>/dev/null || true
  if command -v npx &>/dev/null; then
    npx eslint --fix "$FILE" --quiet 2>/dev/null || true
  fi
fi

# Python files
if [[ "$FILE" =~ \.py$ ]]; then
  if command -v ruff &>/dev/null; then
    ruff check --fix "$FILE" --quiet 2>/dev/null || true
    ruff format "$FILE" --quiet 2>/dev/null || true
  fi
fi

exit 0