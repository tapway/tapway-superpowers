#!/usr/bin/env bash
# Phase G — Platform grounding gate (G1/G2/G3/G6) — TDD validation suite.
#
# RED:  Run before implementation — these assertions must FAIL.
# GREEN: Run after implementation — all assertions pass.
#
# Covers:
#   G1  brainstorming skill has a Step 1.5 "Platform Context" protocol that runs
#       BEFORE options are generated, in ALL THREE variants (skills/,
#       hermes/skills/, codex/skills/).
#   G2  the doc template requires Platform Fit / Rejected-because-platform /
#       UNKNOWN rows.
#   G3  pre-brainstorm-ground hook exists for Claude Code, Codex, and Hermes,
#       fails closed, and is env-gated off by default for public safety.
#   G6  the skill mandates an index-first pack (~4k chars) with fetch-on-demand,
#       never inlining full platform docs.
#
# Usage: bash tests/test-phase-g.sh
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
FAILURES=0
RED_PHASE="${1:-}"

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }

assert_contains() {  # file, needle, label
  local file="$1" needle="$2" label="${3:-}"
  if grep -q "$needle" "$file" 2>/dev/null; then
    [ -n "$RED_PHASE" ] || green "PASS: $label"
    return 0
  else
    red "FAIL: $label — '$needle' not found in $file"
    FAILURES=$((FAILURES+1))
    return 1
  fi
}

assert_absent() {  # file, needle, label
  local file="$1" needle="$2" label="${3:-}"
  if grep -q "$needle" "$file" 2>/dev/null; then
    red "FAIL: $label — '$needle' unexpectedly present in $file"
    FAILURES=$((FAILURES+1))
    return 1
  else
    [ -n "$RED_PHASE" ] || green "PASS: $label"
    return 0
  fi
}

echo "── G1: Step 1.5 Platform Context in all three variants ──"
for v in skills hermes/skills codex/skills; do
  F="$ROOT/$v/brainstorming/SKILL.md"
  if [ ! -f "$F" ]; then
    red "FAIL: missing variant $F"
    FAILURES=$((FAILURES+1))
    continue
  fi
  assert_contains "$F" "Step 1.5" "G1: $v has Step 1.5"
  assert_contains "$F" "Platform Context" "G1: $v names Platform Context"
  # Step 1.5 must precede option generation (Step 3)
  s15=$(grep -n "Step 1.5" "$F" | head -1 | cut -d: -f1)
  s3=$(grep -n "### 3. Generate Options\|## 3. Generate Options\|Generate Options" "$F" | head -1 | cut -d: -f1)
  if [ -n "$s15" ] && [ -n "$s3" ] && [ "$s15" -lt "$s3" ]; then
    [ -n "$RED_PHASE" ] || green "PASS: G1: $v — Step 1.5 (line $s15) precedes options (line $s3)"
  else
    red "FAIL: G1: $v — Step 1.5 must precede option generation (s15=$s15 s3=$s3)"
    FAILURES=$((FAILURES+1))
  fi
done

echo "── G1 retrieval protocol items ──"
F="$ROOT/skills/brainstorming/SKILL.md"
assert_contains "$F" "ownership" "G1: asks ownership"
assert_contains "$F" "contracts" "G1: asks contracts"
assert_contains "$F" "ADR" "G1: asks ADRs"
assert_contains "$F" "UNKNOWN (not retrieved" "G1: UNKNOWN row convention"

echo "── G2: doc template rows ──"
assert_contains "$F" "Platform Fit" "G2: Platform Fit row"
assert_contains "$F" "Rejected because platform" "G2: Rejected-because-platform row"
assert_contains "$F" "codemax platform-context check" "G2: gate command reference"

echo "── G6: index-first budget ──"
assert_contains "$F" "4,000" "G6: budget figure (~4,000 chars)"
assert_contains "$F" "fetch-on-demand\|index-first" "G6: fetch-on-demand wording"

echo "── G3: hooks (Claude Code + Codex + Hermes), env-gated ──"
for hook in "hooks/pre-brainstorm-ground/pre-brainstorm-ground.sh" "codex/hooks/pre-brainstorm-ground.sh" "hermes/agent-hooks/pre-brainstorm-ground.sh"; do
  H="$ROOT/$hook"
  if [ ! -f "$H" ]; then
    red "FAIL: missing hook $H"
    FAILURES=$((FAILURES+1))
    continue
  fi
  assert_contains "$H" "TAPWAY_BRAINSTORM_GATE" "G3: $hook reads TAPWAY_BRAINSTORM_GATE"
  # fail-closed when enabled and no grounding
  if TAPWAY_BRAINSTORM_GATE=1 bash "$H" <<< '{"file_path":"docs/brainstorming/x.md","content":"no grounding"}' 2>/dev/null | grep -q '"decision" *: *"block"'; then
    [ -n "$RED_PHASE" ] || green "PASS: G3: $hook blocks ungrounded write when enabled"
  else
    red "FAIL: G3: $hook did not block an ungrounded write when TAPWAY_BRAINSTORM_GATE=1"
    FAILURES=$((FAILURES+1))
  fi
  # disabled by default: no block without the env var
  if bash "$H" <<< '{"file_path":"docs/brainstorming/x.md","content":"no grounding"}' 2>/dev/null | grep -q '"decision" *: *"block"'; then
    red "FAIL: G3: $hook blocked with gate disabled (must be off by default)"
    FAILURES=$((FAILURES+1))
  else
    [ -n "$RED_PHASE" ] || green "PASS: G3: $hook silent when gate disabled"
  fi
done

echo "── G3: hook wiring in hook manifests ──"
assert_contains "$ROOT/hooks/hooks.json" "pre-brainstorm-ground" "G3: Claude Code hooks.json wired"
assert_contains "$ROOT/codex/hooks.json.template" "pre-brainstorm-ground" "G3: Codex hooks template wired"
assert_contains "$ROOT/hermes/config.hooks.yaml" "pre-brainstorm-ground" "G3: Hermes config wired"


echo "── G3: fail-closed hardening (no-python3, heading-dodge) ──"
HARD="$ROOT/hooks/pre-brainstorm-ground/pre-brainstorm-ground-lib.sh"
# a) targeted brainstorm write with python3 unavailable → BLOCK (not silently allow)
# build a shim PATH with coreutils but WITHOUT python3
NPY=$(mktemp -d)
for t in bash sh cat grep sort tr dirname pwd ls test; do
  w=$(command -v "$t" 2>/dev/null) && [ -n "$w" ] && ln -s "$w" "$NPY/$t"
done
HARD_OUT=$(env TAPWAY_BRAINSTORM_GATE=1 PATH="$NPY" bash "$HARD" \
    '{"tool_input":{"file_path":"docs/brainstorming/nope.md"}}' 2>/dev/null)
rm -rf "$NPY"
if printf '%s' "$HARD_OUT" | /usr/bin/grep -q '"decision" *: *"block"'; then
  green "PASS: G3: lib fails closed when python3 is unavailable"
else
  red "FAIL: G3: lib silently allowed a brainstorm write with python3 missing"
  FAILURES=$((FAILURES+1))
fi
# b) non-brainstorm path with python3 unavailable → allow (fail-closed only applies to gated paths)
if env TAPWAY_BRAINSTORM_GATE=1 PATH=/usr/bin:/bin bash "$HARD" \
    '{"tool_input":{"file_path":"src/main.py"}}' 2>/dev/null | grep -q '"decision" *: *"block"'; then
  red "FAIL: G3: lib blocked a non-brainstorm write with python3 missing (overreach)"
  FAILURES=$((FAILURES+1))
else
  green "PASS: G3: lib allows non-brainstorm writes when python3 missing"
fi
# c) heading-dodge: '## Approach 1' must still be gated like '## Option A'
TMPD=$(mktemp -d)
mkdir -p "$TMPD/docs/brainstorming"
printf '# Brainstorm\n## Approach 1: smart\nno grounding\n' > "$TMPD/docs/brainstorming/dodge.md"
if TAPWAY_BRAINSTORM_GATE=1 bash "$HARD" \
    "{\"tool_input\":{\"file_path\":\"$TMPD/docs/brainstorming/dodge.md\"}}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  green "PASS: G3: heading-dodge (Approach/Alternative) still gated"
else
  red "FAIL: G3: doc dodged the gate by renaming the option heading"
  FAILURES=$((FAILURES+1))
fi
rm -rf "$TMPD"


echo "── Reviewer fixes: creation flow, template form, copy consistency ──"
LIB="$ROOT/hooks/pre-brainstorm-ground/pre-brainstorm-ground-lib.sh"

# a) NEW doc creation with GROUNDED content in the skill-template bullet/bold form → ALLOW
TPL='# Brainstorm
## Option A: reuse
- **Platform Fit:** uses `catalog:demo#alpha.api`
- **Grounding:** `catalog:demo#alpha.api, ADR-demo-bus`
'
TPL_JSON=$(printf '%s' "$TPL" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
if TAPWAY_BRAINSTORM_GATE=1 bash "$LIB" "{\"tool_input\":{\"file_path\":\"docs/brainstorming/new.md\",\"content\":$TPL_JSON}}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  red "FAIL: creation of a template-form grounded doc was blocked"
  FAILURES=$((FAILURES+1))
else
  green "PASS: creation flow — template-form grounded content allowed"
fi

# b) NEW doc with UNGROUNDED content → BLOCK (gates the POST text, not disk state)
P2=$(python3 -c "import json; print(json.dumps({'tool_input':{'file_path':'docs/brainstorming/new2.md','content':'# T\n## Option A: x\nnothing here'}}))")
if TAPWAY_BRAINSTORM_GATE=1 bash "$LIB" "$P2" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  green "PASS: creation flow — ungrounded content blocked (POST-state gating)"
else
  red "FAIL: ungrounded content was allowed through creation"
  FAILURES=$((FAILURES+1))
fi

# c) the three lib copies must be byte-identical (drift guard)
LIBS="$ROOT/hooks/pre-brainstorm-ground/pre-brainstorm-ground-lib.sh $ROOT/codex/hooks/pre-brainstorm-ground-lib.sh $ROOT/hermes/agent-hooks/pre-brainstorm-ground-lib.sh"
EXTRACTORS="$ROOT/hooks/pre-brainstorm-ground/extract-post-text.py $ROOT/codex/hooks/extract-post-text.py $ROOT/hermes/agent-hooks/extract-post-text.py"
if md5sum $LIBS | awk '{print $1}' | sort -u | wc -l | grep -q '^1$' && md5sum $EXTRACTORS | awk '{print $1}' | sort -u | wc -l | grep -q '^1$'; then
  green "PASS: all three lib+extractor copies are byte-identical"
else
  red "FAIL: lib/extractor copies have drifted"
  FAILURES=$((FAILURES+1))
fi

# d) hermes write_file shape {tool_input:{path, content}}
P4=$(python3 -c "import json; print(json.dumps({'tool_input':{'path':'docs/brainstorming/hw.md','content':'# T\n## Option A: ok\nUNKNOWN (not retrieved: pack unavailable)'}}))")
if TAPWAY_BRAINSTORM_GATE=1 bash "$LIB" "$P4" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  red "FAIL: hermes write_file shape (path+content) should be allowed when grounded"
  FAILURES=$((FAILURES+1))
else
  green "PASS: hermes write_file shape gated correctly"
fi

# e) nested terminal path is gated
P5=$(python3 -c "import json; print(json.dumps({'tool_input':{'command':'cat > docs/brainstorming/2026/x.md <<EOF\n# T\n## Option A: bad\nnothing\nEOF'}}))")
if TAPWAY_BRAINSTORM_GATE=1 bash "$LIB" "$P5" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  green "PASS: nested terminal path gated"
else
  red "FAIL: nested terminal path bypassed the gate"
  FAILURES=$((FAILURES+1))
fi

echo "── E2E: hook + gate integrate ──"
# Simulated session: an ungrounded brainstorm doc is blocked; after adding a
# Grounding line + UNKNOWN row, the same hook passes it.
TMP=$(mktemp -d)
mkdir -p "$TMP/docs/brainstorming"
printf '# Brainstorm\n## Option A: thing\nno citations\n' > "$TMP/docs/brainstorming/t.md"
H="$ROOT/hermes/agent-hooks/pre-brainstorm-ground.sh"
if TAPWAY_BRAINSTORM_GATE=1 bash "$H" <<< "{\"file_path\":\"$TMP/docs/brainstorming/t.md\",\"content\":\"$(cat "$TMP/docs/brainstorming/t.md" | tr '\n' ' ' | sed 's/"/\\"/g')\"}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  [ -n "$RED_PHASE" ] || green "PASS: E2E ungrounded doc blocked"
else
  red "FAIL: E2E ungrounded doc not blocked"
  FAILURES=$((FAILURES+1))
fi
printf '# Brainstorm\n## Option A: thing\nPlatform Fit: unknown yet\nUNKNOWN (not retrieved: platform pack unavailable)\n' > "$TMP/docs/brainstorming/t2.md"
if TAPWAY_BRAINSTORM_GATE=1 bash "$H" <<< "{\"file_path\":\"$TMP/docs/brainstorming/t2.md\",\"content\":\"$(cat "$TMP/docs/brainstorming/t2.md" | tr '\n' ' ' | sed 's/"/\\"/g')\"}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  red "FAIL: E2E grounded doc (UNKNOWN row) was blocked"
  FAILURES=$((FAILURES+1))
else
  [ -n "$RED_PHASE" ] || green "PASS: E2E grounded doc allowed"
fi
rm -rf "$TMP"

echo
if [ "$FAILURES" -gt 0 ]; then
  red "RESULT: $FAILURES failure(s)"
  exit 1
fi
green "RESULT: all G-phase assertions passed"
