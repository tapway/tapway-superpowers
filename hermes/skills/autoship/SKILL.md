---
name: autoship
description: >-
  Fully automated implement-and-ship loop (Hermes port of tapway-superpowers autoship skill).
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["automation", "tdd", "implementation", "pipeline"]
    related_skills: [interview, brainstorming, writing-plans, tdd, pr]
---


# Skill: Autoship — Automated Plan-to-PR

**When to invoke:** A plan already exists in `docs/plans/` and you want to execute it all the way to an open PR without manually running each step.

> **Prerequisite:** The plan must exist and be saved to `docs/plans/[feature].md`. If it doesn't exist yet, run `/brainstorming` then `/plan` first.

---

## Modes

| Mode | Trigger | When to use |
|---|---|---|
| **Standard** | "implement it with autopilot" / "autoship" | CI/CD handles deployment; Claude Code is on a developer machine |
| **Deploy** | "implement and deploy" / "autoship with deployment" | Claude Code is running directly on the staging server |

---

## What It Does

**Standard mode:**
```
Read plan → Health check → Self-assign → Worktree
  └─ For each task:
       Test Writer (RED) → RED gate → Implementer (GREEN+REFACTOR) → Reviews
  └─ After all tasks:
       /simplify → /review → Update docs → /pr
```

**Deploy mode** (everything above, plus):
```
  └─ After all tasks:
       /simplify → /review → Update docs
         → Detect deploy method → Deploy to staging
         → Health check loop → Integration/E2E tests
         → /pr (with deployment evidence in body)
```

The coordinator handles everything. You only intervene if:
- A task fails twice with no clear path forward
- `/review` finds Critical issues that require a design decision (not just a fix)
- Deployment or integration tests fail — **never open a PR with a broken deployment**

---

## Protocol

### Phase 0: Locate the Plan

Ask if not already provided:
```
Which plan should I execute? (e.g. docs/plans/user-auth.md)
Or describe the feature and I'll find the matching plan.
```

Read the plan file. Confirm it exists and has a task breakdown.

If deploy mode was triggered, also detect the deployment configuration now (see Phase 4D below) and confirm it before starting the task loop — better to discover a misconfigured deploy command before 30 minutes of implementation.

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

**Step 1 — Simplify**
```
/simplify
```
Apply all suggestions. Run tests to confirm nothing broke.

**Step 2 — Self-Review**
```
/review
```
- Fix every **Critical** finding before continuing
- For **Warnings**: fix if straightforward, note in PR body if not
- **Suggestions**: optional

If Critical fixes are significant enough to require a new task, add it to the status board and execute it using Phase 3 before continuing.

**Step 3 — Update Docs**

Run `/repo-docs` — mandatory on every autoship run, no exceptions.

```
/repo-docs
```

`/repo-docs` updates only the sections affected by this branch's changes if docs already exist, or generates all docs from scratch if this is the first time. Commit any changes it makes:

```bash
git add docs/
git commit -m "docs: update project docs for [feature]"
```

**Step 4 — Frontend E2E Gate (mandatory, standard mode — not just deploy mode)**

If the plan touched the **frontend** (Next.js/React UI, new pages, components, routes, auth flows, or any user-facing behavior), run the `e2e-playwright` skill now — before opening the PR. This is not optional and not deferred to deploy mode:

```text
Use the e2e-playwright skill:
  Scaffold @playwright/test if absent → write e2e/<feature>.spec.ts
  (golden path + edge cases + error states, auth via auth.setup.ts storageState)
  → npx playwright test → debug failures from traces (never weaken assertions)
```

- [ ] `npx playwright test` passes (full suite, no new failures)
- [ ] Golden path, edge cases, and error states all covered

If the E2E suite fails, fix the tests or the app and re-run. **Never open a frontend PR with a failing E2E suite.**

**Step 5 — Open PR** *(see Phase 5 below)*

---

### Phase 4D: Deploy + Integration Tests *(Deploy mode only)*

> Skip this phase entirely in standard mode. Only run when deploy mode was triggered.

#### Step 4D-1 — Detect Deployment Method

Check for these in order and use the first match:

| Signal | Deploy command |
|---|---|
| `docker-compose.yml` or `docker-compose.yaml` | `docker compose pull && docker compose up -d` |
| `Makefile` with a `deploy` target | `make deploy` |
| `package.json` with a `"deploy"` script | `npm run deploy` |
| `Procfile` | `foreman start` or platform-specific command |
| None found | Ask the user for the exact deploy command before continuing |

Record the deploy command. If it was inferred (not explicitly provided by the user), confirm it once before running:
```
Deploy command detected: docker compose pull && docker compose up -d
Proceeding — interrupt if this is wrong.
```

#### Step 4D-2 — Deploy

Run the deploy command. Capture stdout and stderr.

```bash
# Example for docker compose
docker compose pull && docker compose up -d
docker compose logs --tail=30
```

If the command exits non-zero: **stop, report the exact error output, do not continue to health check or PR.**

#### Step 4D-3 — Health Check

After deploying, confirm the app is responding. Try each endpoint in order until one returns 2xx:

```bash
curl -sf http://localhost:[PORT]/health      ||
curl -sf http://localhost:[PORT]/api/health  ||
curl -sf http://localhost:[PORT]/healthz     ||
curl -sf http://localhost:[PORT]/ping        ||
curl -sf http://localhost:[PORT]/
```

Retry every 5 seconds for up to 60 seconds (12 attempts). Record which endpoint responded and the HTTP status.

**If still failing after 60 seconds:**
1. Run `docker compose logs --tail=50` (or equivalent) and report the output
2. Suggest rollback (see below)
3. **Do not open a PR** — the deployment is broken

**Rollback suggestion on health check failure:**
```bash
# Docker compose — restart with previous image
docker compose down && git stash && docker compose up -d

# Systemd service
sudo systemctl restart [service-name]

# PM2
pm2 restart all
```

#### Step 4D-4 — Integration and E2E Tests

Detect which integration/E2E test suites exist and run all of them:

| Signal | Command |
|---|---|
| `tests/integration/` directory | `pytest tests/integration/ --tb=short -q` |
| `tests/e2e/` directory | `pytest tests/e2e/ --tb=short -q` |
| `pytest.ini` or `pyproject.toml` with `integration` marker | `pytest -m integration --tb=short -q` |
| `playwright.config.ts` or `playwright.config.js` | `npx playwright test` |
| `cypress.config.ts` or `cypress.config.js` | `npx cypress run` |
| `package.json` with `"test:e2e"` script | `npm run test:e2e` |
| `package.json` with `"test:integration"` script | `npm run test:integration` |
| `Makefile` with `test-integration` target | `make test-integration` |

Run every suite that exists. Report pass/fail counts for each.

**If any integration or E2E test fails:**
1. Report the exact failing test names and output
2. Diagnose: is this a test environment issue, a data fixture issue, or a real regression?
3. If it's a real regression — fix it as a new task (add to status board, run Phase 3 loop)
4. **Do not open a PR until all integration and E2E tests pass**

#### Step 4D-5 — Record Evidence

Capture results for the PR body:

```
## Deployment Verified ✅
- Environment: staging (hostname: [hostname])
- Deployed at: [timestamp]
- Deploy command: [command used]
- Health check: ✅ [endpoint] → [HTTP status]
- Unit tests: [N/N passed]
- Integration tests: [N/N passed]  (or "none found")
- E2E tests: [N/N passed]  (or "none found")
```

---

### Phase 4: Open PR

```
/pr
```

**Standard mode** — PR body includes:
- Summary of what was built (bullets per task)
- Link to `docs/plans/[feature].md` and `docs/checklists/[feature]-checklist.md`
- Autoship status board (copy the final table)
- Any warnings or known limitations from `/review`

**Deploy mode** — PR body also includes:
- The "Deployment Verified" evidence block from Step 4D-5
- Any integration/E2E test output worth highlighting

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

   **Standard mode:**
   ```
   ## Autoship Complete ✅
   Feature: [name]
   Tasks completed: N/N
   PR: #[number] — [title]
   Review findings: [none / N warnings noted in PR body]
   ```

   **Deploy mode:**
   ```
   ## Autoship Complete ✅ (with deployment)
   Feature: [name]
   Tasks completed: N/N
   Deployed to: staging ([hostname])
   Health: ✅ [endpoint]
   Integration tests: N/N passed
   E2E tests: N/N passed
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
| Deploy diagnosis (on failure) | Sonnet — log analysis requires judgment |

---

## Hard Rules

- ❌ Never skip the plan health check — ambiguous plans waste more time mid-loop than fixing them upfront
- ❌ Never dispatch the Implementer before the RED gate passes
- ❌ Never skip a failing task and continue to the next
- ❌ Never open a PR with Critical review findings unresolved
- ❌ Never open a PR with failing unit tests
- ❌ Never open a PR with a failed deployment or failing integration/E2E tests *(deploy mode)*
- ❌ Never skip the doc update step — update or generate docs before calling `/pr`
- ❌ Never work from `main` — always from a worktree
- ❌ Never push manually — always exit through `/pr`

---

## Failure Recovery

| What failed | Recovery |
|---|---|
| Task fails twice | Pause, report exact blocker to user, wait for instruction |
| Deploy command exits non-zero | Report exact error, suggest checking logs, do not open PR |
| Health check times out (60s) | Print last 50 log lines, suggest rollback command, do not open PR |
| Integration test fails | Diagnose real regression vs env issue; fix before PR if real |
| E2E test fails | Same as integration — fix or document as known limitation with user approval |

---

## When to Use the Built-in `/autopilot` Instead

| Situation | Use |
|---|---|
| Plan already written in `docs/plans/` | `/autoship` (this skill) |
| No plan yet, want everything from scratch | Built-in `/autopilot` |
| Single small task, no plan needed | `/tdd` directly |
| Complex plan, want adversarial plan critique before implementation | Built-in `/autopilot` to generate + critique the plan, then `/autoship` to execute it |
