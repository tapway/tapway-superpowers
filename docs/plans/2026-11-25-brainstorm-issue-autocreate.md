---
issue: 71
title: Create the issue from an accepted brainstorm
date: 2026-11-25
---

# Create the issue from an accepted brainstorm — Implementation Plan

**Goal:** A design decision published as `docs/brainstorming/*.md` enters the issue loop when it is accepted, without turning every exploratory note into an issue, and without a plan and its design doc opening two issues for the same decision.

**Problem:** `PLAN_RE` matches `docs/plans/*.md` only. An accepted design doc creates no issue (measured: `docs/brainstorming/native-auto-update.md` needed issue #67 created by hand), so design work that is settled but not yet planned sits outside the CodeMAX loop.

## Branch 1: feat/brainstorm-issue-autocreate

### Task 1.1: Path kinds and the acceptance gate

**Objective:** Distinguish plan paths from design paths, and let only an accepted design become an issue doc.

**Files:**
- Modify: `hermes/plugin/plan_issue.py`

**Acceptance criteria:**
- `doc_kind()` returns `plan` / `brainstorm` / `None`.
- `is_issue_doc()` is true for every plan, and for a design doc whose frontmatter says `status: accepted` (or `approved`).
- A `proposed`, `draft`, or frontmatter-less design doc is not an issue doc.

### Task 1.2: Creation, idempotency and inheritance

**Objective:** Create one issue for an accepted design, record it in frontmatter, and let a plan inherit the number when it links that design.

**Files:**
- Modify: `hermes/plugin/plan_issue.py`
- Test: `tests/test_plan_issue.py`

**Acceptance criteria:**
- Saving an accepted design doc opens one `codemax` issue and writes `issue: <n>` into its frontmatter.
- A second save calls `gh` zero times.
- A plan whose body links an issued design doc (`**Decision:** [Option B](../brainstorming/x.md)`) records that number and creates nothing.
- A non-accepted design doc returns `skipped="not-accepted"` and calls `gh` zero times.

### Task 1.3: A readable body for a design doc

**Objective:** Map the design-doc shape (Problem / Options / Recommendation / Acceptance) onto the issue contract instead of dumping the file.

**Files:**
- Modify: `hermes/plugin/plan_issue.py`
- Test: `tests/test_plan_issue.py`

**Acceptance criteria:**
- The body carries Summary, Why (Problem), What changes (Recommendation bullets), Acceptance criteria, and a collapsed full document labelled "Full design".
- A leading `Brainstorm:` is stripped from the title; the branch type still prefixes it.

### Task 1.4: Docs and surface parity

**Objective:** Say the new trigger where the hook is documented, in every mirrored copy.

**Files:**
- Modify: `docs/WORKFLOWS.md`, `README.md`, `skills/writing-plans/SKILL.md`, `codex/skills/writing-plans/SKILL.md`, `hermes/skills/writing-plans/SKILL.md`, `hermes/plugin/skills/writing-plans/SKILL.md`

**Acceptance criteria:**
- `scripts/sync-hermes-plugin-skills.sh --check` stays green.
- `tests/check_docs_consistency.py` stays green.

## Testing

- `python3 tests/test_plan_issue.py` — 40 checks, including the new brainstorm cases.
- `python3 tests/test_hermes_plugin.py`, `tests/test_hermes_install.py`, `tests/test_codex_port.py`
- `python3 tests/check_docs_consistency.py`
- `python3 -m pytest -q tests/test_docs_impact.py`