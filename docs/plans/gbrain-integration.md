# Plan: Fold gbrain/CodeMAX into tapway-superpowers

**Goal:** Make the shared gbrain brain part of the normal tapway-superpowers dev
loop — context pulled automatically at task start, docs pushed at task end —
so the team uses superpowers + CodeMAX/gbrain hand-in-hand without manual querying.

**Tech stack:** Claude Code plugin (skills, hooks, commands, markdown)
**Related skills needed:** writing-plans, pr
**Estimated tasks:** 6

## Assumptions

- The gbrain MCP server is reachable at a configurable URL — devs register
  it via `claude mcp add` (see `docs/DEVELOPER_GUIDE.md` §2.1)
- `codemax` CLI is installed on the dev machine (or run via the defined path)
- gbrain is a *source of truth*, not a workflow tool — it is pulled/written at
  defined points, never queried continuously
- Team repo changes go through branch → PR → merge (per dev workflow)

## File Map

```
CREATE  skills/codemax-gbrain/SKILL.md          — the push/pull workflow skill
MODIFY  hooks/session-start/session-start.sh    — pull work-order context from gbrain
MODIFY  hooks/hooks.json                        — (no change needed; session-start already wired)
CREATE  commands/gbrain.md                      — /gbrain query + /gbrain sync
MODIFY  skills/pr/SKILL.md                      — add codemax sync step before PR
MODIFY  README.md                               — document gbrain integration
MODIFY  .claude-plugin/plugin.json              — bump to 18 skills, add keyword
MODIFY  .claude-plugin/marketplace.json         — bump version
```

### Task 1: codemax-gbrain skill
**Files:** `skills/codemax-gbrain/SKILL.md`
**Success criteria:** Skill teaches the pull-on-start / push-on-finish loop with
exact commands and verification steps.

### Task 2: extend session-start hook
**Files:** `hooks/session-start/session-start.sh`
**Success criteria:** If a work order is detected (WO-* in CLAUDE.md or branch),
the hook prints a hint to pull traced context from gbrain; gracefully skips if
gbrain/codemax unavailable.

### Task 3: /gbrain command
**Files:** `commands/gbrain.md`
**Success criteria:** `/gbrain query <terms>` and `/gbrain sync` documented with
exact commands.

### Task 4: extend /pr skill
**Files:** `skills/pr/SKILL.md`
**Success criteria:** /pr includes a "sync living docs to gbrain" step before
opening the PR.

### Task 5: update README + plugin metadata
**Files:** `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
**Success criteria:** README documents the gbrain step; plugin version bumped;
skill count updated.

### Task 6: commit on branch + PR
**Success criteria:** changes on `feat/gbrain-integration`, PR opened against main.