# Architecture — Tapway Superpowers

## Overview

Tapway Superpowers is an **agentic engineering-methodology plugin**: a set of
skills, hooks, and specialized subagents that enforce a strict
plan → TDD → review → PR pipeline inside AI coding agents. It ships two
installable forms from one source repo — a **Claude Code plugin**
(`.claude-plugin/`, slash commands + hooks) and a **Hermes Agent port**
(`hermes/`, native `SKILL.md` files) — so the same engineering discipline runs
on either harness. External consumers are development teams adopting the plugin
in their own repos; internal consumers are the coding agents (Claude Code,
Hermes) that load the skills.

## System Diagram

```mermaid
graph TD
  Team[Dev Team] -->|uses| Claude[Claude Code]
  Team -->|uses| Hermes[Hermes Agent]

  Claude -->|loads| Manifest[.claude-plugin/plugin.json]
  Manifest -->|discovers| Skills[23 Claude skills]
  Manifest -->|discovers| Agents[5 subagents]
  Manifest -->|discovers| Hooks[8 guardrail hooks]
  Hooks -->|fires on| Lifecycle[PreToolUse / PostToolUse / SessionStart / git commit]

  Hermes -->|installs via| Installer[hermes/install.sh + install.ps1]
  Installer -->|installs| HSkills[24 Hermes skills]
  Installer -->|creates| Bundle[/tapway skill bundle]

  Agents -->|delegated by| Pipeline[Strict pipeline: interview → brainstorming → writing-plans → tdd → e2e → review → pr]
  Skills -->|power| Pipeline
  Hooks -->|enforce| QualityGates[Quality + dependency gates]
  QualityGates -->|write to| ProjectRepo[Adopting project repo]
  Pipeline -->|produces| PR[Pull request]
  PR -->|gated by| CI[CI: release.yml + quality.yml + playwright.yml]
```

## Component Breakdown

### Claude Code plugin (`.claude-plugin/`)
- **`plugin.json`** — manifest that declares the plugin's identity and points at
  the 23 skills and 5 subagents (hooks auto-discover via `hooks/hooks.json`).
- **`skills/`** — 23 SKILL.md files, each an instructional playbook an agent
  loads when its trigger phrases fire (e.g. `tdd` on "implement", `pr` on
  "create a PR").
- **`hooks/`** — 8 lifecycle hooks that fire on tool use and git operations:
  `pre-bash-safety`, `pre-commit-secrets`, `pre-commit-gate`, `dependency-audit`
  (PreToolUse, `exit 2` to block), the git `pre-commit` backstop, `post-write-lint`,
  `session-start`, `post-commit-release-note`.
- **`agents/`** — 5 subagent definitions: `code-reviewer`, `test-writer`,
  `security-auditor`, `devops-sre`, `db-reviewer`.
- **`commands/`** — slash commands (`release`, `upgrade-skills`).

### Hermes port (`hermes/`)
- **`skills/`** — 24 Hermes-format SKILL.md files (the same 23 as Claude plus
  `dependency-audit`, which is skill-based on Hermes because Hermes has no git
  commit hook event).
- **`install.sh` / `install.ps1`** — installers that fetch the skills via
  Hermes's native skill hub and create the `/tapway` bundle.
- **`config.hooks.yaml`** — reference shell-hook config (Hermes `pre_tool_call`
  JSON wire protocol) that mirrors the Claude PreToolUse gates.
- **`agent-hooks/`** — Hermes-compatible hook scripts (JSON `{"decision":"block"}`
  protocol for `pre_tool_call`).

### Support layers (shared)
- **`.github/workflows/`** — 3 CI workflows: `release.yml` (semver auto-release),
  `quality.yml` (lint/format/typecheck/coverage + dependency audit),
  `playwright.yml` (frontend + backend E2E).
- **`tests/`** — 6 TDD validation suites (216 checks) proving the skills, hooks,
  and wiring exist and behave.
- **`docs/`** — team guide, legacy-refactor guide, design specs.

## Data Flow

Primary workflow — a developer asks the agent to build a feature:

1. **User prompt** → agent loads `interview` / `brainstorming` if the request is
   underspecified → Confirmed Intent statement.
2. **`writing-plans`** → implementation plan saved to `docs/plans/[feature].md`.
3. **`tdd`** → per task: Test Writer subagent (RED) → RED gate → Implementer
   subagent (GREEN + REFACTOR). Hooks block commits that fail quality gates.
4. **`e2e-playwright`** → frontend Playwright + backend pytest E2E with
   conditional gate (frontend/backend file detection).
5. **`/simplify` → `/review` → `/pr`** → code simplified, self-reviewed
   (Critical/Warning/Suggestion), then PR opened with tests + docs updated.
6. **CI** → `quality.yml` + `playwright.yml` run on the PR; merge triggers
   `release.yml` → `vMAJOR.MINOR.PATCH-stg` tag.

## Key Design Decisions

- **Structural enforcement over documentation** — each skill is wired into the
  pipeline and hooks/CI gates so the discipline happens automatically, not when
  the agent remembers. "A config file the CI always runs catches everything."
- **Conditional gates** — `e2e-playwright` runs frontend E2E only when frontend
  files changed and backend E2E only when backend files changed; `quality-gates`
  hooks are cheap config that run on every PR.
- **Dual-harness, one source** — the Hermes port is generated alongside the
  Claude plugin from the same methodology; Claude-side enforcement uses exit-2
  PreToolUse hooks, Hermes-side uses the shell-hook JSON block protocol (the
  mechanisms differ because the harnesses differ).
- **Exit-code semantics** — Claude Code blocks only on `exit 2` (exit 1 is a
  non-blocking error); git hooks block on any non-zero. Each hook's exit code
  matches its host's contract.
- **Blameless reliability** — `incident-runbook` forbids person-blame in
  postmortems and forbids DB downgrade rollbacks (use expand-contract instead).
- **Code you copy must run** — all runnable examples are TDD-verified; a
  subagent (`db-reviewer`) exists specifically for the highest-signal review
  gap (N+1 queries / indexes / migrations) that static review misses.

## External Dependencies

| Dependency | Type | Purpose | Notes |
|---|---|---|---|
| Claude Code (≥ 2.x) | Harness | Runs the plugin | Plugin marketplace install |
| Hermes Agent | Harness | Runs the port | Native skill hub install |
| GitHub Actions | CI | quality / E2E / release workflows | In the adopting repo |
| osv-scanner, npm audit, pip-audit | Tool | Supply-chain scan | Installed by setup-project / CI |
| @playwright/test, @axe-core/playwright | Tool | Frontend E2E + a11y | In the adopting frontend |
| pytest + pytest-cov, ruff, mypy | Tool | Backend tests, quality gates | In the adopting backend |
| schemathesis, alembic | Tool | API contract + migration testing | Adopting backend |