---
name: tdd-subagent
description: >
  TDD-first subagent execution — each task is split into a Test Writer agent
  (RED phase) and an Implementer agent (GREEN + REFACTOR), with the coordinator
  enforcing the failing-test gate between phases. Guarantees TDD compliance
  across a multi-task plan. Use after the writing-plans skill. Triggers include
  "TDD with subagents", "subagent TDD", "delegate TDD", "enforce TDD".
---

# Skill: TDD-Subagent-Driven Development

**When to invoke:** You have a written plan (see `writing-plans` skill) with 3+ tasks and want to execute it with guaranteed TDD compliance using isolated subagents per phase.

---

## Core Concept

> Split RED from GREEN at the agent boundary — the coordinator is the gate.

Each task becomes two subagent calls: a **Test Writer** (RED only) and an **Implementer** (GREEN + REFACTOR). The coordinator reviews the failing test before dispatching the Implementer. This makes TDD cheating structurally impossible — the Implementer receives a test file that already exists and must never modify it.

```
For each task:
  Test Writer agent → [failing test] → RED gate (coordinator) → Implementer agent → [green tests + commit]
                                            ↑ rejects if test passes or has syntax errors
```

---

## Protocol

### Before Starting
- [ ] Implementation plan is written and saved to `docs/plans/`
- [ ] Git working tree is clean (`git status`)
- [ ] Consider using `git-worktrees` skill if tasks are truly independent (enables true parallelism)

---

### For Each Task

#### Step 1: Dispatch Test Writer (RED Phase)

Provide exactly this context — no more:

```
You are the Test Writer for Task N of [Feature] — RED phase only.

TASK: [exact task description from plan]
TEST FILE: [path where the test should be written, e.g. backend/tests/unit/test_X.py]
DESIRED BEHAVIOR: [one sentence — what should the function do?]

Write ONE test using this naming convention:
  test_[function]_[condition]_[expected_outcome]

Run the test. Paste the EXACT output (stdout + stderr).

SUCCESS CRITERIA: The test FAILS with an assertion error, ImportError, or
AttributeError — NOT a syntax error. A syntax error means the test itself is
broken, not the production code.

STOP HERE. Do not write any production code. Do not create source files.
SURGICAL CHANGES: Touch only the test file listed above.
```

#### Step 2: Gate — Verify RED

Review the Test Writer's output before proceeding:
- [ ] Test file exists at the specified path
- [ ] Test name follows `test_[function]_[condition]_[expected_outcome]`
- [ ] Test output shows a **meaningful failure** (AssertionError, ImportError, AttributeError — not SyntaxError)
- [ ] Test logic validates the actual desired behavior (not a trivially vacuous assertion)

**If the gate fails:** reject and re-dispatch with specific feedback. Common failure modes:
- Test passes immediately → the test is wrong (vacuous assertion like `assert True`)
- SyntaxError → malformed test; fix before dispatching Implementer
- Test imports non-existent module but also crashes on a syntax error in the test itself → separate those problems

Do not proceed to GREEN until the RED gate passes.

#### Step 3: Dispatch Implementer (GREEN + REFACTOR Phases)

```
You are the Implementer for Task N of [Feature] — GREEN then REFACTOR phases only.

The failing test already exists at [test file path]. Do NOT modify it.

TASK: [exact task description from plan]
FILES TO MODIFY: [production files only — never the test file]
SUCCESS CRITERIA: [test function name] passes. Full test suite has no new failures.

GREEN phase — write the MINIMUM code to make the test pass:
- No gold-plating. No "while I'm here" additions.
- No error handling for states the test doesn't exercise.
- No abstractions for single-use code.
- Litmus test: would a senior engineer call this overcomplicated? If yes, simplify.

REFACTOR phase — only if the green code is unclear:
- Improve names and remove duplication.
- Run tests after every refactor step.
- Stop the moment tests are green and code is readable.

SURGICAL CHANGES: Touch only the production files listed above.
CONVENTIONS: [paste relevant items from CLAUDE.md]

Commit with: git commit -m "feat: [behavior added]"
Report: exact test output showing pass, list of files changed, commit hash.
```

#### Step 4: Spec Compliance Review

- [ ] Code matches every requirement in the task description
- [ ] The target test passes (paste the passing output)
- [ ] Full test suite has no new failures
- [ ] No incomplete stubs (`pass`, `TODO`, `raise NotImplementedError`) left behind
- [ ] **Surgical check:** Implementer touched only listed production files; test file is unmodified

Reject out-of-scope changes even if they seem like improvements.

#### Step 5: Code Quality Review

Invoke the `code-review` skill:
- [ ] Type safety (no `any`, proper Pydantic models where applicable)
- [ ] No security issues introduced
- [ ] Follows project naming conventions

#### Step 6: Mark Complete

Only after Steps 4 and 5 pass. Update the plan tracker. Proceed to Task N+1.

---

## Model Selection

| Subagent | Complexity | Model |
|---|---|---|
| Test Writer | All tasks | Haiku — test structure is formulaic |
| Implementer | 1-2 files, clear spec | Haiku |
| Implementer | Multi-file, patterns | Sonnet |
| Implementer | Architecture / design decisions | Opus |

Haiku for Test Writer is always correct: writing a single named test from a spec is mechanical. Save Sonnet/Opus for implementation where judgment matters.

---

## Hard Rules

- ❌ Never dispatch the Implementer before the RED gate passes
- ❌ Never let the Test Writer create or modify production source files
- ❌ Never let the Implementer modify the test file
- ❌ Never skip the spec compliance or code quality review
- ❌ Never paste the plan file path to a subagent — paste the task text directly
- ❌ Never start on `main` without explicit consent
- ❌ Never dispatch multiple Implementers in parallel without git-worktrees isolation

---

## Example Dispatch Sequence

```
Task 1: "add_discount() applies percentage to price"
  ├── Test Writer (Haiku)
  │     → writes test_add_discount_with_percentage_returns_discounted_price()
  │     → reports: AssertionError: 0 != 85.0
  ├── RED gate ✓
  ├── Implementer (Haiku)
  │     → writes add_discount() in pricing.py
  │     → reports: 1 passed in 0.02s | commit abc1234
  ├── Spec review ✓
  ├── Code quality review ✓
  └── Task 1 complete ✓

Task 2: "add_discount() rejects negative percentage"
  ├── Test Writer (Haiku) → ...
```

---

## Exceptions (require explicit approval)

- Auto-generated files (migrations, OpenAPI-derived types) — skip Test Writer, go straight to Implementer
- Pure configuration changes — no test needed, use standard subagent-driven-development skill instead
- Spike / throwaway branches — TDD optional, but state this explicitly before starting
