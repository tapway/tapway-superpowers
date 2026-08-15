#!/usr/bin/env bash
#
# install.sh — Install all 24 Tapway Superpowers skills + enforceable hooks
#              into OpenAI Codex.
#
# Codex discovers skills in:
#   ~/.agents/skills/<name>/SKILL.md                    (USER scope, all repos)
#   <project>/.agents/skills/<name>/SKILL.md            (REPO scope, one project)
# Hooks + config live in:
#   <project>/.codex/hooks.json                         (project hooks)
#   <project>/.codex/hooks/<script>.sh                  (hook scripts)
#   <project>/AGENTS.md                                 (pipeline directive)
#
# This installer copies all 24 skills + the $tapway umbrella to the chosen
# scope, writes the .codex/ hook tree + hooks.json into a consuming project,
# and (optionally) drops the AGENTS.md pipeline directive into it.
#
# Usage:
#   bash codex/install.sh                 # user scope (skills only)
#   CODEX_TARGET_PROJECT=/path/to/proj bash codex/install.sh   # user skills + project hooks/AGENTS
#   bash codex/install.sh repo            # repo scope for skills (skills only)
#
# Env:
#   CODEX_SKILL_SCOPE=user|repo   scope for skills (default: user)
#   CODEX_TARGET_PROJECT=<dir>    consuming project to wire hooks + AGENTS.md into
#   CODEX_DRY_RUN=1               preview commands, no writes
#
# See codex/README.md for the one-time hooks trust-review step.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="${SCRIPT_DIR}/skills"
HOOK_SRC="${SCRIPT_DIR}/hooks"
HJSON_TEMPLATE="${SCRIPT_DIR}/hooks.json.template"
AGENTS_TEMPLATE="${SCRIPT_DIR}/templates/AGENTS.md"

SKILL_SCOPE="${CODEX_SKILL_SCOPE:-user}"
TARGET_PROJECT="${CODEX_TARGET_PROJECT:-}"
DRY_RUN="${CODEX_DRY_RUN:-0}"

# The 24 ported skills (Claude's set). dependency-audit stays a hook, not a skill.
SKILLS=(
  interview
  brainstorming
  writing-plans
  tdd
  e2e-playwright
  quality-gates
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

# Plus the $tapway umbrella that chains the whole pipeline.
UMBRELLA=(tapway)

if [ "$SKILL_SCOPE" = "user" ]; then
  SKILL_DEST="${HOME}/.agents/skills"
elif [ "$SKILL_SCOPE" = "repo" ]; then
  # Repo scope requires a target project (defaults to current repo).
  TARGET_PROJECT="${TARGET_PROJECT:-$(pwd)}"
  SKILL_DEST="${TARGET_PROJECT}/.agents/skills"
else
  echo "Error: CODEX_SKILL_SCOPE must be 'user' or 'repo' (got: $SKILL_SCOPE)" >&2
  exit 1
fi

echo "Installing Tapway Superpowers into Codex"
echo "  skill scope    : $SKILL_SCOPE -> $SKILL_DEST"
[ -n "$TARGET_PROJECT" ] && echo "  target project : $TARGET_PROJECT (hooks + AGENTS.md)"
echo "  dry-run        : $DRY_RUN"
echo

install_skill_dir() {
  local name="$1"
  local src="${SKILL_SRC}/${name}"
  local dest="${SKILL_DEST}/${name}"
  if [ ! -d "$src" ] || [ ! -f "${src}/SKILL.md" ]; then
    echo "  local source missing: $src" >&2
    return 1
  fi
  mkdir -p "$SKILL_DEST"
  rm -rf "$dest"
  if cp -a "$src" "$dest" 2>/dev/null; then
    :
  else
    mkdir -p "$dest"
    cp -R "$src"/. "$dest"/
  fi
  [ -f "${dest}/SKILL.md" ]
}

installed=0
failed=0
for skill in "${SKILLS[@]}" "${UMBRELLA[@]}"; do
  printf "  • %-22s " "$skill"
  if [ "$DRY_RUN" = "1" ]; then
    echo "(dry-run) -> ${SKILL_DEST}/${skill}"
    installed=$((installed + 1))
    continue
  fi
  if install_skill_dir "$skill"; then
    echo "✓"
    installed=$((installed + 1))
  else
    echo "✗ FAILED"
    failed=$((failed + 1))
  fi
done

# --- Wire hooks + AGENTS.md into a consuming project (optional) ---
if [ -n "$TARGET_PROJECT" ] && [ "$DRY_RUN" != "1" ]; then
  if [ ! -d "$TARGET_PROJECT" ]; then
    echo "Error: CODEX_TARGET_PROJECT does not exist: $TARGET_PROJECT" >&2
    exit 1
  fi

  # .codex/hooks.json from template
  mkdir -p "$TARGET_PROJECT/.codex"
  cp "$HJSON_TEMPLATE" "$TARGET_PROJECT/.codex/hooks.json"

  # Hook scripts into .codex/hooks/
  mkdir -p "$TARGET_PROJECT/.codex/hooks"
  for hook in "$HOOK_SRC"/*.sh; do
    [ -f "$hook" ] || continue
    cp "$hook" "$TARGET_PROJECT/.codex/hooks/" && chmod +x "$TARGET_PROJECT/.codex/hooks/$(basename "$hook")"
  done

  # AGENTS.md pipeline directive (never overwrite an existing one)
  if [ -f "$TARGET_PROJECT/AGENTS.md" ]; then
    echo "  • AGENTS.md exists — skipping template (pipeline already enforced)."
  else
    cp "$AGENTS_TEMPLATE" "$TARGET_PROJECT/AGENTS.md"
    echo "  • Wrote $TARGET_PROJECT/AGENTS.md (pipeline directive)."
  fi

  echo "  • Wrote $TARGET_PROJECT/.codex/hooks.json"
  echo "  • Copied $(ls "$HOOK_SRC"/*.sh | wc -l | tr -d ' ') hook scripts to $TARGET_PROJECT/.codex/hooks/"
  echo
  echo "⚠️  NEXT: Codex requires a one-time TRUST REVIEW before non-managed hooks run."
  echo "   Start Codex in the project and run:  /hooks"
  echo "   Review and approve the Tapway hooks. See codex/README.md."
fi

echo
echo "Done. ${installed}/$(( ${#SKILLS[@]} + ${#UMBRELLA[@]} )) skills installed (failed=${failed})."
echo "Verify : ls \"${SKILL_DEST}\""
echo "Trigger: \$tapway  (or follow a step via \$interview, \$brainstorming, \$writing-plans, \$tdd, \$code-review, \$pr)"
if [ "$failed" -gt 0 ]; then
  echo "Note: $failed skills failed to install (missing source?)." >&2
  exit 1
fi
exit 0