# Tapway Superpowers — Hermes Port

A port of the [Tapway Superpowers](https://github.com/tapway/tapway-superpowers) Claude Code plugin for **Hermes Agent**. Same skills, same strict engineering pipeline — running on Hermes instead of Claude Code.

> The original repo is a Claude Code plugin (`.claude-plugin/plugin.json`, slash commands, hooks). Hermes can't load that plugin format, so the *skill content* has been converted to Hermes `SKILL.md` files. The Claude-only hooks (commit guards, secret scanning, post-edit lint) don't auto-run in Hermes — the equivalent discipline is enforced by following the pipeline below.

## Install

All **25** Tapway skills install into Hermes via `install.sh` / `install.ps1`.
The installer also creates a **`/tapway` skill bundle** so the entire strict
pipeline loads with a single slash command.

**Preferred (from a git checkout — pin-able, offline-safe):**
```bash
git fetch --tags && git checkout vX.Y.Z   # optional pin
cd hermes
bash install.sh                           # category default: tapway
bash install.sh tapway-superpowers        # keep an existing category name
```

When `hermes/skills/` is present beside the installer (normal checkout),
**auto mode copies locally** into `$HERMES_HOME/skills/<category>/`. That
avoids Hermes skill-hub `skills-guard` false positives on first-party docs
and pins exactly to the commit/tag you checked out.

**Modes:**
```bash
HERMES_INSTALL_MODE=auto  bash install.sh   # default: local if available, else hub
HERMES_INSTALL_MODE=local bash install.sh   # force copy from this checkout
HERMES_INSTALL_MODE=hub   bash install.sh   # force hermes skills install (GitHub)
HERMES_DRY_RUN=1          bash install.sh   # preview only
```

**Windows (PowerShell):**
```powershell
cd hermes
.\install.ps1
.\install.ps1 tapway-superpowers
$env:HERMES_INSTALL_MODE = "local"; .\install.ps1
$env:HERMES_DRY_RUN = "1"; .\install.ps1
```

**Hub-only (no checkout):** the installer can still call
`hermes skills install tapway/tapway-superpowers/hermes/skills/<name>`.
Authenticate GitHub (`gh auth login` or `GITHUB_TOKEN`) to avoid rate limits.
If the hub scanner blocks a skill, re-run from a checkout with
`HERMES_INSTALL_MODE=local` — see [INSTALL_ISSUES.md](./INSTALL_ISSUES.md).

Then verify:
```bash
ls "$HERMES_HOME/skills/tapway" | wc -l    # expect 25 (or your category path)
hermes skills list | grep -E 'tapway'
hermes bundles list                        # "tapway" bundle present
```

> **Individual skill:** Hermes auto-derives a `/skill-name` command from every
> installed skill. You can also install one skill directly:
> ```bash
> hermes skills install tapway/tapway-superpowers/hermes/skills/tdd --category tapway
> ```
> If hub install is blocked, copy `hermes/skills/tdd` into
> `$HERMES_HOME/skills/tapway/tdd` instead.

### Known caveats

- **Name collisions:** Hermes also ships `writing-plans` and
  `systematic-debugging` under other categories. Both copies can exist on
  disk; list UIs may show one bare name. Prefer `/tapway` or the category
  path when disambiguating.
- **Category drift:** older installs used category `tapway-superpowers`; the
  installer default is `tapway`. Pass your existing category name to avoid a
  second tree.
- **Claude plugin ≠ Hermes skills:** updating the Claude Code plugin does
  **not** refresh Hermes skills — run this installer separately.

Field report from the v1.8.2 update: [INSTALL_ISSUES.md](./INSTALL_ISSUES.md).

### What you get: 25 skills

discovery/planning | implementation | quality/gates | process/infra
---|---|---|---
`interview`, `brainstorming`, `writing-plans` | `tdd`, `e2e-playwright`, `quality-gates`, `dependency-audit`, `api-contract-testing`, `db-migration-testing`, `autoship`, `refactor`, `systematic-debugging` | `code-review`, `pre-review-cleanup`, `security-audit`, `verification`, `doubt`, `observe`, `deprecate`, `incident-runbook` | `pr`, `repo-docs`, `git-worktrees`, `setup-project`, `codemax-gbrain`

## The Strict Pipeline

Both Claude Code and this Hermes port follow the same order — **never skip a step**:

```
/interview → /brainstorming → /writing-plans → [implement with tdd] → /simplify-code → /requesting-code-review → /pr
```

| Step | Hermes skill | Notes |
|---|---|---|
| `interview` | `tapway/interview` | Optional but recommended when the request is underspecified. One question at a time → Confirmed Intent. |
| `brainstorming` | `tapway/brainstorming` | Explore approaches, commit to `docs/brainstorming/`. |
| `writing-plans` | `tapway/writing-plans` | Plan → `docs/plans/[feature].md`. |
| implement | `tapway/tdd` + Hermes `test-driven-development` | RED gate → GREEN → REFACTOR per task, via `delegate_task`. |
| `simplify-code` | `simplify-code` (Hermes core) | Reduce complexity/duplication. |
| `requesting-code-review` | `requesting-code-review` (Hermes core) | Three-tier self-review before PR. |
| `pr` | `tapway/pr` | Rebase, test, docs, push, open PR. |

### What maps to existing Hermes skills
You don't need duplicates for skills Hermes already ships:
- `/simplify` → `simplify-code`
- `/review` → `requesting-code-review`
- `/plan` → `writing-plans` (this port) — Hermes also has a generic `plan` skill; use `writing-plans` for the Tapway structured format
- `/tdd` → `tdd` (this port) + Hermes `test-driven-development`
- `/pr` → `tdd`'s PR workflow + Hermes `github-pr-workflow`
- `/security-review` → Hermes `requesting-code-review` / `github` security audit

### Pin to memory (recommended)
Add this to your Hermes memory so the process runs on every task automatically:

> **Tapway dev process:** Always follow interview → brainstorming → writing-plans → tdd → simplify-code → requesting-code-review → pr. Build the right thing before building it right; never ship without a failing-test gate and a self-review.

## What is NOT ported (Claude Code-only)
These rely on Claude Code's hook/command system and have no Hermes equivalent that runs automatically:
- Commit-to-`main` blocking hook (Hermes has a `hooks` system — see below)
- Pre-commit secret scanning
- Auto-changelog on conventional commits
- Post-edit auto-lint
- `/cleanup`, `/release`, `/upgrade-skills` (template/CI-bound commands)

> Tapway no longer ships a GitHub Actions PR-review workflow (`claude.yml` / `@claude`).
> Code review is done inside the AI agent (`requesting-code-review` / the `/review` skill)
> before a PR is opened, so there is no GitHub Actions review to port anyway.

The **discipline** behind them is preserved by the manual pipeline above.

> **Hermes has a `hermes hooks` system** — shell hooks declared in `config.yaml`
> (`hermes hooks list` / `doctor`). The commit-guard, secret-scan, and post-edit
> lint behaviors *can* be replicated as Hermes hooks; they're left as documented
> discipline here so the port stays pure-skill.


## License
MIT © Tapway — ported for Hermes by `limcheehow`.
