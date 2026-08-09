---
name: quality-gates
description: >
  Lay down the config-layer quality gates that block merged code before it
  ships: test coverage thresholds, TypeScript strict mode, environment
  validation, CODEOWNERS + branch protection, and a CI lint/format/typecheck/
  coverage gate. These are declaration-level enforcements — they catch the most
  bugs per hour for the least effort. Triggers include "coverage gate",
  "strict mode", "tsconfig strict", "env validation", "CODEOWNERS",
  "branch protection", "quality gate", "add coverage", "enforce type safety".
---

# Skill: Quality Gates (Config-Layer Enforcement)

**When to invoke:** When adopting the plugin in a project repo, after `setup-project`,
or when the codebase ships bugs that unit tests don't catch (dead code, `any` types,
missing env vars, unreachable code). This skill lays down the *cheapest* enforcements
first — config files and CI gates that block bad code at merge time, not after.

> **Why config first?** A skill the agent *might* run catches nothing. A config file
> the CI *always* runs catches everything. Coverage thresholds, strict mode, and env
> validation are declaration-level: write them once, and every future PR is gated.

---

## Core Concept

> Process skills (plan → test → review) catch *intent* bugs. Config gates catch
> *mechanical* bugs — and they run on every PR, automatically, with no agent needed.

The five Phase-1 gates, cheapest → most expensive:

| # | Gate | Tool | What it blocks |
|---|---|---|---|
| 1 | Coverage threshold | pytest-cov / c8 | Unreachable code, untested branches |
| 2 | Type-strict mode | tsc / pyright strict | `any`, implicit `any`, null leaks |
| 3 | Env validation | pydantic-settings / zod | Missing/mis-typed env config at runtime |
| 4 | CODEOWNERS + branch protection | GitHub | Unreviewed merges, direct-to-main pushes |
| 5 | CI quality gate | GitHub Actions | Unformatted, unlinted, uncovered, untyped code |

All five are **config**, not skills — they enforce structurally. This skill *lays them
down*; the CI runs them *forever*.

---

## Protocol

### Step 0 — Detect the Stack

- [ ] Check `backend/` and `frontend/` for `pyproject.toml`, `requirements.txt`, `package.json`, `tsconfig.json`.
- [ ] Determine the test runner (pytest / vitest / jest) and type checker (tsc / pyright / mypy).
- [ ] Report what's missing before making any changes.

### Step 1 — Coverage Threshold (backend)

Add a coverage gate so untested code fails the build. For pytest, add to `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = 80      # adjust to project baseline; 80 is a sane floor
```

Install the plugin: `pip install pytest-cov`. The equivalent for a JS/TS backend is `c8` or `nyc` with a `check-coverage` threshold.

For frontend (vitest), add to `frontend/vite.config.ts`:

```ts
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'html'],
    thresholds: { lines: 80, statements: 80, branches: 70, functions: 80 },
  },
}
```

- [ ] Run `pytest --cov` locally — confirm the `fail_under` threshold is reachable (or set it to the current baseline).
- [ ] If coverage is below threshold, either raise coverage or document the exception. **Never silently lower the threshold.**

### Step 2 — Type-Strict Mode (frontend)

Enable strict type checking so `any` and null leaks fail the build. Start from this `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

- [ ] Run `npx tsc --noEmit` — fix all type errors before proceeding.
- [ ] Add a lint rule banning `any`: `@typescript-eslint/no-explicit-any` = `error`.
- [ ] For Python, enable `pyright` strict mode (`pyrightconfig.json` with `"typeCheckingMode": "strict"`) or `mypy --strict`.

### Step 3 — Environment Validation

Prevent missing/mis-typed env config from reaching prod. Validate at startup.

**Backend (pydantic-settings):**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    allowed_origins: list[str] = []
    log_level: str = "info"

    @property
    def is_production(self) -> bool:
        return self.log_level == "info"

# Fail fast at import if a required var is missing:
settings = Settings()
```

**Frontend (zod):**

```ts
import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_ENV: z.enum(['development', 'staging', 'production']),
});

// Throws at startup if validation fails:
export const env = envSchema.parse(process.env);
```

- [ ] Create `.env.example` with every variable, documented, no real secrets.
- [ ] Add `.env` to `.gitignore` (already there) — only `.env.example` is committed.
- [ ] The app fails fast at startup if a required var is missing — never silently defaults to a broken value.

### Step 4 — CODEOWNERS + Branch Protection

Enforce review ownership and safe merge paths.

**`.github/CODEOWNERS`** (at repo root):

```
# Default owner for all files
*            @team/backend

# Backend owns backend code
/backend/    @team/backend

# Frontend owns frontend code
/frontend/   @team/frontend

# Infra/config changes need infrastructure review
/.github/    @team/platform
Dockerfile*  @team/platform
```

- [ ] Replace `@team/*` with the real teams/individuals.
- [ ] Tell the user to enable branch protection in GitHub: **Settings → Branches → Add rule** for `staging` and `main`:
  - ✓ Require a pull request before merging (min 1 approval)
  - ✓ Require status checks to pass (the CI quality gate)
  - ✓ Require branches to be up-to-date
  - ✓ Do not allow force-pushes or deletions

### Step 5 — CI Quality Gate

Create `.github/workflows/quality.yml` (see the template in this skill) that runs lint, format check, typecheck, and coverage on every PR. This is the automated enforcement point — the same gates the agent runs locally, now mandatory in CI.

- [ ] Verify the workflow triggers on `pull_request` and `push` to `staging`/`prod`.
- [ ] Add the workflow name as a required status check in branch protection (Step 4).

---

## Verification / Gate

This skill is done when:

- [ ] `pytest --cov --cov-fail-under=80` passes (or the configured threshold)
- [ ] `npx tsc --noEmit` passes with strict mode enabled
- [ ] App fails fast on missing env vars (validated at startup)
- [ ] `.github/CODEOWNERS` exists with real teams
- [ ] Branch protection enabled with required status checks
- [ ] `.github/workflows/quality.yml` runs lint + format + typecheck + coverage on every PR

If any gate is missing, the project is not fully hardened. Do NOT declare done until all five are in place.

---

## Hard Rules

- ❌ Never silently lower a coverage threshold to make a failing build pass — raise coverage or document the exception
- ❌ Never disable strict mode to silence type errors — fix the types
- ❌ Never commit real secrets to `.env.example` — placeholders only
- ❌ Never add a quality gate and disable it in CI — the gate must actually fail the build
- ❌ Never skip the branch-protection step — config without enforcement is documentation