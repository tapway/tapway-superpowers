#!/usr/bin/env bash
# next_version.sh — compute the next SemVer tag for one release stream.
#
#   bash scripts/next_version.sh -stg     # staging      -> v2.11.4-stg
#   bash scripts/next_version.sh -prod    # production   -> v2.11.4-prod
#   bash scripts/next_version.sh ""       # legacy unsuffixed stream
#
# The bump is derived from conventional commits since the last tag OF THE SAME
# STREAM:
#   feat! / BREAKING CHANGE -> major
#   feat:                   -> minor
#   anything else           -> patch
#
# Streams are strictly separated. The production stream (`-prod`) must not see
# `-stg` tags: `git tag -l "v*"` matches them, and a staging release would then
# bump production (that is how v1.1.0-stg once leaked into the v1.x line).
#
# Migration: production used to be tagged WITHOUT a suffix (`v2.11.3`). When a
# suffixed stream has no tag, or the newest plain tag is ahead of that stream's
# newest tag, the plain tag is the baseline. Without that the first `-prod`
# release would restart at v0.0.1-prod, and an old `v1.2.0-stg` would beat the
# live 2.x line.
#
# Pure git — no gh, no network — so tests/test_next_version.py can drive it.
set -euo pipefail

SUFFIX="${1:-}"

# latest_stream_tag: newest semver tag for the selected stream (plain when
# SUFFIX is empty), ignoring CalVer and other suffixes.
latest_stream_tag() {
  git tag -l "v*" | awk -v s="$SUFFIX" '
    {
      core = $0
      if (s != "") {
        if (length($0) <= length(s) || substr($0, length($0) - length(s) + 1) != s) next
        core = substr($0, 1, length($0) - length(s))
      } else {
        if ($0 ~ /-/) next
      }
      if (core ~ /^v[0-9]+\.[0-9]+\.[0-9]+$/) print $0
    }' | sort -V | tail -1
}

LATEST="$(latest_stream_tag)"

if [ -n "$SUFFIX" ]; then
  PLAIN_LATEST="$(git tag -l 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1 || true)"
  if [ -n "$PLAIN_LATEST" ]; then
    if [ -z "$LATEST" ]; then
      LATEST="$PLAIN_LATEST"
    else
      # Compare version cores, not the suffixed strings.
      STREAM_CORE="${LATEST#v}"; STREAM_CORE="${STREAM_CORE%"$SUFFIX"}"
      PLAIN_CORE="${PLAIN_LATEST#v}"
      NEWEST_CORE="$(printf '%s\n%s\n' "$STREAM_CORE" "$PLAIN_CORE" | sort -V | tail -1)"
      if [ "$NEWEST_CORE" = "$PLAIN_CORE" ]; then
        LATEST="$PLAIN_LATEST"
      fi
    fi
  fi
fi

if [ -z "$LATEST" ]; then
  MAJOR=0; MINOR=0; PATCH=0
  RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
else
  VER="${LATEST#v}"
  VER="${VER%"$SUFFIX"}"
  MAJOR="$(echo "$VER" | cut -d. -f1)"
  MINOR="$(echo "$VER" | cut -d. -f2)"
  PATCH="$(echo "$VER" | cut -d. -f3)"
  RANGE="${LATEST}..HEAD"
fi

BUMP="patch"
if git log "$RANGE" --format="%s%n%b" 2>/dev/null | grep -qE '(^feat!:|BREAKING CHANGE)'; then
  BUMP="major"
elif git log "$RANGE" --format="%s" 2>/dev/null | grep -qE '^(feat|feat\()'; then
  BUMP="minor"
fi

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
esac

echo "v${MAJOR}.${MINOR}.${PATCH}${SUFFIX}"