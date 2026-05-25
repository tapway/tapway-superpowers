---
name: git-worktrees
description: >
  Manage parallel git worktrees for concurrent feature development, long test
  runs alongside coding, or hotfix work without losing main feature context.
  Triggers include "worktree", "parallel branches", "isolate this work",
  "hotfix without losing context".
---

# Skill: Git Worktrees

**When to invoke:** Parallel feature development, running long tests while continuing to code, working on hotfix while main feature work is in progress.

---

## What Are Worktrees?

Git worktrees let you check out multiple branches simultaneously in different directories. Each worktree is independent — you can run tests in one while writing code in another.

---

## Common Commands

```bash
# Create a new worktree for a feature branch
git worktree add ../[project]-feat-auth feat/user-auth

# Create a worktree for a new branch (doesn't exist yet)
git worktree add -b feat/payments ../[project]-payments

# List all worktrees
git worktree list

# Remove a worktree when done
git worktree remove ../[project]-feat-auth

# Prune stale worktree references
git worktree prune
```

---

## Workflow for Parallel Development

```
main repo dir/        ← main branch, production
../project-feat-A/    ← feat/feature-a branch
../project-fix-B/     ← fix/urgent-bug branch
```

### Step-by-step
1. Finish your current work or stash it
2. Create a worktree: `git worktree add -b feat/[name] ../[project]-[name]`
3. Open a new terminal tab and `cd ../[project]-[name]`
4. Work in the new worktree — it has its own index, but shares the `.git` repo
5. When done, merge/PR the branch, then `git worktree remove` it

---

## With Subagents
Worktrees are ideal when dispatching parallel subagents (see `subagent-driven-development` skill):
- Dispatch Agent A to worktree-1 (feature X)
- Dispatch Agent B to worktree-2 (feature Y)
- Both work simultaneously without conflicting

---

## Gotchas
- Each worktree needs its own `.env` / `node_modules` if applicable
- You can't check out the same branch in two worktrees simultaneously
- Worktree directories should be siblings of the main repo, not nested inside it
- Always clean up stale worktrees: `git worktree prune`