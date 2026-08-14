#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# e2e-session-hook.sh — E2E tests for the session-start hook + CodeMAX toggle.
#
# Verifies two things:
#   1. Each CodeMAX goal is reflected in the hook output when enabled:
#        • GitHub issue detected  → hints to pull traced brain context (pull on start)
#        • no issue for branch    → still prints the enabled banner (non-breaking)
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
  git remote add origin "https://github.com/tapway/faketest.git"
  cd "$ROOT_DIR"

  # Fake `gh` on PATH so issue detection is hermetic (no network/auth needed).
  #
  # Hardened against the .git-swallow bug (PR #24 regression): real `gh` fails
  # on a --repo ending in ".git", so a repo that still carries .git must be
  # treated as "no issue" — otherwise the hook would silently report nothing
  # forever. This makes the e2e fail RED if session-start.sh stops stripping
  # .git from the remote URL.
  mkdir -p "$TMP/bin"
  cat > "$TMP/bin/gh" <<'FAKEGH'
#!/bin/bash
# Parse --repo <owner/repo> from the arg list. If it still ends in ".git",
# behave like real gh (which fails on that form): emit nothing = "no issue".
REPO_ARG=""
while [ $# -gt 0 ]; do
  if [ "$1" = "--repo" ] && [ $# -ge 2 ]; then
    REPO_ARG="$2"
    shift 2
    continue
  fi
  shift
done
if [ -z "$REPO_ARG" ] || [[ "$REPO_ARG" == *.git ]]; then
  exit 0   # no usable repo (as real gh would error) → no issue found
fi
echo "${FAKE_GH_ISSUE:-}"
exit 0
FAKEGH
  chmod +x "$TMP/bin/gh"
}

# run the hook, capturing stdout + exit code
run_hook() {
  # Args: env assignments like "CODEMAX_ENABLED=1"
  local out
  out=$(cd "$TMP" && env PATH="$TMP/bin:$PATH" "$@" bash "$HOOK" 2>&1)
  echo "$out"
}

count() { echo "$1" | grep -c "$2" || true; }

# ═══════════════════════════════════════════════════════════════════════════
# PART A — CodeMAX DISABLED (default): must not break the workflow
# ═══════════════════════════════════════════════════════════════════════════
header "A. CodeMAX disabled (default) — must not break workflow"

make_project

# A1. CODEMAX_ENABLED unset entirely
OUT=$(run_hook)
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

# A2. CODEMAX_ENABLED=0 explicitly (even with a GitHub issue matching this branch)
OUT=$(run_hook CODEMAX_ENABLED=0 FAKE_GH_ISSUE=42)
if ! echo "$OUT" | grep -qi "gbrain\|codemax"; then
  ok "A2: CODEMAX_ENABLED=0 with a matching issue → no gbrain output"
else
  fail "A2: CODEMAX_ENABLED=0 still emitted gbrain output"
fi

# A3. Hook always exits 0 (never blocks Claude Code session)
cd "$TMP"
env -u CODEMAX_ENABLED PATH="$TMP/bin:$PATH" bash "$HOOK" >/dev/null 2>&1
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

# B1. GitHub issue detected → pull-context hint (Goal: pull traced context at start)
OUT=$(run_hook CODEMAX_ENABLED=1 FAKE_GH_ISSUE=42)
if echo "$OUT" | grep -q "GitHub issue #42 found for this branch"; then
  ok "B1: issue detected → prints 'GitHub issue #42 found for this branch'"
else
  fail "B1: issue detection output missing: $(echo "$OUT" | grep -i "issue #" || echo none)"
fi
if echo "$OUT" | grep -q "Pull its traced requirement/blueprint/ADR"; then
  ok "B1: pull-context hint present (Goal: context pulled at task start)"
else
  fail "B1: pull-context hint missing"
fi

# B2. No GitHub issue for this branch yet → enabled banner, still non-breaking
OUT=$(run_hook CODEMAX_ENABLED=1)
if echo "$OUT" | grep -q "no GitHub issue detected for this branch yet"; then
  ok "B2: no issue → prints 'no GitHub issue detected' banner"
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
CODEMAX_ENABLED=1 PATH="$TMP/bin:$PATH" bash "$HOOK" >/dev/null 2>&1
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