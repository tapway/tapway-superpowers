# Brainstorm: Porting Tapway Superpowers to OpenAI Codex

- **Date:** 2026-08-14
- **Status:** Proposed (awaiting plan)
- **Author:** CH Lim

## 1. Problem restated

Make Tapway Superpowers' engineering discipline usable from **OpenAI Codex**
(CLI / IDE), the same way it currently works on Claude Code (natively) and
Hermes Agent (`hermes/` port).

**User-facing goal:** a Codex user runs the same strict pipeline —
interview → brainstorming → writing-plans → tdd → code-review → pr — with the
same guardrail hooks, without re-learning a parallel tool.

**Scope locked via interview:**
- **Distribution:** a repo-checked `codex/` tree now (mirror of `hermes/`), plugin packaging later.
- **Depth:** skills + enforceable hooks + custom "commands". **Subagents deliberately deferred.**
- **Skills:** **all 24**, including `codemax-gbrain` (carry `CODEMAX_ENABLED` / `DB_CONNECTION` env behavior into the Codex `SKILL.md`).
- **Trigger path (confirmed):** **3+5+1** — a `$tapway` umbrella skill
  (chains the whole pipeline, analogue of the `hermes` `/tapway` bundle) +
  an `AGENTS.md` pipeline directive written by the installer (background
  discipline) + every granular step kept as its own `$skill` (fine control).
  Codex's built-in `/plan` and `/review` used where they map.

## 2. Current state (grounded survey)

Codex (mid-2026) discovers config in these places:

| Layer | Location | Notes |
|---|---|---|
| Skills (REPO) | `.agents/skills/<name>/SKILL.md` from CWD up to repo root | teams check in per-project skills |
| Skills (USER) | `~/.agents/skills/<name>/SKILL.md` | applies to every repo the user opens |
| Skills (ADMIN/SYSTEM) | `/etc/codex/skills`, bundled | — |
| Config (user) | `~/.codex/config.toml` | always loads |
| Config (project) | `.codex/config.toml` | **only loads if the project is trusted** |
| Hooks | `~/.codex/hooks.json`, `~/.codex/config.toml`, `.codex/hooks.json`, `.codex/config.toml` | inline `[hooks]` or `hooks.json`; non-managed hooks require **trust review** |
| Instructions | `AGENTS.md` (workspace) | analogue of `CLAUDE.md` |

**Codex hook events available:** `SessionStart`, `SessionEnd`, `PreToolUse`,
`PostToolUse`, `PermissionRequest`, `PreCompact`, `PostCompact`,
`UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop`.

**Skill format:** a directory with `SKILL.md`; frontmatter requires `name` and
`description`. Projects want progressive disclosure (name+description first,
full instructions loaded on selection). Invoked explicitly via `$skill-name`
(`$`-mention in prompt) or implicitly when the task matches `description`.

**Critical finding — custom slash commands:** Codex CLI's slash commands are a
**fixed built-in set** (`/plan`, `/review`, `/skills`, `/hooks`, `/agent`,
`/init`, `/compact`, …). Codex does **NOT** support user-defined custom slash
commands the way Claude Code's `.claude/commands/*.md` does. `/plan` and
`/review` exist natively; the rest of the pipeline (`interview`,
`brainstorming`, `tdd`, `pr`, `code-review`, …) must be exposed as **skills**
invoked via `$`-mention (or auto-triggered by their description), not as `/`
commands.

## 3. What the port must map (Claude → Hermes → Codex)

| Claude Code | Hermes port (`hermes/`) | Codex target (`codex/`) |
|---|---|---|
| `plugin.json` + `.claude-plugin/` marketplace | `hermes/skills/` + `install.sh` | `codex/skills/` + `codex/install.sh` → copies to `~/.agents/skills/` (and/or `.agents/skills/` in consuming repo) |
| Slash commands `/interview /brainstorm …` | `hermes` `/tapway` bundle (Hermes-native) | **No user-defined slash cmds.** Expose as skills via `$interview`, `$brainstorming`, `$writing-plans`, `$tdd`, `$pr`, `$code-review`; use built-in `/plan` and `/review` where they map. |
| `hooks.json` (PreToolUse, PostToolUse, SessionStart) | **Dropped** — Hermes couldn't auto-run them | **Can be ported natively**: `.codex/hooks.json` — pre-commit gate, secret-scan, post-write lint, dependency audit, git-issue gate, session-start gbrain. |
| `agents/*.md` subagents | Dropped | Deferred (explicitly out of scope this round). |
| `CLAUDE.md` conventions | `hermes/README.md` discipline | `AGENTS.md` written into consuming projects by the installer. |
| `codemax-gbrain` (env: `CODEMAX_ENABLED`, `DB_CONNECTION`) | `hermes/skills/codemax-gbrain` | Port with same env gate (off unless `CODEMAX_ENABLED=1`). |

**Inside each SKILL.md,** the Hermes port may reference Hermes-specific verbs
(`delegate_task`, `/skill` invocation, `hermes` CLI, Hermes hooks). The Codex
port must normalize those to Codex-native verbs: `apply_patch`, `Bash`,
`AGENTS.md`, `$skill` invocation, built-in `/plan` / `/review`.

## 4. Options

### A. Skills-only copy (mirror the Hermes port)
Copy all 24 `SKILL.md` files into `codex/skills/`; `install.sh` drops them into
`~/.agents/skills/`. No hooks, no `AGENTS.md` wiring. Discipline via pipeline only.

- **Pros:** smallest, fastest, zero trust-review friction. Proven by the Hermes port.
- **Cons:** throws away exactly what Codex now supports (hooks). No enforceable gate.
- **Complexity:** Low.

### B. Skills + native hooks (recommended)
Everything in A, **plus** `codex/hooks` ported to `.codex/hooks.json`, and an
installer that (in a consuming repo) writes `.codex/` + `hooks.json` + hook
scripts + `AGENTS.md` + optional `.agents/skills/`. Adds a Claude→Codex mapping
table in `codex/README.md`.

- **Pros:** only Codex actually delivers enforceability that Hermes couldn't; preserves pre-commit gate / secret-scan / lint / git-issue / gbrain session-start for real.
- **Cons:** hooks need per-project **trust review** (documented, one-time). Slightly more install surface.
- **Complexity:** Medium.

### C. Full distribution plugin + `$skill-installer` now
Package as an OpenAI/Codex plugin (skills + manifest) published to the plugin
directory, installable via `$skill-installer`. Done immediately rather than "later".

- **Pros:** distribution story; discoverable; auto-updates.
- **Cons:** contradicts scope decision ("plugin later"); plugin review/submission overhead.
- **Complexity:** High.

### D. Hybrid: repo tree now (B) + documented plugin path (C)
Ship B now; leave a concrete stub/runbook in `codex/README.md` so converting to a plugin later is a guided step.

- **Pros:** forward-compatible, low risk. Satisfies "both".
- **Cons:** two things to maintain if not disciplined.
- **Complexity:** Medium.

## 5. Evaluation

| Option | Simple? | Fits conventions | Testable | Maintainable | Speed |
|---|---|---|---|---|---|
| A | Yes | Partial (drops enforce layer) | Easy | Easy | Fast |
| B | Yes | Best (native capabilities) | Medium (hook testable via `codex --dry-run`/trust) | Medium | Med |
| C | No | Plugin-first | Harder (submission) | Medium | Slow |
| D | Yes | Best | Medium | Good (runbook keeps plugin path honest) | Med |

## 6. Recommendation

Adopt **Option B**, structured as **Option D**'s forward path:

1. Create `codex/` tree mirroring `hermes/`: `codex/skills/<24 names>/SKILL.md`,
   `codex/hooks/` (shell scripts), `codex/hooks.json` _(template)_,
   `codex/install.sh` (+ `.ps1`), `codex/README.md`.
2. **Be honest about slash commands:** no user-defined `/` commands in Codex —
   the pipeline is exposed as `$skill` mentions + built-in `/plan` and `/review`.
   Document the full Claude-command → Codex-skill table in `codex/README.md`.
3. Port **all 24** skills, normalizing Hermes-specific verbs to Codex-native
   ones. Carry `codemax-gbrain` env behavior (`CODEMAX_ENABLED`, `DB_CONNECTION`).
4. Port the **enforceable hooks** to `.codex/hooks.json`: pre-commit gate,
   secret-scan, post-write lint, dependency audit, git-issue gate,
   session-start gbrain. Document the one-time trust-review step.
5. Installer writes `AGENTS.md` (pipeline + conventions) into consuming repos and
   copies skills to `~/.agents/skills/` (user scope) or `.agents/skills/` (repo scope).
6. Leave a **documented runbook** in `codex/README.md` for converting to a
   distributable Codex plugin later (Option C).

**Assumptions** (if wrong, revisit): user runs Codex CLI/IDE 0.12x+ with
stable hooks; hooks trust-review is acceptable one-time overhead; no subagent
port wanted this round.

## 7. Hooked follow-up

Hand off to `writing-plans` for the implementation plan. Add a parity test
(`tests/test_codex_port.py`) mirroring `test_hermes_install.py`.