---
name: setup-project
description: >
  One-time project setup for teams adopting tapway-superpowers: creates the
  @claude GitHub Actions workflow, verifies CLAUDE.md exists, and prints a
  checklist of any remaining manual steps (GitHub secret). Triggers include
  "set up the @claude workflow", "set up the @claude GitHub Actions workflow",
  "add @claude to this repo", "setup project", "initialize project for the team",
  "project setup".
---

# Skill: Setup Project

**When to invoke:** First time the plugin is adopted in a project repo, or when the session-start hook reports that `.github/workflows/claude.yml` is missing.

---

## What It Does

1. Creates `.github/workflows/claude.yml` — enables `@claude` in PR comments
2. Verifies `CLAUDE.md` exists — the project's source of truth for Claude
3. Commits both files and pushes to the current branch
4. Prints a manual-steps checklist for anything that can't be automated (GitHub secret)

---

## Protocol

### Step 1 — Check Current State

```bash
ls .github/workflows/claude.yml 2>/dev/null && echo "EXISTS" || echo "MISSING"
ls CLAUDE.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
git branch --show-current
```

Report what's missing before making any changes.

### Step 2 — Create the @claude Workflow

If `.github/workflows/claude.yml` does not exist, create it:

```bash
mkdir -p .github/workflows
```

Write the following content exactly to `.github/workflows/claude.yml`:

```yaml
name: Claude Code

on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  pull_request_review:
    types: [submitted]

jobs:
  # Runs automatically on every PR open or update.
  # Read-only: posts review comments but cannot push fix commits.
  auto-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      id-token: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          direct_prompt: |
            Review this pull request. Read the diff carefully and check for:

            **Critical** (must fix before merge):
            - Correctness bugs — logic errors, wrong conditions, off-by-one
            - Security issues — injection, exposed secrets, missing auth, OWASP Top 10
            - Data loss risks — unhandled errors on writes, missing rollbacks
            - Broken contracts — API response shape changes, removed required fields

            **Warnings** (should fix, or justify in PR body):
            - Missing test coverage for new logic
            - Type safety gaps — `any`, unchecked casts, implicit nulls
            - Performance issues — N+1 queries, unbounded loops, large payloads
            - Error handling gaps on external calls

            **Suggestions** (optional improvements):
            - Simplification opportunities
            - Naming clarity
            - Duplication that could be extracted

            Format:
            - Post findings as inline review comments on the specific lines where possible
            - If there are Critical findings, request changes
            - If there are only Warnings/Suggestions, approve with comments
            - If everything looks good, approve with a one-paragraph summary
            - Start your review summary with "## Auto-review" so it's clear this is automated

  # Fires when @claude is mentioned in a PR comment, review, or issue comment.
  # Read-write: can push fix commits to the branch in addition to commenting.
  on-mention:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Step 3 — Verify CLAUDE.md

If `CLAUDE.md` does not exist at the project root, create a minimal one:

```markdown
# [Project Name]

## Project Overview
[One paragraph description — fill this in]

## Stack
- Backend: [e.g. Python FastAPI]
- Frontend: [e.g. Next.js 14]
- Database: [e.g. PostgreSQL]
- Infrastructure: [e.g. Docker + GitHub Actions]

## Key Commands
- Run backend: [command]
- Run frontend: [command]
- Run tests: [command]
- Run linter: [command]

## Conventions
- [Key naming or structure conventions for this project]

## Do Not
- [Things Claude should never do in this repo]
```

Tell the user: "I've created a minimal CLAUDE.md. Fill in the stack, commands, and conventions before the team starts using it — Claude reads this every session."

### Step 4 — Commit and Push

```bash
git add .github/workflows/claude.yml
git add CLAUDE.md  # only if newly created
git commit -m "chore: add @claude GitHub Actions workflow and CLAUDE.md"
git push
```

If on `main` and the pre-bash hook blocks the push (it blocks direct commits to main), create a branch:

```bash
git checkout -b chore/setup-claude-workflow
git push -u origin chore/setup-claude-workflow
```

Then tell the user to merge it via PR.

### Step 5 — Print Manual Steps Checklist

After committing, print this checklist for the user:

```
## Project Setup Complete ✅

Automated:
  ✅ .github/workflows/claude.yml created
  ✅ CLAUDE.md created (or already existed)
  ✅ Changes committed and pushed

Manual steps still required:
  ☐ Add ANTHROPIC_API_KEY to GitHub repo secrets
      → GitHub repo → Settings → Secrets and variables → Actions → New repository secret
      → Name: ANTHROPIC_API_KEY
      → Value: your Anthropic API key (https://console.anthropic.com)

  ☐ Fill in CLAUDE.md (stack, commands, conventions)
      → This is what Claude reads every session to understand your project

  ☐ Test auto-review: open any PR — Claude should post an "## Auto-review" comment automatically within ~30 seconds
  ☐ Test @claude: comment "@claude explain what this PR does" on any PR — Claude should reply and can push fix commits
```

---

## Hard Rules

- ❌ Never overwrite an existing `.github/workflows/claude.yml` — if it exists, skip Step 2 and say "already set up"
- ❌ Never overwrite an existing `CLAUDE.md` — if it exists, skip Step 3 and say "already exists"
- ❌ Never push directly to `main` — if the hook blocks it, create a setup branch instead
