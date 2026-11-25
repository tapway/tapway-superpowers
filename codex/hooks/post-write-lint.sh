#!/bin/bash
# Post-write auto-lint — runs after Codex writes/edits a file via apply_patch.
# Codex sends {tool_name: apply_patch, tool_input:{patch,...}} as JSON on stdin.
# We derive the touched file(s) from the patch header lines (+++ b/<path>).
#
# NOTE: apply_patch `+++ b/<path>` paths are REPO-ROOT-relative (e.g.
# `frontend/src/App.tsx`). We lint from the dir that owns the file so the path
# resolves against the right node_modules / ruff config, and we pass `--`
# before the path so a filename beginning with `-` can never be read as a
# linter flag (option-injection hardening, code-review W1/W3).

INPUT=$(cat)
# Extract the patch text from the payload
PATCH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('patch',''))" 2>/dev/null || echo "")

if [ -z "$PATCH" ]; then
  exit 0
fi

# Pull out the file paths the patch targets (+++ b/... or +++ <path>)
FILES=$(echo "$PATCH" | grep -oE "^\\+\\+\\+ (b/)?[^ ]+" | sed -E 's|^\\+\\+\\+ (b/)?||' | sort -u)

if [ -z "$FILES" ]; then
  exit 0
fi

for FILE in $FILES; do
  [ -f "$FILE" ] || continue

  # TypeScript/JavaScript files
  if [[ "$FILE" =~ \.(ts|tsx|js|jsx)$ ]]; then
    if command -v npx &>/dev/null; then
      # If the file lives under frontend/, run eslint from frontend/ so the
      # (repo-root-relative) path resolves and project config is picked up.
      if [[ "$FILE" == frontend/* ]]; then
        ( cd frontend 2>/dev/null && npx eslint --fix -- "${FILE#frontend/}" --quiet ) 2>/dev/null || true
      else
        npx eslint --fix -- "$FILE" --quiet 2>/dev/null || true
      fi
    fi
  fi

  # Python files
  if [[ "$FILE" =~ \.py$ ]]; then
    if command -v ruff &>/dev/null; then
      ruff check --fix -- "$FILE" --quiet 2>/dev/null || true
      ruff format -- "$FILE" --quiet 2>/dev/null || true
    fi
  fi
done

exit 0