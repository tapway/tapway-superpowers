# Tapway Superpowers — Hermes Port

A port of the [Tapway Superpowers](https://github.com/tapway/tapway-superpowers) Claude Code plugin for **Hermes Agent**. Same skills, same strict engineering pipeline — running on Hermes instead of Claude Code.

> The original repo is a Claude Code plugin (`.claude-plugin/plugin.json`, slash commands, hooks). Hermes can't load that plugin format, so the *skill content* has been converted to Hermes `SKILL.md` files. The Claude-only hooks (commit guards, secret scanning, post-edit lint) don't auto-run in Hermes — the equivalent discipline is enforced by following the pipeline below.

## Install

All **18** Tapway skills are installed through Hermes's **native skill hub** — one
command scaffolds the whole skillpack, no local file copying. The installer also
creates a **`/tapway` skill bundle** so the entire strict pipeline loads with a
single slash command.

**macOS / Linux:**
```bash
bash install.sh            # installs all 19 skills + the /tapway bundle
bash install.sh <category> # optional: custom skills category (default: tapway)

# Preview without installing anything:
HERMES_DRY_RUN=1 bash install.sh
```

**Windows (PowerShell):**
```powershell
.\install.ps1
# Preview: $env:HERMES_DRY_RUN = "1"; .\install.ps1
```

The installer resolves each skill by its GitHub identifier
(`tapway/tapway-superpowers/hermes/skills/<name>`) via `hermes skills install`, so
it works from anywhere and stays in sync with this repo. Authenticate GitHub
(`gh auth login` or a `GITHUB_TOKEN`) to avoid unauthenticated API rate limits.

Then verify:
```bash
hermes skills list | grep tapway   # 18 tapway/* skills present
hermes bundles list                # "tapway" bundle present
```

> **No installer needed?** Because Hermes auto-derives a `/skill-name` command
> from every installed skill, you can also install an individual skill directly:
> ```bash
> hermes skills install tapway/tapway-superpowers/hermes/skills/tdd --category tapway
> ```

### What you get: 19 skills

discovery/planning | implementation | quality/gates | process/infra
---|---|---|---
`interview`, `brainstorming`, `writing-plans` | `tdd`, `e2e-playwright`, `autoship`, `refactor`, `systematic-debugging` | `code-review`, `pre-review-cleanup`, `security-audit`, `verification`, `doubt`, `observe`, `deprecate` | `pr`, `repo-docs`, `git-worktrees`, `setup-project`

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
