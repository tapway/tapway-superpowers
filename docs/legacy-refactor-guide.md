# Legacy Refactor Guide

A step-by-step workflow for teams taking over an existing codebase — one not built with Claude Code or TDD — and wanting to improve it safely and systematically.

---

## When to Use This Guide

- You inherited a codebase with little or no test coverage
- You want to improve architecture, naming, or structure before adding new features
- You're onboarding onto a repo and want to understand it deeply before changing it
- You're preparing a legacy codebase for a team to work on collaboratively

If your codebase already has a test suite, skip to [the short path](#already-have-tests).

---

## The Full Workflow

```
Install superpowers
      │
      ▼
/repo-docs          ← understand before changing anything
      │
      ▼
/code-review + /security-audit (parallel)    ← find the problems
      │
      ▼
/brainstorming      ← align on what "better" looks like
      │
      ▼
Characterization tests    ← lock down current behavior (CRITICAL)
      │
      ▼
/plan               ← break into safe, small, ordered tasks
      │
      ▼
/tdd (per task)     ← refactor with safety net
      │
      ▼
/pr                 ← standard PR workflow (includes doc update)
```

---

## Step 0 — Install Superpowers

On any new machine or in a new repo session:

```bash
claude plugin add tapway-superpowers@tapway-superpowers
```

For bulk mechanical changes (renames, deprecated API replacements), also install the optional community skill:

```bash
claude plugin add code-refactor@andrej-karpathy-skills
```

---

## Step 1 — Generate Documentation (`/repo-docs`)

**Do this before reading any source code.** It forces Claude to map the whole system first, and gives every team member the same starting context.

```
/repo-docs
```

This generates:

| File | Contents |
|---|---|
| `docs/ARCHITECTURE.md` | System components, external dependencies, data flow |
| `docs/WORKFLOWS.md` | API flows, UI interaction flows, sequence diagrams |
| `docs/DB_SCHEMA.md` | Entity definitions, relationships, ERD |
| `docs/DEPLOYMENT.md` | Build steps, environment variables, infrastructure |

Commit these immediately so the whole team has the map:

```bash
git add docs/
git commit -m "docs: generate initial architecture docs for legacy codebase"
git push
```

---

## Step 2 — Audit the Codebase

Run both audits. They surface different things and can run in parallel.

```
/code-review
```
Finds: duplicated logic, god objects, inconsistent naming, N+1 queries, missing error handling, dead code, overly complex functions.

```
/security-audit
```
Finds: exposed secrets, SQL injection risks, missing authentication, unvalidated inputs, insecure dependencies.

**Save the output.** Create a file at `docs/audit-[date].md` and paste both sets of findings. This becomes the evidence base for your refactoring goals.

```bash
git add docs/audit-*.md
git commit -m "docs: add initial code review and security audit findings"
```

---

## Step 3 — Align on Goals (`/brainstorming`)

Don't start changing code yet. Refactoring without a shared goal produces churn.

```
/brainstorming
```

Frame the session: **"Given the audit findings, what does this codebase need to look like in 6 months?"**

Push for measurable goals, not vague ones:

| Vague | Measurable |
|---|---|
| "Better structured" | "Every service has a unit test; no function over 40 lines" |
| "More secure" | "All audit Critical findings resolved; no hardcoded secrets" |
| "Easier to onboard" | "New engineer can run tests and add a feature in < 1 day" |
| "Faster" | "P95 API response under 200ms; no N+1 queries on hot paths" |

Save the goals to `docs/plans/refactor-[scope].md`. This plan will feed directly into `/plan` in Step 5.

---

## Step 4 — Characterization Tests (Most Important Step)

> **This is the step most teams skip. It's the one that makes everything else safe.**

Before touching a single line of production code, write tests that describe what the code does **right now** — not what it should do.

These are called **characterization tests**. They are not checking for correctness. They are taking a behavioral snapshot so that if you accidentally change behavior during refactoring, the test immediately tells you.

### How to write them

Pick the module you plan to refactor first. For every public function or endpoint:

1. Call it with typical inputs
2. Record what it returns (status codes, response shapes, side effects)
3. Write a test that asserts exactly those outputs

```python
# Legacy code has a magic status==3 — we don't know what it means yet
# but we record that this is what currently happens
def test_process_order_returns_status_3_on_success():
    result = process_order({"product_id": 1, "qty": 2})
    assert result["status"] == 3   # characterizing current behavior, not asserting correctness
    assert "order_id" in result
```

```typescript
// Frontend: characterize a component's rendered output before restructuring it
it('renders user card with email visible', () => {
  render(<UserCard user={mockUser} />)
  expect(screen.getByText(mockUser.email)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument()
})
```

### Commit them before any production change

```bash
git add tests/
git commit -m "test: characterization tests for [module] — behavioral snapshot before refactor"
```

This commit is your checkpoint. If anything goes wrong later, `git bisect` back to here.

### What good characterization test coverage looks like

- Every public function/method has at least a happy-path test
- Every API endpoint: status code + response shape covered
- Any function with side effects (DB write, event emitted, email sent): side effect is asserted
- Edge cases you discover while reading the code: add them too

You don't need 100% coverage before starting. Cover the code you're about to refactor first, then expand as you go.

---

## Step 5 — Plan the Refactoring (`/plan`)

Now that you have a safety net, plan the work.

```
/plan
```

The plan should produce `docs/plans/refactor-[scope].md` with tasks that are:

- **Small** — one function extracted, one pattern consolidated, one magic number named
- **Ordered** — foundational changes (extract shared utilities) before dependent changes (update callers)
- **Verifiable** — "characterization tests still pass + new unit test for extracted function passes"

A good refactoring task looks like:

```markdown
### Task 3 — Extract `calculate_pricing` from `process_order`

FILES TO MODIFY: backend/src/services/order_service.py, backend/tests/unit/test_pricing.py
DESIRED BEHAVIOR: pricing logic is in a separate function callable independently
SUCCESS CRITERIA:
  - test_process_order_returns_status_3_on_success still passes (no behavior change)
  - test_calculate_pricing_applies_discount_for_bulk passes (new unit test)
```

If you also have a work package checklist (for team collaboration), generate it with `/plan` and commit it alongside the plan.

---

## Step 6 — Execute with TDD (`/tdd` per task)

For each task in the plan, the TDD loop runs as normal — but the RED phase means something different:

| Phase | What it means for legacy refactoring |
|---|---|
| **RED** | Write a unit test for the extracted/decoupled unit. It fails because the code is still tangled. |
| **GREEN** | Extract/decouple until both the new test AND all characterization tests pass. |
| **REFACTOR** | Remove the now-dead tangled code. Run all tests. |

**The characterization tests are your safety net.** If any of them go red during GREEN or REFACTOR, you changed behavior. Stop, check what broke, revert if necessary.

For bulk mechanical work (rename 40 function calls, update import paths), use the `code-refactor` community skill instead of writing a TDD cycle — it's faster for pure find-and-replace operations. Confirm characterization tests still pass after every bulk change.

---

## Step 7 — PR (`/pr`)

Same as any other PR. The `/pr` skill will:
1. Rebase against main
2. Run the test suite (your characterization tests + new unit tests)
3. Update docs (if architecture changed)
4. Push and open the PR

PR body for a refactoring PR should always include:
- **What code smells were addressed** (link to audit finding)
- **Characterization tests added** (how many, which module)
- **New unit tests added** (what behavior is now independently testable)
- **Behavior change:** None (if any behavior changed, it must be intentional and documented)

---

## Already Have Tests?

Skip Steps 4 (characterization tests) — your existing suite is already the safety net.

Short path:
```
/repo-docs → /code-review → /brainstorming → /plan → /tdd → /pr
```

Still run `/repo-docs` first. Even well-tested codebases benefit from a fresh architecture map before refactoring.

---

## Team Collaboration on a Refactor

Refactoring works well in parallel **if tasks are truly independent**. Use the same worktree + checklist pattern from `docs/team-guide.md`:

1. Alice runs `/repo-docs`, `/code-review`, `/brainstorming`, `/plan` → commits plan + checklist to `main`
2. Each team member self-assigns tasks from the checklist, creates a worktree, runs `/tdd`
3. Everyone runs `/pr` independently
4. Merge order matters — foundational tasks (shared utilities) before dependent tasks (callers)

**Shared characterization tests:** Commit them to `main` before anyone starts working, so the whole team's safety net is the same baseline.

```bash
# Alice writes characterization tests and commits to main first
git add tests/characterization/
git commit -m "test: characterization tests for auth, order, payment modules"
git push origin main

# Each team member pulls before creating their worktree
git fetch origin
git worktree add -b refactor/[scope] ../[project]-refactor-[scope] origin/main
```

---

## Common Pitfalls

| Pitfall | What happens | Prevention |
|---|---|---|
| Skipping characterization tests | Silent behavior regressions ship to production | Always write them before the first production change |
| Refactoring and fixing bugs in the same PR | Reviewer can't tell which change caused what | Separate PRs: refactor first, then fix (or vice versa) |
| Refactoring without `/repo-docs` | Decisions made on incomplete understanding | Always map first |
| Using `code-refactor` on untested code | Bulk rename cascades into broken behavior | Write characterization tests first, then bulk rename |
| Making the plan too large | Merging a 2-week refactor is painful | Scope to 2-3 days of work per PR; merge frequently |
| Changing behavior "while you're in there" | Now it's not a refactor, it's a feature + refactor | Scope hard rules: behavior change = separate PR |
