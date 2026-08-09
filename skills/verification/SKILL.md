---
name: verification
description: >
  Verify a task is actually complete before declaring done — no exceptions.
  Run the relevant tests, lint, type-checks, and feature checks. Triggers
  include "is this done", "verify", "before I mark complete", "final check",
  "ready to ship".
---

# Skill: Verification Before Completion

**When to invoke:** Before declaring ANY task complete. No exceptions.

> **Built-in alternative:** Claude Code's built-in **`/verify`** skill launches the actual app and observes behavior in a browser or terminal — it can replace or supplement this skill when you need to confirm the golden path works end-to-end in a running environment, not just via tests.

---

## The Rule

> A task is not done when the code is written. A task is done when it is verified.
>
> **Loop until green (Karpathy):** If verification fails, fix the issues and re-verify. Don't just report failure — resolve it.

---

## Verification Checklist

### 1. Static Verification (always run first)

- [ ] All tests pass: `cd backend && pytest -q` / `cd frontend && npm test -- --watchAll=false`
- [ ] **Frontend E2E tests pass (if frontend files changed):** Run `git diff --name-only main...HEAD` — if any frontend file changed (`*.tsx`, `*.jsx`, `**/pages/**`, `**/app/**`, `**/components/**`, `*.css`, etc.), run `npx playwright test` (part of the `e2e-playwright` skill). Golden path + edge cases + error states must pass in a real browser. **If no frontend files changed, skip this check.**
- [ ] **Backend integration/E2E tests pass (if backend files changed):** If any backend file changed (`*.py`, `**/backend/**`, `**/api/**`), run `pytest tests/integration/ tests/e2e/ --tb=short -q` (part of the `e2e-playwright` skill). Integration tests must cover each changed endpoint (golden path + error states). E2E tests must cover full user flows. **If no backend files changed, skip this check.**
- [ ] **API contract holds (if endpoints/response models changed):** Run the `api-contract-testing` skill — validate the OpenAPI schema and run Schemathesis. No response-schema violations, no unexpected 5xx.
- [ ] **Migrations tested (if DB schema changed):** Run the `db-migration-testing` skill — `alembic upgrade head` + `downgrade base` round-trip on a fresh test DB, data preservation, zero-downtime for large tables.
- [ ] No regressions — full test suite passes, not just new tests
- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] Python type checks: `mypy src/`
- [ ] Linting passes: `ruff check src/` / `npm run lint`
- [ ] No dead code (commented-out blocks, unused imports)

### 2. Functional Verification (run the feature)

Start the app and exercise the changed behavior directly:

```bash
# Backend
cd backend && uvicorn src.main:app --reload

# Frontend
cd frontend && npm run dev
```

For each changed feature, test:
- **Golden path** — the primary happy-path flow works end-to-end
- **Edge cases** — empty input, null values, max/min boundaries, unauthorized access
- **Error states** — what happens when the API is down, input is invalid, user lacks permission

If the feature involves an API endpoint, hit it directly:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "valid"}'
```

### 3. Spec Verification

- [ ] Re-read the original requirement / task description
- [ ] Every bullet point in the requirement is implemented
- [ ] No features were silently dropped ("I'll do that in a follow-up")
- [ ] The implementation matches what was planned (or plan was updated to reflect the change)

### 4. Security Spot-Check

- [ ] No secrets in code
- [ ] User inputs validated at the API boundary
- [ ] Auth required on all non-public endpoints
- [ ] For sensitive changes: run `/security-review` on the diff before marking done

### 5. Performance / Benchmark Check (if the change affects hot paths)

Performance regressions (N+1 queries, unbounded queries, missing indexes,
unbounded list endpoints) ship silently — they don't fail tests, they just make
production slow. If the change touches a **hot path** (an endpoint or UI viewed
on every page, a list endpoint, a query that hits a large table), verify it here.

**Backend — response-time + query-count check:**

```bash
# 1. Response latency baseline (hit the endpoint repeatedly, take the p95)
curl -s -o /dev/null -w "total=%{time_total}s\n" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/resources?limit=50"   # run 10x, take p95 (discard warm-up)

# 2. N+1 / query-count check (SQLAlchemy)
#    In tests: assert the query count with a counter, or set
#    lazy="raise" on relationships so accidental attribute access crashes:
#      <relationship> = relationship("X", lazy="raise")
```

```python
# backend/tests/e2e/test_query_count.py — fail if an endpoint exceeds N queries
import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session

@pytest.fixture()
def query_counter(engine):   # use the fixture-scoped engine so the counter
    """Count queries against the test engine only (no cross-test pollution)."""
    counts = {"n": 0}
    def _before_cursor_execute(*args, **kwargs):
        counts["n"] += 1
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    yield counts
    event.remove(engine, "before_cursor_execute", _before_cursor_execute)

def test_list_endpoint_query_count(client, query_counter):
    query_counter["n"] = 0
    r = client.get("/api/resources?limit=50")
    assert r.status_code == 200
    assert query_counter["n"] <= 10, f"endpoint fired {query_counter['n']} queries (possible N+1)"
```

**Frontend — load-time sanity (Lighthouse / browser timing):**

```bash
# Lighthouse CI on the changed route (LCP, CLS, INP budget)
npx lighthouse http://localhost:3000/<changed-route> --only-categories=performance
```

- [ ] Changed endpoint p95 latency is in the expected range (no unbounded growth)
- [ ] Query count is bounded (no N+1 from a new eager-load miss)
- [ ] Frontend route passes the Lighthouse performance budget (if applicable)

If a perf regression is found, fix it (eager-load, add indexes, paginate) and
re-run. **Never mark a hot-path change done with a known N+1 or latency
regression.**

---

## Verification Report

```
## Verification Report
- Tests: ✅ N passing, 0 failing
- Type checks: ✅ No errors
- Lint: ✅ No issues
- Golden path: ✅ Tested manually — [what you tested]
- Edge cases: ✅ [what you tested]
- Spec coverage: ✅ All requirements met
- Security: ✅ No issues found

Status: COMPLETE ✅
```

If anything fails:
```
Status: INCOMPLETE ❌
Blockers: [list what failed and why]
Next: [specific fix for each blocker — then re-verify]
```

---

## Red Flags
- "It worked in my quick test" — quick tests miss edge cases
- "The tests should pass" — run them, don't assume
- "I'll fix the lint later" — later never comes
- "I didn't need to run the app, the tests cover it" — tests don't catch UX regressions or missing env config
