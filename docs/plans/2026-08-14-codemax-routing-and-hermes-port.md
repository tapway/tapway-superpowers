# Plan: Hermes codemax-gbrain port + wiki-vs-repo doc routing (writing-plans 7b/7c)

> **For Hermes:** Implemented task-by-task (TDD). This plan drives the feature work already on PR #27.

**Goal:** (1) Give Hermes users a first-class `codemax-gbrain` skill ported from the Claude copy; (2) add a **wiki-vs-repo doc routing** step to the `writing-plans` pipeline so every team member routes each document a plan produces to the right home (shared wiki/brain vs. repo docs) — while staying skippable for non-CodeMAX users and never blocking when the wiki is read-only.

**Status:** implemented (TDD), awaiting merge. **PR:** #27.

---

## Why

Our broader sweep found the brain-pull guidance existed only as a Claude Code
skill (`skills/codemax-gbrain/`); Hermes users had no agent-facing equivalent.
Separately, contributors had no in-pipeline decision point telling them whether
a produced document belongs in the shared wiki or the repo's own docs. The
decision lives in `wiki/CONTRIBUTING.md` (brain) but was never wired into the
planning step, so docs landed in the wrong home and got churned later.

## Goals / Non-goals

**Goals:**
- Ship a Hermes port of `codemax-gbrain` (pull at start, push at end), wired into both install scripts.
- Add `writing-plans` step **7c (wiki vs. repo routing)** to both Claude and Hermes copies.
- Add the missing **7b (GitHub issue after plan)** to the Claude copy (Hermes already had it).
- Add a "route before you sync" pointer to the `codemax-gbrain` Push step.

**Non-goals:**
- No new top-level skill (deliberately): routing is a checkpoint, not a workflow; re-encoding the table a third time would drift.
- No changes to the brain wiki (that's the separate `tapway-brain` PR #21).
- No release cut in this PR.

## Guardrail contract (must hold)

| Case | Routing step | Pipeline continues? |
|---|---|---|
| No CodeMAX (`CODEMAX_ENABLED` unset) | **Skips entirely**; repo-docs only | ✅ yes |
| CodeMAX + read-only wiki | Routes (decides); **never pushes to wiki `master`** (repo-docs or draft only) | ✅ yes |
| CodeMAX + full access | Routes + (optionally) writes wiki | ✅ yes |

A blocked/read-only wiki write must **never** block the pipeline.

## Design

1. **`hermes/skills/codemax-gbrain/SKILL.md`** — port of the Claude skill with
   per-tool sections where they diverge (MCP registration check, enforcement).
2. **`writing-plans` 7c** (both copies) — after 7b, before execution: route each
   produced doc wiki-vs-repo; single authoritative table referenced from
   `CONTRIBUTING.md` / `wiki-maintainer`, not duplicated.
3. **`writing-plans` 7b** — add to the Claude copy for parity.
4. **install scripts** — add `codemax-gbrain` to `hermes/install.sh` + `.ps1`.
5. **Docs/tests** — update skill counters (24→25), add
   `tests/test_wiki_repo_routing.py`.

## Tasks (completed)

| # | Task | Files | Status |
|---|---|---|---|
| 1 | RED: write `tests/test_wiki_repo_routing.py` (24 checks) | `tests/test_wiki_repo_routing.py` | ✅ RED 14 fail |
| 2 | Hermes `codemax-gbrain` port | `hermes/skills/codemax-gbrain/SKILL.md` | ✅ |
| 3 | Wire into install scripts | `hermes/install.sh`, `hermes/install.ps1` | ✅ |
| 4 | `writing-plans` 7b (Claude copy) | `skills/writing-plans/SKILL.md` | ✅ |
| 5 | `writing-plans` 7c routing (both copies) | `skills/writing-plans/SKILL.md`, `hermes/skills/writing-plans/SKILL.md` | ✅ |
| 6 | `codemax-gbrain` "route before sync" push pointer | `skills/codemax-gbrain/SKILL.md`, `hermes/skills/codemax-gbrain/SKILL.md` | ✅ |
| 7 | GREEN: full suite + `test_hermes_install.py` (105 ✓) | — | ✅ 24/24 |

## Verification

- `python3 tests/test_wiki_repo_routing.py` → **24 passed / 0 failed** (was 14 failed in RED).
- `python3 tests/test_hermes_install.py` → 105 passed.
- `bash -n hermes/install.sh` → OK.
- Full standalone suite green; single `test_phase3_hooks` failure is a **pre-existing** `plugin.json` `"hooks": []` stale-field check (isolated: fails on clean tree).