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
| `brainstorming` | Explore approaches, surface trade-offs, name confusion before coding | "Let's think about...", "What are the options..." |
| `writing-plans` | Create detailed implementation plans with file maps and task breakdowns | "Write a plan...", "Break this down..." |
| `tdd` | Enforce test-driven development: red → green → refactor | "Write a test first...", any new feature or bug fix |
| `verification` | Confirm a task is done — runs tests, lint, type-checks, spec coverage | "Is this done?", "Verify...", "Final check..." |
| `refactor` | Improve code without changing behavior — surgical, tested, minimal | "Refactor...", "Simplify...", "Remove duplication..." |
| `code-review` | Three-tier review: Critical, Warnings, Suggestions | "Review my changes...", "Check this before I push..." |
| `systematic-debugging` | Reproduce → Isolate → Hypothesize → Test → Fix → Post-mortem | "Why is X failing?", "Debug...", "Works locally but not in prod..." |
| `subagent-driven-development` | Execute multi-task plans with isolated subagents per task | "Delegate to subagents...", "Run this plan with subagents..." |
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

## Daily Workflow

Once installed, the plugin guides you through an 8-step pipeline:

```
Brainstorm → Plan → TDD → Cleanup → Review → Deploy → Release → Verify
```

1. **Brainstorm** — describe your feature; Claude explores approaches
2. **Write a Plan** — Claude produces a file map + task breakdown (saved to `docs/plans/`)
3. **TDD** — Claude implements task by task, test-first, with minimal code
4. **Pre-Review Cleanup** — scans for placeholders and boilerplate
5. **Code Review** — three-tier self-review before PR
6. **Deploy** — `/deploy` generates a deployment checklist
7. **Release** — `/release patch|minor|major` bumps semver, collates release notes, creates a git tag
8. **Verify** — `/test-all` runs the full suite; systematic debugging if anything fails

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
| `/brainstorming` | Explore approaches before coding |
| `/plan` | Write a detailed implementation plan |
| `/tdd` | Start test-driven development |
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