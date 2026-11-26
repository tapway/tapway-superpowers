---
name: setup-project
description: >-
  One-time project setup: release workflow + AGENTS.md agent guide (Hermes port of tapway-superpowers setup-project skill).
version: 1.3.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["setup", "github-actions", "ci"]
    related_skills: [interview, brainstorming, writing-plans, tdd, pr]
---


# Skill: Setup Project

**When to invoke:** First time the plugin is adopted in a project repo, or when the session-start hook reports that `.github/workflows/release.yml` is missing.

---

## What It Does

1. Creates `.github/workflows/release.yml` — semver auto-release (`vX.Y.Z-stg` / `vX.Y.Z-prod`) on merge to `staging` / `prod`
2. Creates `AGENTS.md` (if missing) with `TARGET_BRANCH: staging` pre-filled
3. Creates `.github/workflows/quality.yml` — the CI quality gate (lint/format/typecheck/coverage + dependency audit) — see the `quality-gates` skill
4. Installs the git `pre-commit` backstop (`hooks/pre-commit/git-pre-commit.sh`) into `.git/hooks/pre-commit`
5. Commits all files and pushes
6. Prints a manual-steps checklist (default branch, filling in AGENTS.md, branch protection, CODEOWNERS)

> **Note:** The previous `setup-project` created a `.github/workflows/claude.yml` GitHub
> Actions PR-review workflow (`auto-review` + `@claude`). That was removed — Tapway now
> does code review inside the AI agent instead of in GitHub CI, so no `claude.yml` is
> created and no `ANTHROPIC_API_KEY` secret is required.

---

## Protocol

### Step 1 — Check Current State

```bash
ls .github/workflows/release.yml  2>/dev/null && echo "EXISTS" || echo "MISSING"
ls AGENTS.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
git branch --show-current
```

Report what's missing before making any changes.

### Step 2 — Create the Auto-Release Workflow

If `.github/workflows/release.yml` does not exist, write the following content exactly to `.github/workflows/release.yml`:

```yaml
name: Auto Release

# vMAJOR.MINOR.PATCH-stg on merge to `staging`, -prod on merge to `prod`.
# The version rules and release notes live in the shared Tapway workflow.
# Promote staging to prod with a merge commit so the -prod notes list every
# change since the last -prod release.

on:
  push:
    branches:
      - staging
      - prod
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: "staging"
        type: choice
        options:
          - staging
          - production

jobs:
  release:
    permissions:
      contents: write
      pull-requests: read   # lets the notes quote PR descriptions
    uses: tapway/tapway-superpowers/.github/workflows/reusable-release.yml@master
    with:
      environment: ${{ github.event_name == 'workflow_dispatch' && inputs.environment || (github.ref_name == 'prod' && 'production' || 'staging') }}
```

### Step 3 — Install the Git Pre-Commit Backstop

Install the platform-agnostic quality gate so every commit (from any agent or human) is guarded:

```bash
mkdir -p .git/hooks
HOOK_SRC="hooks/pre-commit/git-pre-commit.sh"
chmod +x "$HOOK_SRC"
# Install as a copy (not a relative symlink) so the hook is self-contained
cp "$HOOK_SRC" .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

If the repo already has a `.git/hooks/pre-commit`, append a call to the backstop rather than replacing it:

```bash
echo 'bash "$(git rev-parse --show-toplevel)/hooks/pre-commit/git-pre-commit.sh" || exit $?' >> .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Step 4 — Verify AGENTS.md

If `AGENTS.md` does not exist at the project root, create a minimal one:

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
- [Things the agent should never do in this repo]
```

If `AGENTS.md` already exists, check whether it has a `TARGET_BRANCH:` line. If not, add it near the top:
```
TARGET_BRANCH: staging
```

Tell the user: "I've set TARGET_BRANCH: staging — this tells the /pr skill which branch to target. Change it if your integration branch has a different name."

### Step 4 — Commit and Push

```bash
git add .github/workflows/release.yml  # only if newly created
git add AGENTS.md  # only if newly created or modified
git commit -m "chore: add auto-release workflow and AGENTS.md"
git push
```

If on `staging` or `main` and the pre-bash hook blocks the push, create a branch:

```bash
git checkout -b chore/setup-tapway-superpowers
git push -u origin chore/setup-tapway-superpowers
```

Then tell the user to merge it via PR.

### Step 5 — Print Manual Steps Checklist

After committing, print this checklist for the user:

```
## Project Setup Complete ✅

Automated:
  ✅ .github/workflows/release.yml — semver auto-release (vX.Y.Z-stg/prod) on merge
  ✅ AGENTS.md with TARGET_BRANCH: staging
  ✅ Changes committed and pushed

Manual steps still required:
  ☐ Set staging as the default branch in GitHub
      → GitHub repo → Settings → Branches → Default branch → staging
      This ensures gh pr create targets staging by default.

  ☐ Fill in AGENTS.md (stack, commands, conventions)
      → The agent reads this every session to understand your project

  ☐ Verify: merge any PR to staging — a vX.Y.Z-stg release should appear automatically
```

---

## Hard Rules

- ❌ Never overwrite an existing `.github/workflows/release.yml` — skip and say "already set up"
- ❌ Never overwrite an existing `AGENTS.md` — add `TARGET_BRANCH` if missing, otherwise skip
- ❌ Never push directly to `staging` or `main` — if the hook blocks it, create a setup branch instead
- ❌ Do NOT create a `.github/workflows/claude.yml` — Tapway reviews code inside the AI agent, not in GitHub CI
