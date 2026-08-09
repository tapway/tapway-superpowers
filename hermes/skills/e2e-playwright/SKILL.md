---
name: e2e-playwright
description: >
  Enforce frontend end-to-end testing with Playwright for any feature that
  touches the UI. Scaffolds Playwright into the project, writes persistent
  browser specs (golden path, edge cases, auth via storageState), runs them,
  and debug-fixes failures from traces — never by weakening assertions.
  Structurally required for Next.js/React frontend changes before a PR.
  Triggers include "e2e test", "playwright", "browser test", "test the UI",
  "end-to-end", "frontend test", "verify the flow in a browser".
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [e2e, playwright, testing, browser, frontend, quality]
    related_skills: [tdd, verification, autoship, test-driven-development, requesting-code-review, github-pr-workflow]
---

# Skill: E2E Testing with Playwright (Hermes port)

**When to invoke:** Any task that changes the frontend — new pages, components,
routes, auth flows, or UI behavior. If the change surfaces in a browser, it
needs a Playwright E2E test. This is not optional: the pipeline wires it into
`tdd` (runs after unit GREEN), `autoship` (mandatory in the default path), and
`verification` (a failing `npx playwright test` blocks "done"). A PR that
touches the frontend without a green E2E run is not acceptable.

> **Hermes note:** Hermes doesn't have Claude Code's per-task "agents" with a
> coordinator gate built in, but it *does* have `delegate_task` (subagents).
> This port adapts the protocol: you (the coordinator) run the E2E gate
> yourself between implementation and PR, exactly as the Claude plugin's
> coordinators do. The structural guarantee — no frontend feature ships
> without a green E2E run — is preserved.

---

## Core Concept

> Unit tests = "does the function work?" E2E tests = "does the user's journey work?"

E2E is modeled on the same agent-boundary discipline as `tdd`, but for the
browser layer. The iron law: **no frontend feature ships without a green E2E
run**, and the gate is enforced by the pipeline, not by self-discipline.

```
For each frontend feature:
  Scaffold (if needed) → E2E Generator → [write specs] → Run `npx playwright test`
    → debug from traces on failure (never weaken assertions) → GREEN → PR
```

---

## Protocol

### Before Starting

- [ ] Detect the frontend stack from `package.json` — confirm Next.js version, React version, and whether `@playwright/test` is present. Never assume.
- [ ] If Playwright is not installed, run the Scaffold step first (below).
- [ ] You are on a **feature branch**, not `main`.

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
    { name: 'setup', testMatch: /auth\.setup\.ts/, testIgnore: /.*/ },
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

## Verification / Gate

A frontend feature is **not done** until:

- [ ] `npx playwright test` passes (full suite, no new failures)
- [ ] Golden path, edge cases, and error states all covered
- [ ] No `test.only`/`test.skip` left behind (`forbidOnly` catches `.only` in CI)
- [ ] Traces/artifacts not required to be clean — but failures must be root-caused

If the suite fails, do NOT declare the task complete. Fix tests or app, re-run,
and only then mark done.

---

## Hard Rules

- ❌ Never open a frontend PR without a green `npx playwright test` run
- ❌ Never fix a failing test by weakening or removing assertions
- ❌ Never use `page.waitForTimeout()` / manual sleeps — use web-first assertions
- ❌ Never write E2E tests that depend on real network/flaky third-party state
- ❌ Never log in per-test when `auth.setup.ts` + storageState is possible
- ❌ Never commit `playwright-report/`, `test-results/`, or `.auth/` (add to `.gitignore`)