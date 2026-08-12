---
name: writing-plans
description: >-
  Write a structured implementation plan for any multi-step task (3+ files,
  new feature, refactor, migration). Use after brainstorming and before
  implementation. Triggers include "write a plan", "plan this", "design the
  implementation", "break this down".
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow]
    related_skills: [brainstorming, tdd, test-driven-development]
---

# Skill: Writing Plans

**When to invoke:** Any multi-step task (3+ files, new feature, refactor, migration). After brainstorming, before implementation.

## Purpose
Create a detailed, concrete implementation plan that any engineer can execute without needing to ask follow-up questions.

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

### 6. Generate Work Package Checklist (optional, for teams)
After the plan is written, generate a companion checklist at `docs/checklists/[feature-name]-checklist.md`, grouped by discipline (Backend / Frontend / DevOps / QA) so any team member can pick up a self-contained work package. Include a branch name and status marker (🔴/🟡/🟢).

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

### 8. Execution
After committing, say:
> "Plan and checklist committed and pushed. Teammates can pick up a work package from `docs/checklists/[feature-name]-checklist.md`. When ready to implement your package: create a branch, run `tdd`, then open a PR when done."

## Self-Review Checklist
- [ ] Every requirement from the spec is covered by a task
- [ ] No "TBD" or vague language
- [ ] All file paths are exact
- [ ] All function/method names are consistent across tasks
- [ ] Tests are written before implementation in every task
- [ ] Plan saved to `docs/plans/`
