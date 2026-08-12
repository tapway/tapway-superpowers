#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# e2e-session-hook.sh — E2E tests for the session-start hook + CodeMAX toggle.
#
# Verifies two things:
#   1. Each CodeMAX goal is reflected in the hook output when enabled:
#        • WO-* detected  → hints to pull traced brain context (pull on start)
#        • WO-* absent    → still prints the enabled banner (non-breaking)
#   2. CodeMAX DISABLED (default) does NOT break the workflow:
#        • no gbrain output at all
#        • exit code 0 (a hook that exits non-zero can block Claude Code)
#
# Usage:
#   bash tests/e2e-session-hook.sh
#
# Returns:
#   0 = all pass, 1 = failures
# ────────────────────────────────────────────────────────────────────────────
set -u

HOOK="$PWD/hooks/session-start/session-start.sh"
ROOT_DIR="$PWD"
PASS=0
FAIL=0
TMP=""

ok()   { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }
header() { echo -e "\n═══ $1 ═══"; }

cleanup() { [ -n "$TMP" ] && rm -rf "$TMP"; }
trap cleanup EXIT

# ── helpers ──
# make a throwaway git project (so the hook's git calls work)
make_project() {
  TMP="$(mktemp -d)"
  cd "$TMP"
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test"
  echo "TARGET_BRANCH: staging" > CLAUDE.md
  git add CLAUDE.md
  git commit -q -m "init"   # need a commit so branches have real names (not unborn HEAD)
  cd "$ROOT_DIR"
}

# run the hook, capturing stdout + exit code
run_hook() {
  # Args: env assignments like "CODEMAX_ENABLED=1"
  local out
  out=$(cd "$TMP" && env "$@" bash "$HOOK" 2>&1)
  echo "$out"
}

count() { echo "$1" | grep -c "$2" || true; }

# ═══════════════════════════════════════════════════════════════════════════
# PART A — CodeMAX DISABLED (default): must not break the workflow
# ═══════════════════════════════════════════════════════════════════════════
header "A. CodeMAX disabled (default) — must not break workflow"

make_project

# A1. CODEMAX_ENABLED unset entirely
OUT=$(cd "$TMP" && bash "$HOOK" 2>&1)
if ! echo "$OUT" | grep -q "gbrain"; then
  ok "A1: unset CODEMAX_ENABLED → no gbrain output"
else
  fail "A1: unset CODEMAX_ENABLED emitted gbrain output"
fi
if echo "$OUT" | grep -q "Project context loaded"; then
  ok "A1: unset CODEMAX_ENABLED → normal session banner still shows"
else
  fail "A1: normal session banner missing"
fi

# A2. CODEMAX_ENABLED=0 explicitly (even with a WO-* branch present)
git rev-parse --abbrev-ref HEAD >/dev/null 2>&1
cd "$TMP"
git checkout -q -b feat/wo-42-thing
cd "$ROOT_DIR"
OUT=$(cd "$TMP" && CODEMAX_ENABLED=0 bash "$HOOK" 2>&1)
# Check for gbrain-specific output only (the branch name legitimately appears
# in the normal session banner, so don't match on it)
if ! echo "$OUT" | grep -qi "gbrain\|work order\|codemax"; then
  ok "A2: CODEMAX_ENABLED=0 with WO-42 branch → no gbrain output"
else
  fail "A2: CODEMAX_ENABLED=0 still emitted gbrain output"
fi

# A3. Hook always exits 0 (never blocks Claude Code session)
cd "$TMP"
env -u CODEMAX_ENABLED bash "$HOOK" >/dev/null 2>&1
RC=$?
cd "$ROOT_DIR"
if [ "$RC" -eq 0 ]; then
  ok "A3: hook exits 0 when disabled (never blocks session)"
else
  fail "A3: hook exited $RC when disabled"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PART B — CodeMAX ENABLED: each goal appears in the output
# ═══════════════════════════════════════════════════════════════════════════
header "B. CodeMAX enabled — goals reflected"

# B1. WO-* detected → pull-context hint (Goal: pull traced context at start)
cd "$TMP"   # currently on feat/wo-42-thing
OUT=$(CODEMAX_ENABLED=1 bash "$HOOK" 2>&1)
cd "$ROOT_DIR"
if echo "$OUT" | grep -qi "active work order detected → wo-42"; then
  ok "B1: WO detected → prints 'active work order detected → wo-42'"
else
  fail "B1: WO detection output missing: $(echo "$OUT" | grep -i wo-42 || echo none)"
fi
if echo "$OUT" | grep -q "Pull its traced requirement/blueprint/ADR"; then
  ok "B1: pull-context hint present (Goal: context pulled at task start)"
else
  fail "B1: pull-context hint missing"
fi

# B2. WO-* absent → enabled banner, still non-breaking
cd "$TMP"
# Return to the default branch (git-init default is 'master', modern is 'main')
if git branch --list master | grep -q master; then DEF=master; else DEF=main; fi
git checkout -q "$DEF"
git branch -q -D feat/wo-42-thing 2>/dev/null
OUT=$(CODEMAX_ENABLED=1 bash "$HOOK" 2>&1)
cd "$ROOT_DIR"
if echo "$OUT" | grep -q "CodeMAX enabled"; then
  ok "B2: no WO → prints 'CodeMAX enabled' banner"
else
  fail "B2: enabled banner missing"
fi
if echo "$OUT" | grep -q "Project context loaded"; then
  ok "B2: normal session banner still shows when enabled"
else
  fail "B2: normal session banner missing when enabled"
fi

# B3. Hook still exits 0 when enabled (never blocks)
cd "$TMP"
CODEMAX_ENABLED=1 bash "$HOOK" >/dev/null 2>&1
RC=$?
cd "$ROOT_DIR"
if [ "$RC" -eq 0 ]; then
  ok "B3: hook exits 0 when enabled (never blocks session)"
else
  fail "B3: hook exited $RC when enabled"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PART C — Static consistency checks (skill + command + pr reference the flag)
# ═══════════════════════════════════════════════════════════════════════════
header "C. Documentation/flag consistency"

if grep -q "CODEMAX_ENABLED" skills/codemax-gbrain/SKILL.md; then
  ok "C1: codemax-gbrain skill documents CODEMAX_ENABLED"
else
  fail "C1: skill missing CODEMAX_ENABLED reference"
fi
if grep -q "CODEMAX_ENABLED" hooks/session-start/session-start.sh; then
  ok "C2: session-start hook references CODEMAX_ENABLED"
else
  fail "C2: hook missing CODEMAX_ENABLED"
fi
if grep -q "CODEMAX_ENABLED" skills/pr/SKILL.md; then
  ok "C3: /pr skill marks gbrain step as optional"
else
  fail "C3: /pr skill missing optional/codemax flag"
fi
if grep -q "CODEMAX_ENABLED" commands/gbrain.md; then
  ok "C4: /gbrain command notes the opt-in flag"
else
  fail "C4: /gbrain command missing CODEMAX_ENABLED note"
fi

# ── Summary ──
echo ""
echo "════════════════════════════════════════════"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "════════════════════════════════════════════"
[ "$FAIL" -gt 0 ] && exit 1
exit 0