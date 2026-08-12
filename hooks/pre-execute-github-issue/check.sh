#!/bin/bash
# Session-start check: detect whether a GitHub issue already exists for this
# branch. This script NEVER creates an issue — it only detects one.
#
# The issue is created AFTER brainstorming/planning, hydrated with the plan
# content, right before execution (see create-issue.sh + writing-plans skill).
# Creating an empty issue here from just a branch name would pollute GitHub
# with a worthless ticket before the task is even understood.
#
# Exports GITHUB_ISSUE_NUMBER / GITHUB_REPO when an issue already exists.
# Exit 0 always (informational — never blocks a session on issue bookkeeping).

set -euo pipefail

if ! command -v gh &>/dev/null; then
    echo "ℹ️  gh CLI not found — skipping GitHub issue detection."
    exit 0
fi

# Resolve repo from current git remote
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|')
if [ -z "$REPO" ]; then
    echo "ℹ️  No GitHub remote found — skipping issue detection."
    exit 0
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Look for an issue that already references this branch (existing only)
EXISTING_ISSUE=$(gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" --json number,title --jq '.[0].number // ""' 2>/dev/null)

if [ -n "$EXISTING_ISSUE" ]; then
    echo "→ Existing GitHub issue #${EXISTING_ISSUE} found for branch ${BRANCH}"
    if [ -n "${GITHUB_ENV:-}" ]; then
        echo "GITHUB_ISSUE_NUMBER=$EXISTING_ISSUE" >> "$GITHUB_ENV"
        echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
    else
        echo "  GITHUB_ISSUE_NUMBER=$EXISTING_ISSUE (GITHUB_ENV unset)"
    fi
else
    echo "→ No GitHub issue yet for branch ${BRANCH}."
    echo "  It will be auto-created after the brainstorming/plan step (Writing Plans skill)."
fi

exit 0