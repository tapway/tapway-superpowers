#!/usr/bin/env bash
# install.sh — Install Tapway Superpowers skills into Hermes Agent
#
# Copies the 6 Tapway-specific skills into your Hermes skills directory and
# optionally reminds you to pin the dev process to memory. Idempotent: re-running
# just refreshes the files.
#
# Usage:
#   bash install.sh [path-to-hermes-skills-dir]
#
# If no path is given it auto-detects the default Hermes skills location.

set -euo pipefail

# --- locate this script's skills folder (parent of this file) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR"

# --- locate Hermes skills dir ---
if [ "$#" -ge 1 ]; then
  HERMES_SKILLS="$1"
elif [ -n "${HERMES_SKILLS_HOME:-}" ]; then
  HERMES_SKILLS="$HERMES_SKILLS_HOME"
elif [ -n "${HERMES_HOME:-}" ]; then
  HERMES_SKILLS="$HERMES_HOME/skills"
elif [ -n "${XDG_CONFIG_HOME:-}" ]; then
  HERMES_SKILLS="$XDG_CONFIG_HOME/hermes/skills"
elif [ -n "${APPDATA:-}" ]; then
  HERMES_SKILLS="$APPDATA/Local/hermes/skills"
else
  HERMES_SKILLS="$HOME/Local/hermes/skills"
  # Fallback for common layouts
  [ -d "$HOME/.hermes/skills" ] && HERMES_SKILLS="$HOME/.hermes/skills"
fi

# Skills this installer brings (Tapway-specific; others already exist in Hermes core)
SKILLS=(interview brainstorming writing-plans tdd repo-docs pr)

echo "Source : $SRC_DIR"
echo "Target : $HERMES_SKILLS"
echo

mkdir -p "$HERMES_SKILLS/tapway"

for s in "${SKILLS[@]}"; do
  if [ -f "$SRC_DIR/$s/SKILL.md" ]; then
    mkdir -p "$HERMES_SKILLS/tapway/$s"
    cp "$SRC_DIR/$s/SKILL.md" "$HERMES_SKILLS/tapway/$s/SKILL.md"
    echo "  ✓ installed tapway/$s"
  else
    echo "  ! missing source for $s (skipped)"
  fi
done

echo
echo "Done. Restart Hermes (or run 'hermes skills list' to verify)."
echo
echo "Recommended: pin the dev process to memory so it runs on every task:"
echo "  interview → brainstorming → writing-plans → [tdd] → simplify-code → requesting-code-review → pr"
echo "You can do this via the Hermes memory tool or by editing your profile's memory file."
