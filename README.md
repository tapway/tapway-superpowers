# Tapway Superpowers

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude Code plugin with 13 AI skills, 5 guardrail hooks, and specialized subagents for full-stack development (Next.js 14 + Python FastAPI). The plugin enforces best practices structurally — TDD via agent boundaries, mandatory PR gates, docs on every push — so good habits happen automatically.

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

## Table of Contents

- [Modes](#modes)
  - [Individual — solo feature or bug fix](#individual--solo-feature-or-bug-fix)
  - [Team Collaboration — parallel work packages](#team-collaboration--parallel-work-packages)
  - [Legacy Refactor — existing repo without tests](#legacy-refactor--existing-repo-without-tests)
- [GitHub Actions — AI-Powered PR Review](#github-actions--ai-powered-pr-review)
- [What You Get](#what-you-get)
  - [13 Skills](#13-skills)
  - [5 Guardrail Hooks](#5-guardrail-hooks)
  - [4 Specialized Agents](#4-specialized-agents)
- [Slash Commands Reference](#slash-commands-reference)
- [Built-in Claude Code Skills](#built-in-claude-code-skills)
- [Guardrails That Run Silently](#guardrails-that-run-silently)
- [Upgrading](#upgrading)
- [For Template Users](#for-template-users)
- [Uninstalling](#uninstalling)

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
/brainstorming → /plan → [implement] → /simplify → /review → /pr
```

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

**Auto-review on every PR + `@claude` for fixes.** Every PR gets an automatic three-tier code review when opened. After review, anyone can mention `@claude` in a comment to push fix commits directly to the branch. See [GitHub Actions — AI-Powered PR Review](#github-actions--ai-powered-pr-review) for setup instructions and the required `ANTHROPIC_API_KEY` secret.

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

## GitHub Actions — AI-Powered PR Review

The plugin ships a GitHub Actions workflow (`.github/workflows/claude.yml`) that gives every PR an automatic AI code review and lets any team member trigger fix commits by mentioning `@claude` in a comment.

> **This must be added to each project repo separately.** Run `/setup-project` in any repo to create and commit the file automatically.

### Prerequisites

**Add `ANTHROPIC_API_KEY` to GitHub repo secrets — this is required for any of the below to work.**

```
GitHub repo → Settings → Secrets and variables → Actions → New repository secret
  Name:  ANTHROPIC_API_KEY
  Value: your key from https://console.anthropic.com
```

Without this secret, the workflow will be present but every run will fail with an authentication error.

### How It Works — Two Jobs

The workflow contains two separate jobs with different triggers and permissions:

#### 1. `auto-review` — fires on every PR, no mention needed

| Property | Value |
|---|---|
| **Trigger** | PR opened, updated (`synchronize`), or reopened |
| **Permissions** | Read-only (`contents: read`, `pull-requests: write`) |
| **What it does** | Posts a three-tier code review as inline PR comments |

Claude reads the full diff and posts findings categorised as:

- **Critical** — must fix before merge (bugs, security issues, data loss risks, broken contracts)
- **Warning** — should fix or justify (missing tests, type gaps, N+1 queries, unhandled errors)
- **Suggestion** — optional improvements (simplification, naming, duplication)

If Critical findings exist, Claude requests changes. If only Warnings/Suggestions, it approves with comments. The review summary is prefixed with `## Auto-review` so it's clearly labelled as automated.

#### 2. `on-mention` — fires when `@claude` is mentioned

| Property | Value |
|---|---|
| **Trigger** | `@claude` in any PR comment, review comment, or review body |
| **Permissions** | Read-write (`contents: write`) — can push fix commits |
| **What it does** | Executes whatever instruction follows `@claude` |

Common uses:
```
@claude fix the Critical findings from the auto-review
@claude fix the failing test in test_auth_service.py
@claude resolve the merge conflict in this file
@claude explain why this approach was chosen
```

### Setup

**Option A — Automated (recommended):**
```
/setup-project
```
Creates `.github/workflows/claude.yml`, commits it, and prints the remaining manual steps including the secret reminder.

**Option B — Manual:**
```bash
mkdir -p .github/workflows
# Copy .github/workflows/claude.yml from this repo into your project
git add .github/workflows/claude.yml
git commit -m "chore: add @claude GitHub Actions workflow"
git push
```
Then add `ANTHROPIC_API_KEY` to GitHub repo secrets.

### Verifying It Works

1. Open any PR in the repo
2. Within ~30 seconds, an `## Auto-review` comment should appear from the `auto-review` job
3. On the same PR, comment `@claude explain what this PR does` — the `on-mention` job should reply within ~30 seconds

If either job doesn't fire or errors out, check:
- `ANTHROPIC_API_KEY` is set in repo secrets (Settings → Secrets and variables → Actions)
- Both jobs have `id-token: write` in their `permissions` block — the action uses OIDC for authentication and will fail with "Unable to get ACTIONS_ID_TOKEN_REQUEST_URL" without it
- Both jobs have `actions/checkout@v4` as the **first step** — the action runs `git fetch` internally and will fail with "fatal: not a git repository" if the repo isn't checked out first
- The workflow file exists at `.github/workflows/claude.yml`
- GitHub Actions is enabled for the repo (Settings → Actions → General)

### Cost

Each `auto-review` run costs roughly $0.50–2.00 depending on the size of the diff (input tokens). `on-mention` runs vary by task. For a small team running 20–30 PRs/month, expect under $30/month total.

To limit auto-review to specific branches (e.g. only PRs targeting `main`):
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main]   # add this line
```

---

## What You Get

### 13 Skills

AI behaviors that activate automatically when you use relevant keywords. Also invokable explicitly with `/skill-name`.

| Skill | What it does | Triggers |
|---|---|---|
| `brainstorming` | Explore approaches, surface trade-offs, save decisions to `docs/brainstorming/` | "Let's think about...", "What are the options..." |
| `writing-plans` | Implementation plans with file maps, task breakdowns, and work package checklists. Saves to `docs/plans/` + `docs/checklists/` | "Write a plan...", "Break this down..." |
| `autoship` | Fully automated plan-to-PR: validates plan, runs TDD subagents per task, then simplify → review → docs → PR. **Deploy mode** (on staging server): also deploys, health-checks, and runs integration/E2E tests before PR | "implement it with autopilot", "autoship" / "implement and deploy", "ship and deploy" |
| `tdd` | Test Writer agent (RED) → coordinator gate → Implementer agent (GREEN + REFACTOR). Structurally enforces TDD. | "Start implementing...", "implement", any new feature or bug fix |
| `verification` | Confirm a task is done — tests, lint, type-checks, spec coverage | "Is this done?", "Verify...", "Final check..." |
| `refactor` | **Protocol A** (active codebase): surgical incremental refactoring. **Protocol B** (legacy): characterization-test-first sequence | "Refactor...", "Clean up...", "Legacy refactor..." |
| `code-review` | Three-tier review: Critical, Warnings, Suggestions | "Review my changes...", "Check this before I push..." |
| `systematic-debugging` | Repro → Isolate → Hypothesize → Test → Fix → Post-mortem saved to `docs/post-mortems/` | "Why is X failing?", "Debug...", "Works locally but not in prod..." |
| `pr` | Rebase, conflict resolution, test gate, **update docs**, push, open PR, update checklist | "Create a PR...", "I'm done...", "Push and PR..." |
| `git-worktrees` | Manage parallel git worktrees for concurrent feature work | "Worktree...", "Parallel branches..." |
| `repo-docs` | Generate `ARCHITECTURE.md`, `WORKFLOWS.md`, `DB_SCHEMA.md`, `DEPLOYMENT.md` | "Document this repo...", "Write architecture docs..." |
| `security-audit` | Full-codebase OWASP Top 10 audit — for pre-launch or major refactors | "Security audit...", "Audit the whole codebase..." |
| `pre-review-cleanup` | Scan for template placeholders, boilerplate, and stale scaffold code | "Clean up template files...", "Remove boilerplate..." |
| `setup-project` | One-time setup: creates `.github/workflows/claude.yml` and `CLAUDE.md`, commits, prints checklist for remaining manual steps | "set up the @claude workflow", "setup project", "add @claude to this repo" |

> All skills apply Andrej Karpathy's coding principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.

---

### 5 Guardrail Hooks

Automatic checks that fire on Claude Code lifecycle events.

| Hook | Event | What it does |
|---|---|---|
| `pre-bash-safety` | PreToolUse (Bash) | Blocks force-push, hard-reset on `main`, direct commits to `main`. Blocks prod commands unless `ALLOW_PROD=1` is set. |
| `post-write-lint` | PostToolUse (Write\|Edit) | Runs the project linter on changed files |
| `pre-commit-secrets` | PreToolUse (git commit) | Scans staged files for secrets, keys, and credentials before allowing a commit |
| `session-start` | SessionStart | Displays project info, git status, and environment summary when Claude Code opens |
| `post-commit-release-note` | PostToolUse (git commit) | Parses conventional commits and appends formatted entries to `CHANGELOG.unreleased.md` |

---

### 4 Specialized Agents

Subagent definitions for use with the TDD and autoship skills:

| Agent | Purpose |
|---|---|
| `code-reviewer` | Systematic review with security, performance, and type-safety checks |
| `test-writer` | Write tests following project conventions (pytest / Jest) |
| `security-auditor` | OWASP Top 10 audit for auth, payments, and user data paths |
| `devops-sre` | Docker, CI/CD, and infrastructure configuration review |

---

## Slash Commands Reference

| Command | Mode | Purpose |
|---|---|---|
| `/setup-project` | All | One-time project setup: creates `.github/workflows/claude.yml` and `CLAUDE.md`, commits, and prints a manual-steps checklist (GitHub secret). Run this in any new repo adopting the plugin. |
| `/brainstorming` | All | Explore approaches before coding |
| `/plan` | All | Write implementation plan + work package checklist |
| `/autoship` | Individual / Team | Run full plan-to-PR loop automatically. Add "and deploy" to also deploy + run integration tests before PR (staging server only) |
| `/tdd` | Individual / Team | TDD subagents for task-by-task implementation |
| `/refactor` | Individual / Legacy | Incremental (Protocol A) or legacy characterization-test workflow (Protocol B) |
| `/pr` | All | Rebase, test, update docs, push, open PR, update checklist — **mandatory exit** |
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
- **Linting after every file edit** — runs the project linter automatically
- **Release notes auto-generated** — every conventional commit appends to `CHANGELOG.unreleased.md`
- **Docs updated on every PR** — `/pr` runs `/repo-docs` or updates affected doc sections before pushing
- **Missing workflow detected on session start** — if `.github/workflows/claude.yml` is absent, the session-start hook warns and tells you to run `/setup-project`

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
