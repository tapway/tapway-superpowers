# Changelog

All notable changes to tapway-superpowers are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

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
