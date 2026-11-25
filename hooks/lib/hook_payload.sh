# hooks/lib/hook_payload.sh — sourced by hook entrypoints before they parse a
# payload. Normalises Claude (`tool_input`), Hermes (`args`) and Codex (flat)
# shapes into one object so every gate reads the same fields.
#
#   payload="$(cat | normalize_payload)"
#
# Falls back to passing the payload through when python3 is unavailable; the
# gate scripts then fail closed on their own.

normalize_payload() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
  if command -v python3 >/dev/null 2>&1 && [ -f "$here/hook_payload.py" ]; then
    python3 "$here/hook_payload.py"
  else
    cat
  fi
}