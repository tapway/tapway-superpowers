---
name: setup-project
description: >
  One-time project setup for teams adopting tapway-superpowers: creates the
  auto-release workflow (semver vX.Y.Z-stg/prod), verifies CLAUDE.md exists
  with TARGET_BRANCH set, commits everything, and prints a checklist of
  remaining manual steps. Triggers include "setup project", "initialize
  project for the team", "project setup", "add the release workflow".
---

# Skill: Setup Project

**When to invoke:** First time the plugin is adopted in a project repo, or when the session-start hook reports that `.github/workflows/release.yml` is missing.

---

## What It Does

1. Creates `.github/workflows/release.yml` — semver auto-release (`vX.Y.Z-stg` / `vX.Y.Z-prod`) on merge to `staging` / `prod`
2. Creates `CLAUDE.md` (if missing) with `TARGET_BRANCH: staging` pre-filled
3. Creates `.github/workflows/quality.yml` — the CI quality gate (lint/format/typecheck/coverage) — see the `quality-gates` skill
4. Commits all files and pushes
5. Prints a manual-steps checklist (default branch, filling in CLAUDE.md, branch protection, CODEOWNERS)

> **Note:** The previous `setup-project` created a `.github/workflows/claude.yml` GitHub
> Actions PR-review workflow (`auto-review` + `@claude`). That was removed — Tapway now
> does code review inside the AI agent instead of in GitHub CI, so no `claude.yml` is
> created and no `ANTHROPIC_API_KEY` secret is required.

---

## Protocol

### Step 1 — Check Current State

```bash
ls .github/workflows/release.yml  2>/dev/null && echo "EXISTS" || echo "MISSING"
ls CLAUDE.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
git branch --show-current
```

Report what's missing before making any changes.

### Step 2 — Create the Auto-Release Workflow

If `.github/workflows/release.yml` does not exist, write the following content exactly to `.github/workflows/release.yml`:

```yaml
name: Auto Release

# Fires automatically on every merge to `staging` or `prod`.
# Can also be triggered manually (Actions → Run workflow).
# Produces a Semantic Versioning tag with an environment suffix:
#   vMAJOR.MINOR.PATCH-stg   (staging)
#   vMAJOR.MINOR.PATCH-prod  (production)
#
# Bump derived from conventional commits since the last tag for the same env:
#   feat! / BREAKING CHANGE  →  MAJOR
#   feat:                    →  MINOR
#   anything else            →  PATCH
#
# Each environment keeps its own independent version stream.

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
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # full history needed to read existing tags & commits

      - name: Compute next version
        id: ver
        run: |
          set -e

          # Determine environment suffix:
          #   - workflow_dispatch: use the input value
          #   - push to prod branch: -prod
          #   - push to staging branch (or anything else): -stg
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            INPUT="${{ github.event.inputs.environment }}"
            [ "$INPUT" = "production" ] && ENV="-prod" || ENV="-stg"
          else
            BRANCH="${GITHUB_REF_NAME}"
            ENV="-stg"
            [ "$BRANCH" = "prod" ] && ENV="-prod"
          fi

          # Latest semver tag for this env, e.g. v1.2.3-stg
          LATEST=$(git tag -l "v*${ENV}" 2>/dev/null | sort -V | tail -1)

          if [ -z "$LATEST" ]; then
            MAJOR=0; MINOR=0; PATCH=0
          else
            VER=${LATEST#v}
            VER=${VER%%"${ENV}"}
            MAJOR=$(echo "$VER" | cut -d. -f1)
            MINOR=$(echo "$VER" | cut -d. -f2)
            PATCH=$(echo "$VER" | cut -d. -f3)
          fi

          RANGE="${LATEST:-$(git rev-list --max-parents=0 HEAD)}..HEAD"

          BUMP="patch"
          if git log "${RANGE}" --format="%s%n%b" 2>/dev/null \
             | grep -qE '(^feat!|BREAKING CHANGE)'; then
            BUMP="major"
          elif git log "${RANGE}" --format="%s" 2>/dev/null \
             | grep -qE '^(feat|feat\()'; then
            BUMP="minor"
          fi

          case "$BUMP" in
            major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
            minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
            patch) PATCH=$((PATCH + 1)) ;;
          esac

          VERSION="v${MAJOR}.${MINOR}.${PATCH}${ENV}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "bump=${BUMP}"        >> "$GITHUB_OUTPUT"
          echo "Computed version: ${VERSION} (${BUMP} bump)"

      - name: Tag and publish release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ steps.ver.outputs.version }}"

          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag "$VERSION"
          git push origin "$VERSION"

          # Extract the top CHANGELOG section (between first ## [ and second ## [ or ---)
          awk '/^## \[/{if(p)exit; p=1; next} p && /^(## \[|---)/{exit} p{print}' CHANGELOG.md \
            > /tmp/release-notes.md

          gh release create "$VERSION" \
            --title "$VERSION" \
            --target "${{ github.ref_name }}" \
            --notes-file /tmp/release-notes.md
```

### Step 3 — Verify CLAUDE.md

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

### Step 4 — Commit and Push

```bash
git add .github/workflows/release.yml  # only if newly created
git add CLAUDE.md  # only if newly created or modified
git commit -m "chore: add auto-release workflow and CLAUDE.md"
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
  ✅ CLAUDE.md with TARGET_BRANCH: staging
  ✅ Changes committed and pushed

Manual steps still required:
  ☐ Set staging as the default branch in GitHub
      → GitHub repo → Settings → Branches → Default branch → staging
      This ensures gh pr create targets staging by default.

  ☐ Fill in CLAUDE.md (stack, commands, conventions)
      → Claude reads this every session to understand your project

  ☐ Verify: merge any PR to staging — a vX.Y.Z-stg release should appear automatically
```

---

## Hard Rules

- ❌ Never overwrite an existing `.github/workflows/release.yml` — skip and say "already set up"
- ❌ Never overwrite an existing `CLAUDE.md` — add `TARGET_BRANCH` if missing, otherwise skip
- ❌ Never push directly to `staging` or `main` — if the hook blocks it, create a setup branch instead
- ❌ Do NOT create a `.github/workflows/claude.yml` — Tapway reviews code inside the AI agent, not in GitHub CI
