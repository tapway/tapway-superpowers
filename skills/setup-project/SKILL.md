---
name: setup-project
description: >
  One-time project setup for teams adopting tapway-superpowers: creates the
  @claude GitHub Actions workflow, the auto-release workflow (YYYY.WW.XX.YY-env
  CalVer), verifies CLAUDE.md exists with TARGET_BRANCH set, commits everything,
  and prints a checklist of remaining manual steps. Triggers include "set up the
  @claude workflow", "set up the @claude GitHub Actions workflow", "add @claude
  to this repo", "setup project", "initialize project for the team",
  "project setup".
---

# Skill: Setup Project

**When to invoke:** First time the plugin is adopted in a project repo, or when the session-start hook reports that `.github/workflows/claude.yml` is missing.

---

## What It Does

1. Creates `.github/workflows/claude.yml` — auto-review on every PR + `@claude` fix commands
2. Creates `.github/workflows/release.yml` — CalVer auto-release on merge to `staging` / `prod`
3. Creates `CLAUDE.md` (if missing) with `TARGET_BRANCH: staging` pre-filled
4. Commits all files and pushes
5. Prints a manual-steps checklist (GitHub secret, filling in CLAUDE.md)

---

## Protocol

### Step 1 — Check Current State

```bash
ls .github/workflows/claude.yml   2>/dev/null && echo "EXISTS" || echo "MISSING"
ls .github/workflows/release.yml  2>/dev/null && echo "EXISTS" || echo "MISSING"
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

### Step 3 — Create the Auto-Release Workflow

If `.github/workflows/release.yml` does not exist, write the following content exactly to `.github/workflows/release.yml`:

```yaml
name: Auto Release

# Fires on every merge to staging or prod.
# Computes a CalVer tag: YYYY.WW.XX.YY-stg or YYYY.WW.XX.YY-prod
#
# YYYY = year, WW = ISO week number (01-53)
# XX   = major increment within the week (resets to 1 each new week)
# YY   = minor increment within XX (bugfixes, small changes)
#
# XX increments when any merged commit contains "feat!" or "BREAKING CHANGE".
# YY increments for all other merges.

on:
  push:
    branches:
      - staging
      - prod

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Compute next version
        id: ver
        run: |
          set -e
          YEAR=$(date +%Y)
          WEEK=$(date +%V)
          BRANCH="${GITHUB_REF_NAME}"
          ENV="-stg"
          [ "$BRANCH" = "prod" ] && ENV="-prod"
          PREFIX="${YEAR}.${WEEK}."
          LATEST=$(git tag -l "${PREFIX}*${ENV}" 2>/dev/null | sort -V | tail -1)
          if [ -z "$LATEST" ]; then
            XX=1; YY=0
          else
            INNER=${LATEST#"${PREFIX}"}; INNER=${INNER%"${ENV}"}
            XX=$(echo "$INNER" | cut -d. -f1); YY=$(echo "$INNER" | cut -d. -f2)
            if git log "${LATEST}..HEAD" --format="%s%n%b" 2>/dev/null \
               | grep -qE '(^feat!|BREAKING CHANGE)'; then
              XX=$((XX + 1)); YY=0
            else
              YY=$((YY + 1))
            fi
          fi
          VERSION="${YEAR}.${WEEK}.${XX}.${YY}${ENV}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "Computed version: ${VERSION}"

      - name: Tag and publish release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ steps.ver.outputs.version }}"
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag "$VERSION"
          git push origin "$VERSION"
          gh release create "$VERSION" \
            --title "$VERSION" \
            --target "${{ github.ref_name }}" \
            --generate-notes
```

### Step 4 — Verify CLAUDE.md

If `CLAUDE.md` does not exist at the project root, create a minimal one:

```markdown
# [Project Name]

TARGET_BRANCH: staging

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

If `CLAUDE.md` already exists, check whether it has a `TARGET_BRANCH:` line. If not, add it near the top:
```
TARGET_BRANCH: staging
```

Tell the user: "I've set TARGET_BRANCH: staging — this tells the /pr skill which branch to target. Change it if your integration branch has a different name."

### Step 5 — Commit and Push

```bash
git add .github/workflows/claude.yml
git add .github/workflows/release.yml  # only if newly created
git add CLAUDE.md  # only if newly created or modified
git commit -m "chore: add GitHub Actions workflows and CLAUDE.md"
git push
```

If on `staging` or `main` and the pre-bash hook blocks the push, create a branch:

```bash
git checkout -b chore/setup-tapway-superpowers
git push -u origin chore/setup-tapway-superpowers
```

Then tell the user to merge it via PR.

### Step 6 — Print Manual Steps Checklist

After committing, print this checklist for the user:

```
## Project Setup Complete ✅

Automated:
  ✅ .github/workflows/claude.yml  — auto-review on every PR + @claude fix commands
  ✅ .github/workflows/release.yml — CalVer auto-release (YYYY.WW.XX.YY-stg/prod) on merge
  ✅ CLAUDE.md with TARGET_BRANCH: staging
  ✅ Changes committed and pushed

Manual steps still required:
  ☐ Add ANTHROPIC_API_KEY to GitHub repo secrets (needed for claude.yml jobs)
      → GitHub repo → Settings → Secrets and variables → Actions → New repository secret
      → Name: ANTHROPIC_API_KEY
      → Value: your Anthropic API key (https://console.anthropic.com)
      Note: release.yml uses GITHUB_TOKEN (built-in) and needs no extra secrets.

  ☐ Set staging as the default branch in GitHub
      → GitHub repo → Settings → Branches → Default branch → staging
      This ensures gh pr create targets staging by default.

  ☐ Fill in CLAUDE.md (stack, commands, conventions)
      → Claude reads this every session to understand your project

  ☐ Verify: merge any PR to stg — a YYYY.WW.1.0-stg release should appear automatically
  ☐ Test auto-review: open any PR — Claude should post an "## Auto-review" comment within ~30 seconds
  ☐ Test @claude: comment "@claude explain what this PR does" on any open PR
```

---

## Hard Rules

- ❌ Never overwrite an existing `.github/workflows/claude.yml` — skip and say "already set up"
- ❌ Never overwrite an existing `.github/workflows/release.yml` — skip and say "already set up"
- ❌ Never overwrite an existing `CLAUDE.md` — add `TARGET_BRANCH` if missing, otherwise skip
- ❌ Never push directly to `staging` or `main` — if the hook blocks it, create a setup branch instead
