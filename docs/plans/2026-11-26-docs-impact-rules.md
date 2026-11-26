---
issue: 108
title: Docs impact asks for the document each kind of change affects
date: 2026-11-26
---

# Docs impact asks for the document each kind of change affects — Implementation Plan

**Goal:** A PR that changes the database schema, deployment, architecture or workflows must update the matching document, or say why it does not need to.

**Problem:** `Docs impact` only checks that a `Docs:` line exists and that listed files changed. A schema change passes with an unrelated document or any reason.

**Out of scope:** Judging whether a document's content is correct; writing missing documents in other repos; enabling the check in other repos.

## Branch 1: feat/docs-impact-rules

### Task 1.1: Rules per document

**Files:**
- Modify: `scripts/docs_impact.py`
- Create: `tests/test_docs_impact_rules.py`
- Modify: `.github/workflows/skills-tests.yml`

**Acceptance:**
- [x] Schema changes need `docs/DB_SCHEMA.md`, deployment changes need `docs/DEPLOYMENT.md`; otherwise the check fails
- [x] Architecture and workflow changes warn when their document is untouched
- [x] `Docs: no impact (<rule>) — reason` satisfies that rule only
- [x] A repo can set `database: false`, or override a rule, in `.docs-impact.json`, read from the target branch
- [x] Promotions, syncs, version syncs and Dependabot are exempt
- [x] Existing declarations keep working

### Task 1.2: Authoring and docs

**Files:**
- Modify: `repo-docs` skill (all copies)
- Modify: `.github/pull_request_template.md`, `README.md`

**Acceptance:**
- [x] Authors are told the per-rule line and which changes ask for which document

### Task 1.3: Remove the repo-wiki-writer skill

**Why:** It overlaps with `repo-docs`.

**Files:**
- Delete: `skills/repo-wiki-writer/`
- Modify: `pr` and `autoship` skills, `.claude-plugin/plugin.json`, `README.md`, `tests/check_docs_consistency.py`

**Acceptance:**
- [x] The skill is gone and no skill or doc tells the agent to run it
- [x] `/pr` and `/autoship` no longer require a GitHub Wiki update

## Decisions

- **A written reason is accepted:** forced edits produce filler, and reviewers can challenge the reason.
- **Warn first for architecture and workflows:** file paths cannot tell a design change from a small edit.
- **Schema applies only where there is storage:** it triggers on schema files, so a stateless repo is never asked.
