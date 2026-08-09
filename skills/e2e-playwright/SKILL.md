---
name: e2e-playwright
description: >
  Enforce end-to-end testing for both frontend (Playwright browser tests) and
  backend (pytest integration/E2E). Scaffolds Playwright + pytest, writes
  persistent specs (golden path, edge cases, error states, auth via
  storageState for frontend, httpx + ASGITransport + real test DB for backend),
  runs them, and debug-fixes failures from traces — never by weakening
  assertions. Conditionally mandated: frontend E2E when frontend files change,
  backend E2E when backend files change, both skip for docs-only.
  Triggers include "e2e test", "playwright", "browser test", "test the UI",
  "end-to-end", "frontend test", "integration test", "backend test",
  "verify the flow".
---

# Skill: E2E Testing — Frontend (Playwright) + Backend (pytest)

**When to invoke:** Any task that changes the frontend or backend — new pages,
components, routes, auth flows, API endpoints, services, or UI behavior. If the
change surfaces in a browser or an API, it needs an E2E test. This is not
optional: the pipeline wires it into `tdd` (runs after unit GREEN), `autoship`
(mandatory in the default path), and `verification` (a failing E2E suite blocks
"done"). A PR that touches frontend or backend without a green E2E run is not
acceptable.

> **Why structural?** Unit tests prove functions work in isolation. E2E tests
> prove the *user's flow* works in a real browser (frontend) or through the full
> API chain (backend). Both are required. A feature is not verifiable until its
> golden path, edge cases, and error states pass in an actual browser or through
> the real API stack.

---

## Core Concept

> Unit tests = "does the function work?" E2E tests = "does the user's journey work?"

E2E is modeled on the same agent-boundary discipline as `tdd`, but for the
browser and API layers. The iron law: **no frontend or backend feature ships
without a green E2E run**, and the gate is enforced by the pipeline, not by
self-discipline.

```
For each frontend feature:
  Scaffold (if needed) → write e2e/*.spec.ts → Run `npx playwright test`
    → debug from traces on failure (never weaken assertions) → GREEN → PR

For each backend feature:
  Write tests/integration/ + tests/e2e/ → Run `pytest tests/integration/ tests/e2e/`
    → fix failures (never weaken assertions) → GREEN → PR
```

---

## Protocol

### Before Starting

- [ ] You are on a **feature branch**, not `main`.

### Step 0 — Frontend Change Detection (the conditional gate)

This skill is **mandated when frontend files changed** and **skipped entirely when only backend files changed**. Detect this concretely — never guess:

```bash
# Get the list of changed files in this branch vs main
git diff --name-only main...HEAD
```

Classify each changed file:

| Pattern | Layer |
|---|---|
| `*.tsx`, `*.jsx`, `*.vue` | Frontend |
| `**/pages/**`, `**/app/**`, `**/components/**`, `**/src/app/**` | Frontend |
| `**/public/**`, `*.css`, `*.scss`, `*.module.css` | Frontend |
| `playwright.config.*`, `e2e/**` | Frontend (E2E) |
| `*.py`, `**/backend/**`, `**/api/**` | Backend |
| `*.md`, `docs/**`, `.github/**`, `*.yml`, `*.json` (config) | Neither (docs/config) |

**Decision:**
- **Any frontend file changed** → frontend E2E (Playwright) is **mandated**. Continue to Step A.
- **Any backend file changed** → backend E2E (pytest integration) is **mandated**. Continue to Step F.
- **Only docs / config files changed** → both E2E gates are **skipped**. The unit-test gate in `tdd` + `verification` is sufficient.
- **Mixed (frontend + backend)** → both gates are **mandated**.

Record the decision explicitly: `"Frontend files changed: [list]. Frontend E2E: REQUIRED."` / `"Backend files changed: [list]. Backend E2E: REQUIRED."` / `"No frontend or backend files changed. E2E gates: SKIPPED."`

### Step 1 — Detect Stack & Scaffold (only if E2E is mandated)

**Frontend stack** (if frontend files changed):
- [ ] Detect from `package.json` (check root and `frontend/` subdirectory — Tapway projects use `frontend/package.json`). Confirm Next.js version, React version, and whether `@playwright/test` is present. Never assume.
- [ ] If Playwright is not installed, run the Scaffold step (below).
- [ ] If `playwright.config.ts` already exists, skip to Step B.

**Backend stack** (if backend files changed):
- [ ] Detect from `pyproject.toml` / `requirements.txt` (check root and `backend/` subdirectory). Confirm FastAPI version, Python version, and whether `pytest` + `httpx` are installed.
- [ ] If `pytest` is absent, install it: `pip install pytest httpx pytest-asyncio`
- [ ] Check for existing test directories: `backend/tests/integration/`, `backend/tests/e2e/`. If absent, create them.

### Step A — Scaffold (one-time, only if `@playwright/test` is absent)

Detect the project (framework, port, env), then:

```bash
npm init playwright@latest        # or: npm i -D @playwright/test
npx playwright install --with-deps # installs browsers + OS deps
```

Create/verify `playwright.config.ts`:

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,          // blocks accidental .only in CI
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',          // artifact-based debugging
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'setup', testMatch: /.*auth\.setup\.ts/ },
    { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/user.json' }, dependencies: ['setup'] },
    // add firefox/webkit projects as needed
  ],
  webServer: {
    command: 'npm run dev',              // or your build+start command
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

Create the CI workflow (see `.github/workflows/playwright.yml`).

### Step B — Identify Auth & Covered Routes

- [ ] Read the app's routes and identify which need authentication.
- [ ] If login is required, create `e2e/auth.setup.ts` that logs in once and saves `storageState` (persistent-session pattern) — don't log in per-test:

```ts
import { test as setup, expect } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.E2E_USER!);
  await page.getByLabel('Password').fill(process.env.E2E_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: 'e2e/.auth/user.json' });
});
```

### Step C — Write E2E Specs (one spec per feature journey)

For each changed frontend feature, write `e2e/<feature>.spec.ts` covering:

1. **Golden path** — the primary happy-path journey end-to-end.
2. **Edge cases** — empty inputs, boundaries, missing data.
3. **Error states** — API down, invalid input, unauthenticated access.

**Resilient locator rules (never brittle):**
- Prefer **role/semantic locators**: `getByRole`, `getByLabel`, `getByText`, `getByPlaceholder`.
- **Never** use `page.waitForTimeout()` / manual sleeps — use web-first assertions (`await expect(...).toBeVisible()`).
- Test isolation: fresh state per test where state matters.
- Use Page Object Models for shared flows (login, nav) to avoid duplication.

```ts
import { test, expect } from '@playwright/test';

test('user can complete the checkout flow', async ({ page }) => {
  await page.goto('/products');
  await page.getByRole('button', { name: 'Add to cart' }).first().click();
  await page.getByRole('link', { name: 'Cart (1)' }).click();
  await page.getByRole('button', { name: 'Checkout' }).click();
  await expect(page).toHaveURL(/\/checkout/);
  await page.getByRole('button', { name: 'Place order' }).click();
  await expect(page.getByText('Order confirmed')).toBeVisible();
});
```

### Step D — Run & Verify (the gate)

```bash
npx playwright test
```

- [ ] Golden path passes
- [ ] Edge cases pass
- [ ] Error states pass
- [ ] Full suite has **no new failures** (no regressions in other specs)

### Step E — Debug Failures from Artifacts (never weaken assertions)

If a test fails, open the trace/video/screenshot that Playwright saved
(`playwright-report/`, `test-results/`) and diagnose root cause:

- **Test bug** (wrong locator, wrong expectation) → fix the test *correctly*.
- **App bug** (behavior doesn't match spec) → fix the app, then re-run.
- ❌ **Never** fix a failing test by removing or weakening the assertion to make it pass. That's how regressions ship. If the behavior is genuinely a spec change, update the spec *and* the product requirement explicitly.

---

### Step F — Backend Integration & E2E Tests (pytest)

For any backend change (`*.py`, `**/backend/**`, `**/api/**`), write integration/E2E tests that exercise the API through the FastAPI test client — not mocked internals. These prove the request → router → service → DB → response chain works end-to-end.

**Test layers:**

| Layer | Directory | What it tests | Tool |
|---|---|---|---|
| Integration | `backend/tests/integration/` | Single endpoint or service + real test DB | `pytest tests/integration/` |
| E2E (backend) | `backend/tests/e2e/` | Full user flow across multiple endpoints (e.g. register → login → create resource → delete) | `pytest tests/e2e/` |

**Setup — `conftest.py` fixtures (FastAPI + httpx + test DB):**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app  # adjust import path
from test_db import test_engine, override_get_db  # your test DB session

@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    # Register + login a test user, return auth headers
    ...
```

**Write integration tests (one per endpoint/behavior):**

```python
# backend/tests/integration/test_auth_endpoints.py
import pytest

@pytest.mark.asyncio
async def test_login_returns_token(client):
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "valid"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(client):
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
```

**Write E2E tests (full user flows across endpoints):**

```python
# backend/tests/e2e/test_user_journey.py
import pytest

@pytest.mark.asyncio
async def test_user_can_register_login_and_create_resource(client):
    # Register
    r = await client.post("/auth/register", json={"email": "new@test.com", "password": "Valid123!"})
    assert r.status_code == 201
    # Login
    r = await client.post("/auth/login", json={"email": "new@test.com", "password": "Valid123!"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create resource
    r = await client.post("/resources", json={"name": "My Resource"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["name"] == "My Resource"
    # Verify it's persisted
    r = await client.get("/resources", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
```

**Rules:**
- Use `httpx.AsyncClient` + `ASGITransport` — not `TestClient` (sync) or `async_asgi_testclient` (unmaintained).
- Use a **real test database** (SQLite in-memory or test Postgres), not mocks for the DB layer. Integration tests must hit the DB.
- Each test is independent — use fixtures for setup/teardown, never rely on test execution order.
- Mock only external third-party services (payment gateways, email providers). Never mock your own DB or internal services in integration/E2E tests.

### Step G — Run & Verify Backend (the gate)

```bash
cd backend
pytest tests/integration/ tests/e2e/ --tb=short -q
```

- [ ] Integration tests pass (golden path + error states per endpoint)
- [ ] E2E tests pass (full user flows across multiple endpoints)
- [ ] No new failures vs. baseline

If tests fail, fix the app or the test (correctly). **Never weaken assertions.** Same rule as frontend E2E.

### Step H — Contract & Migration Safety (backend changes only)

If the change touched an **API endpoint or response model**, run the `api-contract-testing` skill before PR:

```bash
openapi-spec-validator openapi.yaml          # or: npx @stoplight/spectral-cli lint openapi.yaml
schemathesis run --base-url http://localhost:8000 http://localhost:8000/openapi.json --checks all
```

- [ ] OpenAPI schema validates
- [ ] Every changed endpoint's responses match the documented schema
- [ ] Schemathesis fuzzing passes (no response-schema violations, no unexpected 5xx)

If the change touched the **database schema** (new/renamed/dropped columns, new tables, backfills), run the `db-migration-testing` skill before PR:

```bash
cd backend && pytest tests/integration/test_migrations.py -v
```

- [ ] `alembic upgrade head` applies cleanly to a fresh test DB
- [ ] `alembic downgrade base` rolls back cleanly (round-trip)
- [ ] Data-preservation test passes for renames/drops/backfills
- [ ] Large-table changes use the zero-downtime expand-contract pattern

**Never merge a backend PR with contract drift or an untested migration.** These are the two most common prod-outage classes.

---

## Verification / Gate

A feature is **not done** until the relevant E2E gates pass:

**Frontend E2E (if frontend files changed):**
- [ ] `npx playwright test` passes (full suite, no new failures)
- [ ] Golden path, edge cases, and error states all covered
- [ ] No `test.only`/`test.skip` left behind (`forbidOnly` catches `.only` in CI)

**Backend E2E (if backend files changed):**
- [ ] `pytest tests/integration/ tests/e2e/ --tb=short -q` passes
- [ ] Integration tests cover each changed endpoint (golden path + error states)
- [ ] E2E tests cover full user flows across multiple endpoints
- [ ] No new failures vs. baseline

**Both gates:**
- [ ] Traces/artifacts not required to be clean — but failures must be root-caused

If any suite fails, do NOT declare the task complete. Fix tests or app, re-run,
and only then mark done.

---

## Hard Rules

- ❌ Never open a frontend PR without a green `npx playwright test` run
- ❌ Never open a backend PR without green `pytest tests/integration/ tests/e2e/` (if backend files changed)
- ❌ Never fix a failing test by weakening or removing assertions
- ❌ Never use `page.waitForTimeout()` / manual sleeps — use web-first assertions
- ❌ Never write E2E tests that depend on real network/flaky third-party state
- ❌ Never log in per-test when `auth.setup.ts` + storageState is possible
- ❌ Never mock your own DB or internal services in integration/E2E tests — use a real test DB
- ❌ Never commit `playwright-report/`, `test-results/`, `.pytest_cache/`, or `.auth/`
