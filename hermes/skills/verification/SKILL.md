---
name: verification
description: >-
  Verify a task is actually complete before declaring done (Hermes port of tapway-superpowers verification skill).
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["verification", "testing", "done"]
    related_skills: [interview, brainstorming, writing-plans, tdd, pr]
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
- [ ] **Pre-commit quality gate passed:** if the change touches code files, the commit-time gate (lint + format + typecheck + coverage) must pass. The git pre-commit backstop (`hooks/pre-commit/git-pre-commit.sh`, installed by `setup-project`) enforces this on every commit; verify accordingly before declaring done.
- [ ] **Dependency audit clean:** run `osv-scanner .`, `npm audit`, and `pip-audit` (part of the `dependency-audit` skill). No critical/high vulnerabilities in changed or existing dependencies.
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
