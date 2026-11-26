---
issue: 112
title: Issue generator posts only what was written and approved
date: 2026-11-26
---

# Issue generator posts only what was written and approved — Implementation Plan

**Goal:** A GitHub issue says only what the plan or design says, and is posted only after the user approves it.

**Problem:** The team reported that issues are posted without review, get invented acceptance criteria and test plans, leak local paths, miss the plan's detail when it shares a design issue, and that the grounding gate skips absolute paths.

**Out of scope:** Changing the CodeMAX server or the `codemax` CLI.

## Branch 1: fix/issue-generator

### Task 1.1: Draft first, post after approval

**Files:**
- Modify: `hermes/plugin/plan_issue.py`
- Modify: `hooks/post-plan-issue/post-plan-issue.sh`

**Acceptance:**
- [x] Saving a plan or accepted design posts nothing and says how to preview and post
- [x] `--post` creates the issue, or updates the design issue the plan shares with its tasks
- [x] A repo without `.codemax.yml` is told so

### Task 1.2: Say only what was written

**Files:**
- Modify: `hermes/plugin/plan_issue.py`

**Acceptance:**
- [x] Missing acceptance criteria or test plan read "Not specified"
- [x] Bold `Acceptance` and `Test plan` blocks are read; other headings containing "test" are not
- [x] Only repo-relative paths appear, and a design doc is labelled "Design"

### Task 1.3: Gates

**Files:**
- Modify: `hermes/plugin/gates.py`
- Modify: `hooks/pre-brainstorm-ground/pre-brainstorm-ground.sh`
- Modify: `brainstorming` and `writing-plans` skills (all copies), `README.md`, `docs/WORKFLOWS.md`

**Acceptance:**
- [x] The grounding gate checks absolute paths
- [x] Both gates find `.codemax.yml` at the repo root and honour `CODEMAX_ENABLED`
- [x] The skills say how to install `codemax` and to get approval before posting

## Test plan

- `python3 tests/test_plan_issue.py`
- `./scripts/sync-hermes-plugin-skills.sh --check`
