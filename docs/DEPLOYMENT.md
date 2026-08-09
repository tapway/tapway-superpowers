# Deployment — Tapway Superpowers

This repo is a **developer-tooling plugin**, not a deployed application. Its
"deployment" is the act of making the plugin/skills available to a user's coding
agent — either by installing directly from this GitHub repo, or by publishing a
**release** that agents can pull.

## Environment Overview

| Environment | Target | Notes |
|---|---|---|
| Local dev | This repo on a dev machine | Authoring skills/hooks/agents |
| Installed | Adopting project repos | Claude Code plugin or Hermes port |
| Release | GitHub Releases (`vMAJOR.MINOR.PATCH`) | Public distribution point |

## Prerequisites

| Tool | Minimum | Where it's needed |
|---|---|---|
| Claude Code | 2.x | Running the Claude plugin |
| Hermes Agent | current stable | Running the Hermes port |
| `gh` (GitHub CLI) | any | Creating releases, auth for install |
| git | any | Cloning the repo |

For adopting projects (not this repo), the plugin requires the related tools its
skills invoke — `@playwright/test`, `pytest`, `ruff`, `mypy`, `osv-scanner`,
`npm audit`, `pip-audit`, `schemathesis` — installed in that project as needed
(`setup-project` / `quality-gates` / `dependency-audit` skills handle this).

## Install — Claude Code (plugin)

```bash
# 1. Register this repo as a marketplace
claude plugin marketplace add https://github.com/tapway/tapway-superpowers

# 2. Install the plugin
claude plugin install tapway-superpowers@tapway-superpowers
```

Skills, agents, and hooks activate immediately (hooks auto-discover from
`hooks/hooks.json`). Optional companion plugins:

```bash
claude plugin install andrej-karpathy-skills@karpathy-skills
claude plugin install claude-code-setup@claude-plugins-official
```

Verify with `/hooks` (Claude Code shows every configured hook) and by checking
the skills load when you use a trigger phrase.

## Install — Hermes Agent (port)

From inside a clone of this repo:

```bash
cd hermes
bash install.sh            # macOS / Linux — installs all 24 skills + the /tapway bundle
# or Windows (PowerShell):
.\install.ps1
```

Preview without installing: `HERMES_DRY_RUN=1 bash install.sh`

Verify:

```bash
hermes skills list | grep tapway   # 24 tapway/* skills present
hermes bundles list                # "tapway" bundle present
```

**Optional — Hermes shell hooks** (mirror the Claude PreToolUse gates):

```bash
# Copy the reference config + scripts into your Hermes home:
mkdir -p ~/.hermes/agent-hooks
cp hermes/agent-hooks/tapway-*.sh ~/.hermes/agent-hooks/
# Then copy the `hooks:` block from hermes/config.hooks.yaml into ~/.hermes/config.yaml
```

## Adopting the Plugin in a Project Repo

Each adopting project runs `setup-project` (a slash command / skill) to:

1. Create `.github/workflows/release.yml` (semver auto-release)
2. Create `.github/workflows/quality.yml` (lint/format/typecheck/coverage + dependency audit)
3. Install the git `pre-commit` backstop (`.git/hooks/pre-commit`)
4. Create `CLAUDE.md` with `TARGET_BRANCH: staging`

Then enable the plugins' CI workflows: `playwright.yml` (E2E), `quality.yml`
(quality gates), `release.yml` (release) — all in `.github/workflows/`.

## Publish (Release)

Releases are created automatically on merge to `staging` or `prod` via
`.github/workflows/release.yml` (semver `vMAJOR.MINOR.PATCH-stg` / `-prod`), or
manually:

```bash
# From the repo root, after merging to main:
gh release create v1.7.0 \
  --target main \
  --title "v1.7.0 — <summary>" \
  --notes-file <(awk '/^## \[/{if(p)exit; p=1; next} p && /^(## \[|---)/{exit} p{print}' CHANGELOG.md)
```

The plugin marketplace and Hermes installers both fetch from the repo's latest
release/tag, so publishing a tag is what makes a version available to users.

## Health Check & Verification

- **Claude:** run `/hooks` — expect 8 hooks listed. Trigger a skill word (e.g.
  "write a plan") and confirm the skill loads.
- **Hermes:** `hermes skills list | grep tapway` → 24; `hermes bundles list` →
  tapway present.
- **CI:** open a sample PR against a project that adopted the plugin — `quality.yml`
  and `playwright.yml` must run; a commit with failing lint must be blocked by the
  git `pre-commit` backstop.
- **TDD suites:** `python3 tests/test_*.py` → all 216 checks pass.

## Rollback

- **Claude:** `claude plugin uninstall tapway-superpowers@tapway-superpowers`
- **Hermes:** remove the skills via `hermes skills remove tapway/<skill>` (or
  leave the bundle; it's additive). Removing `config.hooks.yaml`'s `hooks:` block
  and `~/.hermes/agent-hooks/` scripts disables the Hermes gates.
- **Release:** a bad release is fixed by a patch release, not by deleting a tag
  (tags are immutable history).

## Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Hooks "never fire" in Claude | Stale manifest; matcher syntax; exit code | Verify `hooks/hooks.json` uses `Bash(git commit:*)` and `exit 2` for blocking hooks |
| Push rejected "workflow scope" | PAT lacks `workflow` scope for `.github/workflows/*` | Use a workflow-scoped PAT to push workflow changes |
| Hermes gate silently allows | Missing JSON parser (`jq`/`python3`) | Install `jq` (hooks prefer it) |
| Plugin skills not found | `plugin.json` `skills:` list out of date | Re-check `./skills/<name>` is present in the manifest |
| CI quality gate never blocks | `|| true` on gate steps | Remove — gates must fail the build |
| N+1 in production | ORM lazy-load in loops | Run `db-reviewer` subagent / add `lazy="raise"` + eager loads |