# Tapway Superpowers

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude Code plugin (and now a Hermes Agent port) with 17 AI skills, 5 guardrail hooks, and specialized subagents for full-stack development (Next.js 14 + Python FastAPI). The plugin enforces best practices structurally — TDD via agent boundaries, mandatory PR gates, docs on every push — so good habits happen automatically.

**Pick your tool:**
- **Claude Code users** → install the plugin below (slash commands + hooks).
- **Hermes Agent users** → see [Hermes Support](#hermes-support) for a ready-to-install skill port that runs the same pipeline.

## Quick Install

```bash
# 1. Register this repo as a marketplace
claude plugin marketplace add https://github.com/tapway/tapway-superpowers

# 2. Install the plugin
claude plugin install tapway-superpowers@tapway-superpowers
```

Skills and hooks activate immediately. No restart, no config files.

**Recommended companion plugins:**
```bash
claude plugin install andrej-karpathy-skills@karpathy-skills
claude plugin install claude-code-setup@claude-plugins-official
```

---

## Hermes Support

Prefer **Hermes Agent** over Claude Code? A port of these skills ships in this repo under [`hermes/`](hermes/). Same skills, same strict pipeline — `interview → brainstorming → writing-plans → tdd → simplify-code → requesting-code-review → pr` — running on Hermes's own skill system.

```bash
# From inside the cloned repo:
cd hermes
bash install.sh        # macOS / Linux — installs all 24 skills + the /tapway bundle
# or, on Windows (PowerShell):
.\install.ps1
```

This installs all **18** Tapway skills through Hermes's native skill hub and creates a
`/tapway` skill bundle that loads the whole pipeline with one slash command. A few
Claude-only pieces (commit hooks, secret scanning) don't auto-run
in Hermes — the equivalent discipline is preserved by following the pipeline. Full details
and the skill-to-Hermes mapping are in [`hermes/README.md`](hermes/README.md).

---

## Table of Contents

- [Documentation](#documentation)
- [Modes](#modes)
  - [Individual — solo feature or bug fix](#individual--solo-feature-or-bug-fix)
  - [Team Collaboration — parallel work packages](#team-collaboration--parallel-work-packages)
  - [Legacy Refactor — existing repo without tests](#legacy-refactor--existing-repo-without-tests)
- [Code Review — Inside the Agent](#code-review--inside-the-agent)
- [Release Convention — Semantic Versioning](#release-convention--semantic-versioning)
- [What You Get](#what-you-get)
  - [24 Skills](#24-skills)
  - [8 Guardrail Hooks](#8-guardrail-hooks)
  - [5 Specialized Agents](#5-specialized-agents)
- [Slash Commands Reference](#slash-commands-reference)
- [Hermes Support](#hermes-support)
- [Built-in Claude Code Skills](#built-in-claude-code-skills)
- [Guardrails That Run Silently](#guardrails-that-run-silently)
- [Upgrading](#upgrading)
- [For Template Users](#for-template-users)
- [Uninstalling](#uninstalling)

---

## Documentation

Standardized technical documentation (generated via the `repo-docs` skill):

- **[Architecture](docs/ARCHITECTURE.md)** — system diagram, component breakdown, key design decisions
- **[Workflows](docs/WORKFLOWS.md)** — sequence diagrams for feature build, autoship, legacy refactor, incident response, and release
- **[Deployment](docs/DEPLOYMENT.md)** — install/publish for Claude Code + Hermes, adopting in a project, rollback, common issues
- **Team guide** — [docs/team-guide.md](docs/team-guide.md)
- **Legacy refactor guide** — [docs/legacy-refactor-guide.md](docs/legacy-refactor-guide.md)

> `DB_SCHEMA.md` is intentionally omitted — this is a tooling/plugin repo with no
> application database.

---

## Modes

Not sure which mode applies? Use this table:

| Situation | Mode |
|---|---|
| Solo developer, building a new feature or fixing a bug | [Individual](#individual--solo-feature-or-bug-fix) |
| Team of 2+ people working on the same repo in parallel | [Team Collaboration](#team-collaboration--parallel-work-packages) |
| Taking over or improving an existing codebase without tests | [Legacy Refactor](#legacy-refactor--existing-repo-without-tests) |

---

### Individual — solo feature or bug fix

**Full guide:** this section covers it. No separate document needed.

#### Workflow

```
/interview → /brainstorming → /plan → [implement] → /simplify → /review → /pr
```

`/interview` is optional but recommended any time the request is underspecified. `/observe` runs before `/pr` on any new endpoint. `/doubt` is called on demand for high-stakes decisions.

**Step 0 — Clarify** (when the request is fuzzy)
```
/interview
```
One question at a time. Stops when it can predict your next three questions. Outputs a **Confirmed Intent** statement (outcome / user / why now / success / constraints / out of scope) that feeds into `/brainstorming` or `/plan`. Never start planning until intent is confirmed.

**Step 1 — Brainstorm** (optional, but recommended for anything non-trivial)
```
/brainstorming
```
Explore approaches, surface trade-offs, name confusion before writing code. Output is committed to `docs/brainstorming/`. Run `/deep-research` first if the domain is unfamiliar.

**Step 2 — Plan**
```
/plan
```
Generates `docs/plans/[feature].md` with file map, task breakdown, and success criteria. For multi-task features, also generates a work package checklist at `docs/checklists/[feature]-checklist.md`.

**Step 3 — Implement**

*Fast path — fully automated:*
```
"implement it with autopilot"   →   /autoship
```
Reads the plan, validates it, runs TDD subagents per task, then simplify → review → PR. You only intervene if a task blocks twice.

*Deploy mode — on a staging server:*
```
"implement and deploy"   →   /autoship (deploy mode)
```
Same as above, but adds a deployment phase before opening the PR: detects the deploy method (docker compose / make / npm), deploys, waits for a health check, runs integration and E2E tests, then includes the deployment evidence in the PR body. Never opens a PR with a broken deployment.

*Manual path — step by step:*
```
/tdd
```
Test Writer agent (RED) → coordinator gate → Implementer agent (GREEN + REFACTOR) per task. Structurally impossible to skip the failing test.

**Between steps — on demand**

```
/doubt
```
Use this any time you're about to commit to an irreversible decision: service boundary, schema migration, auth flow, security assumption. Spawns a fresh-context adversarial reviewer that sees only the artifact + contract — never your reasoning. Max 3 cycles.

```
/observe
```
Run this before `/pr` on any new endpoint, background task, or external integration. Defines on-call questions first, then adds structured logging (with correlation IDs), RED metrics (bounded labels), OpenTelemetry auto-instrumentation, and symptom-based alerts. Includes staging verification: induce failures, confirm telemetry catches them.

**Step 4 — Pre-PR sequence** (always, in this order)
```
/simplify       ← reduce complexity and duplication
/review         ← three-tier self-review (Critical / Warnings / Suggestions)
/pr             ← rebase, test, update docs, push, open PR
```

**`/pr` is mandatory** — it rebases against `main`, runs the full test suite, updates project docs, and opens a structured PR. Never push manually.

---

### Team Collaboration — parallel work packages

**Full guide:** [docs/team-guide.md](docs/team-guide.md) — step-by-step walkthrough with Alice, Bob, and Charlie working on JWT auth in parallel, with exact commands and Claude prompts for every step.

#### Workflow

```
Tech lead: /brainstorming → /plan → commit docs → assign packages
Each member: worktree → /tdd or /autoship → /pr
After all PRs: merge in dependency order → /release
```

#### How It Works

**One worktree per person per package.** Never two people editing the same branch.

```bash
# After self-assigning in docs/checklists/[feature]-checklist.md:
git worktree add -b feat/[feature]-[package] ../[project]-[package] origin/main
cd ../[project]-[package] && claude
# Tell Claude: "I'm picking up the [Backend] work package for [feature]. Let's start implementing."
```

**Docs as the coordination layer.** `docs/checklists/` is the live status board — who has what, what's in progress, what's merged. No Slack threads needed for "who's doing what".

```
docs/
  brainstorming/   ← why we chose this approach
  plans/           ← what we're building and how
  checklists/      ← who is doing what, current status
```

**Code review happens inside the AI agent, not in GitHub CI.** Every PR is reviewed by the agent using the `/review` (Claude Code) or `requesting-code-review` (Hermes) skill before it's opened — a three-tier Critical/Warning/Suggestion self-review run by the implementing agent. There is no GitHub Actions-based PR review workflow; review discipline is enforced by the pipeline, not by CI.

**Merge order matters.** If Package B depends on Package A's schema changes, merge A first and have B rebase:
```bash
git fetch origin && git rebase origin/main
# resolve any conflicts, then re-push
```

#### Quick Reference

```bash
# Self-assign and start
# 1. Edit docs/checklists/[feature]-checklist.md → set Assignee + 🟡
git add docs/checklists/ && git commit -m "chore: claim [package] for [name]" && git push

# 2. Create worktree
git worktree add -b feat/[feature]-[package] ../[project]-[package] origin/main
cd ../[project]-[package] && claude

# 3. Implement (automated or manual)
# "implement it with autopilot"   OR   /tdd

# 4. Exit via PR (never push manually)
# /simplify → /review → /pr
```

---

### Legacy Refactor — existing repo without tests

**Full guide:** [docs/legacy-refactor-guide.md](docs/legacy-refactor-guide.md) — complete workflow for teams taking over an existing codebase.

#### The Core Problem

You cannot safely refactor code you haven't locked down with tests. On legacy code that means writing **characterization tests** — tests that capture current behavior before you change anything — before the first line of refactored code is written.

#### Workflow

```
Install superpowers → /repo-docs → /code-review + /security-audit
  → /brainstorming (refactor goals)
  → Characterization tests  ← lock down current behavior FIRST
  → /plan → /tdd → /pr
```

#### Key Differences from the Standard Workflow

| Step | Standard (new feature) | Legacy refactor |
|---|---|---|
| Tests | Written for desired behavior | Written for **current** behavior first |
| RED phase | Fails because feature doesn't exist | Fails because code is too coupled to unit-test |
| GREEN phase | Implement the behavior | Decouple/extract until test + characterization tests pass |
| Plan scope | New capabilities | Specific code smells with measurable before/after |

#### For Bulk Mechanical Changes

For renames, deprecated API replacements, and import path updates across many files — use the optional `code-refactor` community skill:

```bash
claude plugin add code-refactor@andrej-karpathy-skills
```

**Always write characterization tests before running bulk changes on untested code.** Bulk renames on untested code cascade silently into broken behavior.

#### Quick Start

```bash
# 1. Generate architecture docs first
/repo-docs

# 2. Run audits (parallel)
/code-review
/security-audit

# 3. Set refactoring goals
/brainstorming
# "Given the audit findings, what does this codebase need to look like in 6 months?"

# 4. Write characterization tests — before any production change
# See docs/legacy-refactor-guide.md for examples

# 5. Plan + execute + PR
/plan → /tdd → /pr
```

---

## Code Review — Inside the Agent

Tapway does **not** run PR review in GitHub CI. Code review is performed by the AI agent during development, before a PR is opened:

| Tool | Review skill | When |
|---|---|---|
| Claude Code | `/review` (built-in) — three-tier Critical / Warnings / Suggestions | Every PR, before `/pr` |
| Hermes | `requesting-code-review` (core) | Every PR, before `pr` |

This is structural in the pipeline (`/simplify → /review → /pr`), so a PR that reaches GitHub has already been simplified and self-reviewed by the implementing agent. If Critical findings are raised, the agent fixes them before opening the PR.

No `ANTHROPIC_API_KEY` secret, no `claude.yml` workflow, and no GitHub Actions review cost.

---

## Release Convention — Semantic Versioning

Releases are created **automatically** every time a PR merges to `staging` or `prod`, via `.github/workflows/release.yml`.

### Format

```
vMAJOR.MINOR.PATCH-env
```

| Segment | Meaning | Example |
|---|---|---|
| `MAJOR` | Breaking change (`feat!` or `BREAKING CHANGE`) | `2` |
| `MINOR` | New feature (`feat:`) | `1` |
| `PATCH` | Bugfix / small change (anything else) | `3` |
| `-env` | Target environment | `-stg` or `-prod` |

### Rules

- **PATCH increments** on every merge by default
- **MINOR increments** (and PATCH resets to 0) when any merged commit is `feat: ...`
- **MAJOR increments** (and MINOR/PATCH reset to 0) when any merged commit contains `feat!` or `BREAKING CHANGE`
- `stg` and `prod` maintain **independent** MAJOR.MINOR.PATCH streams

### Examples

```
v1.1.0-stg   ← feature merge to staging
v1.1.1-stg   ← bugfix on top of 1.1.0
v1.2.0-stg   ← next feature
v2.0.0-stg   ← breaking change (MAJOR bump)
v1.1.0-prod  ← promoted to prod (prod's own stream)
```

### Setup

`release.yml` is created automatically by `/setup-project`. It requires only the built-in `GITHUB_TOKEN` — no extra secrets needed.

Set `staging` as your repo's default branch (GitHub → Settings → Branches → Default branch) so `gh pr create` targets it automatically (branch name: `staging`, tag suffix: `-stg`).

---

## What You Get

### 24 Skills

AI behaviors that activate automatically when you use relevant keywords. Also invokable explicitly with `/skill-name`.

| Skill | What it does | Triggers |
|---|---|---|
| `brainstorming` | Explore approaches, surface trade-offs, save decisions to `docs/brainstorming/` | "Let's think about...", "What are the options..." |
| `writing-plans` | Implementation plans with file maps, task breakdowns, and work package checklists. Saves to `docs/plans/` + `docs/checklists/` | "Write a plan...", "Break this down..." |
| `autoship` | Fully automated plan-to-PR: validates plan, runs TDD subagents per task, then simplify → review → docs → PR. **Deploy mode** (on staging server): also deploys, health-checks, and runs integration/E2E tests before PR | "implement it with autopilot", "autoship" / "implement and deploy", "ship and deploy" |
| `tdd` | Test Writer agent (RED) → coordinator gate → Implementer agent (GREEN + REFACTOR). Structurally enforces TDD. | "Start implementing...", "implement", any new feature or bug fix |
| `e2e-playwright` | Enforce end-to-end testing for both frontend (Playwright browser tests) and backend (pytest integration/E2E). Scaffolds Playwright + pytest, writes persistent specs (golden path + edge cases + error states), runs them, and debug-fixes failures from traces — never by weakening assertions. Conditionally mandated: frontend E2E runs when frontend files change, backend E2E when backend files change, both skip for docs-only. Gates PRs in the TDD pipeline. | "e2e test", "playwright", "browser test", "test the UI", "end-to-end", "frontend test", "integration test", "backend test", "verify the flow" |
| `quality-gates` | Lay down the config-layer quality gates: coverage thresholds (pytest-cov `--fail-under`), TypeScript strict mode, env validation (pydantic-settings/zod), CODEOWNERS + branch protection, and a CI lint/format/typecheck/coverage gate. Declarative enforcements that run on every PR automatically. | "coverage gate", "strict mode", "tsconfig strict", "env validation", "CODEOWNERS", "branch protection", "quality gate", "add coverage", "enforce type safety" |
| `api-contract-testing` | Prevent API contract drift. Validates every response against the OpenAPI schema, fuzzes the API with Schemathesis (property-based testing), and uses Pact contracts where services deploy independently. Catches the highest-severity backend gap: an API that changes shape without breaking its contract. | "contract test", "schemathesis", "openapi", "api contract", "pact", "schema validation", "fuzz the api", "api drift" |
| `db-migration-testing` | Make database migrations safe to ship: test every migration up AND down (round-trip), verify zero-downtime expand-contract for large tables, confirm rollback and data preservation before touching prod. Prevents the second most common prod-outage class. | "migration", "alembic", "schema change", "migrate", "add column", "backfill", "zero-downtime migration", "rollback migration", "db migration test" |
| `dependency-audit` | Audit and remediate supply-chain vulnerabilities in dependencies. Scans with osv-scanner (multi-ecosystem), npm audit (Node), pip-audit (Python); upgrades vulnerable packages in the lockfile and verifies the fix. Enforced at commit time + CI, and on demand for remediation. | "dependency audit", "osv-scanner", "npm audit", "pip-audit", "vulnerable package", "supply chain", "update dependencies", "fix vulnerabilities" |
| `incident-runbook` | Create SEV1-4 incident runbooks and blameless postmortems that close the alert→action gap. Every observe alert links to a runbook this skill writes: symptom → suspected causes → check → mitigate → escalate → rollback, plus 5-Whys postmortems with owned action items. | "runbook", "incident", "postmortem", "on-call", "create a runbook", "write a postmortem", "SEV" |
| `verification` | Confirm a task is done — tests, lint, type-checks, spec coverage | "Is this done?", "Verify...", "Final check..." |
| `refactor` | **Protocol A** (active codebase): surgical incremental refactoring. **Protocol B** (legacy): characterization-test-first sequence | "Refactor...", "Clean up...", "Legacy refactor..." |
| `code-review` | Three-tier review: Critical, Warnings, Suggestions | "Review my changes...", "Check this before I push..." |
| `systematic-debugging` | Repro → Isolate → Hypothesize → Test → Fix → Post-mortem saved to `docs/post-mortems/` | "Why is X failing?", "Debug...", "Works locally but not in prod..." |
| `pr` | Rebase, conflict resolution, test gate, **update docs**, push, open PR, update checklist | "Create a PR...", "I'm done...", "Push and PR..." |
| `git-worktrees` | Manage parallel git worktrees for concurrent feature work | "Worktree...", "Parallel branches..." |
| `repo-docs` | Generate `ARCHITECTURE.md`, `WORKFLOWS.md`, `DB_SCHEMA.md`, `DEPLOYMENT.md` | "Document this repo...", "Write architecture docs..." |
| `security-audit` | Full-codebase OWASP Top 10 audit — for pre-launch or major refactors | "Security audit...", "Audit the whole codebase..." |
| `pre-review-cleanup` | Scan for template placeholders, boilerplate, and stale scaffold code | "Clean up template files...", "Remove boilerplate..." |
| `setup-project` | One-time setup: creates `.github/workflows/release.yml` and `CLAUDE.md`, commits, prints checklist for remaining manual steps | "setup project", "initialize project for the team", "project setup" |
| `interview` | Requirements extraction — one question at a time before planning begins. Stops when it can predict your next 3 questions. Outputs a Confirmed Intent statement. | "interview me", "help me figure out requirements", "I'm not sure what I want" |
| `doubt` | Adversarial in-flight decision review. Fresh-context subagent gets only artifact + contract (never your reasoning). Finds problems, doesn't approve. Max 3 cycles. | "second opinion", "double-check this decision", "stress-test this design" |
| `observe` | Structured observability shipped with the feature: on-call questions first → structured logs + correlation IDs → RED metrics → OTel → symptom-based alerts → staging verification | "add observability", "add logging", "add metrics", "add tracing", "instrument this" |
| `deprecate` | Safe removal of APIs, modules, or features: decision gate → replacement first → advisory/compulsory type → migration guide → Strangler/Adapter/Feature-flag → zero-usage gate → remove | "deprecate this", "remove this API", "sunset this feature", "migrate away from X" |

> All skills apply Andrej Karpathy's coding principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.

---

### 8 Guardrail Hooks

Automatic checks that fire on Claude Code lifecycle events.

| Hook | Event | What it does |
|---|---|---|
| `pre-bash-safety` | PreToolUse (Bash) | Blocks force-push, hard-reset on `main`, direct commits to `main`. Blocks prod commands unless `ALLOW_PROD=1` is set. |
| `pre-commit-secrets` | PreToolUse (git commit) | Scans staged files for secrets, keys, and credentials before allowing a commit |
| `pre-commit-gate` | PreToolUse (git commit) | Blocks the commit (`exit 2`) when lint / format / typecheck / coverage fail — the progress quality gate |
| `dependency-audit` | PreToolUse (git commit) | Blocks the commit (`exit 2`) when critical/high vulnerabilities are found (osv-scanner / npm audit / pip-audit) |
| `pre-commit` (backstop) | Git `pre-commit` hook | Platform-agnostic backstop installed by setup-project; catches lint/format/typecheck failures from any agent or human |
| `post-write-lint` | PostToolUse (Write\|Edit) | Runs the project linter on changed files |
| `session-start` | SessionStart | Displays project info, git status, and environment summary when Claude Code opens |
| `post-commit-release-note` | PostToolUse (git commit) | Parses conventional commits and appends formatted entries to `CHANGELOG.unreleased.md` |

---

### 5 Specialized Agents

Subagent definitions for use with the TDD and autoship skills:

| Agent | Purpose |
|---|---|
| `code-reviewer` | Systematic review with security, performance, and type-safety checks |
| `test-writer` | Write tests following project conventions (pytest / Jest) |
| `db-reviewer` | Database-layer review: N+1 detection, index coverage, migration safety, EXPLAIN ANALYZE |
| `security-auditor` | OWASP Top 10 audit for auth, payments, and user data paths |
| `devops-sre` | Docker, CI/CD, and infrastructure configuration review |

---

## Slash Commands Reference

| Command | Mode | Purpose |
|---|---|---|
| `/setup-project` | All | One-time project setup: creates `.github/workflows/release.yml` and `CLAUDE.md`, commits, prints a manual-steps checklist. Run this in any new repo adopting the plugin. |
| `/interview` | All | Extract requirements one question at a time before planning. Use when the request is underspecified. Output feeds into `/brainstorming` or `/plan`. |
| `/brainstorming` | All | Explore approaches before coding |
| `/plan` | All | Write implementation plan + work package checklist |
| `/autoship` | Individual / Team | Run full plan-to-PR loop automatically. Add "and deploy" to also deploy + run integration tests before PR (staging server only) |
| `/tdd` | Individual / Team | TDD subagents for task-by-task implementation |
| `/refactor` | Individual / Legacy | Incremental (Protocol A) or legacy characterization-test workflow (Protocol B) |
| `/doubt` | All | Adversarial review of any high-stakes decision before it's locked in. Use for irreversible changes, service boundaries, security assumptions. |
| `/observe` | All | Add structured logging, RED metrics, OTel, and alerts to any new endpoint or task. Run before `/pr`. |
| `/pr` | All | Rebase, test, update docs, push, open PR, update checklist — **mandatory exit** |
| `/deprecate` | All | Safe removal of any API, module, or feature. Enforces: replacement first, migration guide, zero-usage gate. |
| `/repo-docs` | Legacy / All | Generate architecture, schema, workflow, deployment docs |
| `/cleanup` | Individual | Remove template artifacts *(tapway-claude-template users only)* |
| `/review` | All | Three-tier self-review before PR |
| `/release <patch\|minor\|major>` | All | Semver bump, release notes, git tag |
| `/upgrade-skills` | All | Update all plugins to latest |

---

## Built-in Claude Code Skills

These ship with Claude Code — no installation needed. Several are wired into the skills above.

| Built-in | What it does | When to use |
|---|---|---|
| `/deep-research` | Multi-source web research with fact-checking and citations | Before `/brainstorming` for unfamiliar tech |
| `/bugfix` | Repro-first: failing test → root cause → minimal fix → regression test | Focused code bugs |
| `/investigate` | Parallel hypothesis agents with adversarial refutation; formal root-cause report | Production incidents |
| `/simplify` | Reviews changed code for reuse, simplification, efficiency; applies fixes | Always after `/tdd`, before `/review` |
| `/security-review` | Security review of the current branch diff | Before PRs touching auth, payments, user data |
| `/verify` | Launches the app and observes behavior in a running environment | Golden-path confirmation beyond tests |

**`/security-review` vs `/security-audit`:** `/security-review` scans the current diff (fast, pre-PR). `/security-audit` scans the full codebase (thorough, pre-launch or after major refactors).

---

## Guardrails That Run Silently

These happen automatically — no commands needed:

- **Can't commit to `main` directly** — the hook blocks it and tells you to create a branch
- **Can't run prod commands accidentally** — blocked unless `ALLOW_PROD=1` is set
- **Secrets caught before commit** — staged files scanned for keys and credentials on every `git commit`
- **Commits blocked on quality failures** — `pre-commit-gate` blocks (`exit 2`) a commit whose lint/format/typecheck/coverage fails
- **Commits blocked on vulnerable dependencies** — `dependency-audit` blocks a commit with critical/high CVEs (osv-scanner / npm audit / pip-audit)
- **Every commit from any agent or human** — the git `pre-commit` backstop enforces lint/format/typecheck outside the agent
- **Linting after every file edit** — runs the project linter automatically
- **Release notes auto-generated** — every conventional commit appends to `CHANGELOG.unreleased.md`
- **Docs updated on every PR** — `/pr` runs `/repo-docs` or updates affected doc sections before pushing
- **Missing workflow detected on session start** — if `.github/workflows/release.yml` is absent, the session-start hook warns and tells you to run `/setup-project`

---

## Upgrading

```
/upgrade-skills
```

Or manually:

```bash
claude plugin marketplace update
claude plugin update tapway-superpowers@tapway-superpowers
```

Restart Claude Code after updating to apply changes.

---

## For Template Users

If you cloned the [tapway-claude-template](https://github.com/tapway/tapway-claude-template), this plugin is already declared in `.claude/settings.json` and auto-installs on first open. No install commands needed.

---

## Uninstalling

```bash
claude plugin uninstall tapway-superpowers@tapway-superpowers
```

Your code and project docs are unaffected.

---

## License

MIT © Tapway
