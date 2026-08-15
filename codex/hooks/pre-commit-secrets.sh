#!/bin/bash
# Pre-commit secrets scanner — blocks commits containing secrets.
# Codex sends the Bash payload as JSON on stdin; the `if` filter in
# hooks.json restricts this to `git commit` commands.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Only run on commits
echo "$COMMAND" | grep -qE "git commit" || exit 0

SECRETS_PATTERNS=(
  "sk-[a-zA-Z0-9]{32,}"          # OpenAI keys
  "AKIA[0-9A-Z]{16}"             # AWS access keys
  "ghp_[a-zA-Z0-9]{36}"         # GitHub tokens
  "password\s*=\s*['\"][^'\"]+['\"]"  # Hardcoded passwords
  "secret\s*=\s*['\"][^'\"]{8,}['\"]" # Hardcoded secrets
  "api_key\s*=\s*['\"][^'\"]{8,}['\"]" # API keys
)

STAGED=$(git diff --cached --name-only)

for FILE in $STAGED; do
  for PATTERN in "${SECRETS_PATTERNS[@]}"; do
    if git show ":$FILE" 2>/dev/null | grep -qiE "$PATTERN"; then
      echo "❌ BLOCKED: Possible secret detected in $FILE (pattern: $PATTERN)" >&2
      echo "   Use environment variables instead. See .env.example" >&2
      exit 2
    fi
  done
done

echo "✅ No secrets detected in staged files."
exit 0