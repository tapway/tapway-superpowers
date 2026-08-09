#!/usr/bin/env bash
#
# install.sh — Install all 23 Tapway Superpowers skills into Hermes Agent
#              (gbrain-style: one command scaffolds the whole skillpack).
#
# Unlike the earlier copy-based installer, this uses Hermes's native skill hub.
# Each skill is installed by its GitHub identifier, so there is no dependence
# on local file layout — it works from anywhere, stays in sync with the repo,
# and is idempotent (re-running just refreshes/updates nothing that changed).
#
# After installing the skills it creates a `/tapway` skill bundle so you can
# load the whole strict pipeline with a single slash command.
#
# Usage:
#   bash install.sh                                 # default category: tapway
#   bash install.sh <hermes-skills-category>        # e.g. "sweng"
#
# Prereqs:
#   - `hermes` CLI on PATH (hermes-agent installed)
#   - Skills are fetched from the tapway/tapway-superpowers GitHub repo, so an
#     authenticated GitHub (gh auth login, or GITHUB_TOKEN) is recommended to
#     avoid unauthenticated API rate limits (60 req/hr).
#
# Dry-run / preview first (no writes):
#   HERMES_DRY_RUN=1 bash install.sh

set -euo pipefail

REPO="tapway/tapway-superpowers"
SKILL_ROOT="hermes/skills"
CATEGORY="${1:-tapway}"

# All 23 ported skills. Order = pipeline order.
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
  pr
  repo-docs
  git-worktrees
  setup-project
)

if ! command -v hermes >/dev/null 2>&1; then
  echo "Error: 'hermes' CLI not found on PATH." >&2
  echo "Install Hermes Agent first:  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash" >&2
  exit 1
fi

echo "Installing Tapway Superpowers into Hermes (category: $CATEGORY)"
echo "Source repo: $REPO/$SKILL_ROOT"
echo

installed=0
for skill in "${SKILLS[@]}"; do
  identifier="$REPO/$SKILL_ROOT/$skill"
  printf "  • %-20s " "$skill"

  if [ -n "${HERMES_DRY_RUN:-}" ]; then
    echo "(dry-run) hermes skills install $identifier --category $CATEGORY --yes"
    installed=$((installed + 1))
    continue
  fi

  if hermes skills install "$identifier" --category "$CATEGORY" --yes; then
    echo "✓ installed tapway/$skill"
    installed=$((installed + 1))
  else
    echo "✗ FAILED to install tapway/$skill" >&2
    echo "  Try: HERMES_DRY_RUN=1 bash install.sh  (preview the commands)" >&2
    echo "  Or authenticate GitHub: gh auth login  (avoids rate limits)" >&2
  fi
done

echo
if [ -n "${HERMES_DRY_RUN:-}" ]; then
  echo "[dry-run] Would create bundle:"
  echo "          hermes bundles create tapway \\"
  n=${#SKILLS[@]}
  for i in "${!SKILLS[@]}"; do
    suffix="\\"
    [ $((i + 1)) -eq "$n" ] && suffix=""
    printf "            --skill %s %s\n" "${SKILLS[$i]}" "$suffix"
  done
  echo "            --description \"Tapway strict engineering pipeline\" --force"
  echo
  echo "Dry-run complete: $installed/$installed skills would be installed."
  exit 0
fi

# Create (or refresh) the /tapway bundle that loads the whole pipeline.
bundle_args=()
for skill in "${SKILLS[@]}"; do
  bundle_args+=(--skill "$skill")
done
hermes bundles create tapway \
  "${bundle_args[@]}" \
  --description "Tapway strict engineering pipeline" \
  --force

echo
echo "Done. $installed/$installed skills installed."
echo "  • Verify:         hermes skills list | grep tapway"
echo "  • Run the whole pipeline:  /tapway"
echo "  • Or invoke a single step: /interview /brainstorming /writing-plans /tdd ... /pr"
echo
echo "Recommended: pin the dev process to memory so it runs on every task:"
echo "  interview → brainstorming → writing-plans → [tdd] → simplify-code → requesting-code-review → pr"
echo "You can do this via the Hermes memory tool or by editing your profile's memory file."
