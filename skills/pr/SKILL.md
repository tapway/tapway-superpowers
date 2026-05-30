---
name: pr
description: >
  Full PR preparation and creation workflow: rebase against main, resolve
  conflicts, run tests, push branch, and open a PR with a conventional commit
  title and structured body. Always operates inside a git worktree. Triggers
  include "create a PR", "open a pull request", "push and PR", "submit my
  work", "I'm done with this task", "/pr".
---

# Skill: PR Creation & CI/CD Workflow

**When to invoke:** When a work package or feature is complete and ready for review. Always run from inside a git worktree, never from `main`.

---

## Core Principle

> One worktree = one branch = one PR. Never work directly on `main`.

---

## Protocol

### Step 1: Verify You're in a Worktree

```bash
git branch --show-current   # must NOT be main or master
git worktree list            # confirm you're in a worktree, not the main checkout
```

If you're on `main`, stop. Use the `git-worktrees` skill to create a worktree first:
```bash
git worktree add -b feat/[feature-name] ../[project]-[feature-name]
```

---

### Step 2: Sync with Main

```bash
git fetch origin
git rebase origin/main
```

**If conflicts appear**, resolve them with intent-aware analysis:
- Read both sides of every conflict marker
- Preserve the intent of both branches — do not simply pick one side
- After resolving: `git add [file] && git rebase --continue`
- Run `git diff origin/main` after rebase to sanity-check the result

Ask Claude for help with specific conflicts:
```
claude "resolve the conflict in src/services/auth.py — preserve the rate limiting from main and the new JWT logic from this branch"
```

---

### Step 3: Run Tests

Run the test suite for every discipline that was touched:

| What changed | Command |
|---|---|
| Python backend | `cd backend && pytest --tb=short -q` |
| TypeScript frontend | `cd frontend && npm test -- --watchAll=false` |
| Both | Run both sequentially |

All tests must be green before pushing. If a test fails that was passing before your changes, fix it before continuing.

---

### Step 4: Update Docs

Check which files changed in this branch:
```bash
git diff --name-only origin/main
```

**If `docs/ARCHITECTURE.md` does not exist** — run `/repo-docs` first to generate all documentation from scratch, then continue. This only happens once per repo.

**If docs already exist** — update only the sections affected by this PR's changes. Do not regenerate whole files; read the existing doc, find the relevant section, and edit it in place.

| Files changed in this PR | Doc section to update |
|---|---|
| `backend/src/api/routes/` | `docs/WORKFLOWS.md` — add or update the affected API flow sequence diagram |
| `backend/src/models/` or `backend/src/db/` | `docs/DB_SCHEMA.md` — update entity definitions and ERD |
| `backend/src/services/` or new modules | `docs/ARCHITECTURE.md` — update component breakdown |
| `frontend/src/components/` or `frontend/src/app/` | `docs/WORKFLOWS.md` — update the UI interaction flow |
| `docker-compose.yml`, `Dockerfile`, CI files | `docs/DEPLOYMENT.md` — update build/deploy steps |
| `.env.example` | `docs/DEPLOYMENT.md` — update environment variables table |
| New external service or dependency added | `docs/ARCHITECTURE.md` — add to system diagram and external dependencies table |

After updating, commit the docs to the branch so they are part of the PR:
```bash
git add docs/
git commit -m "docs: update [ARCHITECTURE|WORKFLOWS|DB_SCHEMA|DEPLOYMENT] for [what changed]"
```

If nothing in the changed files affects any doc section, skip the commit but note "docs: no update needed" in the PR body.

---

### Step 5: Push the Branch

```bash
git push -u origin $(git branch --show-current)
```

If the push is rejected (someone else pushed to the same branch):
```bash
git fetch origin && git rebase origin/$(git branch --show-current)
# resolve any conflicts, then push again
```

---

### Step 6: Create the PR

Use `gh pr create` with a structured body:

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
[Paste output of `git diff --name-only origin/main`]
```

Run:
```bash
gh pr create \
  --title "feat(scope): description" \
  --body "$(cat <<'EOF'
## Summary
- ...

## Test Plan
- [ ] ...
EOF
)"
```

---

### Step 7: Update the Work Package Checklist

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

## GitHub Actions — @claude in PRs

This project uses `anthropics/claude-code-action` so team members can mention `@claude` in any PR comment to get AI-assisted fixes.

**Workflow file:** `.github/workflows/claude.yml` (already in this repo)

**How to use it:**
- `@claude fix the failing test in test_auth_service.py` — Claude analyzes and pushes a fix commit
- `@claude resolve the merge conflict in this PR` — Claude resolves and commits
- `@claude explain why this is failing` — Claude comments with an analysis (no commit)

**Cost:** Targeting specific problems with `@claude` keeps spend low — typically under $5/month for a team running 50 PRs.

---

## Hard Rules

- ❌ Never push directly to `main` or `master`
- ❌ Never open a PR with failing tests
- ❌ Never create a PR from the main checkout — always from a worktree
- ❌ Never skip the rebase step — stale branches cause CI failures and reviewer confusion
- ❌ Never skip the doc update step — if changed files affect any doc section, update it before pushing
- ❌ Never leave the work package checklist unchecked after the PR is open

---

## Quick Reference

```bash
# Full flow in one sequence
git fetch origin && git rebase origin/main
# (resolve conflicts if any)
cd backend && pytest -q && cd ..
cd frontend && npm test -- --watchAll=false && cd ..
# update affected docs/ sections, then:
git add docs/ && git commit -m "docs: update [section] for [change]"
git push -u origin $(git branch --show-current)
gh pr create --title "feat(scope): ..." --body "..."
```
