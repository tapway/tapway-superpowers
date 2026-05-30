---
name: autoship
description: >
  Fully automated implementation loop: reads a written plan, validates it,
  executes every task using the TDD subagent pattern (Test Writer → Implementer
  per task), then runs simplify → review → PR without human intervention.
  Triggers include "implement it with autopilot", "autoship", "ship this",
  "execute the plan", "run the plan end to end", "implement end to end",
  "just ship it".
---

# Skill: Autoship — Automated Plan-to-PR

**When to invoke:** A plan already exists in `docs/plans/` and you want to execute it all the way to an open PR without manually running each step. The full loop runs automatically; you only get pulled in if something genuinely blocks progress.

> **Prerequisite:** The plan must exist and be saved to `docs/plans/[feature].md`. If it doesn't exist yet, run `/brainstorming` then `/plan` first.

---

## What It Does

```
Read plan → Health check → Self-assign → Worktree
  └─ For each task:
       Test Writer (RED) → RED gate → Implementer (GREEN+REFACTOR) → Reviews
  └─ After all tasks:
       /simplify → /review → /pr
```

The coordinator handles everything. You only intervene if:
- A task fails twice with no clear path forward
- `/review` finds Critical issues that require a design decision (not just a fix)

---

## Protocol

### Phase 0: Locate the Plan

Ask if not already provided:
```
Which plan should I execute? (e.g. docs/plans/user-auth.md)
Or describe the feature and I'll find the matching plan.
```

Read the plan file. Confirm it exists and has a task breakdown.

---

### Phase 1: Plan Health Check (Before Any Code)

Review every task in the plan against these criteria. Fix problems now — they are much cheaper to fix in the plan than mid-implementation.

**For each task, verify:**
- [ ] Task description is unambiguous — one engineer reading it would implement the same thing as another
- [ ] `FILES TO MODIFY` lists exact paths (no "the service file" — must be `backend/src/services/auth_service.py`)
- [ ] Success criteria is **verifiable** ("test_X passes" or "endpoint returns 201") — not vague ("it works")
- [ ] A test can be written for this task (not auto-generated code or pure config)
- [ ] No task depends on a later task (execution order is correct)

**If any task fails the health check:**
- Fix it in the plan file directly
- Re-save `docs/plans/[feature].md`
- Report what was changed

Do not proceed to Phase 2 until every task passes the health check.

---

### Phase 2: Setup

```bash
# Confirm clean state
git status  # must be clean

# Create worktree (if not already in one)
git worktree add -b feat/[feature-name] ../[project]-[feature-name] origin/main
cd ../[project]-[feature-name]

# Self-assign in checklist
# Edit docs/checklists/[feature]-checklist.md:
#   **Assignee:** autoship 🤖   **Status:** 🟡 In progress
git add docs/checklists/ && git commit -m "chore: self-assign [feature] for autoship"
```

---

### Phase 3: Task Loop

Maintain a running status board and update it after every task:

```
## Autoship Status: [Feature]
| Task | Status | Commit |
|---|---|---|
| Task 1: ... | ✅ Done | abc1234 |
| Task 2: ... | 🔄 In progress | — |
| Task 3: ... | ⏳ Pending | — |
```

**For each task:**

#### Step A — Dispatch Test Writer (RED)
```
You are the Test Writer for Task N of [Feature] — RED phase only.

TASK: [exact task description]
TEST FILE: [exact path — e.g. backend/tests/unit/test_auth_service.py]
DESIRED BEHAVIOR: [one sentence]

Write ONE test: test_[function]_[condition]_[expected_outcome]
Run it. Paste exact output.

SUCCESS CRITERIA: FAILS with AssertionError, ImportError, AttributeError,
or TypeScript compilation error — NOT a syntax error.

STOP. Do not write production code.
SURGICAL CHANGES: Touch only the test file.
```

#### Step B — RED Gate
- [ ] Test exists at the correct path
- [ ] Test name follows `test_[function]_[condition]_[expected_outcome]`
- [ ] Output shows a meaningful failure (not SyntaxError)
- [ ] Test logic validates the actual desired behavior

**Gate fails → retry once with specific feedback. Fails again → pause and report to user.**

#### Step C — Dispatch Implementer (GREEN + REFACTOR)
```
You are the Implementer for Task N of [Feature] — GREEN then REFACTOR.

Failing test at [test file path]. Do NOT modify it.

TASK: [exact task description]
FILES TO MODIFY: [production files only]
SUCCESS CRITERIA: [test name] passes. No new failures in full suite.

GREEN: minimum code to make test pass — no gold-plating.
REFACTOR: only if code is unclear — run tests after every step.

SURGICAL CHANGES: production files only.
CONVENTIONS: [key items from CLAUDE.md]

Commit: git commit -m "feat/fix/refactor: [behavior]"
Report: test output, files changed, commit hash.
```

#### Step D — Task Reviews
**Spec compliance:**
- [ ] Code matches every requirement in the task spec
- [ ] Test passes, full suite clean
- [ ] No stubs (`pass`, `TODO`, `NotImplementedError`)
- [ ] Surgical check: only listed files modified

**Code quality:** invoke `code-review` skill
- [ ] Type safety, no security issues, follows conventions

**Both pass → mark task ✅ in status board. Proceed to next task.**

#### On Failure
- Task fails spec review → re-dispatch Implementer with specific failure feedback (retry once)
- Task fails twice → **pause, update status board to ❌, report to user with exact blocker**
- Do not skip a failing task and continue — later tasks may depend on it

---

### Phase 4: Post-Implementation

Once all tasks are ✅:

**1. Simplify**
```
/simplify
```
Apply all suggestions. Run tests to confirm nothing broke.

**2. Self-Review**
```
/review
```
- Fix every **Critical** finding before continuing
- For **Warnings**: fix if straightforward, note in PR body if not
- **Suggestions**: optional

If Critical fixes are significant enough to require a new task, add it to the status board and execute it using Phase 3 before continuing.

**3. Open PR**
```
/pr
```
PR body should include:
- Summary of what was built (bullets per task)
- Link to `docs/plans/[feature].md` and `docs/checklists/[feature]-checklist.md`
- Autoship status board (copy the final table)
- Any warnings or known limitations from `/review`

---

### Phase 5: Wrap-Up

After PR is open:
1. Update checklist: all tasks ✅, status 🟢 Done, `**PR:** #[number]`
2. Commit checklist update to the branch:
   ```bash
   git add docs/checklists/
   git commit -m "chore: mark [feature] complete, PR #[number]"
   git push
   ```
3. Report to user:
   ```
   ## Autoship Complete ✅
   Feature: [name]
   Tasks completed: N/N
   PR: #[number] — [title]
   Review findings: [none / N warnings noted in PR body]
   ```

---

## Model Selection

| Phase | Model |
|---|---|
| Plan health check | Sonnet — requires judgment about ambiguity |
| Test Writer | Haiku — formulaic |
| Implementer (1-2 files) | Haiku |
| Implementer (multi-file) | Sonnet |
| Implementer (architecture) | Opus |
| Simplify + Review | Sonnet |

---

## Hard Rules

- ❌ Never skip the plan health check — ambiguous plans waste more time mid-loop than fixing them upfront
- ❌ Never dispatch the Implementer before the RED gate passes
- ❌ Never skip a failing task and continue to the next
- ❌ Never open a PR with Critical review findings unresolved
- ❌ Never open a PR with failing tests
- ❌ Never work from `main` — always from a worktree
- ❌ Never push manually — always exit through `/pr`

---

## When to Use the Built-in `/autopilot` Instead

| Situation | Use |
|---|---|
| Plan already written in `docs/plans/` | `/autoship` (this skill) |
| No plan yet, want everything from scratch | Built-in `/autopilot` |
| Single small task, no plan needed | `/tdd` directly |
| Complex plan, want adversarial plan critique before implementation | Built-in `/autopilot` to generate + critique the plan, then `/autoship` to execute it |
