#!/bin/bash
# Push an incremental status update to the GitHub issue.
# Usage: ./update.sh <status> <message>
#   status: todo | in_progress | review | done
#   message: human-readable description of the current step

set -euo pipefail

STATUS="${1:?Usage: update.sh <status> <message>}"
MESSAGE="${2:?Usage: update.sh <status> <message>}"
REPO="${GITHUB_REPO:-}"
ISSUE_NUMBER="${GITHUB_ISSUE_NUMBER:-}"

if [ -z "$REPO" ] || [ -z "$ISSUE_NUMBER" ]; then
    echo "WARNING: GITHUB_REPO or GITHUB_ISSUE_NUMBER not set — skipping update."
    exit 0
fi

# Map status labels
LABEL_STATUS="status:${STATUS}"

# Remove any existing status label, add the new one
# (gh --remove-label accepts a single label or comma list; remove each status label)
for OLD in status:todo status:in_progress status:review status:done; do
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-label "$OLD" 2>/dev/null || true
done
gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --add-label "$LABEL_STATUS" 2>/dev/null || true

# Add a comment with the step update
COMMENT_BODY="**Progress update:** ${STATUS}
${MESSAGE}

---
*Pushed by tapway-superpowers*
"

gh issue comment "$ISSUE_NUMBER" \
    --repo "$REPO" \
    --body "$COMMENT_BODY" \
    2>/dev/null || true

echo "→ Pushed ${STATUS} update to issue #${ISSUE_NUMBER}"