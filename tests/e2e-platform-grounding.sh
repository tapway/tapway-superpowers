#!/usr/bin/env bash
# E2E: full-chain platform grounding — spec repo → codemax build/check → hook.
#
# Exercises the ACTUAL artifacts (tapway/platform-specs checkout, codemax CLI,
# pre-brainstorm-ground hook) the way an agent session would hit them:
#   1. build the samurai-v2 pack from the real specs repo
#   2. write an ungrounded brainstorm doc → codemax check FAILS
#   3. same doc + UNKNOWN row → codemax check PASSES
#   4. doc with a REAL citation (catalog:samurai-v2#… contract + platform ADR)
#      → check PASSES, proving citations resolve against the live catalog
#   5. hook blocks the ungrounded write, allows the grounded one
#
# Usage: bash tests/e2e-platform-grounding.sh [specs-dir] [workdir]
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SPECS_DIR="${1:-${TAPWAY_SPECS_DIR:-$HOME/platform-specs-local}}"
WORK="${2:-$(mktemp -d)}"
CODEMAX_DIR="${CODEMAX_DIR:-/home/tapway/projects/codemax-g16}"

FAIL=0
ok()   { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }

command -v python3 >/dev/null || { echo "python3 required"; exit 2; }

echo "── E2E platform grounding (specs: $SPECS_DIR) ──"

# 1. pack build from the real spec repo
python3 - <<PY > /dev/null 2>&1 || { fail "pack build (python import)"; }
import sys
sys.path.insert(0, "$CODEMAX_DIR/src")
from codemax.platform_spec import compile_platform_pack
pack = compile_platform_pack("$SPECS_DIR", "samurai-v2")
assert pack.component_count >= 10, pack.component_count
assert pack.digest
PY
[ $? -eq 0 ] && ok "pack builds from live specs repo ($(python3 -c "
import sys; sys.path.insert(0,'$CODEMAX_DIR/src')
from codemax.platform_spec import compile_platform_pack
print(compile_platform_pack('$SPECS_DIR','samurai-v2').component_count)
" 2>/dev/null) components)"

# 2. ungrounded doc fails the CLI gate
mkdir -p "$WORK/docs/brainstorming"
printf '# Options\n## Option A: vibes\nno citations\n' > "$WORK/docs/brainstorming/u.md"
if PYTHONPATH="$CODEMAX_DIR/src" python3 -m codemax.cli platform-context check \
    --specs-dir "$SPECS_DIR" --platform samurai-v2 --doc "$WORK/docs/brainstorming/u.md" >/dev/null 2>&1; then
  fail "ungrounded doc must fail the gate"
else
  ok "ungrounded doc fails the gate (exit != 0)"
fi

# 3. UNKNOWN row passes
printf '# Options\n## Option A: thing\nUNKNOWN (not retrieved: pack unavailable)\n' > "$WORK/docs/brainstorming/k.md"
if PYTHONPATH="$CODEMAX_DIR/src" python3 -m codemax.cli platform-context check \
    --specs-dir "$SPECS_DIR" --platform samurai-v2 --doc "$WORK/docs/brainstorming/k.md" >/dev/null 2>&1; then
  ok "UNKNOWN row passes the gate"
else
  fail "UNKNOWN row should pass"
fi

# 4. real citations resolve against the live catalog
ADR_ID="$(PYTHONPATH='${CODEMAX_DIR}/src' python3 -c "
import sys; sys.path.insert(0,'$CODEMAX_DIR/src')
from codemax.platform_spec import compile_platform_pack
print(compile_platform_pack('$SPECS_DIR','samurai-v2').adr_ids[0])
" 2>/dev/null)"
printf '# Options\n## Option A: aligned\nGrounding: %s\n' "$ADR_ID" > "$WORK/docs/brainstorming/r.md"
if PYTHONPATH="$CODEMAX_DIR/src" python3 -m codemax.cli platform-context check \
    --specs-dir "$SPECS_DIR" --platform samurai-v2 --doc "$WORK/docs/brainstorming/r.md" >/dev/null 2>&1; then
  ok "real ADR citation resolves ($ADR_ID)"
else
  fail "real ADR citation should resolve ($ADR_ID)"
fi

# 4b. fabricated citation fails
printf '# Options\n## Option A: lies\nGrounding: ADR-totally-fake-xyz\n' > "$WORK/docs/brainstorming/f.md"
if PYTHONPATH="$CODEMAX_DIR/src" python3 -m codemax.cli platform-context check \
    --specs-dir "$SPECS_DIR" --platform samurai-v2 --doc "$WORK/docs/brainstorming/f.md" >/dev/null 2>&1; then
  fail "fabricated citation must fail"
else
  ok "fabricated citation fails (exit != 0)"
fi

# 5. hook end-to-end
H="$ROOT/hermes/agent-hooks/pre-brainstorm-ground.sh"
if TAPWAY_BRAINSTORM_GATE=1 bash "$H" \
    <<< "{\"tool_input\":{\"file_path\":\"$WORK/docs/brainstorming/u.md\"}}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  ok "hook blocks ungrounded doc"
else
  fail "hook should block ungrounded doc"
fi
if TAPWAY_BRAINSTORM_GATE=1 bash "$H" \
    <<< "{\"tool_input\":{\"file_path\":\"$WORK/docs/brainstorming/k.md\"}}" 2>/dev/null | grep -q '"decision" *: *"block"'; then
  fail "hook should allow UNKNOWN-row doc"
else
  ok "hook allows UNKNOWN-row doc"
fi

rm -rf "$WORK"
echo
if [ "$FAIL" -gt 0 ]; then
  printf '\033[31mRESULT: %d failure(s)\033[0m\n' "$FAIL"
  exit 1
fi
printf '\033[32mRESULT: E2E platform grounding passed\033[0m\n'
