# Tapway Superpowers

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude Code plugin that adds 12 AI skills, 5 guardrail hooks, and specialized subagents for full-stack development with Next.js 14 + Python FastAPI. Built for the Tapway team's "vibe coding" workflow — the AI enforces best practices so you don't have to think about them.

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

## What You Get

### 12 Skills

AI behaviors that activate automatically when you use relevant keywords in conversation. Also invokable explicitly with `/skill-name`.

| Skill | What it does | Triggers when you say... |
|---|---|---|
| `brainstorming` | Explore approaches, surface trade-offs, name confusion before coding. Output saved to `docs/brainstorming/`. | "Let's think about...", "What are the options..." |
| `writing-plans` | Create implementation plans with file maps, task breakdowns, and work package checklists by discipline. Saved to `docs/plans/` + `docs/checklists/`. | "Write a plan...", "Break this down..." |
| `tdd` | TDD-first subagent execution: Test Writer agent (RED) → coordinator gate → Implementer agent (GREEN + REFACTOR). Default skill for all implementation work. | "Start implementing...", "implement", any new feature or bug fix |
| `verification` | Confirm a task is done — runs tests, lint, type-checks, spec coverage | "Is this done?", "Verify...", "Final check..." |
| `refactor` | Improve code without changing behavior — surgical, tested, minimal | "Refactor...", "Simplify...", "Remove duplication..." |
| `code-review` | Three-tier review: Critical, Warnings, Suggestions | "Review my changes...", "Check this before I push..." |
| `systematic-debugging` | Reproduce → Isolate → Hypothesize → Test → Fix → Post-mortem | "Why is X failing?", "Debug...", "Works locally but not in prod..." |
| `pr` | Full PR workflow: rebase, conflict resolution, test gate, push, and open PR with structured body. Updates work package checklist. | "Create a PR...", "I'm done with this task...", "Push and PR..." |
| `git-worktrees` | Manage parallel git worktrees for concurrent feature work | "Worktree...", "Parallel branches..." |
| `repo-docs` | Generate standardized architecture, schema, and deployment docs | "Document this repo...", "Write architecture docs..." |
| `security-audit` | OWASP Top 10 audit for auth, payments, user data, file uploads | "Security review...", "Audit auth...", "Is this safe?" |
| `pre-review-cleanup` | Scan for template placeholders, boilerplate, and stale scaffold code | "Clean up template files...", "Remove boilerplate..." |

All skills are strengthened with Andrej Karpathy's coding principles: Think Before Coding, Simplicity First, Surgical Changes, and Goal-Driven Execution.

### 5 Guardrail Hooks

Automatic checks that fire on Claude Code lifecycle events. No configuration needed.

| Hook | Event | What it does |
|---|---|---|
| `pre-bash-safety` | PreToolUse (Bash) | Blocks force-push, hard-reset on main, commits to main. Blocks prod commands unless `ALLOW_PROD=1` is set. |
| `post-write-lint` | PostToolUse (Write\|Edit) | Runs the project linter on changed files |
| `pre-commit-secrets` | PreToolUse (git commit) | Scans staged files for secrets, keys, and credentials before allowing a commit |
| `session-start` | SessionStart | Displays project info, git status, and environment summary when Claude Code starts |
| `post-commit-release-note` | PostToolUse (git commit) | Parses conventional commits and appends formatted entries to `CHANGELOG.unreleased.md` |

### 4 Specialized Agents

Subagent definitions included in the repo for manual use:

| Agent | Purpose |
|---|---|
| `code-reviewer` | Systematic code review with security, performance, and type-safety checks |
| `test-writer` | Write tests following project conventions (pytest/Jest) |
| `security-auditor` | OWASP Top 10 audit for auth, payments, and user data paths |
| `devops-sre` | Docker, CI/CD, and infrastructure configuration review |

## Team Collaboration

### Docs Structure

All plans, decisions, and checklists are stored **in the project repo** alongside the code — not in this plugin. After installing the plugin, your project gets:

```
docs/
  brainstorming/   ← why we chose this approach  (saved by /brainstorming)
  plans/           ← what we're building and how  (saved by /plan)
  checklists/      ← who is doing what, current status  (saved by /plan)
```

These files are committed and pushed immediately so the whole team sees them. They are the single source of truth for any in-flight feature.

### Work Package Flow

When a feature spans multiple disciplines (Frontend + Backend + DevOps), `/plan` generates a work package checklist. Each team member:

1. Opens `docs/checklists/[feature]-checklist.md` and self-assigns a package
2. Creates an isolated worktree: `git worktree add -b feat/[feature]-[package] ../[project]-[package]`
3. Implements using `/tdd` inside that worktree
4. Runs `/pr` when done — this is the **only** way to push; direct `git push` is not the workflow

### `/pr` is Mandatory

Every change that leaves a worktree must go through `/pr`. It enforces:
- Rebase against `main` before push (no stale branches in review)
- Full test suite green before push (no broken PRs)
- Structured PR body with summary, test plan, and files changed
- Work package checklist updated to 🟢 with PR number linked

Skipping `/pr` and pushing manually bypasses all of these gates.

---

## Daily Workflow

Once installed, the plugin guides you through a pipeline. Steps 1–3 are team-level (done once per feature). Steps 4–8 are per work package (each team member runs these in their own worktree).

```
Brainstorm → Plan → Commit Docs → [Assign] → TDD → Cleanup → Self-Review → PR → Team Review → Deploy → Release
```

**Team-level (once per feature):**
1. **Brainstorm** `/brainstorming` — explore approaches; output committed to `docs/brainstorming/`
2. **Plan** `/plan` — file map + task breakdown + work package checklist committed to `docs/plans/` + `docs/checklists/`
3. **Assign** — each team member opens `docs/checklists/[feature]-checklist.md`, edits it to claim a package (`**Assignee:** @name, 🟡`), commits that change, then creates a worktree:
   ```bash
   git worktree add -b feat/[feature]-[package] ../[project]-[package] origin/main
   cd ../[project]-[package] && claude
   ```
   Then tells Claude: _"I'm picking up the [Backend/Frontend/DevOps/QA] work package for [feature]. Let's start implementing."_

**Per work package (each assignee runs these in their worktree):**

4. **TDD** `/tdd` — implement task by task; Test Writer agent (RED) → Implementer agent (GREEN + REFACTOR) per task
5. **Cleanup** `/cleanup` — scan for and remove placeholders, boilerplate, stale scaffold code
6. **Self-Review** `/review` — three-tier self-review (Critical / Warnings / Suggestions) before anyone else sees the code
7. **PR** `/pr` — rebase against `main`, run full test suite, push branch, open PR, mark checklist 🟢 — **mandatory, not optional**
8. **Team Review** — teammates and `@claude` review on GitHub; AI-assisted fixes via `@claude fix ...` comments

**After all packages merge:**

9. **Deploy** `/deploy` — pre-deployment checklist
10. **Release** `/release patch|minor|major` — semver bump, release notes, git tag

### Guardrails That Run Silently

- You can't accidentally commit to `main` — the hook blocks it and tells you to create a branch
- You can't accidentally run prod commands — the hook requires `ALLOW_PROD=1`
- Every conventional commit auto-generates a release note entry
- Secrets in staged files are caught before commit
- Linting runs automatically after file edits

### Slash Commands

Available when the plugin is installed:

| Command | Purpose |
|---|---|
| `/brainstorming` | Explore approaches before coding (saves to `docs/brainstorming/`) |
| `/plan` | Write a detailed implementation plan + work package checklist (saves to `docs/plans/` + `docs/checklists/`) |
| `/tdd` | Start test-driven development via subagents |
| `/pr` | Rebase, run tests, push branch, open PR, update checklist |
| `/cleanup` | Remove template artifacts |
| `/review` | Self-review changes before PR |
| `/deploy` | Pre-deployment checklist |
| `/test-all` | Run full test suite |
| `/release <patch\|minor\|major>` | Bump version, generate release notes, tag |
| `/upgrade-skills` | Update all plugins to latest |

## Upgrading

When new versions of this plugin are released:

```
/upgrade-skills
```

Or manually:

```bash
claude plugin marketplace update
claude plugin update tapway-superpowers@tapway-superpowers
```

Restart Claude Code after updating to apply changes.

## For Template Users

If you cloned the [tapway-claude-template](https://github.com/tapway/tapway-claude-template), this plugin is already declared in `.claude/settings.json` and auto-installs on first open. You don't need to run any install commands.

## Uninstalling

```bash
claude plugin uninstall tapway-superpowers@tapway-superpowers
```

Your code and configuration files are unaffected.

## License

MIT © Tapway