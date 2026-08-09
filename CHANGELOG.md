# Changelog

All notable changes to tapway-superpowers are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Changed

- **Documentation overhaul (repo-docs skill)** — generated `docs/ARCHITECTURE.md` (system diagram, components, key design decisions), `docs/WORKFLOWS.md` (Mermaid sequence diagrams for feature build, autoship, legacy refactor, incident response, release), and `docs/DEPLOYMENT.md` (install/publish for Claude + Hermes, adopting in a project, rollback, common issues). `DB_SCHEMA.md` intentionally omitted (tooling repo, no app DB).
- **`plugin.json` manifest fix** — `skills:` was missing 5 of 23 skills (e2e-playwright, quality-gates, api-contract-testing, db-migration-testing, incident-runbook) and `agents:` was empty despite 5 agent dirs. Now 23/23 skills + 5/5 agents in sync.
- **README** — skill count 22 → 24 (incl. Hermes-only dependency-audit), hooks 5 → 8 (added pre-commit-gate, dependency-audit, git pre-commit backstop), agents 4 → 5, ToC fixed (was stale "13 Skills"), new Documentation index, Guardrails section updated.
- **hermes/README** — "All 18 skills" → 24 (was stale since v1.5.0).

---
## [1.7.0] — 2026-08-09

### Added

- **`incident-runbook` skill** (Claude + Hermes) — closes the alert→action gap: SEV1-4 severity triage, symptom → suspected causes → check → mitigate → escalate → rollback runbook playbook, blameless 5-Whys postmortems with owned action items. Ships `runbook.md` + `postmortem.md` templates. Wired into `observe` (every alert must link to a runbook).
- **`db-reviewer` subagent** — database-layer review: N+1 query detection, index coverage on WHERE/JOIN columns, migration up/down safety, EXPLAIN ANALYZE on hot queries. Wired into `pr` (Step 4b) and `code-review` (Database Layers section).

### Changed

- **Hermes skill count** — 23 → 24 (`incident-runbook`).
- **Agents** — 4 → 5 (`db-reviewer`).

---
## [1.6.0] — 2026-08-09

### Added

- **`e2e-playwright` — accessibility (a11y) step** — mandatory `@axe-core/playwright` audit (WCAG A/AA tags) on every changed frontend route, woven into the same Playwright suite. Verified by a real E2E test: axe catches image-alt / label / button-name / color-contrast violations in a live browser and passes clean pages. Enforced automatically by the existing E2E CI gate (a violation = a test failure).
- **`verification` — performance/benchmark check** — hot-path perf gate: p95 latency baseline, SQLAlchemy query-count assertions (N+1 detection, `lazy="raiseload"` guidance), Lighthouse performance budget for frontend routes.
- **`security-audit` — auth-design review section** — beyond-OWASP design review: RBAC/ABAC matrix, IDOR checks, object-level vs function-level auth, OAuth state/PKCE, JWT algorithm pinning, session design, nested-resource re-checks, default-deny posture. Includes a finding template.

### Changed

- Both Claude (`skills/`) and Hermes (`hermes/skills/`) copies of all three skills extended.

---
## [1.5.0] — 2026-08-09

### Added

- **Enforceable hooks (Phase 3)** — repaired the broken hook system and added two commit-time quality gates:
  - **Root-cause fixes:** `plugin.json` no longer carries a stale empty `hooks` array; `hooks/hooks.json` uses the official auto-discovery + `Bash(git commit:*)` colon matcher form (the legacy space form never matched); blocking hooks now `exit 2` (exit 1 is treated as non-blocking by Claude Code — this was why hooks never fired/blocked).
  - **`pre-commit-gate` hook** (NEW) — lint + format + typecheck + coverage at commit time, blocks via exit 2 (Claude) / JSON `{"decision":"block"}` (Hermes shell hooks).
  - **`dependency-audit` hook + skill** (NEW) — osv-scanner / npm audit / pip-audit scan at commit time + CI; remediation skill for vulnerable deps.
  - **git `pre-commit` backstop** (NEW) — platform-agnostic `.git/hooks/pre-commit` hook installed by `setup-project`, catches commits from any agent or human.
  - **Hermes enforcement** — `hermes/config.hooks.yaml` shell-hook config (pre_tool_call blocking JSON protocol) + `hermes/agent-hooks/tapway-pre-commit-gate.sh` + `tapway-dependency-audit.sh`; `verification` + `pr` skills gained commit-gate + dep-audit checkpoints.

### Changed

- **Hermes skill count** — 22 → 23 (`dependency-audit`). Claude plugin count unchanged (22; hook-based enforcement).
- **CI quality gate** — added blocking `pip-audit` + `npm audit` steps (osv-scanner best-effort).

---
## [1.4.1] — 2026-08-09

### Fixed

- **`api-contract-testing`** — example code used removed `schemathesis.from_uri` API; fixed to `schemathesis.openapi.from_url` (both Claude + Hermes copies). Verified against Schemathesis v4.24.
- **`db-migration-testing`** — `test_column_rename_preserves_data` was vacuous (empty table → `all([])` trivially passes). Now seeds data pre-migration, applies the rename, and asserts values survived (template + both SKILL.md copies).
- **`db-migration-testing` (review round 2)** — the data-preservation test's relative migration steps were wrong: `downgrade -2` landed at base on a 2-migration chain (INSERT crashed with `OperationalError`), and `upgrade -1` after `downgrade -1` errored ("Relative revision -1 didn't produce 1 migrations"). Fixed to `downgrade -1` → seed → `upgrade +1`. **Verified by execution**: the fixed template passes 4/4 against a real alembic chain (create users with `display_name` → rename to `full_name`).
- **Test suites** — all three validation scripts wrapped in `if __name__ == "__main__":` so pytest collection no longer crashes (was raising `SystemExit` during import). Added API-correctness assertions (rejects removed `schemathesis.from_uri`).

### Changed

- **Test count** — 102 → 107 checks (phase2 suite 26 → 31: added API-correctness + migration-pattern assertions).

---

## [1.4.0] — 2026-08-09

### Added

- **`api-contract-testing` skill** — prevents API contract drift: OpenAPI schema validation, Schemathesis property-based fuzzing, Pact consumer-driven contracts. Wired into `e2e-playwright` (Step H) and `verification`. Ships `schemathesis.toml` template.
- **`db-migration-testing` skill** — makes migrations safe to ship: up/down round-trip tests, data preservation, zero-downtime expand-contract for large tables. Wired into `e2e-playwright` (Step H) and `verification`. Ships `test_migration.py` template.

### Changed

- **Skill count** — 20 → 22 (`install.sh` / `install.ps1` / READMEs updated).

---

## [1.3.0] — 2026-08-09

### Added

- **`quality-gates` skill** — config-layer hardening (Phase 1 of the gap analysis): lays down coverage thresholds (`pytest-cov --fail-under`), TypeScript strict mode (`tsconfig.strict.json` template), env validation (pydantic-settings/zod, `.env.example` template), CODEOWNERS + branch protection, and a CI lint/format/typecheck/coverage gate. Five declarative gates that block bad code at merge time, not after.
- **`.github/workflows/quality.yml`** — CI quality-gate workflow: backend lint (ruff) + format + typecheck (mypy) + tests/coverage gate; frontend lint + prettier check + tsc strict + tests/coverage.
- **`quality-gates` templates** — `coverage-pyproject.toml`, `tsconfig.strict.json`, `.env.example`, `CODEOWNERS`.
- **Wiring** — `setup-project` now also creates `.github/workflows/quality.yml`; `.gitignore` excludes `.coverage`, `htmlcov/`, `coverage.xml`.

### Changed

- **Skill count** — 19 → 20 (`install.sh` / `install.ps1` / READMEs updated).

---

## [1.2.0] — 2026-08-09

### Added

- **`e2e-playwright` skill** — structural end-to-end testing for both frontend (Playwright browser tests) and backend (pytest integration/E2E). Scaffolds `@playwright/test` + pytest, writes persistent specs (golden path + edge cases + error states, auth via `auth.setup.ts` storageState for frontend, httpx + ASGITransport + real test DB for backend), runs them, and debug-fixes failures from traces — never by weakening assertions. Conditionally mandated: frontend E2E when frontend files change, backend E2E when backend files change, both skip for docs-only.
- **`.github/workflows/playwright.yml`** — CI workflow with two jobs: `frontend-e2e` (Playwright, path-filtered to frontend changes) and `backend-e2e` (pytest integration/E2E, path-filtered to backend changes). Both upload artifacts on failure. Add `E2E_USER` / `E2E_PASSWORD` repo secrets for auth-dependent suites.
- **Structural enforcement** — `e2e-playwright` is wired into the pipeline so it's not optional: `tdd` runs it after unit GREEN for frontend and backend work, `autoship` makes it a **mandatory standard-mode gate** (not just deploy mode), and `verification` adds both `npx playwright test` and `pytest tests/integration/ tests/e2e/` to the checklist. The `test-writer` agent now emits E2E specs for both UI and API changes.

### Changed

- **Skill count** — 18 → 19 (`install.sh` / `install.ps1` / README counts updated).

---

## [1.1.0] — 2026-08-05

### Added

- **Hermes Agent port** — all 18 Tapway skills converted to Hermes `SKILL.md` format so Hermes users can run the same strict engineering pipeline as the Claude Code plugin (`interview → brainstorming → writing-plans → tdd → simplify-code → requesting-code-review → pr`). Ships under [`hermes/`](hermes/).
- **`hermes/install.sh` / `install.ps1`** — gbrain-style installer using Hermes's native skill hub (`hermes skills install <github-id>`). Installs all 18 skills and creates a **`/tapway` skill bundle** so the whole pipeline loads with one slash command. Supports `HERMES_DRY_RUN` for safe preview. No local file-layout dependency; stays in sync with the repo.
- **`hermes/README.md`** — skill-to-Hermes mapping and the strict-pipeline reference.

### Changed

- **`pr` skill** — target branch now read from `AGENTS.md` / `.hermes.md` / `CLAUDE.md` (with `staging` fallback) instead of `CLAUDE.md` only, so Hermes projects that don't ship `CLAUDE.md` work correctly.
- **`release.yml`** — replaced the CalVer convention (`YYYY.WW.XX.YY-env`) with **Semantic Versioning** (`vMAJOR.MINOR.PATCH-stg` / `-prod`). The bump is derived from conventional commits: `feat!`/`BREAKING CHANGE` → MAJOR, `feat:` → MINOR, otherwise PATCH. Each environment keeps an independent version stream.
- **`setup-project` skill & session-start hook** — no longer create or check for a `.github/workflows/claude.yml` PR-review workflow; only `release.yml` is set up.

### Removed

- **GitHub Actions PR review** (`.github/workflows/claude.yml`) — removed. Tapway now does code review inside the AI agent (`/review` in Claude Code, `requesting-code-review` in Hermes) before a PR is opened, instead of in GitHub CI. No `ANTHROPIC_API_KEY` secret is required.

---

## [1.2.0] — 2026-06-14

### Added

- **`/interview` skill** — requirements extraction through structured one-question-at-a-time interviewing before any planning or building begins. Surfaces the real goal behind the stated request: who benefits, why now, success criteria, constraints, out of scope. Stops when you can predict the user's reaction to the next 3 questions. Output is a Confirmed Intent statement that feeds directly into `/brainstorming` or `/plan`.
- **`/doubt` skill** — adversarial in-flight decision review. Spawns a fresh-context subagent to disprove rather than validate a decision. The reviewer receives only the artifact and its contract, never the reasoning — eliminating confirmation bias. Finding classes: Contract misread / Actionable / Trade-off / Noise. Max 3 cycles. Includes explicit cross-model review offer for high-stakes decisions.
- **`/observe` skill** — structured observability implementation shipped alongside features, not as a post-launch afterthought. Protocol: define on-call questions first, then choose signal (log / metric / trace), implement structured logging with correlation IDs, RED metrics with bounded label values, OpenTelemetry with auto-instrumentation, symptom-based alerting with runbooks, and staging verification by inducing failures. Never log PII; never use unbounded values as metric labels.
- **`/deprecate` skill** — safe removal of APIs, endpoints, feature flags, and internal modules. Decision gate (unique value? consumer count? replacement exists?), build replacement first, choose advisory vs compulsory type, migration guide at `docs/migrations/`, Strangler/Adapter/Feature-flag patterns, 14-day zero-traffic verification for external APIs, CHANGELOG `### Removed` entry. Includes zombie code protocol.

### Changed

- **`/tdd` skill** — added **Step 0: Source Check** before dispatching any subagent. Detects stack versions from dependency files, fetches official docs for framework-specific tasks, and states the stack explicitly at the top of every subagent prompt. Prevents training-data drift on fast-moving frameworks.
- **`release.yml`** — trigger branch renamed `stg` → `staging` to match the actual branch name. Release notes now extracted from `CHANGELOG.md` via awk instead of GitHub's auto-generated changelog.
- **`/pr` skill** and **`/setup-project` skill** — updated all references from `stg` → `staging` to match the correct branch name.

---

## [1.1.0] — 2026-06-01

### Added

- **`/setup-project` skill** — one-time project setup for any repo adopting the plugin: creates `.github/workflows/claude.yml` (with both auto-review and on-mention jobs), creates a minimal `CLAUDE.md` if missing, commits both, and prints a manual-steps checklist (GitHub secret, filling in CLAUDE.md). The session-start hook now warns if the workflow file is absent and prompts the user to run this skill.
- **`/autoship` deploy mode** — triggered by "implement and deploy" or "ship and deploy". Adds Phase 4D before opening the PR: auto-detects deployment method (docker compose / make / npm / Procfile), deploys, runs a 60-second health-check loop against `/health` `/healthz` `/ping`, runs all integration and E2E test suites found (pytest, Playwright, Cypress), and includes deployment evidence in the PR body. Never opens a PR with a broken deployment.
- **Auto-review GitHub Actions job** — `.github/workflows/claude.yml` now contains two separate jobs: `auto-review` (fires on every PR open/update, read-only, posts three-tier Critical/Warning/Suggestion inline review automatically) and `on-mention` (fires on `@claude` mentions, read-write, can push fix commits). Previously only the on-mention job existed.
- **`docs/legacy-refactor-guide.md`** — complete workflow guide for teams taking over an existing codebase without tests: bootstrap with `/repo-docs`, audit with `/code-review` + `/security-audit`, goal alignment with `/brainstorming`, characterization tests before any production change, then `/plan` → `/tdd` → `/pr`.
- **`externalSkills` field in `plugin.json`** — documents the optional `code-refactor` community skill (bulk renames, deprecated API replacements) as a complement to `/refactor` Protocol B.

### Changed

- **`/pr` skill** — added mandatory Step 4 (Update Docs): runs `git diff --name-only origin/main`, triggers `/repo-docs` on first-ever PR if `docs/ARCHITECTURE.md` is absent, otherwise updates only the affected doc sections per a file-to-doc mapping table. Steps renumbered: Push=5, Create PR=6, Update Checklist=7.
- **`/autoship` skill** — Phase 4 now explicitly includes a doc update step (same logic as `/pr`) before calling `/pr`, making the full flow transparent.
- **`/refactor` skill** — rewritten with two clearly labelled protocols: **Protocol A** (incremental, for codebases that already have tests — original content preserved) and **Protocol B** (legacy, characterization-test-first sequence for repos without coverage). Community skill `code-refactor` documented at the bottom.
- **README** — complete restructure with a table of contents and three mode sections (Individual, Team Collaboration, Legacy Refactor), each with a workflow diagram, step-by-step guide, and quick-reference block. Added "GitHub Actions — AI-Powered PR Review" section with setup instructions, two-job breakdown, `ANTHROPIC_API_KEY` reminder with exact GitHub Settings navigation path, cost estimate, and troubleshooting checklist.
- **Session-start hook** — now checks for `.github/workflows/claude.yml` on every session start and prints a setup warning with fix instructions if the file is absent.

### Fixed

- **`id-token: write` permission** — added to both `auto-review` and `on-mention` jobs in `.github/workflows/claude.yml`. `claude-code-action@v1` uses GitHub OIDC for authentication; without this permission every run failed with `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL`.

---

## [1.0.0] — 2026-05-30

### Added

- **`/tdd` skill** — replaces and consolidates the former `tdd` and `subagent-driven-development` skills into a single, structurally enforced TDD workflow. Each task is split into a **Test Writer agent** (RED phase) and an **Implementer agent** (GREEN + REFACTOR), with the coordinator as the gate between phases. TDD cheating is structurally impossible.
- **`/pr` skill** — full PR preparation workflow: worktree verification, rebase against `main`, conflict resolution, test gate (pytest + npm test), `gh pr create` with conventional commit title and structured body, and work package checklist update. Mandatory exit from every implementation session.
- **`/autoship` skill** — fully automated plan-to-PR loop. Reads a written plan from `docs/plans/`, runs a health check on every task (verifiable criteria, exact file paths, no ambiguity), executes each task with the TDD subagent pattern (Test Writer → RED gate → Implementer), then runs `/simplify` → `/review` → `/pr` without human intervention. Pauses only on repeated task failure or Critical review findings requiring a design decision. Invoke with: _"implement it with autopilot"_.
- **Work package checklists** — `/plan` now generates a companion `docs/checklists/[feature]-checklist.md` broken by discipline (Backend, Frontend, DevOps, QA). Team members self-assign packages and track status (🔴 / 🟡 / 🟢).
- **Docs structure** — all brainstorming outputs, plans, and checklists are saved to `docs/` in the project repo and committed immediately so teammates can see them.
- **GitHub Actions** — `.github/workflows/claude.yml` wires `anthropics/claude-code-action@v1` to `@claude` mentions in PR comments and review submissions for AI-assisted fixes.
- **Team collaboration guide** — `docs/team-guide.md` with a full 3-person parallel workflow walkthrough (Alice, Bob, Charlie), exact commands, conflict resolution, and a quick reference card.
- **Hook execute permissions** — all five hook scripts ship with `chmod +x` so they run correctly on fresh installs.

### Changed

- **`/brainstorming` skill** — save step commits the output immediately; optional Step 0 `/deep-research` added for unfamiliar domains.
- **`/plan` skill** — commits and pushes plan + checklist before implementation; work package "How to Pick Up" section with exact commands and Claude prompts.
- **`/tdd` skill** — enforces worktree before starting; pre-PR sequence updated to `[/cleanup] → /simplify → /review → /pr`.
- **`/systematic-debugging` skill** — repro-first test before fix; parallel hypothesis generation; regression test retention; references `/bugfix` and `/investigate`.
- **`/verification` skill** — adds live app verification (golden path + edge cases); references built-in `/verify`.
- **`/security-audit` skill** — scope table added: `/security-review` for diffs, `/security-audit` for full codebase.
- **`git-worktrees` skill** — step 5 updated to full pre-PR sequence; step 6 added for worktree cleanup.
- **README** — Team Collaboration section, daily workflow pipeline, Built-in Claude Code Skills reference table.

### Removed

- **`subagent-driven-development` skill** — merged into `/tdd`.

---

## [0.1.0] — 2026-05-29

Initial release with 12 skills, 5 guardrail hooks, and 4 specialized agents.

### Skills
`brainstorming`, `writing-plans`, `tdd`, `verification`, `refactor`, `code-review`, `systematic-debugging`, `subagent-driven-development`, `git-worktrees`, `repo-docs`, `security-audit`, `pre-review-cleanup`

### Hooks
`pre-bash-safety`, `post-write-lint`, `pre-commit-secrets`, `session-start`, `post-commit-release-note`
