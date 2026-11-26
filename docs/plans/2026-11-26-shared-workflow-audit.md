---
issue: 102
title: Require a plan on every PR with a shared audit workflow
date: 2026-11-26
---

# Require a plan on every PR with a shared audit workflow — Implementation Plan

> Written after the implementation, to record what was built and why.

**Goal:** One `audit` workflow that any repo can call, requiring a plan on every non-routine PR.

**Problem:** The check existed only in this repo, blocked only `feat` and `refactor` PRs, scanned for secrets against `master` whatever the PR targeted, and would fail work packages that implement an already-merged plan.

**Out of scope:** Adding the caller file to the `samurai-*` and `city-*` repos, and making the check required in their branch rules.

## Branch 1: feat/shared-workflow-audit

### Task 1.1: Shared audit

**Files:**
- Create: `scripts/workflow_audit.py`
- Create: `tests/test_workflow_audit.py`
- Modify: `.github/workflows/workflow-audit.yml`
- Modify: `.github/workflows/skills-tests.yml`

**Acceptance:**
- [x] A PR passes if it adds or updates `docs/plans/*.md`, or has a `Plan:` line naming a plan on the target branch
- [x] Promotions, sync-backs, release version syncs and Dependabot PRs are exempt; forks never are
- [x] Added secrets and non-conventional commits still block, compared with the PR's target branch
- [x] The workflow can be called from other repos and needs only `contents: read`
- [ ] Exercised from a consumer repo after promotion to `master`

### Task 1.2: Authoring and docs

**Files:**
- Modify: `writing-plans` and `pr` skills (all copies)
- Modify: `.github/pull_request_template.md`, `README.md`

**Acceptance:**
- [x] A plan shared by several work packages is merged first, and each package PR links it
- [x] Package branches start from the integration branch

## Decisions

- **Link or change:** requiring the plan in every diff would force pointless edits on work packages.
- **Annotations instead of PR comments:** the previous check commented on every push and needed `pull-requests: write`.
- **Script fetched from `master`:** callers pick up rule changes without a new PR in each repo.
