#!/usr/bin/env bash
# pre-brainstorm-ground-lib.sh — shared grounding-gate logic (sourced by all
# three harness adapters). Requires the payload as $1 (raw JSON string).
#
# Gate rules (mirrors codemax.platform_spec.check_grounding):
#   1. Determine the POST-write text when the payload carries it:
#      Claude Write (tool_input.content), Claude Edit (tool_input.new_string),
#      Hermes write_file (tool_input.path + tool_input.content), terminal
#      heredoc bodies (tool_input.command). Fall back to the on-disk file
#      (pre-state) only when the payload carries no content.
#   2. Gate the POST text: every '##/### Option|Approach|Alternative|Proposal'
#      section needs a 'Grounding:' line (bullet/bold tolerated) or an
#      'UNKNOWN (not retrieved: …)' row. Docs with no option sections at all
#      are still gated: creation requires at least one option with grounding.
#   3. Fail closed when a brainstorm doc is targeted but the gate cannot run
#      (python3 missing, unreadable file, unparseable payload).
#
# This is the cheap front line; `codemax platform-context check` remains the
# authoritative CI gate (it also verifies citation resolvability).

set -uo pipefail

payload="${1:-}"

jsonget() {  # field path like tool_input.file_path
  command -v python3 >/dev/null 2>&1 || return 1
  printf '%s' "$payload" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for key in '$1'.split('.'):
    if isinstance(d, dict) and key in d:
        d = d[key]
    else:
        sys.exit(1)
if isinstance(d, str):
    print(d)
" 2>/dev/null
}

block() {
  # pure-bash JSON emit: escape backslashes and double quotes; strip control
  # chars. Never depends on python3 (must work when python3 is missing).
  local reason
  reason="${1//\\/\\\\}"
  reason="${reason//\"/\\\"}"
  if command -v tr >/dev/null 2>&1; then
    reason="$(printf '%s' "$reason" | tr -d '\000-\037')"
  fi
  printf '{"decision":"block","reason":"%s"}\n' "$reason"
  exit 0
}

# ── fail closed if a brainstorm doc is targeted but we cannot parse ──────────
case "$payload" in
  *docs/brainstorming/*.md*)
    command -v python3 >/dev/null 2>&1 || block "gate cannot run (python3 unavailable) while a brainstorm doc write was attempted — install python3 or set TAPWAY_BRAINSTORM_GATE=0 explicitly"
    ;;
esac

# ── collect candidate paths (all harness shapes) ────────────────────────────
paths=()
for field in tool_input.file_path tool_input.path file_path path; do
  v="$(jsonget "$field")"
  if [ -n "$v" ]; then
    case "$v" in
      docs/brainstorming/*.md|*/docs/brainstorming/*.md) paths+=("$v") ;;
    esac
  fi
done

# terminal/hermes commands: any write redirect into docs/brainstorming
command_str="$(jsonget tool_input.command)"
if [ -n "$command_str" ]; then
  while IFS= read -r m; do
    [ -n "$m" ] && paths+=("$m")
  done < <(printf '%s' "$command_str" | grep -oE 'docs/brainstorming/[A-Za-z0-9._/-]+\.md' | sort -u)
fi

[ "${#paths[@]}" -eq 0 ] && { printf '{}\n'; exit 0; }

# ── POST-state text: prefer payload content over on-disk pre-state ──────────
post_text="$(jsonget tool_input.content)"
[ -z "$post_text" ] && post_text="$(jsonget tool_input.new_string)"

# For terminal commands, extract heredoc/echo POST-write text
if [ -z "$post_text" ] && [ -n "$command_str" ]; then
  EXTRACTOR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/extract-post-text.py"
  [ -f "$EXTRACTOR" ] || EXTRACTOR="$(dirname "$0")/extract-post-text.py"
  post_text="$(printf '%s' "$command_str" | python3 "$EXTRACTOR" 2>/dev/null)"
fi

# ── gate: use POST text when present, else the on-disk file ─────────────────
for p in "${paths[@]}"; do
  if [ -n "$post_text" ]; then
    src="$post_text"
  elif [ -f "$p" ]; then
    src=""
  else
    block "brainstorm doc $p does not exist yet and the write carries no content to validate — write the doc with '## Option' sections, each carrying a 'Grounding:' line (catalog:<platform>#<id>, ADR-…) or an 'UNKNOWN (not retrieved: …)' row. See brainstorming skill Step 1.5."
  fi

  if [ -n "$src" ]; then
    # gate the incoming text directly (text via temp file — the heredoc owns stdin)
    SRC_TMP="$(mktemp)"
    printf '%s' "$src" > "$SRC_TMP"
    result="$(python3 - "$SRC_TMP" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
option_re = re.compile(r"^#{2,3}\s+((?:Option|Approach|Alternative|Proposal)\b[^\n]*)$", re.IGNORECASE | re.MULTILINE)
grounding_re = re.compile(r"^\s*(?:[-*+]\s*)?(?:\*\*)?grounding\s*(?:\*\*)?:", re.IGNORECASE | re.MULTILINE)
unknown_re = re.compile(r"UNKNOWN\s*\(\s*not retrieved[^)]*\)", re.IGNORECASE)
matches = list(option_re.finditer(text))
if not matches:
    print("UNGROUNDED:document has no option sections — a brainstorm doc must carry at least one '## Option' with grounding")
    sys.exit(0)
problems = []
for i, m in enumerate(matches):
    end = matches[i+1].start() if i+1 < len(matches) else len(text)
    body = text[m.end():end]
    if not grounding_re.search(body) and not unknown_re.search(body):
        problems.append(m.group(1))
if problems:
    print("UNGROUNDED:" + ", ".join(problems))
PYEOF
)"
    rm -f "$SRC_TMP"
  else
    # on-disk pre-state (payload carried no content — e.g. Edit with old_string only)
    result="$(python3 - "$p" <<'PYEOF'
import json as _json, re, sys
path = sys.argv[1]
try:
    text = open(path, encoding="utf-8", errors="strict").read()
except Exception:
    print("UNGROUNDED:cannot read " + path + " — failing closed")
    sys.exit(0)
option_re = re.compile(r"^#{2,3}\s+((?:Option|Approach|Alternative|Proposal)\b[^\n]*)$", re.IGNORECASE | re.MULTILINE)
grounding_re = re.compile(r"^\s*(?:[-*+]\s*)?(?:\*\*)?grounding\s*(?:\*\*)?:", re.IGNORECASE | re.MULTILINE)
unknown_re = re.compile(r"UNKNOWN\s*\(\s*not retrieved[^)]*\)", re.IGNORECASE)
matches = list(option_re.finditer(text))
if not matches:
    sys.exit(0)  # not an options doc yet — the CI gate handles format rules
problems = []
for i, m in enumerate(matches):
    end = matches[i+1].start() if i+1 < len(matches) else len(text)
    body = text[m.end():end]
    if not grounding_re.search(body) and not unknown_re.search(body):
        problems.append(m.group(1))
if problems:
    print("UNGROUNDED:" + ", ".join(problems))
PYEOF
)"
  fi

  if [ -n "$result" ] && [[ "$result" == UNGROUNDED* ]]; then
    block "brainstorm doc $p has ungrounded options (${result#UNGROUNDED:}): each '## Option' section needs a 'Grounding:' line or an 'UNKNOWN (not retrieved: …)' row. Skill: brainstorming Step 1.5."
  fi
done

printf '{}\n'
exit 0
