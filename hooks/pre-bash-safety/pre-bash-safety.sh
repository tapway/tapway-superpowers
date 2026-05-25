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

# Block commits directly to main/master
if echo "$COMMAND" | grep -qE "git commit"; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    echo "ERROR: Commits to $CURRENT_BRANCH are blocked by project policy." >&2
    echo "Create a feature branch: git checkout -b feat/<your-feature>" >&2
    exit 1
  fi
fi

# Warn on rm -rf
if echo "$COMMAND" | grep -qE "rm -rf"; then
  echo "WARNING: Destructive rm -rf detected. Proceeding cautiously." >&2
fi

# Environment guarding — block prod operations without explicit opt-in
if [[ "${ALLOW_PROD:-0}" != "1" ]]; then
  if echo "$COMMAND" | grep -qiE "DATABASE_URL.*prod"; then
    echo "ERROR: Production database operation detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 1
  fi

  if echo "$COMMAND" | grep -qiE "docker compose.*(production|prod)"; then
    echo "ERROR: Docker production operation detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 1
  fi

  if echo "$COMMAND" | grep -qE "\-\-production"; then
    echo "ERROR: Production flag detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 1
  fi
fi

exit 0