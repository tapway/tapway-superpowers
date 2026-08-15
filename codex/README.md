# Tapway Superpowers for OpenAI Codex

Port of [Tapway Superpowers](../README.md) to **OpenAI Codex** (CLI / IDE),
parallel to the existing `hermes/` port. Lets a Codex user run the same strict
pipeline — interview → brainstorming → writing-plans → tdd → code-review → pr —
with the same enforceable guardrail hooks, without re-learning a parallel tool.

**No custom slash commands.** Codex's `/` commands are a fixed built-in set; the
pipeline is exposed as `$skill` mentions plus the `$tapway` umbrella, and the
built-in `/plan` `/review` are used where they map. See the mapping table below.

---

## Install

Prereq: Codex CLI 0.12x+ (with stable hooks), `gh` auth for the issue gate.

```bash
# 1. Skills (user scope — apply to every repo you open)
bash codex/install.sh

# OR install skills into one project (repo scope) and wire hooks + AGENTS.md:
CODEX_TARGET_PROJECT=/path/to/project bash codex/install.sh
```

This copies the **24 skills + `$tapway` umbrella** to `~/.agents/skills/` (or
`<project>/.agents/skills/`), and — when `CODEX_TARGET_PROJECT` is set — writes:

- `<project>/.codex/hooks.json` (hook manifest)
- `<project>/.codex/hooks/*.sh` (hook scripts)
- `<project>/AGENTS.md` (pipeline directive, only if one doesn't already exist)

**Windows:** `powershell -File codex/install.ps1` (same env vars).

> ⚙ **One-time trust review (required).** Codex will not run non-managed hooks
> until you approve them. Start Codex in the project and run **`/hooks`**, then
> review and trust the Tapway hooks.

## Usage

Invoke the whole pipeline with **`$tapway`**, or a single step with its skill:

```
$tapway                → full pipeline (interview → … → pr)
$interview             → requirement interview
$brainstorming         → explore approaches before coding
$writing-plans         → bite-sized TDD plan → docs/plans/
$tdd                   → strict RED-GREEN-REFACTOR
$code-review           → three-tier self-review
$pr                    → rebase, test, push, PR (the only exit gate)
```

Skills also auto-trigger when your task matches their `description`.

---

## Claude → Codex command mapping

| Claude Code | Codex equivalent | Notes |
|---|---|---|
| `/interview` | `$interview` skill | Explicit `$`-mention or auto-trigger via description |
| `/brainstorming` | `$brainstorming` skill | — |
| `/plan` | `$writing-plans` skill **or** built-in `/plan` | Codex has native `/plan`; Tapway's `writing-plans` skill has the structured format |
| `/tdd` | `$tdd` skill | — |
| `/simplify` | `$refactor` skill | Or Codex's native simplify if available |
| `/review` | Built-in `/review` | Map Tapway review discipline onto it (`review_model` config) |
| `/pr` | `$pr` skill | — |
| `/gbrain` | `$codemax-gbrain` skill | Env-gated: `CODEMAX_ENABLED=1` |
| `/release` | *Dropped* | Release is a repo-level CI concern |
| `/upgrade-skills` | *Dropped* | Codex auto-detects changes; re-run `codex/install.sh` |
| `/tapway` (Hermes bundle) | `$tapway` umbrella skill | Chains the full pipeline in order |

---

## Hook event mapping (Claude `hooks.json` → Codex `hooks.json`)

| Claude hook | Claude event | Codex event | Codex matcher | Script source |
|---|---|---|---|---|
| `pre-bash-safety.sh` | `PreToolUse:Bash` | `PreToolUse` | `^Bash$` | `codex/hooks/pre-bash-safety.sh` |
| `pre-commit-secrets.sh` | `PreToolUse:Bash(git commit:*)` | `PreToolUse` | `^Bash$` + command filter | `codex/hooks/pre-commit-secrets.sh` |
| `pre-commit-gate.sh` | `PreToolUse:Bash(git commit:*)` | `PreToolUse` | `^Bash$` + command filter | `codex/hooks/pre-commit-gate.sh` |
| `dependency-audit.sh` | `PreToolUse:Bash(git commit:*)` | `PreToolUse` | `^Bash$` + command filter | `codex/hooks/dependency-audit.sh` |
| `post-write-lint.sh` | `PostToolUse:Write\|Edit\|MultiEdit` | `PostToolUse` | `apply_patch` | `codex/hooks/post-write-lint.sh` |
| `post-commit-release-note.sh` | `PostToolUse:Bash(git commit:*)` | `PostToolUse` | `^Bash$` + command filter | `codex/hooks/post-commit-release-note.sh` |
| `session-start.sh` | `SessionStart` | `SessionStart` | `startup\|resume` | `codex/hooks/session-start.sh` |
| `check.sh` (github-issue) | `SessionStart` | `SessionStart` | `startup\|resume` | `codex/hooks/pre-execute-github-issue-check.sh` |

**Key adaptation:** Claude Code passed the Bash command to a hook as `$1`;
Codex sends the tool invocation as **JSON on stdin**
(`{"tool_name":"Bash","tool_input":{"command":"..."}}`). Every ported hook
parses `tool_input.command` from stdin. See the files under `codex/hooks/`.

**Codex hook exit codes:** `0` allow, `2` block the tool call; `0` + stdout
JSON `{"additionalContext": "..."}` allows + injects context.

---

## CodeMAX / gbrain

`codemax-gbrain` is **off by default** — it only activates when
`CODEMAX_ENABLED=1` is set. It uses the `DB_CONNECTION` env for gbrain state and
reads/writes the CodeMAX panel API (tool-agnostic). To use the gbrain MCP server
from Codex, register it in `~/.codex/config.toml`:

```toml
[mcp_servers.gbrain]
command = "node"
args = ["gbrain-mcp-server.js"]
env = { GBRAIN_TOKEN = "your-token" }
```

---

## Roadmap: converting to a distributable plugin (Option C)

This round ships a repo-checked `codex/` tree (the `hermes/`-parallel model).
To later distribute it as an OpenAI/Codex **plugin**:

1. Wrap `codex/skills/` + `codex/hooks/` + `hooks.json.template` in a plugin
   manifest (skills + metadata) per the Codex plugin spec.
2. Publish to the plugin directory and install via `$skill-installer`.
3. Keep the `$tapway` umbrella and `AGENTS.md` logic unchanged — only the
   packaging layer moves.

This is intentionally a *guide*, not done now — per the brainstorm scoping,
repository-tree distribution first, plugin "later".

---

## Scope decisions (from the brainstorm)

- **24 skills** ported (Claude's set, mirrors `hermes/`). `dependency-audit`
  stays a hook, not a skill.
- **Subagents deferred** — `agents/*.md` subagents are out of scope this round.
- **No custom slash commands** — `$skill` mentions + built-in `/plan` `/review`.
- **Hooks** are the differentiator: Codex is the first target that can actually
  *enforce* the pre-commit gate / secret-scan / lint / gbrain-session-start.

See the full rationale in `docs/brainstorming/codex-port.md`.