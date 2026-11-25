---
issue: 46
title: Auto-create the GitHub issue when a plan is written
date: 2026-11-18
---

# Auto-create the GitHub issue after a plan — Implementation Plan

**Goal:** Make the plan → GitHub issue step happen without anyone remembering it, in Claude Code, Codex and Hermes, and make the issue that comes out worth reading.

**Problem:** Today nothing enforces or triggers issue creation. The SessionStart hook is detect-only (its manifest description wrongly claims it auto-creates), `create-issue.sh` is only mentioned in the writing-plans skill prose, and the only blocking gate (`pre-pr-contract`) fires at `gh pr create` and only when the branch already commits a `docs/plans/*.md`. Measured: zero `codemax`-labelled issues in `tapway/codemax` and `tapway/tapway-superpowers`; the `codemax` label does not even exist in either repo; 13/13 codemax plans carry no `issue:` frontmatter.

**Out of scope:** changing the CodeMAX kanban schema; backfilling issues for historical plans.

## Branch 1: feat/plan-issue-autocreate

### Task 1.1: A plan → issue renderer that reads well

**Objective:** One stdlib module that turns any `docs/plans/*.md` into a title and a body with Summary / Why / What changes / Acceptance criteria / Test plan / Files / Links, plus a collapsed full plan.

**Files:**
- Create: `hermes/plugin/plan_issue.py`
- Test: `tests/test_plan_issue.py`

**Acceptance criteria:**
- AC-1.1.1 Every rendered body has `## Summary` and `## Acceptance criteria`, even for a plan with no recognisable sections.
- AC-1.1.2 Task headings become checklist bullets under `## What changes`, grouped by their parent section.
- AC-1.1.3 Title strips plan boilerplate ("— Implementation Plan") and takes its type prefix from the branch (`feat/` → `feat:`).
- AC-1.1.4 The rendered body stays under GitHub's 65536-char limit.

### Task 1.2: Issue creation that is idempotent and safe

**Objective:** `ensure_issue()` reuses an existing `codemax` issue for the branch, creates one otherwise, and always writes `issue: <n>` back into the plan frontmatter.

**Files:**
- Modify: `hermes/plugin/plan_issue.py`
- Test: `tests/test_plan_issue.py`

**Acceptance criteria:**
- AC-1.2.1 A plan that already has `issue:` never calls `gh`.
- AC-1.2.2 Branches `master`, `staging`, `main`, `prod` are skipped (no issue for a promotion branch).
- AC-1.2.3 `record_issue` inserts frontmatter when the plan has none, and preserves the rest of the file byte-for-byte.
- AC-1.2.4 A failed `gh issue create` (missing label, no auth) leaves the plan untouched and returns an error instead of half-writing.

### Task 1.3: PostToolUse hook in Claude Code and Codex

**Objective:** The moment a `docs/plans/*.md` write completes, create the issue and write the number back.

**Files:**
- Create: `hooks/post-plan-issue/post-plan-issue.sh`
- Create: `codex/hooks/post-plan-issue.sh`
- Modify: `hooks/hooks.json`, `codex/hooks.json.template`, `codex/install.sh`
- Test: `tests/test_plan_issue.py`, `tests/test_codex_port.py`

**Acceptance criteria:**
- AC-1.3.1 A write outside `docs/plans/` is ignored (exit 0, no output).
- AC-1.3.2 A write to a plan with no `issue:` triggers exactly one `gh issue create` and leaves `issue: <n>` in the file.
- AC-1.3.3 `TAPWAY_ISSUE_AUTOCREATE=0` disables it for one run.
- AC-1.3.4 The hook is registered for `Write|Edit|MultiEdit` in both manifests, and the Codex port ships the renderer it imports.

### Task 1.4: Hermes runs it in-process

**Objective:** `post_tool_call` creates the issue from inside Hermes, without shell hooks installed.

**Files:**
- Modify: `hermes/plugin/__init__.py`
- Test: `tests/test_hermes_plugin.py`, `tests/test_plan_issue.py`

**Acceptance criteria:**
- AC-1.4.1 A Hermes `write_file`/`patch` to a plan with no issue creates one.
- AC-1.4.2 The hook never raises: a failure logs and lets the tool result stand.

### Task 1.5: The same gate on the PR side, in Hermes

**Objective:** Hermes agents cannot open a PR whose plan lacks an issue, matching the Claude/Codex `pre-pr-contract` hook.

**Files:**
- Modify: `hermes/plugin/gates.py`
- Test: `tests/test_hermes_plugin.py`, `tests/test_workflow_contract_gate.py`

**Acceptance criteria:**
- AC-1.5.1 `gh pr create` with a changed plan lacking `issue:` → `{"action": "block"}`.
- AC-1.5.2 A non-git cwd, an empty diff, or a non-PR command → allowed.
- AC-1.5.3 `TAPWAY_PR_GATE=0` allows.

## Branch 2: feat/issue-gate-docs

### Task 2.1: Docs and manifests tell the truth

**Objective:** Remove the stale "auto-creates if missing" description, document the new behaviour, and keep the skill mirrors honest.

**Files:**
- Modify: `hooks/hooks.json`, `skills/writing-plans/SKILL.md`, `hermes/skills/writing-plans/SKILL.md`, `docs/team-guide.md`, `CHANGELOG.md`
- Test: `tests/check_docs_consistency.py`

**Acceptance criteria:**
- AC-2.1.1 No manifest claims a detect-only script creates issues.
- AC-2.1.2 The writing-plans skill says the issue is created automatically, with the manual command as the fallback.
- AC-2.1.3 `test_codex_port.py` and `check_docs_consistency.py` stay green.

## Testing

- `python -m pytest tests/test_plan_issue.py tests/test_workflow_contract_gate.py -q`
- `python tests/test_codex_port.py`
- `python tests/test_hermes_plugin.py`
- `python tests/check_docs_consistency.py`
- `python tests/test_phase3_hooks.py`
- Live proof: this plan's own issue is created by the new hook, then read back with `gh issue view`.