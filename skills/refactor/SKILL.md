---
name: refactor
description: >
  Improve code quality without changing behavior. Two protocols: (1) Incremental
  — for active codebases that already have tests; (2) Legacy — for existing repos
  without test coverage, using characterization tests before any code changes.
  For bulk mechanical changes (renames, pattern replacements across many files)
  use the optional community skill: code-refactor. Triggers include "refactor",
  "clean up", "simplify", "remove duplication", "improve naming", "legacy
  refactor", "characterization tests", "existing repo".
---

# Skill: Refactor

Two protocols depending on whether the codebase has tests:

| Situation | Protocol |
|---|---|
| Codebase has a test suite covering the code to change | **Incremental Protocol** (below) |
| Existing repo with no or minimal tests | **Legacy Protocol** (below) |
| Bulk mechanical changes: renames, deprecated API replacements, import path updates | **`code-refactor` community skill** (below) |

---

## Protocol A — Incremental (Active Codebase with Tests)

**When to invoke:** Code quality improvements, removing duplication, simplifying complex functions, improving naming, before a major feature build.

### Rules of Safe Refactoring

1. **Tests first** — never refactor without a test suite that covers the code being changed
2. **Small steps** — one change at a time, tests pass after each step
3. **No behavior change** — refactoring must not change what the code does
4. **Commit often** — commit after each successful refactor step
5. **Surgical changes:** Touch only what the refactor targets. Don't improve neighboring code, comments, or formatting. Every changed line must trace directly to the refactor goal. Remove only the dead code your changes created — leave pre-existing dead code alone.
6. **Simplicity litmus:** After refactoring, ask: would a senior engineer call this overcomplicated? If the refactor added more lines than it removed, question whether it was worth it.

### Common Refactors

**Extract Function/Method** — when a function does more than one thing:
```python
# Before
def process_order(order_data):
    # 50 lines of validation
    # 30 lines of pricing
    # 40 lines of database save

# After
def process_order(order_data):
    validated = validate_order(order_data)
    priced = calculate_pricing(validated)
    return save_order(priced)
```

**Extract Component (React)** — when a JSX block is > 20 lines or used in multiple places:
```tsx
// Before: inline in ParentComponent
// After: <UserCard user={user} />
```

**Replace Magic Numbers/Strings:**
```python
# Before
if status == 3:
# After
class OrderStatus(IntEnum):
    SHIPPED = 3
if status == OrderStatus.SHIPPED:
```

**Consolidate Duplicated Logic** — if the same logic appears 2+ times → extract to `utils/` or a shared service.

### Steps

1. Run tests: confirm they pass
2. Identify the refactor target
3. Make one change
4. Run tests: confirm they still pass
5. Commit: `refactor: extract UserCard component`
6. Repeat

### This Is NOT Refactoring
- Adding new behavior
- Fixing bugs
- Changing interfaces (that's a breaking change)
- Rewriting from scratch

These require their own PRs with their own tests.

---

## Protocol B — Legacy (Existing Repo Without Tests)

**When to invoke:** The codebase has no meaningful test coverage and you need to make structural improvements safely.

The golden rule: **never change code you haven't first locked down with a test**. On legacy code, that means writing characterization tests — tests that capture how the code behaves right now, not how it should behave.

### Full Sequence

```
/repo-docs → /code-review + /security-audit → /brainstorming (goals)
  → Characterization tests (lock down current behavior)
  → /plan (prioritized refactor tasks)
  → /tdd (tests exist; GREEN = same behavior preserved)
  → /pr
```

### Step 1 — Understand the Codebase

```
/repo-docs
```

Generate `docs/ARCHITECTURE.md`, `docs/WORKFLOWS.md`, `docs/DB_SCHEMA.md`, `docs/DEPLOYMENT.md`. Do not skip this — without a map, every refactor decision is a guess.

### Step 2 — Audit

Run both in parallel:
```
/code-review   # structural problems, anti-patterns, duplication
/security-audit  # vulnerabilities, exposed secrets, injection points
```

Document the findings. This becomes the raw material for goal-setting.

### Step 3 — Goal Alignment

```
/brainstorming
```

Frame the session around: "Given this audit, what does 'better' look like in 6 months?" Force prioritization — you cannot refactor everything at once.

Common refactoring goals:
- **Testability** — decouple dependencies so unit tests are possible
- **Readability** — reduce cognitive load for new engineers
- **Performance** — eliminate N+1 queries, cache hot paths
- **Safety** — harden against the security findings
- **API consistency** — unify naming conventions, response shapes

Output: a ranked list of goals with measurable success criteria.

### Step 4 — Characterization Tests (Critical)

Before touching any production code, write tests that describe current behavior.

**Purpose:** These tests are not for correctness — they're a behavioral snapshot. If you change behavior accidentally, the test fails and catches it.

**What to cover:**
- Every public function/endpoint in the target module
- Happy path and the most common error paths
- Return shapes, status codes, side effects (DB writes, events emitted)

**Example:**
```python
# Not testing if this is right — testing what currently happens
def test_create_order_returns_dict_with_id():
    result = create_order({"product_id": 1, "qty": 2})
    assert "id" in result          # current behavior: returns a dict with id
    assert result["status"] == 3   # current behavior: status is 3 (magic number)
    # Note: status==3 is a code smell we'll fix later, but the test captures it now
```

Commit the characterization tests before writing a single line of refactored code:
```bash
git add tests/
git commit -m "test: add characterization tests for [module] before refactor"
```

### Step 5 — Plan

```
/plan
```

Break the refactoring into small, isolated tasks. Each task must:
- Target one code smell or one file/function
- Be verifiable: "characterization tests still pass + new test for extracted function passes"
- Be independent of other tasks (or clearly ordered if not)

### Step 6 — Execute

```
/tdd
```

The TDD loop is the same, but the RED phase is different:

| Phase | Greenfield TDD | Legacy refactor TDD |
|---|---|---|
| RED | Write test for new behavior → fails because code doesn't exist | Write test for extracted unit → fails because it's still coupled |
| GREEN | Implement the behavior | Decouple/extract until the new test AND all characterization tests pass |
| REFACTOR | Clean up the new code | Remove the now-dead coupling |

The characterization tests are your safety net — if any of them go red during GREEN or REFACTOR, you've accidentally changed behavior. Stop and revert.

### Step 7 — PR

```
/pr
```

PR body must include:
- Which characterization tests were added
- Which code smells were addressed
- Before/after metrics if measurable (lines of code, cyclomatic complexity, test coverage %)

---

## Optional: `code-refactor` Community Skill

For bulk mechanical changes that don't require writing new tests, the `code-refactor` community skill handles:
- Renaming functions/variables across many files simultaneously
- Replacing deprecated API calls with new ones
- Updating import paths after a directory restructure
- Applying a consistent formatting/naming convention across a module

**Install it separately:**
```bash
claude plugin add code-refactor@andrej-karpathy-skills
# or check the Skills Directory for the exact plugin ID
```

**Use it when:** the change is purely mechanical (find-and-replace with context awareness) and you would be confident doing it with a well-scoped sed/grep. Not for structural changes — use Protocol B for those.

**Do not use it on legacy code without characterization tests first** — bulk renames on untested code can cascade silently.

---

## Hard Rules

- ❌ Never refactor without tests — if tests don't exist, write characterization tests first (Protocol B)
- ❌ Never combine refactoring with feature work in the same PR — mixed intent makes review impossible
- ❌ Never make a "quick improvement" to code outside the refactor target — scope creep breaks bisectability
- ❌ Never skip `/repo-docs` on a legacy codebase — you cannot safely refactor what you don't understand
