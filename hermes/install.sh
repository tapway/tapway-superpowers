#!/usr/bin/env bash
#
# install.sh — Install all 24 Tapway Superpowers skills into Hermes Agent
#              (gbrain-style: one command scaffolds the whole skillpack).
#
# Modes (HERMES_INSTALL_MODE):
#   auto  (default) — prefer local copy when this checkout has hermes/skills/;
#                     otherwise use the Hermes skill hub. If the hub blocks a
#                     skill (skills-guard false positive), fall back to local
#                     when available.
#   local           — copy from this repo's hermes/skills/ only (offline-safe,
#                     bypasses hub scanner). Requires running from a checkout.
#   hub             — hermes skills install from GitHub only (no local fallback).
#
# Optional:
#   HERMES_DRY_RUN=1          preview commands, no writes
#   HERMES_SKILLS_REF=<git-ref>  documented pin (hub always tracks default branch
#                                tip today; local mode uses whatever is checked out)
#
# Usage:
#   bash install.sh                                 # default category: tapway
#   bash install.sh <hermes-skills-category>        # e.g. "tapway-superpowers"
#
# Prereqs:
#   - `hermes` CLI on PATH
#   - For hub mode: GitHub auth recommended (gh auth login / GITHUB_TOKEN)
#
# See hermes/INSTALL_ISSUES.md for the field report that motivated this installer.

set -euo pipefail

REPO="tapway/tapway-superpowers"
SKILL_ROOT="hermes/skills"
CATEGORY="${1:-tapway}"
MODE="${HERMES_INSTALL_MODE:-auto}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_SKILLS_DIR="${SCRIPT_DIR}/skills"

# All 24 ported skills. Order = pipeline order.
SKILLS=(
  interview
  brainstorming
  writing-plans
  tdd
  e2e-playwright
  quality-gates
  dependency-audit
  api-contract-testing
  db-migration-testing
  autoship
  refactor
  systematic-debugging
  code-review
  pre-review-cleanup
  security-audit
  verification
  doubt
  observe
  deprecate
  incident-runbook
  pr
  repo-docs
  git-worktrees
  setup-project
  codemax-gbrain
)

# 24 ported skills in pipeline order (plus codemax-gbrain = 25).
# Skills known to collide with Hermes builtin / other hub names.
# Tapway copies still install under the category folder; `hermes skills list`
# may show only one row per bare name.
NAME_COLLISIONS=(writing-plans systematic-debugging)

if ! command -v hermes >/dev/null 2>&1; then
  echo "Error: 'hermes' CLI not found on PATH." >&2
  echo "Install Hermes Agent first:  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash" >&2
  exit 1
fi

resolve_hermes_home() {
  # Prefer hermes config path; fall back to platform defaults.
  local cfg
  if cfg="$(hermes config path 2>/dev/null)" && [ -n "$cfg" ]; then
    dirname "$cfg"
    return 0
  fi
  if [ -n "${HERMES_HOME:-}" ]; then
    echo "$HERMES_HOME"
    return 0
  fi
  # Windows Hermes default (git-bash)
  if [ -d "${HOME}/AppData/Local/hermes" ]; then
    echo "${HOME}/AppData/Local/hermes"
    return 0
  fi
  echo "${HOME}/.hermes"
}

HERMES_HOME_DIR="$(resolve_hermes_home)"
DEST_ROOT="${HERMES_HOME_DIR}/skills/${CATEGORY}"

have_local_skills() {
  [ -d "${LOCAL_SKILLS_DIR}/tdd" ] && [ -f "${LOCAL_SKILLS_DIR}/tdd/SKILL.md" ]
}

install_local() {
  local skill="$1"
  local src="${LOCAL_SKILLS_DIR}/${skill}"
  local dest="${DEST_ROOT}/${skill}"

  if [ ! -d "$src" ] || [ ! -f "${src}/SKILL.md" ]; then
    echo "local source missing: $src" >&2
    return 1
  fi

  mkdir -p "$DEST_ROOT"
  rm -rf "$dest"
  # Portable copy (GNU cp -a / BSD cp -R / busybox)
  if cp -a "$src" "$dest" 2>/dev/null; then
    :
  else
    mkdir -p "$dest"
    cp -R "$src"/. "$dest"/
  fi
  [ -f "${dest}/SKILL.md" ]
}

# Returns 0 if hub install actually landed the skill; 1 if blocked/failed.
# NOTE: as of Hermes 2026-08, `hermes skills install` exits 0 even when the
# skills-guard blocks community packages ("Installation blocked"). We MUST
# parse stdout/stderr — exit code alone is not trustworthy.
install_hub() {
  local skill="$1"
  local identifier="${REPO}/${SKILL_ROOT}/${skill}"
  local out
  local ec=0

  set +e
  out="$(hermes skills install "$identifier" --category "$CATEGORY" --yes 2>&1)"
  ec=$?
  set -e

  # Always show hub output (truncated) for debugging
  echo "$out" | tail -n 12 | sed 's/^/      /'

  if echo "$out" | grep -qiE 'Installation blocked|Blocked \(community|Verdict: DANGEROUS'; then
    return 1
  fi
  if echo "$out" | grep -qiE 'Error:|FAILED|Traceback'; then
    return 1
  fi
  # Success signals
  if echo "$out" | grep -qiE "Installed:|already installed"; then
    return 0
  fi
  # Fall back to exit code only if no clear signal
  [ "$ec" -eq 0 ]
}

echo "Installing Tapway Superpowers into Hermes"
echo "  category : $CATEGORY"
echo "  mode     : $MODE"
echo "  hermes   : $HERMES_HOME_DIR"
if have_local_skills; then
  echo "  local    : $LOCAL_SKILLS_DIR (available)"
else
  echo "  local    : (not available — run from a full git checkout for offline/local mode)"
fi
if [ -n "${HERMES_SKILLS_REF:-}" ]; then
  echo "  ref pin  : $HERMES_SKILLS_REF (applies to local checkout; hub follows default branch)"
fi
echo "  source   : ${REPO}/${SKILL_ROOT}"
echo

installed=0
failed=0
blocked=0
used_local=0
used_hub=0
failed_names=()

for skill in "${SKILLS[@]}"; do
  printf "  • %-22s " "$skill"

  if [ -n "${HERMES_DRY_RUN:-}" ]; then
    case "$MODE" in
      local) echo "(dry-run) local-copy → ${DEST_ROOT}/${skill}" ;;
      hub)   echo "(dry-run) hermes skills install ${REPO}/${SKILL_ROOT}/${skill} --category ${CATEGORY} --yes" ;;
      *)
        if have_local_skills; then
          echo "(dry-run) auto → local-copy ${skill}"
        else
          echo "(dry-run) auto → hub ${skill} (no local fallback)"
        fi
        ;;
    esac
    installed=$((installed + 1))
    continue
  fi

  ok=0
  via=""

  case "$MODE" in
    local)
      if install_local "$skill"; then
        ok=1; via="local"
      fi
      ;;
    hub)
      if install_hub "$skill"; then
        ok=1; via="hub"
      else
        blocked=$((blocked + 1))
      fi
      ;;
    auto|*)
      if have_local_skills; then
        # Prefer local when present: deterministic, version-pinned to checkout,
        # and immune to hub skills-guard false positives.
        if install_local "$skill"; then
          ok=1; via="local"
        fi
      else
        if install_hub "$skill"; then
          ok=1; via="hub"
        else
          blocked=$((blocked + 1))
          # No local fallback available
          ok=0
        fi
      fi
      ;;
  esac

  if [ "$ok" -eq 1 ]; then
    echo "✓ ${via}"
    installed=$((installed + 1))
    if [ "$via" = "local" ]; then used_local=$((used_local + 1)); fi
    if [ "$via" = "hub" ]; then used_hub=$((used_hub + 1)); fi
  else
    echo "✗ FAILED"
    failed=$((failed + 1))
    failed_names+=("$skill")
  fi
done

echo
total=${#SKILLS[@]}

if [ -n "${HERMES_DRY_RUN:-}" ]; then
  echo "[dry-run] Would create bundle: hermes bundles create tapway --skill … (×${total}) --force"
  echo "Dry-run complete: ${installed}/${total} skills would be installed."
  exit 0
fi

# Create (or refresh) the /tapway bundle that loads the whole pipeline.
bundle_args=()
for skill in "${SKILLS[@]}"; do
  bundle_args+=(--skill "$skill")
done
if hermes bundles create tapway \
  "${bundle_args[@]}" \
  --description "Tapway strict engineering pipeline" \
  --force; then
  echo "Bundle: /tapway refreshed"
else
  echo "Warning: hermes bundles create failed — skills may still be usable individually" >&2
fi

echo
echo "Done. ${installed}/${total} skills installed (hub=${used_hub}, local=${used_local}, blocked_or_failed=${failed})."
if [ "$failed" -gt 0 ]; then
  echo "Failed skills: ${failed_names[*]}" >&2
  echo "Hints:" >&2
  echo "  • From a git checkout:  HERMES_INSTALL_MODE=local bash hermes/install.sh ${CATEGORY}" >&2
  echo "  • Hub auth:             gh auth login   (or set GITHUB_TOKEN)" >&2
  echo "  • See:                  hermes/INSTALL_ISSUES.md" >&2
fi

echo "  • Verify:         hermes skills list | grep -E 'tapway|${CATEGORY}'"
echo "  • On disk:        ls \"${DEST_ROOT}\""
echo "  • Pipeline:       /tapway"
echo
echo "Name collisions with Hermes core/community skills (both copies can exist on disk;"
echo "list UIs may show a single bare name): ${NAME_COLLISIONS[*]}"
echo
echo "Recommended memory pin:"
echo "  interview → brainstorming → writing-plans → [tdd] → simplify-code → requesting-code-review → pr"

# Non-zero exit if anything failed — do not claim 24/24 when skills are missing.
if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
