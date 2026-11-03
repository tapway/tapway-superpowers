#!/usr/bin/env bash
# Mirror hermes/skills/ into the Hermes plugin package.
#
#   ./scripts/sync-hermes-plugin-skills.sh          # refresh hermes/plugin/skills
#   ./scripts/sync-hermes-plugin-skills.sh --check   # exit 1 when the mirror drifts
#
# The plugin ships its own copy of the skills so `hermes plugins install` can
# install a self-contained subdirectory. Editing hermes/skills/ without running
# this leaves the two trees out of sync; tests/test_hermes_plugin.py fails when
# they differ, and CI runs --check on every PR.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/hermes/skills"
DST="$ROOT/hermes/plugin/skills"
MODE="${1:-sync}"

if [ ! -d "$SRC" ]; then
  echo "error: $SRC does not exist" >&2
  exit 2
fi

if [ "$MODE" = "--check" ]; then
  if diff -r "$SRC" "$DST"; then
    echo "hermes/plugin/skills is in sync with hermes/skills"
    exit 0
  fi
  echo "error: hermes/plugin/skills drifted from hermes/skills — run $0" >&2
  exit 1
fi

if [ "$MODE" != "sync" ]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

mkdir -p "$DST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$SRC/" "$DST/"
else
  find "$DST" -mindepth 1 -delete
  cp -a "$SRC/." "$DST/"
fi
echo "synced $SRC -> $DST"