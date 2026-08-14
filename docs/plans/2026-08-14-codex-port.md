# Codex Port Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Port all 24 Tapway Superpowers skills + enforceable hooks into a `codex/` tree that installs into Codex's native skill/hook system (`.agents/skills/` + `.codex/hooks.json` + `AGENTS.md`), mirroring the existing `hermes/` port.

**Architecture:** A self-contained `codex/` directory in the repo, parallel to `hermes/`. It contains 24 normalized `SKILL.md` files, ported hook scripts, a `hooks.json` template, an `install.sh` (+ `.ps1`) that copies skills to `~/.agents/skills/` (user scope) and optionally writes `.codex/` + `AGENTS.md` into a consuming project, and a `$tapway` umbrella skill. No custom slash commands — Codex doesn't support them; pipeline steps are invoked via `$skill` mentions + built-in `/plan` `/review`.

**Tech Stack:** Bash (install scripts, hook scripts), Markdown (SKILL.md, AGENTS.md), TOML/JSON (hooks.json), Python (tests).

**Brainstorm:** `docs/brainstorming/codex-port.md` (committed `fd803b2`)

---

## Key design decisions (from brainstorm)

1. **Skill set = Claude's 24** (includes `codemax-gbrain`, excludes `dependency-audit` as a skill — it's a hook in Claude and stays a hook in Codex).
2. **Hook port = 7 hooks** from `hooks/hooks.json` → `.codex/hooks.json` template, mapped to Codex's native hook events.
3. **No custom slash commands.** Codex's `/` commands are a fixed built-in set. Pipeline exposed as `$skill` mentions + `$tapway` umbrella + `AGENTS.md` directive + built-in `/plan` `/review`.
4. **Skill normalization:** Hermes-specific verbs (`delegate_task`, Hermes CLI, `hermes hooks`) → Codex-native (`apply_patch`, `Bash`, `$skill`, `AGENTS.md`).
5. **`codemax-gbrain`** carries `CODEMAX_ENABLED` / `DB_CONNECTION` env gate — off by default.
6. **Plugin packaging deferred** — documented runbook in `codex/README.md`.

---

## Claude → Codex command mapping table

| Claude Code | Codex equivalent | Notes |
|---|---|---|
| `/interview` | `$interview` skill | Explicit `$`-mention or auto-trigger via description |
| `/brainstorming` | `$brainstorming` skill | — |
| `/plan` | `$writing-plans` skill OR built-in `/plan` | Codex's native `/plan` exists; Tapway's `writing-plans` skill has the structured format |
| `/tdd` | `$tdd` skill | — |
| `/simplify` | `$refactor` skill (Protocol B) | Or Codex's native simplify if available |
| `/review` | Built-in `/review` | Codex has native `/review` with `review_model` config; map Tapway review discipline onto it |
| `/pr` | `$pr` skill | — |
| `/gbrain` | `$codemax-gbrain` skill | Env-gated: `CODEMAX_ENABLED=1` |
| `/release` | Dropped (no Codex equivalent) | Release is a repo-level CI concern; documented in `codex/README.md` |
| `/upgrade-skills` | Dropped | Codex auto-detects skill changes; `codex install.sh` re-run for updates |
| `/tapway` (Hermes bundle) | `$tapway` umbrella skill | Chains the full pipeline in order |

---

## Hook event mapping (Claude hooks.json → Codex hooks.json)

| Claude hook | Claude event | Codex event | Codex matcher | Script source |
|---|---|---|---|---|
| `pre-bash-safety.sh` | PreToolUse:Bash | `PreToolUse` | `^Bash$` | `codex/hooks/pre-bash-safety.sh` |
| `pre-commit-secrets.sh` | PreToolUse:Bash(git commit:*) | `PreToolUse` | `^Bash$` + `if` filter | `codex/hooks/pre-commit-secrets.sh` |
| `pre-commit-gate.sh` | PreToolUse:Bash(git commit:*) | `PreToolUse` | `^Bash$` + `if` filter | `codex/hooks/pre-commit-gate.sh` |
| `dependency-audit.sh` | PreToolUse:Bash(git commit:*) | `PreToolUse` | `^Bash$` + `if` filter | `codex/hooks/dependency-audit.sh` |
| `post-write-lint.sh` | PostToolUse:Write\|Edit\|MultiEdit | `PostToolUse` | `apply_patch` | `codex/hooks/post-write-lint.sh` |
| `post-commit-release-note.sh` | PostToolUse:Bash(git commit:*) | `PostToolUse` | `^Bash$` + `if` filter | `codex/hooks/post-commit-release-note.sh` |
| `session-start.sh` | SessionStart | `SessionStart` | `startup\|resume` | `codex/hooks/session-start.sh` |
| `check.sh` (github-issue) | SessionStart | `SessionStart` | `startup\|resume` | `codex/hooks/pre-execute-github-issue-check.sh` |

**Codex hook trust review:** Non-managed command hooks must be reviewed and trusted before they run. The installer prints a reminder; `codex/README.md` documents the one-time `/hooks` trust step.

---

## Branch 1: `feat/codex-skills-port` — Skills + $tapway umbrella

### Task 1: Create codex/ directory structure

**Objective:** Scaffold the `codex/` tree mirroring `hermes/`.

**Files:**
- Create: `codex/skills/` (dir)
- Create: `codex/hooks/` (dir)
- Create: `codex/templates/` (dir)

**Step 1:** Create directories

```bash
cd /root/projects/tapway-superpowers
mkdir -p codex/skills codex/hooks codex/templates
```

**Step 2:** Verify

```bash
ls -d codex/skills codex/hooks codex/templates
```

Expected: all three directories exist.

**Step 3:** Commit

```bash
git add codex/
git commit -m "chore: scaffold codex/ tree structure"
```

---

### Task 2: Port 12 pipeline skills (batch via subagents)

**Objective:** Copy and normalize the first 12 skills from Claude `skills/` → `codex/skills/`, replacing Hermes/Claude-specific verbs with Codex-native ones.

**Files (create):**
- `codex/skills/interview/SKILL.md`
- `codex/skills/brainstorming/SKILL.md`
- `codex/skills/writing-plans/SKILL.md`
- `codex/skills/tdd/SKILL.md`
- `codex/skills/e2e-playwright/SKILL.md`
- `codex/skills/quality-gates/SKILL.md`
- `codex/skills/api-contract-testing/SKILL.md`
- `codex/skills/db-migration-testing/SKILL.md`
- `codex/skills/autoship/SKILL.md`
- `codex/skills/refactor/SKILL.md`
- `codex/skills/systematic-debugging/SKILL.md`
- `codex/skills/code-review/SKILL.md`

**Normalization rules (apply to every skill):**
1. Replace `claude` / `Claude Code` → `Codex` in prose
2. Replace `CLAUDE.md` → `AGENTS.md`
3. Replace `delegate_task` → "ask Codex to delegate to a subagent" (Codex supports subagent delegation via AGENTS.md instructions)
4. Replace `.claude/commands/` → `$skill` invocation
5. Replace `claude plugin` → `codex` (or drop if context doesn't apply)
6. Replace `PreToolUse:Bash` hook references → `.codex/hooks.json` PreToolUse
7. Keep frontmatter `name` and `description` — Codex requires both; ensure `description` front-loads trigger words for implicit invocation
8. Remove any Hermes-specific CLI commands (`hermes skills install`, `hermes bundles`)
9. Replace `Write|Edit|MultiEdit` tool names → `apply_patch` (Codex's tool name)

**Step 1:** For each skill, read the Claude source, apply normalization, write to `codex/skills/`.

**Step 2:** Verify frontmatter on each

```bash
for s in interview brainstorming writing-plans tdd e2e-playwright quality-gates api-contract-testing db-migration-testing autoship refactor systematic-debugging code-review; do
  echo "--- $s ---"
  head -5 "codex/skills/$s/SKILL.md"
done
```

Expected: each has `---` frontmatter with `name:` and `description:`.

**Step 3:** Commit

```bash
git add codex/skills/
git commit -m "feat: port 12 pipeline skills to codex (normalized)"
```

---

### Task 3: Port 12 quality/process/infra skills (batch via subagents)

**Objective:** Copy and normalize the remaining 12 skills.

**Files (create):**
- `codex/skills/pre-review-cleanup/SKILL.md`
- `codex/skills/security-audit/SKILL.md`
- `codex/skills/verification/SKILL.md`
- `codex/skills/doubt/SKILL.md`
- `codex/skills/observe/SKILL.md`
- `codex/skills/deprecate/SKILL.md`
- `codex/skills/incident-runbook/SKILL.md`
- `codex/skills/pr/SKILL.md`
- `codex/skills/repo-docs/SKILL.md`
- `codex/skills/git-worktrees/SKILL.md`
- `codex/skills/setup-project/SKILL.md`
- `codex/skills/codemax-gbrain/SKILL.md`

**Special handling for `codemax-gbrain`:**
- Carry `CODEMAX_ENABLED` env gate (off by default)
- Carry `DB_CONNECTION` env behavior
- Replace `claude mcp add gbrain` → Codex MCP config in `.codex/config.toml` under `[mcp_servers.gbrain]`
- Replace `codemax` CLI references → keep (codemax panel API is tool-agnostic)
- Document: gbrain MCP server registered in `~/.codex/config.toml`:
  ```toml
  [mcp_servers.gbrain]
  command = "node"
  args = ["gbrain-mcp-server.js"]
  env = { GBRAIN_TOKEN = "your-token" }
  ```

**Special handling for `setup-project`:**
- Replace `CLAUDE.md` target → `AGENTS.md`
- Replace Claude plugin install steps → `codex/install.sh` reference
- Replace `.github/workflows/release.yml` check → keep (repo-level CI, tool-agnostic)
- Add: "run `codex/install.sh` to install Tapway skills into this project"

**Special handling for `pr`:**
- Replace `claude` CLI git workflow → generic git workflow (works with Codex's `Bash` tool)
- Replace "Claude Code" → "Codex" in prose

**Step 1:** For each skill, read the Claude source, apply normalization, write to `codex/skills/`.

**Step 2:** Verify count

```bash
ls codex/skills/ | wc -l   # expect 24
```

Expected: 24 directories.

**Step 3:** Commit

```bash
git add codex/skills/
git commit -m "feat: port 12 quality/process/infra skills to codex (normalized)"
```

---

### Task 4: Create the $tapway umbrella skill

**Objective:** A single skill that chains the full pipeline, analogous to the Hermes `/tapway` bundle.

**Files:**
- Create: `codex/skills/tapway/SKILL.md`

**Step 1:** Write the umbrella skill

```markdown
---
name: tapway
description: >
  Load the full Tapway engineering pipeline: interview → brainstorming →
  writing-plans → tdd → code-review → pr. Use when starting a new feature,
  bug fix, or any task that should follow the strict development process.
  Trigger with $tapway in your prompt.
---

# Tapway Pipeline

When invoked, follow these steps **in order**. Do not skip steps.

## 1. Interview (optional but recommended)
If the request is underspecified, ask clarifying questions one at a time
until you have a Confirmed Intent. Use the `$interview` skill's protocol.

## 2. Brainstorming
If multiple approaches exist, explore them with the `$brainstorming` skill.
Save output to `docs/brainstorming/[topic].md`. Commit.

## 3. Writing Plans
Turn the brainstorm recommendation into a bite-sized TDD implementation plan
with the `$writing-plans` skill. Save to `docs/plans/[feature].md`. Commit.
Create a GitHub issue hydrated with the plan content (see
`codex/hooks/pre-execute-github-issue-create.sh`).

## 4. Implement with TDD
Follow strict RED-GREEN-REFACTOR per task. Write the failing test first,
verify it fails, implement minimal code, verify it passes. Use the `$tdd`
skill's protocol. Commit after each task.

## 5. Pre-Review Cleanup
Run the `$pre-review-cleanup` skill to scan for template placeholders,
leftover scaffolding, and stale TODOs.

## 6. Code Review
Run the `$code-review` skill for a three-tier self-review (security,
quality, architecture). Use Codex's built-in `/review` for an additional
model-based review if configured.

## 7. PR
Run the `$pr` skill: rebase against main, run full test suite, push, open PR.
**Never push directly to main.** The PR is the only exit gate.

## CodeMAX / gbrain (optional)
If `CODEMAX_ENABLED=1` is set in your environment, pull context from gbrain
at task start (after step 3) and sync docs back before step 7. Use the
`$codemax-gbrain` skill. If not set, skip — no hooks, no errors.
```

**Step 2:** Verify

```bash
head -5 codex/skills/tapway/SKILL.md
```

Expected: frontmatter with `name: tapway` and `description:`.

**Step 3:** Commit

```bash
git add codex/skills/tapway/
git commit -m "feat: add \$tapway umbrella skill for codex pipeline"
```

---

### Task 5: Create the AGENTS.md template

**Objective:** A template the installer writes into consuming projects to enforce the pipeline as background discipline.

**Files:**
- Create: `codex/templates/AGENTS.md`

**Step 1:** Write the template

```markdown
# Project Agent Instructions

## Development Process

**Always follow this pipeline for any feature or bug fix:**

1. **Interview** — if the request is underspecified, ask clarifying questions
   one at a time.
2. **Brainstorming** — explore approaches before coding. Save to
   `docs/brainstorming/`. Commit.
3. **Writing Plans** — create a bite-sized TDD plan. Save to
   `docs/plans/`. Commit.
4. **TDD** — RED (failing test) → GREEN (minimal implementation) → REFACTOR.
   Never write production code without a failing test first.
5. **Pre-Review Cleanup** — scan for placeholders, stale scaffolding.
6. **Code Review** — three-tier self-review (security, quality, architecture).
7. **PR** — rebase, test, push, open PR. Never push directly to main.

Invoke with `$tapway` or follow each step via its skill:
`$interview` `$brainstorming` `$writing-plans` `$tdd` `$code-review` `$pr`

## Guardrails

- **Never commit to main/master directly.** Always use a feature branch + PR.
- **Never force push.** Use a PR instead.
- **Never hardcode secrets.** Use environment variables.
- **Run lint + typecheck + tests before every commit.**
- **CodeMAX/gbrain is optional.** Set `CODEMAX_ENABLED=1` to activate.
```

**Step 2:** Commit

```bash
git add codex/templates/AGENTS.md
git commit -m "feat: add AGENTS.md template for codex installer"
```

---

## Branch 2: `feat/codex-hooks-port` — Enforceable hooks

### Task 6: Port 7 hook scripts to codex/hooks/

**Objective:** Copy hook shell scripts from `hooks/` → `codex/hooks/`, adapting for Codex's tool name differences.

**Files (create):**
- `codex/hooks/pre-bash-safety.sh`
- `codex/hooks/pre-commit-secrets.sh`
- `codex/hooks/pre-commit-gate.sh`
- `codex/hooks/dependency-audit.sh`
- `codex/hooks/post-write-lint.sh`
- `codex/hooks/post-commit-release-note.sh`
- `codex/hooks/session-start.sh`
- `codex/hooks/pre-execute-github-issue-check.sh`
- `codex/hooks/pre-execute-github-issue-create.sh`

**Adaptations needed:**
1. **`pre-bash-safety.sh`**: Codex passes the command via stdin JSON (not `$1`). Parse with `jq` or `python3 -c` to extract the `command` field from the JSON payload. Claude Code passed it as `$1`; Codex sends `{"tool_name":"Bash","tool_input":{"command":"..."}}` via stdin.
2. **`pre-commit-secrets.sh`**, **`pre-commit-gate.sh`**, **`dependency-audit.sh`**: Same stdin JSON parsing. The `if` filter in Codex's `hooks.json` handles the `git commit` matching (Codex's matcher is `^Bash$` and the `if` field can filter on command content).
3. **`post-write-lint.sh`**: Codex's tool is `apply_patch`, not `Write|Edit|MultiEdit`. Parse the JSON stdin to extract the file path from the patch content. Codex sends `{"tool_name":"apply_patch","tool_input":{"patch":"..."}}`.
4. **`session-start.sh`**: Replace `CLAUDE.md` references → `AGENTS.md`. Replace Claude-specific session context with Codex session context.
5. **`post-commit-release-note.sh`**: Parse stdin JSON for commit detection.
6. **`pre-execute-github-issue-check.sh`** and **`create.sh`**: Minimal changes — `gh` CLI is tool-agnostic. Update `CLAUDE.md` → `AGENTS.md` references.

**Codex hook stdin JSON format (PreToolUse):**
```json
{
  "hook_event": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "git commit -m '...'" },
  "session_id": "..."
}
```

**Hook exit codes (Codex):**
- `0` = allow, no output
- `2` = block the tool call (same as Claude Code)
- `0` + stdout JSON `{"additionalContext": "..."}` = allow + inject context

**Step 1:** For each hook, read the Claude source, adapt stdin parsing, write to `codex/hooks/`.

**Step 2:** A shared stdin parser helper to avoid duplication:

```bash
# codex/hooks/_lib.sh — shared helper
#!/bin/bash
# Parse the tool_input.command from Codex's stdin JSON payload.
# Usage: COMMAND=$(source _lib.sh; get_bash_command)
get_bash_command() {
  python3 -c "
import sys, json
payload = json.load(sys.stdin)
print(payload.get('tool_input', {}).get('command', ''))
" 2>/dev/null
}
```

Actually, keep it simpler — inline the parser in each script to avoid path issues. Each script starts with:

```bash
#!/bin/bash
# Read Codex hook payload from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
```

**Step 3:** Make all hooks executable

```bash
chmod +x codex/hooks/*.sh
```

**Step 4:** Commit

```bash
git add codex/hooks/
git commit -m "feat: port 7+2 hook scripts to codex (stdin JSON adapted)"
```

---

### Task 7: Create codex/hooks.json template

**Objective:** The hooks manifest that the installer writes into `.codex/hooks.json` in consuming projects.

**Files:**
- Create: `codex/hooks.json.template`

**Step 1:** Write the template

```json
{
  "description": "Tapway Superpowers enforceable quality gates for Codex",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/session-start.sh\"",
            "timeout": 10,
            "statusMessage": "Loading session context"
          },
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/pre-execute-github-issue-check.sh\"",
            "timeout": 30,
            "statusMessage": "Checking for GitHub issue"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/pre-bash-safety.sh\"",
            "timeout": 10,
            "statusMessage": "Checking Bash safety"
          },
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/pre-commit-secrets.sh\"",
            "timeout": 10,
            "statusMessage": "Scanning for secrets"
          },
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/pre-commit-gate.sh\"",
            "timeout": 120,
            "statusMessage": "Running pre-commit quality gate"
          },
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/dependency-audit.sh\"",
            "timeout": 120,
            "statusMessage": "Auditing dependencies"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "apply_patch",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/post-write-lint.sh\"",
            "timeout": 30,
            "statusMessage": "Auto-linting edited file"
          }
        ]
      },
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/post-commit-release-note.sh\"",
            "timeout": 10,
            "statusMessage": "Generating release note"
          }
        ]
      }
    ]
  }
}
```

**Note on `if` filters:** Codex's `hooks.json` does not support Claude's `"if": "Bash(git commit:*)"` syntax. Instead, the hook script itself checks whether the command contains `git commit` and exits `0` (no-op) if it doesn't. This is a per-script responsibility, documented in each script's header comment.

**Step 2:** Commit

```bash
git add codex/hooks.json.template
git commit -m "feat: add codex hooks.json template"
```

---

## Branch 3: `feat/codex-installer` — install.sh + README + tests

### Task 8: Write codex/install.sh

**Objective:** Bash installer that copies skills to `~/.agents/skills/` (user scope) and optionally writes `.codex/` + `AGENTS.md` into a consuming project.

**Files:**
- Create: `codex/install.sh`

**Step 1:** Write the installer. Key behaviors:
- Copy all 24 skills + `$tapway` umbrella into `~/.agents/skills/` (user scope — Codex auto-discovers)
- `--project` flag: also write `.codex/hooks.json` + `.codex/hooks/*.sh` + `AGENTS.md` into the current project (repo scope)
- `--dry-run` flag: preview only
- Print hook trust-review reminder
- Exit non-zero on failure

```bash
#!/usr/bin/env bash
#
# install.sh — Install Tapway Superpowers skills + hooks into Codex
#
# Usage:
#   bash install.sh                  # user scope: skills → ~/.agents/skills/
#   bash install.sh --project        # also write .codex/ + AGENTS.md into CWD project
#   bash install.sh --dry-run        # preview, no writes
#   bash install.sh --project --dry-run
#
# Prereqs:
#   - Codex CLI (codex) on PATH (optional — skills work without it)
#
# Codex auto-discovers skills from ~/.agents/skills/ (user) and
# .agents/skills/ (repo). No restart needed; Codex detects changes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_SKILLS_DIR="${SCRIPT_DIR}/skills"
LOCAL_HOOKS_DIR="${SCRIPT_DIR}/hooks"
LOCAL_TEMPLATE_DIR="${SCRIPT_DIR}/templates"

# All 24 ported skills + $tapway umbrella. Order = pipeline order.
SKILLS=(
  interview
  brainstorming
  writing-plans
  tdd
  e2e-playwright
  quality-gates
  api-contract-testing
  db-migration-testing
  autoship
  refactor
  systematic-debugging
  code-review
  pre-review-cleanup
  security-audit
  verification
  doubt
  observe
  deprecate
  incident-runbook
  pr
  repo-docs
  git-worktrees
  setup-project
  codemax-gbrain
  tapway
)

PROJECT_MODE=0
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --project) PROJECT_MODE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

USER_SKILLS_DIR="${HOME}/.agents/skills"

echo "Installing Tapway Superpowers into Codex"
echo "  user skills dir : ${USER_SKILLS_DIR}"
if [ "$PROJECT_MODE" = "1" ]; then
  echo "  project mode    : enabled (.codex/ + AGENTS.md into $(pwd))"
fi
if [ "$DRY_RUN" = "1" ]; then
  echo "  dry-run          : preview only, no writes"
fi
echo ""

installed=0
failed=0

# --- Install skills to user scope ---
mkdir -p "${USER_SKILLS_DIR}"

for skill in "${SKILLS[@]}"; do
  src="${LOCAL_SKILLS_DIR}/${skill}"
  dest="${USER_SKILLS_DIR}/${skill}"

  if [ ! -d "$src" ] || [ ! -f "${src}/SKILL.md" ]; then
    echo "  ✗ ${skill} — source missing"
    failed=$((failed + 1))
    continue
  fi

  if [ "$DRY_RUN" = "1" ]; then
    echo "  (dry-run) ${skill} → ${dest}"
    installed=$((installed + 1))
    continue
  fi

  rm -rf "$dest"
  if cp -a "$src" "$dest" 2>/dev/null; then
    :
  else
    mkdir -p "$dest"
    cp -R "$src"/. "$dest"/
  fi

  if [ -f "${dest}/SKILL.md" ]; then
    echo "  ✓ ${skill}"
    installed=$((installed + 1))
  else
    echo "  ✗ ${skill} — copy failed"
    failed=$((failed + 1))
  fi
done

# --- Project mode: write .codex/ + AGENTS.md ---
if [ "$PROJECT_MODE" = "1" ]; then
  PROJECT_HOOKS_DIR="$(pwd)/.codex/hooks"
  mkdir -p "$PROJECT_HOOKS_DIR"

  # Copy hook scripts
  for hook_script in "${LOCAL_HOOKS_DIR}"/*.sh; do
    name=$(basename "$hook_script")
    if [ "$DRY_RUN" = "1" ]; then
      echo "  (dry-run) hook → ${PROJECT_HOOKS_DIR}/${name}"
    else
      cp "$hook_script" "${PROJECT_HOOKS_DIR}/${name}"
      chmod +x "${PROJECT_HOOKS_DIR}/${name}"
      echo "  ✓ hook: ${name}"
    fi
  done

  # Write hooks.json from template
  if [ "$DRY_RUN" = "1" ]; then
    echo "  (dry-run) hooks.json → $(pwd)/.codex/hooks.json"
  else
    cp "${SCRIPT_DIR}/hooks.json.template" "$(pwd)/.codex/hooks.json"
    echo "  ✓ .codex/hooks.json"
  fi

  # Write AGENTS.md (don't overwrite if exists)
  if [ -f "$(pwd)/AGENTS.md" ]; then
    echo "  ⚠ AGENTS.md already exists — skipping (merge manually)"
  else
    if [ "$DRY_RUN" = "1" ]; then
      echo "  (dry-run) AGENTS.md → $(pwd)/AGENTS.md"
    else
      cp "${LOCAL_TEMPLATE_DIR}/AGENTS.md" "$(pwd)/AGENTS.md"
      echo "  ✓ AGENTS.md"
    fi
  fi
fi

echo ""
echo "Done. ${installed}/${#SKILLS[@]} skills installed."

if [ "$PROJECT_MODE" = "1" ] && [ "$DRY_RUN" = "0" ]; then
  echo ""
  echo "⚠️  HOOK TRUST REVIEW REQUIRED"
  echo "   Codex requires you to review and trust non-managed hooks before they run."
  echo "   Run /hooks in Codex CLI to review and approve the installed hooks."
  echo "   This is a one-time step per project."
fi

echo ""
echo "  • Verify skills:   ls ~/.agents/skills/ | grep -E 'interview|tdd|pr|tapway'"
echo "  • Pipeline:        \$tapway <your task>"
echo "  • Individual:      \$interview, \$brainstorming, \$writing-plans, \$tdd, \$pr"
echo "  • Built-in:        /plan, /review (Codex native)"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
```

**Step 2:** Make executable

```bash
chmod +x codex/install.sh
```

**Step 3:** Test dry-run

```bash
bash codex/install.sh --dry-run
```

Expected: prints all 25 skills as dry-run, exit 0.

**Step 4:** Commit

```bash
git add codex/install.sh
git commit -m "feat: add codex install.sh (user + project scope)"
```

---

### Task 9: Write codex/install.ps1 (Windows parity)

**Objective:** PowerShell installer mirroring `install.sh` for Windows Codex users.

**Files:**
- Create: `codex/install.ps1`

**Step 1:** Write the PowerShell script mirroring `install.sh` logic:
- Copy skills to `$env:USERPROFILE\.agents\skills\`
- `--project` flag: write `.codex\hooks\` + `hooks.json` + `AGENTS.md`
- `--dry-run` flag
- Print hook trust reminder

**Step 2:** Commit

```bash
git add codex/install.ps1
git commit -m "feat: add codex install.ps1 for Windows parity"
```

---

### Task 10: Write codex/README.md

**Objective:** Full documentation for the Codex port — install, usage, hook trust, command mapping, and the plugin-packaging runbook.

**Files:**
- Create: `codex/README.md`

**Step 1:** Write the README. Structure:
1. **Overview** — what this port provides (24 skills + hooks + $tapway umbrella)
2. **Install** — `bash codex/install.sh` (user scope) or `--project` (repo scope)
3. **The Strict Pipeline** — same as hermes/README.md but with `$skill` invocation
4. **Claude → Codex Command Mapping** — the table from this plan
5. **Hooks** — what's ported, how to trust them (`/hooks`), the one-time step
6. **What is NOT ported** — subagents (deferred), `/release` `/upgrade-skills` (dropped)
7. **$tapway Umbrella** — how to use it
8. **AGENTS.md** — what the installer writes, why it matters
9. **CodeMAX / gbrain** — env gate, how to enable
10. **Plugin Packaging Runbook** (future) — steps to convert `codex/` into a distributable Codex/OpenAI plugin

**Step 2:** Commit

```bash
git add codex/README.md
git commit -m "docs: add codex/README.md with install, mapping, and plugin runbook"
```

---

### Task 11: Write tests/test_codex_port.py

**Objective:** Parity test mirroring `tests/test_hermes_install.py` — verifies all 24 skills exist, frontmatter is valid, no Claude-specific triggers leaked, hooks.json maps 1:1, install.sh dry-run works.

**Files:**
- Create: `tests/test_codex_port.py`

**Step 1:** Write the test

```python
#!/usr/bin/env python3
"""Tests for codex/ port: skill parity, hook mapping, install.sh structure."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / "codex"
SKILLS = CODEX / "skills"
HOOKS = CODEX / "hooks"

PASS: list[str] = []
FAIL: list[str] = []

def check(cond: bool, msg: str) -> None:
    if cond:
        PASS.append(msg)
        print(f"  PASS  {msg}")
    else:
        FAIL.append(msg)
        print(f"  FAIL  {msg}")

# 24 pipeline skills (excludes tapway umbrella)
EXPECTED_SKILLS = [
    "interview", "brainstorming", "writing-plans", "tdd",
    "e2e-playwright", "quality-gates", "api-contract-testing",
    "db-migration-testing", "autoship", "refactor",
    "systematic-debugging", "code-review", "pre-review-cleanup",
    "security-audit", "verification", "doubt", "observe",
    "deprecate", "incident-runbook", "pr", "repo-docs",
    "git-worktrees", "setup-project", "codemax-gbrain",
]

# Claude-specific substrings that must NOT appear in Codex skills
CLAUDE_TRIGGERS = [
    "CLAUDE.md",
    "claude plugin",
    "claude mcp add",
    "delegate_task",
    ".claude/commands",
    "PreToolUse:Write|Edit|MultiEdit",
]

# Expected hooks in hooks.json.template
EXPECTED_HOOKS = [
    "pre-bash-safety.sh",
    "pre-commit-secrets.sh",
    "pre-commit-gate.sh",
    "dependency-audit.sh",
    "post-write-lint.sh",
    "post-commit-release-note.sh",
    "session-start.sh",
    "pre-execute-github-issue-check.sh",
]


def main() -> int:
    print("[1] Skill parity — all 24 exist with valid frontmatter")
    for name in EXPECTED_SKILLS:
        skill_path = SKILLS / name / "SKILL.md"
        check(skill_path.is_file(), f"codex/skills/{name}/SKILL.md exists")
        if skill_path.is_file():
            text = skill_path.read_text(encoding="utf-8")
            check(text.startswith("---"), f"{name} has frontmatter")
            check(re.search(r"^name:", text, re.M) is not None, f"{name} has name field")
            check(re.search(r"^description:", text, re.M) is not None, f"{name} has description field")

    print("\n[2] $tapway umbrella skill exists")
    tapway = SKILLS / "tapway" / "SKILL.md"
    check(tapway.is_file(), "codex/skills/tapway/SKILL.md exists")
    if tapway.is_file():
        text = tapway.read_text(encoding="utf-8")
        check("interview" in text and "brainstorming" in text, "tapway references pipeline steps")
        check("$tapway" in text or "tapway" in text, "tapway self-references")

    print("\n[3] No Claude-specific triggers leaked into Codex skills")
    for name in EXPECTED_SKILLS:
        skill_path = SKILLS / name / "SKILL.md"
        if skill_path.is_file():
            text = skill_path.read_text(encoding="utf-8")
            for trig in CLAUDE_TRIGGERS:
                check(trig not in text, f"{name} free of '{trig}'")

    print("\n[4] Hook scripts exist")
    for hook in EXPECTED_HOOKS:
        check((HOOKS / hook).is_file(), f"codex/hooks/{hook} exists")

    print("\n[5] hooks.json.template structure")
    template_path = CODEX / "hooks.json.template"
    check(template_path.is_file(), "codex/hooks.json.template exists")
    if template_path.is_file():
        data = json.loads(template_path.read_text(encoding="utf-8"))
        check("PreToolUse" in data["hooks"], "hooks.json has PreToolUse")
        check("PostToolUse" in data["hooks"], "hooks.json has PostToolUse")
        check("SessionStart" in data["hooks"], "hooks.json has SessionStart")
        # Verify apply_patch matcher (not Write|Edit|MultiEdit)
        post = data["hooks"]["PostToolUse"]
        matchers = [g.get("matcher", "") for g in post]
        check(any("apply_patch" in m for m in matchers), "PostToolUse uses apply_patch matcher")

    print("\n[6] install.sh structure")
    install = (CODEX / "install.sh").read_text(encoding="utf-8")
    for name in EXPECTED_SKILLS:
        check(name in install, f"install.sh lists {name}")
    check("--project" in install, "install.sh supports --project flag")
    check("--dry-run" in install, "install.sh supports --dry-run flag")
    check("trust" in install.lower(), "install.sh mentions hook trust review")

    print("\n[7] AGENTS.md template exists")
    agents = CODEX / "templates" / "AGENTS.md"
    check(agents.is_file(), "codex/templates/AGENTS.md exists")
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        check("interview" in text and "brainstorming" in text, "AGENTS.md lists pipeline")
        check("CODEMAX_ENABLED" in text, "AGENTS.md mentions CODEMAX_ENABLED gate")
        check("$tapway" in text, "AGENTS.md references $tapway")

    print("\n[8] README.md exists")
    readme = CODEX / "README.md"
    check(readme.is_file(), "codex/README.md exists")

    print("\n[9] install.sh --dry-run executes successfully")
    result = subprocess.run(
        ["bash", str(CODEX / "install.sh"), "--dry-run"],
        capture_output=True, text=True, timeout=30,
    )
    check(result.returncode == 0, "install.sh --dry-run exits 0")
    check("25" in result.stdout or str(len(EXPECTED_SKILLS) + 1) in result.stdout,
          "dry-run reports 25 skills (24 + tapway)")

    print("\n[10] codemax-gbrain env gate")
    gbrain = SKILLS / "codemax-gbrain" / "SKILL.md"
    if gbrain.is_file():
        text = gbrain.read_text(encoding="utf-8")
        check("CODEMAX_ENABLED" in text, "codemax-gbrain has CODEMAX_ENABLED gate")
        check("DB_CONNECTION" in text or "CODEMAX" in text, "codemax-gbrain has DB env reference")

    print("\n" + "=" * 68)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 68)
    if FAIL:
        print("Failures:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2:** Run the test (expect FAIL — skills not ported yet)

```bash
python3 tests/test_codex_port.py
```

Expected: FAIL — skills don't exist yet (this is the RED phase).

**Step 3:** Commit

```bash
git add tests/test_codex_port.py
git commit -m "test: add codex port parity test (RED — expecting failures)"
```

---

### Task 12: Update README.md "Pick your tool" section

**Objective:** Add Codex as a third option in the repo's top-level README.

**Files:**
- Modify: `README.md` (lines 5-9)

**Step 1:** Update the "Pick your tool" section

Old:
```markdown
**Pick your tool:**
- **Claude Code users** → install the plugin below (slash commands + hooks).
- **Hermes Agent users** → see [Hermes Support](#hermes-support) for a ready-to-install skill port that runs the same pipeline.
```

New:
```markdown
**Pick your tool:**
- **Claude Code users** → install the plugin below (slash commands + hooks).
- **Hermes Agent users** → see [Hermes Support](#hermes-support) for a ready-to-install skill port that runs the same pipeline.
- **OpenAI Codex users** → see [Codex Support](#codex-support) for skills + enforceable hooks that run natively in Codex CLI/IDE.
```

**Step 2:** Add Codex Support section (after Hermes Support section, before Table of Contents)

```markdown
## Codex Support

Prefer **OpenAI Codex** over Claude Code? A port of these skills ships in this repo under [`codex/`](codex/). Same skills, same strict pipeline — running on Codex's native skill and hook system. Codex's enforceable hooks mean the guardrails (pre-commit gate, secret scanning, lint) actually run automatically, unlike the Hermes port.

```bash
# From inside the cloned repo:
cd codex
bash install.sh                    # user scope: skills → ~/.agents/skills/
bash install.sh --project          # also write .codex/ hooks + AGENTS.md into your project
bash install.sh --dry-run         # preview only
```

This installs all **24** Tapway skills + a `$tapway` umbrella skill into Codex's skill discovery path. The `--project` flag also writes enforceable hooks (`.codex/hooks.json`) and an `AGENTS.md` pipeline directive into the consuming project. Full details and the Claude→Codex command mapping are in [`codex/README.md`](codex/README.md).

> **Hook trust:** Codex requires a one-time review of non-managed hooks via `/hooks` in the CLI. This is documented in the installer output and `codex/README.md`.
```

**Step 3:** Update Table of Contents — add `- [Codex Support](#codex-support)` after the Hermes Support entry.

**Step 4:** Commit

```bash
git add README.md
git commit -m "docs: add Codex Support section to README"
```

---

### Task 13: Update tests/check_docs_consistency.py

**Objective:** Keep the docs-consistency test green by accounting for the new `codex/` tree.

**Files:**
- Modify: `tests/check_docs_consistency.py`

**Step 1:** Add codex checks to the test:

```python
# After the hermes checks:
c = open("codex/README.md").read() if os.path.exists("codex/README.md") else ""
checks.append(("codex/README.md exists", os.path.exists("codex/README.md"), "present" if c else "missing"))
checks.append(("codex/skills/ count=25", len(os.listdir("codex/skills")) == 25 if os.path.exists("codex/skills") else False, len(os.listdir("codex/skills")) if os.path.exists("codex/skills") else 0))
checks.append(("README 'Codex Support'", "Codex Support" in open("README.md").read(), "present"))
```

**Note:** `codex/skills/` count = 25 (24 pipeline skills + `tapway` umbrella).

**Step 2:** Run the consistency test

```bash
python3 tests/check_docs_consistency.py
```

Expected: ALL PASS (after implementation is complete).

**Step 3:** Commit

```bash
git add tests/check_docs_consistency.py
git commit -m "test: add codex checks to docs consistency test"
```

---

### Task 14: Run full test suite + verify

**Objective:** All tests pass, proving the port is complete and consistent.

**Step 1:** Run all tests

```bash
python3 tests/test_codex_port.py
python3 tests/check_docs_consistency.py
python3 tests/test_hermes_install.py
```

Expected: all pass.

**Step 2:** Dry-run the installer

```bash
bash codex/install.sh --dry-run
bash codex/install.sh --project --dry-run
```

Expected: all 25 skills listed, hooks + AGENTS.md previewed, exit 0.

**Step 3:** Verify skill count

```bash
ls codex/skills/ | wc -l   # expect 25 (24 + tapway)
```

**Step 4:** Final commit if any remaining changes

```bash
git add -A
git commit -m "test: all codex port tests green"
```

---

## Execution order

```
Branch 1 (feat/codex-skills-port):
  Task 1  → scaffold dirs
  Task 2  → 12 pipeline skills (parallel subagents)
  Task 3  → 12 quality/process skills (parallel subagents)
  Task 4  → $tapway umbrella
  Task 5  → AGENTS.md template
  → commit, merge to main

Branch 2 (feat/codex-hooks-port):
  Task 6  → 7+2 hook scripts
  Task 7  → hooks.json template
  → commit, merge to main

Branch 3 (feat/codex-installer):
  Task 8  → install.sh
  Task 9  → install.ps1
  Task 10 → README.md
  Task 11 → test_codex_port.py
  Task 12 → README.md update
  Task 13 → check_docs_consistency.py update
  Task 14 → full test suite verification
  → commit, merge to main, tag
```

**Parallelization map:**
- Task 2 and Task 3 can run as 2 parallel subagent batches (each creates NEW files only)
- Task 6 hooks can run as 1 parallel subagent batch (each creates NEW files only)
- Tasks 8-13 are sequential (shared README, shared test file)

## Pitfalls

- **Codex hook stdin is JSON, not positional args.** Claude Code passed the Bash command as `$1`; Codex sends `{"tool_name":"Bash","tool_input":{"command":"..."}}` via stdin. Every hook script must parse stdin JSON, not `$1`.
- **Codex's `PostToolUse` matcher is `apply_patch`, not `Write|Edit|MultiEdit`.** Claude used `Write|Edit|MultiEdit`; Codex uses `apply_patch` as its file-editing tool name.
- **Codex hooks require trust review.** Non-managed hooks are skipped until trusted via `/hooks`. This is a one-time step per project. Document it; don't try to bypass it.
- **No custom slash commands.** Don't create `.codex/commands/` — Codex doesn't support user-defined slash commands. Use `$skill` invocation instead.
- **`dependency-audit` is a hook, not a skill, in Codex.** The Claude `skills/` set has 24 (no `dependency-audit` dir); Hermes added it as a skill. For Codex, keep it as a hook (matching Claude's architecture) to avoid inflating the skill count.
- **`codex/skills/` count = 25, not 24.** The 24 pipeline skills + the `$tapway` umbrella = 25 directories. The docs-consistency test must account for this.
