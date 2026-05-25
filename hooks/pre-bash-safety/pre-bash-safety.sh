#!/bin/bash
# Pre-bash safety check — blocks dangerous commands before Claude runs them

COMMAND="$1"

# Block force pushes
if echo "$COMMAND" | grep -qE "git push.*(--force|-f)"; then
  echo "ERROR: Force push is blocked by project policy. Use a PR instead." >&2
  exit 1
fi

# Block hard resets on main
if echo "$COMMAND" | grep -qE "git reset --hard" && git rev-parse --abbrev-ref HEAD | grep -qE "^main$|^master$"; then
  echo "ERROR: Hard reset on main/master is blocked." >&2
  exit 1
fi

# Warn on rm -rf
if echo "$COMMAND" | grep -qE "rm -rf"; then
  echo "WARNING: Destructive rm -rf detected. Proceeding cautiously." >&2
fi

exit 0