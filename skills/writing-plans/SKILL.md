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
**Related skills needed:** tdd, subagent-driven-development
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

### 6. Execution Options
After saving, ask:
> "Should I execute this plan inline (batch with checkpoints) or using subagent-driven-development (fresh agent per task)?"

---

## Self-Review Checklist
- [ ] Every requirement from the spec is covered by a task
- [ ] No "TBD" or vague language
- [ ] All file paths are exact
- [ ] All function/method names are consistent across tasks
- [ ] Tests are written before implementation in every task