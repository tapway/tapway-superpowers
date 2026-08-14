#!/bin/bash
# Create a GitHub issue for a task, hydrated with the plan content.
# Call this AFTER brainstorming/planning, right before execution —
# NOT at session start. The issue body is built from docs/plans/[feature].md
# so the GitHub ticket carries real context, not a bare branch name.
#
# Usage: create-issue.sh [plan-file]
#   plan-file: path to the plan doc (default: auto-detect latest in docs/plans/)
#
# Exports GITHUB_ISSUE_NUMBER / GITHUB_REPO for downstream use.
# Exits 0 if an issue already exists for the branch (reuses it).

set -euo pipefail

REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|' | sed -E 's|\.git$||')
if [ -z "$REPO" ]; then
    echo "ERROR: No GitHub remote found." >&2
    exit 2
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
TASK_TITLE="${BRANCH//-/ }"
TASK_TITLE="$(echo "$TASK_TITLE" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')"

# Is there already an issue for this branch?
EXISTING=$(gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" --json number --jq '.[0].number // ""' 2>/dev/null)
if [ -n "$EXISTING" ]; then
    echo "→ Reusing existing issue #${EXISTING}: https://github.com/${REPO}/issues/${EXISTING}"
    if [ -n "${GITHUB_ENV:-}" ]; then
        echo "GITHUB_ISSUE_NUMBER=$EXISTING" >> "$GITHUB_ENV"
        echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
    fi
    exit 0
fi

# Resolve the plan file: explicit arg, else newest in docs/plans/
PLAN_FILE="${1:-}"
if [ -z "$PLAN_FILE" ] && [ -d "docs/plans" ]; then
    PLAN_FILE=$(ls -t docs/plans/*.md 2>/dev/null | head -1 || true)
fi

# Build the issue body
{
    echo "## Task: ${TASK_TITLE}"
    echo "**Branch:** \`${BRANCH}\`"
    echo "**Repo:** ${REPO}"
    echo "**Status:** todo"
    echo ""
    echo "---"
    echo ""
    if [ -n "$PLAN_FILE" ] && [ -f "$PLAN_FILE" ]; then
        echo "_Plan: \`${PLAN_FILE}\`_"
        echo ""
        echo "<details><summary>📋 Implementation plan</summary>"
        echo ""
        cat "$PLAN_FILE"
        echo ""
        echo "</details>"
    else
        echo "_No plan doc attached yet — plan will be added during brainstorming/planning._"
    fi
    echo ""
    echo "---"
    echo ""
    echo "*Auto-created by tapway-superpowers issue enforcement gate (post-plan).*"
} > /tmp/gh-issue-body.md

ISSUE_NUMBER=$(gh issue create \
    --repo "$REPO" \
    --title "⚙ ${TASK_TITLE}" \
    --label "codemax" \
    --body-file /tmp/gh-issue-body.md \
    --json number \
    --jq '.number' 2>/dev/null)

rm -f /tmp/gh-issue-body.md

if [ -z "$ISSUE_NUMBER" ]; then
    echo "ERROR: Failed to create GitHub issue for ${REPO}" >&2
    exit 2
fi

echo "→ Created issue #${ISSUE_NUMBER}: https://github.com/${REPO}/issues/${ISSUE_NUMBER}"
if [ -n "${GITHUB_ENV:-}" ]; then
    echo "GITHUB_ISSUE_NUMBER=$ISSUE_NUMBER" >> "$GITHUB_ENV"
    echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
fi