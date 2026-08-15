#!/bin/bash
# Post-commit release note generator.
# Parses conventional commit messages and appends to CHANGELOG.unreleased.md.
# Codex sends the Bash payload as JSON on stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

echo "$COMMAND" | grep -qE "git commit" || exit 0

COMMIT_MSG=$(git log -1 --format=%B 2>/dev/null)
SHORT_HASH=$(git log -1 --format=%h 2>/dev/null)
COMMIT_DATE=$(git log -1 --format=%ad --date=short 2>/dev/null)

if [[ -z "$COMMIT_MSG" ]]; then
  exit 0
fi

# Parse conventional commit format: type(scope): message or type: message
if [[ "$COMMIT_MSG" =~ ^([a-zA-Z]+)(\([a-zA-Z0-9._-]+\))?(!)?:[[:space:]]+(.*) ]]; then
  TYPE="${BASH_REMATCH[1]}"
  SCOPE="${BASH_REMATCH[2]}"
  BREAKING="${BASH_REMATCH[3]}"
  DESCRIPTION="${BASH_REMATCH[4]}"
else
  exit 0
fi

CHANGELOG="CHANGELOG.unreleased.md"

if [[ ! -f "$CHANGELOG" ]]; then
  echo "## Unreleased" > "$CHANGELOG"
  echo "" >> "$CHANGELOG"
fi

CHANGELOG_LINE="- **${TYPE}${SCOPE}${BREAKING}:** ${DESCRIPTION} (${COMMIT_DATE}, ${SHORT_HASH})"
echo "${CHANGELOG_LINE}" >> "$CHANGELOG"

exit 0