---
name: pr
description: >
  Full PR preparation and creation workflow: rebase against the integration
  branch (stg by default), resolve conflicts, run tests, run /repo-docs,
  push branch, and open a PR targeting stg. Always operates inside a git
  worktree. Triggers include "create a PR", "open a pull request", "push and
  PR", "submit my work", "I'm done with this task", "/pr".
---

# Skill: PR Creation & CI/CD Workflow

**When to invoke:** When a work package or feature is complete and ready for review. Always run from inside a git worktree, never from the integration branch.

---

## Core Principle

> One worktree = one branch = one PR. Never work directly on `stg` (or your project's integration branch).

---

## Protocol

### Step 1: Verify You're in a Worktree

```bash
git branch --show-current   # must NOT be stg/main/master
git worktree list            # confirm you're in a worktree, not the main checkout
```

If you're on `stg` (or `main`), stop. Use the `git-worktrees` skill to create a worktree first:
```bash
git worktree add -b feat/[feature-name] ../[project]-[feature-name]
```

---

### Step 2: Determine Target Branch

Read the project's integration branch from `CLAUDE.md`:
```bash
TARGET=$(grep "^TARGET_BRANCH:" CLAUDE.md 2>/dev/null | awk '{print $2}')
TARGET=${TARGET:-stg}   # default to stg if not set
echo "Targeting: $TARGET"
```

If `CLAUDE.md` has no `TARGET_BRANCH` entry, default to `stg`. Add it once to avoid the lookup:
```
TARGET_BRANCH: stg
```

---

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

Ask Claude for help with specific conflicts:
```
claude "resolve the conflict in src/services/auth.py — preserve the rate limiting from stg and the new JWT logic from this branch"
```

---

### Step 4: Run Tests

Run the test suite for every discipline that was touched:

| What changed | Command |
|---|---|
| Python backend | `cd backend && pytest --tb=short -q` |
| TypeScript frontend | `cd frontend && npm test -- --watchAll=false` |
| Both | Run both sequentially |

All tests must be green before pushing. If a test fails that was passing before your changes, fix it before continuing.

---

### Step 5: Update Docs

Run `/repo-docs` — this is mandatory on every PR, no exceptions.

```
/repo-docs
```

`/repo-docs` will:
- Generate `docs/ARCHITECTURE.md`, `docs/WORKFLOWS.md`, `docs/DB_SCHEMA.md`, `docs/DEPLOYMENT.md` from scratch if they don't exist
- Update only the sections affected by changes in this branch if docs already exist

After `/repo-docs` completes, commit any doc changes:
```bash
git add docs/
git commit -m "docs: update project docs for [feature/change]"
```

If `/repo-docs` made no changes (output says "no sections affected"), skip the commit but note "docs: no changes" in the PR body.

---

### Step 6: Push the Branch

```bash
git push -u origin $(git branch --show-current)
```

If the push is rejected (someone else pushed to the same branch):
```bash
git fetch origin && git rebase origin/$(git branch --show-current)
# resolve any conflicts, then push again
```

---

### Step 7: Create the PR

Use `gh pr create` with a structured body. Target branch defaults to `stg`:

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
- [ ] Unit tests pass (`pytest -q` / `npm test`)
- [ ] No regressions in full suite
- [ ] [Any manual verification step]

## Files Changed
[Paste output of `git diff --name-only origin/$TARGET`]
```

Run:
```bash
gh pr create \
  --base $TARGET \
  --title "feat(scope): description" \
  --body "$(cat <<'EOF'
## Summary
- ...

## Test Plan
- [ ] ...
EOF
)"
```

> **What happens automatically after this PR is opened:**
> - The `auto-review` GitHub Actions job fires within ~30 seconds and posts a three-tier code review (Critical / Warning / Suggestion) as inline PR comments — no mention needed.
> - When the PR is merged, the `release.yml` workflow creates a `YYYY.WW.XX.YY-stg` tag and GitHub release automatically.

---

### Step 8: Update the Work Package Checklist

After the PR is open:
1. Edit `docs/checklists/[feature]-checklist.md`
2. Check off completed tasks
3. Set the work package status to 🟢 Done
4. Add the PR link next to the Assignee line: `**PR:** #123`

Commit the checklist update directly to the branch — it will be included in the PR:
```bash
git add docs/checklists/
git commit -m "chore: update work package checklist for [package]"
git push
```

---

## Hard Rules

- ❌ Never push directly to `stg`, `main`, or `master`
- ❌ Never open a PR with failing tests
- ❌ Never create a PR from the integration branch — always from a worktree
- ❌ Never skip the rebase step — stale branches cause CI failures and reviewer confusion
- ❌ Never skip `/repo-docs` — docs must be updated on every PR
- ❌ Never leave the work package checklist unchecked after the PR is open

---

## Quick Reference

```bash
# Read target branch
TARGET=$(grep "^TARGET_BRANCH:" CLAUDE.md 2>/dev/null | awk '{print $2}'); TARGET=${TARGET:-stg}

# Sync
git fetch origin && git rebase origin/$TARGET

# Tests
cd backend && pytest -q && cd ..
cd frontend && npm test -- --watchAll=false && cd ..

# Docs (mandatory)
# /repo-docs
git add docs/ && git commit -m "docs: update project docs for [change]"

# Push and PR
git push -u origin $(git branch --show-current)
gh pr create --base $TARGET --title "feat(scope): ..." --body "..."
```
