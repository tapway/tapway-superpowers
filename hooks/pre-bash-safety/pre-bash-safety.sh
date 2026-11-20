#!/bin/bash
# Pre-bash safety check — blocks dangerous commands before Claude runs them.
#
# Claude Code sends the tool call as JSON on stdin ({"tool_input":{"command":...}});
# hooks/lib/hook_payload.sh normalises the Claude, Hermes and Codex shapes.
# This hook used to read the command from "$1", which Claude Code never sets,
# so none of the rules below ever fired. tests/test_pre_bash_safety.py now
# drives it the way Claude Code does.

. "$(dirname "$0")/../lib/hook_payload.sh"
SEGMENTS_PY='
import json, re, sys
try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except ValueError:
    cmd = ""
cmd = re.sub(r"\\\r?\n", " ", cmd)
print(re.sub(r"[;&|]+", "\n", cmd))
'
COMMAND=$(normalize_payload | python3 -c "$SEGMENTS_PY" 2>/dev/null)

if [ -z "$COMMAND" ]; then
  exit 0
fi

# The rules below grep one shell segment per line: COMMAND has `\` continuations
# joined and `;`, `&&`, `||`, `|` turned into newlines, so a flag on one command
# never matches a rule about another. Patterns are POSIX ERE (no \b), so they
# behave the same with GNU grep and macOS/BSD grep.
S='[[:space:]]'

# Block force pushes: --force, --force-with-lease, -f or -f inside short flags
# (-uf), and +refspec. Branch names like feat/x-fix do not match.
if echo "$COMMAND" | grep -E "(^|$S)git($S.*)?${S}push($S|\$)" \
   | grep -qE "$S(--force(-with-lease)?(=[^[:space:]]*)?|-[a-zA-Z]*f[a-zA-Z]*)($S|\$)|$S\+[^[:space:]]"; then
  echo "ERROR: Force push is blocked by project policy. Use a PR instead." >&2
  exit 2
fi

# Block hard resets on main
if echo "$COMMAND" | grep -qE "(^|$S)git($S.*)?${S}reset$S+--hard" \
   && git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -qE "^(main|master)$"; then
  echo "ERROR: Hard reset on main/master is blocked." >&2
  exit 2
fi

# Block commits directly to main/master
if echo "$COMMAND" | grep -qE "(^|$S)git($S.*)?${S}commit($S|\$)"; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    echo "ERROR: Commits to $CURRENT_BRANCH are blocked by project policy." >&2
    echo "Create a feature branch: git checkout -b feat/<your-feature>" >&2
    exit 2
  fi
fi

# Warn on rm -rf
if echo "$COMMAND" | grep -qE "rm -rf"; then
  echo "WARNING: Destructive rm -rf detected. Proceeding cautiously." >&2
fi

# Environment guarding — block prod operations without explicit opt-in.
# `prod` / `production` must not be part of a longer word: PROD_URL and
# app.prod.yml match, "products" and "reproduce" do not.
PROD='(^|[^a-zA-Z])prod(uction)?([^a-zA-Z]|$)'
if [[ "${ALLOW_PROD:-0}" != "1" ]]; then
  if echo "$COMMAND" | grep -qiE "DATABASE_URL[^[:space:]]*$PROD"; then
    echo "ERROR: Production database operation detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 2
  fi

  # Only a compose command that changes something: reading a prod compose file is fine.
  if echo "$COMMAND" | grep -iE "(^|$S)docker[- ]compose($S|\$)" \
     | grep -E "$S(up|down|build|run|exec|rm|restart|start|stop|pull|push|create|kill)($S|\$)" \
     | grep -qiE "$PROD"; then
    echo "ERROR: Docker production operation detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 2
  fi

  # Build tools and package managers use --production for a build mode, not an environment.
  if echo "$COMMAND" | grep -E "(^|$S)--production($S|=|\$)" \
     | grep -vE "(^|$S)(npm|pnpm|yarn|bun|npx|next|vite|webpack|ng|nx|turbo)$S" | grep -q .; then
    echo "ERROR: Production flag detected." >&2
    echo "Set ALLOW_PROD=1 to proceed." >&2
    exit 2
  fi
fi

exit 0
