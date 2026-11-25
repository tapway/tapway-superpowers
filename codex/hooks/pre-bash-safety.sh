#!/bin/bash
# Pre-bash safety check — blocks dangerous commands before Codex runs them.
# Codex sends {tool_name, tool_input:{command}, ...} as JSON on stdin
# (json.loads reads tool_input.command below). Codex has no tool-guard behind
# this hook, so it must fail closed on its own.

SEGMENTS_PY='
import json, re, sys
raw = sys.stdin.read()
if not raw.strip():
    sys.exit(0)  # no tool call, nothing to check
try:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError("payload is not an object")
    # Claude: tool_input, Hermes: args, Codex: tool_input or a flat payload.
    tool_input = payload.get("tool_input", payload.get("args"))
    if tool_input is None and "command" in payload:
        tool_input = payload
    if not isinstance(tool_input, dict):
        raise TypeError("tool_input is not an object")
    cmd = tool_input.get("command", "")
    if not isinstance(cmd, str):
        raise TypeError("command is not a string")
except Exception as exc:
    print(f"unreadable tool call ({type(exc).__name__}: {exc})", file=sys.stderr)
    sys.exit(3)
cmd = re.sub(r"\\\r?\n", " ", cmd)
print(re.sub(r"[;&|]+", "\n", cmd))
'
# Fails closed: a missing python3 or an unreadable tool call blocks instead of
# letting every command through with no rule checked.
if ! command -v python3 >/dev/null 2>&1; then
  echo "Blocked by pre-bash-safety: python3 is required" >&2
  exit 2
fi
INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | python3 -c "$SEGMENTS_PY")
if [ $? -ne 0 ]; then
  echo "Blocked by pre-bash-safety: could not read the tool call; refusing to guess" >&2
  exit 2
fi

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

# Which branch does a git command act on? Not the hook's own directory: the
# harness starts hooks in the project root, and in a git-worktree session that
# is the main checkout (often on master) while the command runs in the worktree
# on a feature branch. So start from the payload's `cwd`, follow a `cd DIR`
# segment earlier in the same command, and honour `git -C DIR`.
PAYLOAD_CWD=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
    c = d.get("cwd") if isinstance(d, dict) else None
    print(c if isinstance(c, str) else "")
except Exception:
    print("")
')
resolve_dir() {  # resolve_dir BASE TARGET -> TARGET made absolute against BASE
  local t="${2}"
  t="${t#[\"\']}"
  t="${t%[\"\']}"
  case "$t" in
    /*|[A-Za-z]:*) printf '%s' "$t" ;;
    "~") printf '%s' "$HOME" ;;
    "~/"*) printf '%s/%s' "$HOME" "${t#??}" ;;
    *) printf '%s/%s' "${1}" "$t" ;;
  esac
}
# branches_for ERE: the branch each segment matching ERE runs on, one per line.
branches_for() {
  local dir="${PAYLOAD_CWD:-$PWD}" line gdir
  while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*cd[[:space:]]+([^[:space:]]+)[[:space:]]*$ ]]; then
      dir=$(resolve_dir "$dir" "${BASH_REMATCH[1]}")
      continue
    fi
    if echo "$line" | grep -qE "${1}"; then
      gdir="$dir"
      if [[ "$line" =~ git[[:space:]]+-C[[:space:]]+([^[:space:]]+) ]]; then
        gdir=$(resolve_dir "$dir" "${BASH_REMATCH[1]}")
      fi
      git -C "$gdir" rev-parse --abbrev-ref HEAD 2>/dev/null
    fi
  done <<< "$COMMAND"
}

# Block hard resets on main
if branches_for "(^|$S)git($S.*)?${S}reset$S+--hard" | grep -qE "^(main|master)$"; then
  echo "ERROR: Hard reset on main/master is blocked." >&2
  exit 2
fi

# Block commits directly to main/master
CURRENT_BRANCH=$(branches_for "(^|$S)git($S.*)?${S}commit($S|\$)" | grep -E "^(main|master)$" | head -1)
if [ -n "$CURRENT_BRANCH" ]; then
  echo "ERROR: Commits to $CURRENT_BRANCH are blocked by project policy." >&2
  echo "Create a feature branch: git checkout -b feat/<your-feature>" >&2
  exit 2
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
