# Tapway Superpowers — Hermes Port

A port of the [Tapway Superpowers](https://github.com/tapway/tapway-superpowers) Claude Code plugin for **Hermes Agent**. Same skills, same strict engineering pipeline — running on Hermes instead of Claude Code.

> The original repo is a Claude Code plugin (`.claude-plugin/plugin.json`, slash commands, hooks). Hermes can't load that plugin format, so the *skill content* has been converted to Hermes `SKILL.md` files. The Claude-only hooks (commit guards, secret scanning, post-edit lint) don't auto-run in Hermes — the equivalent discipline is enforced by following the pipeline below.

## Install

Run the installer (it copies the 6 Tapway skills into your Hermes skills directory):

**macOS / Linux:**
```bash
bash install.sh
# or specify a custom skills dir:
bash install.sh /path/to/hermes/skills
```

**Windows (PowerShell):**
```powershell
.\install.ps1
```

Then restart Hermes (or run `hermes skills list` to confirm `tapway/interview`, `tapway/brainstorming`, `tapway/writing-plans`, `tapway/tdd`, `tapway/repo-docs`, `tapway/pr` are present).

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
- Commit-to-`main` blocking hook
- Pre-commit secret scanning
- Auto-changelog on conventional commits
- Post-edit auto-lint
- `@claude` PR fix comments (GitHub Actions workflow)
- `/autoship`, `/cleanup`, `/release`, `/upgrade-skills` (template/CI-bound commands)

The **discipline** behind them is preserved by the manual pipeline above.

## License
MIT © Tapway — ported for Hermes by `limcheehow`.
