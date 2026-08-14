---
name: writing-plans
description: >
  Write a structured implementation plan for any multi-step task (3+ files,
  new feature, refactor, migration). Use after brainstorming and before
  implementation. Triggers include "write a plan", "plan this", "design the
  implementation", "break this down".
---

# Skill: Writing Plans

**When to invoke:** Any multi-step task (3+ files, new feature, refactor, migration). After brainstorming, before implementation.

---

## Purpose

Create a detailed, concrete implementation plan that any engineer can execute without needing to ask follow-up questions.

---

## Protocol

### 1. Plan Header
Every plan starts with:
```markdown
## Plan: [Feature Name]
**Goal:** [One sentence]
**Tech stack:** Next.js 14 + TypeScript / Python FastAPI
**Related skills needed:** tdd
**Estimated tasks:** N

### Assumptions
- [Assumption 1 — if wrong, the plan changes]
- [Assumption 2]

### Simpler Alternative Considered
[What's the simplest thing that could work? Why wasn't it chosen? If the
chosen approach IS the simplest, say so explicitly.]
```

### 2. File Map
List every file that will be created or modified:
```
CREATE  frontend/src/components/auth/LoginForm.tsx
CREATE  frontend/src/services/auth.ts
MODIFY  frontend/src/app/layout.tsx
CREATE  backend/src/api/routes/auth.py
CREATE  backend/src/services/auth_service.py
MODIFY  backend/src/models/__init__.py
CREATE  backend/tests/unit/test_auth_service.py
CREATE  backend/tests/integration/test_auth_routes.py
```

### 3. Task Breakdown
Each task = one commit. Format:

```
### Task N: [Task name]
**Files:** [file1.py, file2.ts]
**Success criteria:** [verifiable — "test_X passes", "ruff is clean on file1.py", "endpoint returns 201 on valid input"]
**Steps:**
1. Write test: `test_[what]_[when]_[expected]`
2. Verify test fails (expected failure message: ...)
3. Implement: [exact function/component name, signature]
4. Verify test passes
5. `git commit -m "feat: [what was added]"`
```

Tasks should be 2-5 minutes of work each. If longer, split it.

**Surgical changes rule:** Each task touches only the files listed. No fixing neighboring code, no unrelated refactors, no style "improvements" to unchanged files.

### 4. No Placeholders Rule
Never write:
- "Add error handling" ← vague
- "Implement the service" ← vague
- "TBD" ← never acceptable

Always write:
- "Add try/except for `DatabaseConnectionError`, return `{"error": "db_unavailable"}` with status 503"
- "Create `AuthService.login(email: str, password: str) -> AuthToken` that calls `UserRepository.find_by_email()`"

### 5. Save the Plan
Save to `docs/plans/[feature-name].md` before starting implementation.

### 6. Generate Work Package Checklist
After the plan is written, generate a companion checklist at `docs/checklists/[feature-name]-checklist.md`.

Group tasks by discipline so any team member can pick up a self-contained work package:

```markdown
# Work Package Checklist: [Feature Name]
**Plan:** docs/plans/[feature-name].md
**Branch:** feat/[feature-name]
**Status:** 🔴 Not started | 🟡 In progress | 🟢 Done

---

## 🔧 Backend (Python FastAPI)
**Assignee:** _(unassigned)_
- [ ] Task 1: [description] — `test_X_passes`
- [ ] Task 2: [description] — `endpoint returns 201`

## 🎨 Frontend (Next.js / TypeScript)
**Assignee:** _(unassigned)_
- [ ] Task 3: [description] — `ComponentX renders`
- [ ] Task 4: [description] — `auth.test.ts passes`

## 🚀 DevOps / Infrastructure
**Assignee:** _(unassigned)_
- [ ] Task 5: [description] — `docker-compose up succeeds`

## 🧪 QA / Integration Tests
**Assignee:** _(unassigned)_
- [ ] Task 6: [description] — `E2E login flow passes`

---

## How to Pick Up a Work Package

**Step 1 — Claim it** (edit this file):
```
**Assignee:** @your-name   **Status:** 🟡 In progress
```
Commit and push the change so teammates know it's taken.

**Step 2 — Create your worktree** (run in the project root):
```bash
git fetch origin
git worktree add -b feat/[feature]-[package] ../[project]-[package] origin/main
cd ../[project]-[package]
```

**Step 3 — Open Claude Code and start work**:
```bash
claude
```
Then tell Claude:
```
I'm picking up the [Backend / Frontend / DevOps / QA] work package for [feature name].
My tasks are in docs/checklists/[feature]-checklist.md.
Let's start implementing.
```
Claude will read the plan and checklist and begin `/tdd` automatically.

**Step 4 — When all your tasks are done**:
```
/cleanup    ← only if using tapway-claude-template (removes scaffold placeholders)
/simplify   ← always (reduces complexity, removes duplication)
/review     ← always (self code-review before anyone else sees it)
/pr         ← always (rebase, test, push, open PR, update checklist)
```

**Step 5 — After your PR is merged**:
```bash
cd ../[project-root]
git worktree remove ../[project]-[package]
git worktree prune
```
```

Only include discipline sections that have tasks. Omit empty sections.

### 7. Commit the Docs
Commit both files before any implementation begins — teammates can't pick up work packages they can't see:
```bash
git add docs/plans/[feature-name].md docs/checklists/[feature-name]-checklist.md
git commit -m "docs: add plan and work package checklist for [feature-name]"
git push
```

### 7b. Create the GitHub Issue (after plan, before execution)
Now that the task is understood and the plan exists, create the GitHub issue — **this is what feeds the CodeMAX kanban**. Do this *after* brainstorming/planning and *before* executing, not at session start (an empty issue from a bare branch name is worthless).

If the tapway-superpowers hook is available (repo has `hooks/pre-execute-github-issue/`):
```bash
bash hooks/pre-execute-github-issue/create-issue.sh docs/plans/[feature-name].md
```
This creates (or reuses) a `codemax`-labeled issue with the full plan as the body, and sets `GITHUB_ISSUE_NUMBER` / `GITHUB_REPO`.

If the hook is not present, create it directly (conversational — just do it):
```
Create a GitHub issue titled "⚙ [Feature Name]" labeled codemax in the current repo,
with the plan from docs/plans/[feature-name].md as the body, and note the branch.
```

The resulting issue auto-syncs to the kanban via the CodeMAX webhook. Push incremental progress to it as you work (in_progress → review → done).

### 7c. Route the docs the plan produces (wiki vs. repo)
Each document the plan creates belongs either in the **shared wiki / brain** or in the **repo's own docs**. Decide before implementing, so a doc lands in the right home the first time — no churn later.

**Skip guard:** if the team does **not** run CodeMAX (`CODEMAX_ENABLED` unset), **skip this step entirely** — just update the **repo docs** the plan produces and move on. Nothing wiki-related runs, nothing fails.

**One-line rule for the rest:**
> Version-locked + travels with the code → **repo docs**. Knowledge that outlives a commit, explains the "why", spans platforms, or is synthesized → **wiki** (with shared infra → `references/`).

For each artifact the plan produces, ask: "wiki or repo?" — and route it:
| Plan output | Home |
|---|---|
| README / ARCHITECTURE / DEPLOYMENT / DB schema / OpenAPI, code, docstrings | **repo docs** |
| Requirement, blueprint, ADR, work order | **wiki** → `platforms/<name>/{requirements,blueprints,decisions,work-orders}/` |
| Cross-platform / shared infra (VSS, keycloak, edge tunnel) | **wiki** → `references/` |
| User manual for an app UI | **wiki** → `general/user-manuals/<app>.md` |
| Runnable artifact (config, script) | **repo / config repo** (keep spec inline in wiki) |

The authoritative routing table lives once in CodeMAX's
`docs/CONSUMING_A_CODEMAX_INSTANCE.md` → "Wiki vs. repo docs" — reference it,
don't duplicate it.

**Read-only / no wiki write access:** still decide the routing, but do **not** push to wiki `master`. Either record the decision in the plan/repo-docs only, or (where supported) submit wiki pages as a **draft** for approval. A failed or blocked wiki write must **never block the pipeline** — proceed to the next step either way.

### 8. Execution
After committing, say:
> "Plan and checklist committed and pushed. Teammates can pick up a work package from `docs/checklists/[feature-name]-checklist.md`. When ready to implement your package: create a worktree, run /tdd, then /pr when done."

---

## Self-Review Checklist
- [ ] Every requirement from the spec is covered by a task
- [ ] No "TBD" or vague language
- [ ] All file paths are exact
- [ ] All function/method names are consistent across tasks
- [ ] Tests are written before implementation in every task
- [ ] Plan saved to `docs/plans/`
- [ ] Work package checklist saved to `docs/checklists/`