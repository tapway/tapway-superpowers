#!/usr/bin/env bash
# next_version.sh — compute the next SemVer tag for one release stream.
#
#   bash scripts/next_version.sh -stg     # staging      -> v2.11.4-stg
#   bash scripts/next_version.sh -prod    # production   -> v2.11.4-prod
#   bash scripts/next_version.sh ""       # legacy unsuffixed stream
#
# The bump is derived from conventional commits since the last tag OF THE SAME
# STREAM:
#   "type!:" subject, or a "BREAKING CHANGE:" footer line -> major
#   feat:                   -> minor
#   anything else           -> patch
#
# The two streams share one version line:
#   -prod takes the newest -stg version merged into HEAD, when it is ahead.
#   -stg  continues from -prod when a hotfix has put production ahead.
# Otherwise each bumps from its own newest tag.
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

# newer A B: true when version core A is strictly higher than B.
newer() {
  [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -1)" = "$1" ]
}
core_of() { local v="${1#v}"; echo "${v%%-*}"; }
BASE_CORE="$(core_of "${LATEST:-v0.0.0}")"

# Parity: production releases the version staging gave the same code. Only a
# -stg tag already merged into HEAD counts, so unpromoted work is never claimed.
# With nothing newer from staging (a hotfix, or no staging branch) production
# bumps its own line below.
if [ "$SUFFIX" = "-prod" ]; then
  STG="$(git tag --merged HEAD -l 'v*-stg' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+-stg$' | sort -V | tail -1 || true)"
  if [ -n "$STG" ] && newer "$(core_of "$STG")" "$BASE_CORE"; then
    echo "v$(core_of "$STG")-prod"
    exit 0
  fi
fi

# The other direction: after a production hotfix, staging continues from it.
if [ "$SUFFIX" = "-stg" ]; then
  PROD="$(git tag -l 'v*-prod' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+-prod$' | sort -V | tail -1 || true)"
  if [ -n "$PROD" ] && newer "$(core_of "$PROD")" "$BASE_CORE"; then
    LATEST="$PROD"
  fi
fi

if [ -z "$LATEST" ]; then
  MAJOR=0; MINOR=0; PATCH=0
  RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
else
  VER="$(core_of "$LATEST")"
  MAJOR="$(echo "$VER" | cut -d. -f1)"
  MINOR="$(echo "$VER" | cut -d. -f2)"
  PATCH="$(echo "$VER" | cut -d. -f3)"
  RANGE="${LATEST}..HEAD"
fi

BUMP="patch"
# A baseline tag that is not an ancestor means the branch history was rewritten
# (a squashed staging sync). `tag..HEAD` then reaches the abandoned history and
# an old `feat!` there would force a major bump for an unrelated release. With
# no trustworthy commit range, take the conservative patch bump from the line
# being continued; subsequent releases see their own tag as an ancestor again.
if [ -z "$LATEST" ] || git merge-base --is-ancestor "$LATEST" HEAD 2>/dev/null; then
  # First-parent only: a promotion/sync merge brings another branch's whole
  # history into `tag..HEAD`, and an old `feat!` there must not classify this
  # release. Squash merges land as a single first-parent commit, so their
  # conventional title is still read.
  if git log --first-parent "$RANGE" --format="%s" 2>/dev/null | grep -qE '^[a-z]+(\([^)]*\))?!:' ||
     git log --first-parent "$RANGE" --format="%b" 2>/dev/null | grep -qE '^BREAKING[ -]CHANGE:'; then
    BUMP="major"
  elif git log --first-parent "$RANGE" --format="%s" 2>/dev/null | grep -qE '^(feat|feat\()'; then
    BUMP="minor"
  fi
fi

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
esac

echo "v${MAJOR}.${MINOR}.${PATCH}${SUFFIX}"