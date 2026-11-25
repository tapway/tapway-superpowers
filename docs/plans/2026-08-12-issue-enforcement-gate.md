# GitHub Issue Enforcement Gate — Implementation Plan

> **Date:** 2026-08-12
> **For Hermes:** This is the tapway-superpowers side of the GitHub ↔ CodeMAX kanban feature. The CodeMAX side (schema, webhook, polling, panel filters) lives at `codemax/docs/plans/2026-08-12-github-issue-kanban-sync.md`.
> **Cross-repo dependency:** The CodeMAX kanban API must be extended with the new fields (`github_issue_id`, `pr_url`, `labels`, `repo`) before this gate writes to it. However, the gate works independently for GitHub lifecycle — it just ensures **every execution has a GitHub issue**.

**Goal:** tapway-superpowers enforces that every Plan→Execute handoff creates a GitHub issue, and push incremental updates (status, PR links, comments) per sub-step.

**Architecture:** tapway-superpowers gains a `pre-execute` hook (or skill) that checks `gh issue list` for the current task. If no issue exists, it auto-creates one with a structured body from the plan doc. As execution progresses, it calls `gh issue comment` and `gh issue edit` to push incremental updates. The CodeMAX webhook (or polling) picks these up and mirrors to the kanban.

**Tech Stack:** `gh` CLI (GitHub CLI), shell scripts, `jq` for JSON parsing, tapway-superpowers hooks system.

---

## Design decisions

| Decision | Choice |
|---|---|
| Gate type | **Pre-execute hook** — runs before any code execution starts |
| Issue creation | Auto-create via `gh issue create` with plan-derived body |
| Incremental push | `gh issue comment` per step + `gh issue edit` on status change |
| PR linking | `gh issue edit` with `--add-assignee` (or body update) to link PR |
| Auth | `gh` CLI authenticated via `~/.git-credentials` or `GITHUB_TOKEN` |
| Repo resolution | From the plan doc's metadata or the current git remote |

---

## Branch 1: feat/issue-enforcement-gate

### Task 1.1: Create the pre-execute hook

**Objective:** Add a `pre-execute` hook to tapway-superpowers that checks for a GitHub issue before proceeding with execution.

**Files:**
- Create: `hooks/pre-execute-github-issue/`
- Create: `hooks/pre-execute-github-issue/check.sh`
- Create: `hooks/pre-execute-github-issue/create.sh`
- Create: `hooks/pre-execute-github-issue/update.sh`

**Step 1: Check if gh CLI is available**

```bash
#!/bin/bash
# hooks/pre-execute-github-issue/check.sh
# Pre-execute gate: ensure a GitHub issue exists for this task.
# Exit 0 = issue exists (or was created), exit 1 = blocked.

set -euo pipefail

if ! command -v gh &>/dev/null; then
    echo "ERROR: gh CLI not found. Install GitHub CLI to use issue enforcement."
    exit 1
fi

# Resolve repo from current git remote
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|')
if [ -z "$REPO" ]; then
    echo "WARNING: No GitHub remote found — skipping issue enforcement."
    exit 0
fi

# Determine the task/plan name from the current branch or plan file
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
TASK_TITLE="${BRANCH//-/ }"  # kebab-case → human-readable
TASK_TITLE="${TASK_TITLE^}"  # Capitalize first letter

# Load plan context if available
PLAN_FILE="docs/plans/$(ls -t docs/plans/ 2>/dev/null | head -1)"
if [ -n "$PLAN_FILE" ] && [ -f "$PLAN_FILE" ]; then
    PLAN_BODY=$(head -20 "$PLAN_FILE" 2>/dev/null)
else
    PLAN_BODY=""
fi

# Check if an issue for this branch already exists
EXISTING_ISSUE=$(gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" --json number,title --jq '.[0].number // "none"' 2>/dev/null)

if [ "$EXISTING_ISSUE" != "none" ]; then
    echo "→ Using existing issue #${EXISTING_ISSUE} for ${BRANCH}"
    echo "GITHUB_ISSUE_NUMBER=$EXISTING_ISSUE" >> "$GITHUB_ENV"
    echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
    exit 0
fi

# Create a new issue
echo "→ Creating GitHub issue for ${BRANCH}..."

# Build issue body
ISSUE_BODY="## Task: ${TASK_TITLE}
**Branch:** \`${BRANCH}\`
**Repo:** ${REPO}
**Status:** todo

### Plan
$(echo "$PLAN_BODY" | head -40)

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
    exit 1
fi

echo "→ Created issue #${ISSUE_NUMBER}: https://github.com/${REPO}/issues/${ISSUE_NUMBER}"
echo "GITHUB_ISSUE_NUMBER=$ISSUE_NUMBER" >> "$GITHUB_ENV"
echo "GITHUB_REPO=$REPO" >> "$GITHUB_ENV"
```

**Step 2: Create incremental update script**

```bash
#!/bin/bash
# hooks/pre-execute-github-issue/update.sh
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

# Update issue body with new status
gh issue edit "$ISSUE_NUMBER" \
    --repo "$REPO" \
    --add-label "status:${STATUS}" \
    --remove-label "status:todo,status:in_progress,status:review,status:done" \
    2>/dev/null || true

# Add a comment with the step update
COMMENT_BODY="**Step update:** ${STATUS}
${MESSAGE}

---
*Pushed by tapway-superpowers*
"

gh issue comment "$ISSUE_NUMBER" \
    --repo "$REPO" \
    --body "$COMMENT_BODY" \
    2>/dev/null || true

echo "→ Pushed ${STATUS} update to issue #${ISSUE_NUMBER}"
```

**Step 3: Wire the hook into the pipeline**

In `hooks/hooks.json`, add the pre-execute gate:

```json
{
  "pre-execute": [
    {
      "name": "github-issue-gate",
      "script": "hooks/pre-execute-github-issue/check.sh",
      "description": "Ensure a GitHub issue exists before executing",
      "blocking": true
    }
  ],
  "on-step-progress": [
    {
      "name": "github-issue-update",
      "script": "hooks/pre-execute-github-issue/update.sh",
      "description": "Push incremental step updates to the GitHub issue"
    }
  ]
}
```

**Step 4: Verify**

```bash
cd /root/projects/tapway-superpowers
# Dry-run: check the script parses correctly
bash -n hooks/pre-execute-github-issue/check.sh
bash -n hooks/pre-execute-github-issue/update.sh
```

Expected: no syntax errors.

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add GitHub issue enforcement gate (pre-execute hook)"
```

---

### Task 1.2: Integrate with the pipeline flow

**Objective:** Make the `autoship` and `tdd` pipeline skills call the update script at key lifecycle points.

**Step 1: Add update calls to the autoship skill**

In the autoship skill's SKILL.md, add calls to the update script at each phase transition:

```bash
# After Plan phase
hooks/pre-execute-github-issue/update.sh "in_progress" "Planning complete — starting implementation"

# After TDD (all tests pass)
hooks/pre-execute-github-issue/update.sh "in_progress" "TDD phase complete — all tests pass"

# After PR is opened
hooks/pre-execute-github-issue/update.sh "review" "PR opened for review: $PR_URL"

# After merge
hooks/pre-execute-github-issue/update.sh "done" "Merged to main"
```

**Step 2: Verify**

```bash
cd /root/projects/tapway-superpowers
# Full syntax check
bash -n hooks/pre-execute-github-issue/*.sh
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: integrate issue updates into pipeline flow"
```

---

## Verification checklist

- [ ] `check.sh` detects missing `gh` CLI and exits with clear error
- [ ] Auto-creates issue with plan-derived body when none exists
- [ ] Reuses existing issue when found (by branch tag in body)
- [ ] `update.sh` pushes status updates via `gh issue comment`
- [ ] `update.sh` manages labels (removes old status label, adds new)
- [ ] Exports `GITHUB_ISSUE_NUMBER` and `GITHUB_REPO` for downstream use
- [ ] Shell scripts pass `bash -n` syntax check
- [ ] All scripts are idempotent (safe to re-run)