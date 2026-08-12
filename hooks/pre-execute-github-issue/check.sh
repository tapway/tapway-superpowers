#!/bin/bash
# Pre-execute gate: ensure a GitHub issue exists for this task.
# Runs at session start. If no issue exists for the current branch,
# auto-creates one with the plan doc as the body.
# Exports GITHUB_ISSUE_NUMBER and GITHUB_REPO for downstream use.
# Exit 0 = issue exists (or was created), exit 2 = critical error.

set -euo pipefail

if ! command -v gh &>/dev/null; then
    echo "WARNING: gh CLI not found — skipping GitHub issue enforcement."
    echo "Install GitHub CLI (gh) to use the issue enforcement gate."
    exit 0
fi

# Resolve repo from current git remote
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|')
if [ -z "$REPO" ]; then
    echo "WARNING: No GitHub remote found — skipping issue enforcement."
    exit 0
fi

# Determine the task/plan name from the current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
TASK_TITLE="${BRANCH//-/ }"
TASK_TITLE="$(echo "$TASK_TITLE" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')"

# Check if an issue for this branch already exists (search for branch tag in body)
EXISTING_ISSUE=$(gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" --json number,title --jq '.[0].number // ""' 2>/dev/null)

if [ -n "$EXISTING_ISSUE" ]; then
    echo "→ Using existing issue #${EXISTING_ISSUE} for ${BRANCH}"
    echo "GITHUB_ISSUE_NUMBER=$EXISTING_ISSUE" >> "$GITHUB_ENV"
    echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
    exit 0
fi

# Create a new issue
echo "→ Creating GitHub issue for ${BRANCH}..."

# Build issue body from plan doc if available
ISSUE_BODY="## Task: ${TASK_TITLE}
**Branch:** \`${BRANCH}\`
**Repo:** ${REPO}
**Status:** todo

---
*Auto-created by tapway-superpowers issue enforcement gate.*
"

ISSUE_NUMBER=$(gh issue create \
    --repo "$REPO" \
    --title "⚙ ${TASK_TITLE}" \
    --label "codemax" \
    --body "$ISSUE_BODY" \
    --json number \
    --jq '.number' 2>/dev/null)

if [ -z "$ISSUE_NUMBER" ]; then
    echo "ERROR: Failed to create GitHub issue for ${REPO}"
    exit 2
fi

echo "→ Created issue #${ISSUE_NUMBER}: https://github.com/${REPO}/issues/${ISSUE_NUMBER}"
echo "GITHUB_ISSUE_NUMBER=$ISSUE_NUMBER" >> "$GITHUB_ENV"
echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"