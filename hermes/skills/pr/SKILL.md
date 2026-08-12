---
name: pr
description: >-
  Full PR preparation and creation workflow: rebase against the integration
  branch (staging by default), resolve conflicts, run tests, run repo-docs,
  push branch, and open a PR targeting staging. Always operates on a feature
  branch (never the integration branch). Triggers include "create a PR",
  "open a pull request", "push and PR", "submit my work", "I'm done with this
  task", "/pr".
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, pull-request, github, workflow, ci]
    related_skills: [tdd, repo-docs, github-pr-workflow, requesting-code-review]
---

# Skill: PR Creation Workflow (Hermes port)

**When to invoke:** When a work package or feature is complete and ready for review. Always run from a feature branch, never from the integration branch.

> **Hermes note:** Prefer the `gh` CLI (`gh auth login`). Do not embed API tokens in shell examples.

## Core Principle
> One branch = one PR. Never work directly on `staging` (or your project's integration branch).

## Protocol

### Step 1: Verify You're on a Feature Branch
```bash
git branch --show-current   # must NOT be staging/main/master
```
If you're on `staging`/`main`, stop. Create a feature branch first:
```bash
git checkout -b feat/[feature-name]
```

### Step 2: Determine Target Branch
Read the project's integration branch from agent context files at the repo root
(`AGENTS.md`, `.hermes.md`) looking for a `TARGET_BRANCH` entry. Default to
`staging` if unset. If the repo also keeps a Claude Code project guide, read
`TARGET_BRANCH` from that file the same way (first non-empty wins):
```bash
TARGET=""
for f in AGENTS.md .hermes.md; do
  [ -f "$f" ] || continue
  TARGET=$(grep "^TARGET_BRANCH:" "$f" 2>/dev/null | head -1 | awk '{print $2}')
  [ -n "$TARGET" ] && break
done
TARGET=${TARGET:-staging}
echo "Targeting: $TARGET"
```

### Step 3: Sync with Target Branch
```bash
git fetch origin
git rebase origin/$TARGET
```
**If conflicts appear**, resolve them with intent-aware analysis:
- Read both sides of every conflict marker
- Preserve the intent of both branches — do not simply pick one side
- After resolving: `git add [file] && git rebase --continue`
- Run `git diff origin/$TARGET` after rebase to sanity-check the result

### Step 4: Run Tests
Run the test suite for every discipline that was touched:

| What changed | Command |
|---|---|
| Python backend | `cd backend && pytest --tb=short -q && cd ..` |
| TypeScript frontend | `cd frontend && npm test -- --watchAll=false && cd ..` |
| Both | Run both sequentially |

All tests must be green before pushing. If a test that passed before your changes now fails, fix it before continuing.

### Step 4b: Verification-Before-Commit Gate

Before creating the PR, run the verification gates so every commit and the final PR are clean:

```bash
# 1. Quality gate: lint + format + typecheck + coverage (same as the git pre-commit backstop)
ruff check . && ruff format --check . 2>/dev/null   # backend, if ruff installed
npx prettier --check . && npx tsc --noEmit          # frontend, if node present

# 2. Dependency audit: supply-chain scan
osv-scanner . ; npm audit --audit-level=high ; pip-audit

# 3. Full test suite (Step 4)
pytest --tb=short -q      # backend
npm test -- --watchAll=false  # frontend
```

- [ ] All quality-gate checks pass (complete the `verification` skill's checklist)
- [ ] Dependency audit reports no critical/high vulnerabilities (see `dependency-audit` skill)
- [ ] Every `git commit` in this branch passed the pre-commit gate (lint/format/typecheck)

The git `pre-commit` backstop (`hooks/pre-commit/git-pre-commit.sh`, installed by
`setup-project`) enforces the quality gate on every commit. If it's not installed, install
it via `setup-project` before opening the PR.

### Step 5: Update Docs (mandatory)
Run the `repo-docs` skill — this is mandatory on every PR, no exceptions:
```
/repo-docs
```
`repo-docs` will generate `docs/ARCHITECTURE.md`, `docs/WORKFLOWS.md`, `docs/DB_SCHEMA.md` (if applicable), `docs/DEPLOYMENT.md` from scratch if they don't exist, or update only the sections affected by this branch if docs already exist.

After `repo-docs` completes, commit any doc changes:
```bash
git add docs/
git commit -m "docs: update project docs for [feature/change]"
```
If `repo-docs` made no changes (output says "no sections affected"), note "docs: no changes" in the PR body.

### Step 6: Push the Branch
```bash
git push -u origin $(git branch --show-current)
```
If the push is rejected (someone else pushed to the same branch):
```bash
git fetch origin && git rebase origin/$(git branch --show-current)
# resolve any conflicts, then push again
```

### Step 7: Create the PR
Use `gh pr create` with a structured body. Target branch defaults to `staging`:

**Title format:** `feat/fix/refactor(scope): short description`
- Examples: `feat(auth): add JWT login endpoint`, `fix(payments): handle Stripe webhook retry`
- Scope = the component or layer changed (auth, payments, api, ui, infra)

**Body format:**
```markdown
## Summary
- [Bullet 1 — what was built/fixed]
- [Bullet 2]
- [Bullet 3]

## Work Package
[Link to docs/checklists/[feature]-checklist.md if applicable]

## Test Plan
- [ ] Unit tests pass (pytest -q / npm test)
- [ ] No regressions in full suite
- [ ] [Any manual verification step]

## Files Changed
[Paste output of `git diff --name-only origin/$TARGET`]
```

```bash
gh pr create \
  --base "$TARGET" \
  --title "feat(scope): description" \
  --body "$(cat <<'EOF'
## Summary
- ...

## Test Plan
- [ ] ...
EOF
)"
```

If `gh` is unavailable, authenticate it first (`gh auth login`) or use the
Hermes `github` skill's REST helper. **Do not** paste personal access tokens
into one-off shell one-liners.

### Step 8: Update the Work Package Checklist (teams)
After the PR is open:
1. Edit `docs/checklists/[feature]-checklist.md`
2. Check off completed tasks
3. Set the work package status to 🟢 Done
4. Add the PR link next to the Assignee line: `**PR:** #123`

Commit the checklist update directly to the branch:
```bash
git add docs/checklists/
git commit -m "chore: update work package checklist for [package]"
git push
```

## Hard Rules
- ❌ Never push directly to `staging`, `main`, or `master`
- ❌ Never open a PR with failing tests
- ❌ Never create a PR from the integration branch — always from a feature branch
- ❌ Never skip the rebase step — stale branches cause CI failures and reviewer confusion
- ❌ Never skip `repo-docs` — docs must be updated on every PR
- ❌ Never leave the work package checklist unchecked after the PR is open

## Quick Reference
```bash
# Read target branch (AGENTS.md / .hermes.md, default staging)
TARGET=""
for f in AGENTS.md .hermes.md; do
  [ -f "$f" ] || continue
  TARGET=$(grep "^TARGET_BRANCH:" "$f" 2>/dev/null | head -1 | awk '{print $2}')
  [ -n "$TARGET" ] && break
done
TARGET=${TARGET:-staging}

# Sync
git fetch origin && git rebase origin/$TARGET

# Tests
cd backend && pytest -q && cd ..
cd frontend && npm test -- --watchAll=false && cd ..

# Docs (mandatory)
# run repo-docs skill
git add docs/ && git commit -m "docs: update project docs for [change]"

# Push and PR
git push -u origin $(git branch --show-current)
gh pr create --base "$TARGET" --title "feat(scope): ..." --body "..."
```
