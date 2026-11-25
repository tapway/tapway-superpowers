---
issue: 62
title: tool-guard — keep secrets out of transcripts and make servers ask before changes
date: 2026-11-20
---

# tool-guard, server template and skill-eval harness — Implementation Plan

**Goal:** Every Tapway repo, laptop and server gets the same runtime guardrails
from this plugin: the agent cannot read or print secrets, cannot push to
protected branches, and on servers asks a human before any command that changes
something. Every repo can prove its own skills behave with a shared eval harness.

**Problem (measured 2026-11-20):**
- `pre-bash-safety` read the command from `$1`; Claude Code sends it as JSON on
  stdin. Piping `git push --force origin main` the way Claude Code does exits 0,
  so none of its rules (force-push, commit to `main`, `ALLOW_PROD`) ever fired.
  Its test only checked that the file contains `exit 2`.
- Nothing stops an agent from *reading* secrets at runtime: `cat .env`,
  `printenv`, `docker inspect`, `redis-cli -a <pw>` all pass.
  `pre-commit-secrets` only scans staged files. The team guide exports
  `GBRAIN_TOKEN`, `GITHUB_TOKEN` and `CODEMAX_ADMIN_TOKEN` in the shell profile,
  so one `env` prints all three.
- 5 of 74 tapway-skills skills tell the agent to read container environments
  (`docker inspect --format '{{json .Config.Env}}'`, `docker exec ... printenv`).
- Agents now run on servers (`/autoship` deploy mode, Inspector `/deploy-inspector`).
  Samurai Inspector built a repo-local guard for this; 202 of its guard tests are
  the parity baseline for the shared version.

**Out of scope:** a Hermes `pre_tool_call` port of tool-guard (follow-up; the
payload adapter already normalises Hermes input); fixing the five tapway-skills
skills (separate PR in that repo); moving Inspector onto the shared engine
(Inspector follow-up once this ships).

## Branch: feat/tool-guard

### Task 1: tool-guard engine with per-repo config

**Files:** `hooks/tool-guard/tool_guard.py`, `hooks/tool-guard/tool-guard.sh`,
`hooks/tool-guard/README.md`, `hooks/hooks.json`; test `tests/test_tool_guard.py`.

- AC-1.1 Blocks env/credential files, env dumps, docker env exposure and
  secrets in argv, through `bash -c`, `eval`, `$()`, backticks, `sudo`, `env`,
  `timeout` and chains; heredoc bodies are data.
- AC-1.2 Blocks commits/pushes to protected branches (default `main`, `master`),
  force and bulk pushes, and PRs outside `pr_flow`.
- AC-1.3 Asks before changing commands only when `ask_before_changes` is on or
  `TAPWAY_GUARD_ASK=1`; off by default so `/autoship` is not interrupted.
- AC-1.4 `.claude/tool-guard.json` keys validated; unknown key, wrong type,
  bad regex or bad JSON blocks every call (fail closed). `python3` missing →
  blocked.
- AC-1.5 Wired for Bash and Read/Edit/Write/MultiEdit/Grep/Glob/NotebookEdit/NotebookRead.
- AC-1.6 Parity: Samurai Inspector's 202 guard tests pass against this engine
  with Inspector's config.

### Task 2: make pre-bash-safety fire

**Files:** `hooks/pre-bash-safety/pre-bash-safety.sh`, `codex/hooks/pre-bash-safety.sh`;
test `tests/test_pre_bash_safety.py`.

- AC-2.1 Reads the command from the stdin payload via `hooks/lib/hook_payload.sh`.
- AC-2.2 Now that the rules are live, no false positives on everyday commands:
  `git push origin feat/x-fix`, `--follow-tags`, `products`, `reproduce`,
  `npm install --production`.
- AC-2.3 Claude and Codex copies carry identical rules.

### Task 3: server template and guide

**Files:** `server/managed-settings.json`, `docs/SERVER_GUARDRAILS.md`.

- AC-3.1 Force-installs tapway-superpowers and tapway-skills with auto-update,
  allows only Tapway and official marketplaces, sets `TAPWAY_GUARD_ASK=1`,
  denies env/credential reads, disables bypass mode, keeps repo hooks on.
- AC-3.2 The guide covers setup, verification, and how a merge reaches a server
  (version-sync PR, auto-update, restart).

### Task 4: skill-eval harness

**Files:** `evals/lib/canary-env.sh`, `evals/lib/canary-repo.sh`,
`evals/templates/case.yaml`, `evals/README.md`, `scripts/skill-evals.sh`;
test `tests/test_skill_evals_harness.py`.

- AC-4.1 Canary helpers never print a value; canaries differ per run.
- AC-4.2 Template graders catch canaries, opened/edited env files and unapproved
  changes, and ignore `.env.example` / `sample.env`.
- AC-4.3 The runner assembles any repo's skills, cases and include.txt files,
  rejects paths outside the repo, runs hooks-off, unpublished and cost-capped.

### Task 5: docs and CI

**Files:** `README.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`,
`tests/check_docs_consistency.py`, `.github/workflows/skills-tests.yml`, `.gitignore`.

- AC-5.1 Hook count and tables updated; consistency check passes.
- AC-5.2 The three new suites run in `skills-tests.yml` on every PR.
