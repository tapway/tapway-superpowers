#!/usr/bin/env bash
# pre-pr-contract.sh — block `gh pr create` when the branch's docs break the
# contracts (B5 front line; CI is authoritative).
#
#   C1: docs/brainstorming/*.md — every option section cites the brain.
#   C2: docs/plans/*.md        — frontmatter carries `issue: <number>`.
#
# Input: hook payload (any harness shape — normalised by hooks/lib).
# Output: {"decision":"block","reason":"…"} or {}.

set -uo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
HOOK_LIB="$ROOT/hooks/lib"
# shellcheck source=../lib/hook_payload.sh
[ -f "$HOOK_LIB/hook_payload.sh" ] && . "$HOOK_LIB/hook_payload.sh"

payload="$(cat | normalize_payload)"
command_text="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    print("")
' 2>/dev/null)"

case "$command_text" in
  *"gh pr create"*) ;;
  *) printf '{}\n'; exit 0 ;;
esac

if [ "${TAPWAY_PR_GATE:-1}" != "1" ]; then printf '{}\n'; exit 0; fi

base="${TAPWAY_PR_BASE:-origin/staging}"
# Run in the caller's repo, not the plugin directory.
changed="$(git diff --name-only "$base"...HEAD 2>/dev/null || true)"
if [ -z "$changed" ]; then
  # No base to compare against (new repo / detached) — do not guess.
  printf '{}\n'; exit 0
fi

# shellcheck disable=SC2086
if ! findings="$(python3 "$ROOT/scripts/workflow_gate.py" $changed 2>&1)"; then
  reason="$(printf '%s' "$findings" | head -5 | paste -sd ';' -)"
  python3 - "$reason" <<'PY'
import json, sys
print(json.dumps({
    "decision": "block",
    "reason": "tapway-superpowers refused `gh pr create`: " + sys.argv[1]
    + " — fix the docs, or set TAPWAY_PR_GATE=0 for one run.",
}))
PY
  exit 0
fi

printf '{}\n'