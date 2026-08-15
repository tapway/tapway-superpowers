#!/bin/bash
# Dependency audit — scans lockfiles for known vulnerabilities before commit.
# Uses exit 2 to BLOCK the commit if critical/high vulnerabilities are found.
# Codex sends the Bash payload as JSON on stdin.
#
# Tools (installed separately or by setup-project):
#   - osv-scanner  (Google, multi-ecosystem)  https://google.github.io/osv-scanner/
#   - npm audit    (Node)                     built into npm
#   - pip-audit    (Python)                   pip install pip-audit

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

echo "$COMMAND" | grep -qE "git commit" || exit 0

FAIL_MODE="${DEP_AUDIT_STRICT:-0}"
FAILED=0
SCANNED=0

echo "→ Running dependency audit..."

# --- Lockfile detection (staged files + committed lockfiles) ---
STAGED_LOCKFILES=$(git diff --cached --name-only 2>/dev/null | grep -E "package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|poetry\.lock$|Pipfile\.lock$|uv\.lock$|go\.sum$|Cargo\.lock$" 2>/dev/null || true)
TRACKED_LOCKFILES=$(git ls-files 2>/dev/null | grep -E "package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|poetry\.lock$|Pipfile\.lock$|uv\.lock$|go\.sum$|Cargo\.lock$" 2>/dev/null || true)
LOCKFILES="${STAGED_LOCKFILES}${TRACKED_LOCKFILES}"

# --- Node (npm audit) ---
if echo "$LOCKFILES" | grep -qE "package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$"; then
  if [ -f package-lock.json ] && command -v npm >/dev/null 2>&1; then
    echo "→ npm audit"
    SCANNED=1
    OUT=$(npm audit --audit-level=high 2>&1)
    RC=$?
    if [ "$RC" != "0" ]; then
      echo "$OUT" | tail -20
      if [ "$FAIL_MODE" = "1" ] || echo "$OUT" | grep -qiE "severity: (critical|high)"; then
        echo "❌ npm audit found vulnerabilities"
        FAILED=1
      else
        echo "⚠ npm audit found issues (high/critical-level blocking enabled)"
      fi
    fi
  fi
fi

# --- Python (pip-audit) ---
if echo "$LOCKFILES" | grep -qE "requirements.*\.txt$|pyproject\.toml$|poetry\.lock$|Pipfile\.lock$|uv\.lock$"; then
  if command -v pip-audit >/dev/null 2>&1; then
    echo "→ pip-audit"
    SCANNED=1
    OUT=$(pip-audit 2>&1)
    RC=$?
    if [ "$RC" != "0" ]; then
      echo "$OUT" | tail -20
      if [ "$FAIL_MODE" = "1" ] || echo "$OUT" | grep -qiE "critical|high"; then
        echo "❌ pip-audit found vulnerabilities"
        FAILED=1
      else
        echo "⚠ pip-audit found issues (critical/high-level blocking enabled)"
      fi
    fi
  fi
fi

# --- Multi-ecosystem (osv-scanner) ---
if command -v osv-scanner >/dev/null 2>&1; then
  if echo "$LOCKFILES" | grep -qE "package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|poetry\.lock$|Pipfile\.lock$|uv\.lock$|go\.sum$|Cargo\.lock$"; then
    echo "→ osv-scanner"
    SCANNED=1
    OUT=$(osv-scanner --format json . 2>&1 || true)
    if echo "$OUT" | grep -q '"isVulnerable": true'; then
      echo "$OUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for r in d.get('results', []):
        for p in r.get('packages', []):
            for v in p.get('vulnerabilities', []):
                sev = (v.get('database_specific', {}) or {}).get('severity', 'UNKNOWN')
                print(f\"  {p.get('package', {}).get('name', '?')} — {v.get('id', '?')} [{sev}]\")
except Exception:
    pass
" 2>/dev/null
      if [ "$FAIL_MODE" = "1" ] || echo "$OUT" | grep -qiE '"severity":\s*"(critical|high)"'; then
        echo "❌ osv-scanner found critical/high vulnerabilities"
        FAILED=1
      else
        echo "⚠ osv-scanner found vulnerabilities (non-critical/high — review before merge)"
      fi
    fi
  fi
fi

if [ "$SCANNED" = "0" ]; then
  echo "→ No lockfiles or scanners detected — dependency audit skipped (nothing to scan)."
fi

# --- Result ---
if [ "$FAILED" = "1" ]; then
  echo "❌ Dependency audit FAILED — commit blocked." >&2
  echo "   Run: osv-scanner . / npm audit fix / pip-audit fix ; then re-commit." >&2
  exit 2   # BLOCK
fi

echo "✅ Dependency audit passed."
exit 0