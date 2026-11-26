---
issue: 97
title: Describe each change in release notes
date: 2026-11-26
---

# Describe each change in release notes — Implementation Plan

> Written after the implementation (PR #96), to record what was built and why.

**Goal:** Every release describes each pull request merged since the previous tag of the same environment, using the PR's own description, so a `-prod` release covers all the staging work since the last `-prod`.

**Problem:** GitHub's generated notes are one title per PR. The `setup-project` template and `reusable-release.yml` took notes from `CHANGELOG.md` or set no starting tag, so staging changes were not guaranteed to appear in production notes.

**Out of scope:** AI-written summaries; replacing the `release.yml` of projects that were already set up; listing commits pushed without a PR.

## Branch 1: feat/descriptive-release-notes

### Task 1.1: Notes builder

**Files:**
- Create: `scripts/release_notes.py`
- Create: `tests/test_release_notes.py`
- Modify: `.github/workflows/skills-tests.yml`

**Acceptance:**
- [x] PRs are grouped into breaking changes, features, fixes and other changes
- [x] Text comes from `## Release note`, falling back to Summary, Problem, then the first paragraph
- [x] Release and sync PRs are left out, and `@` names do not notify anyone
- [x] An unreadable PR keeps its title

### Task 1.2: Release paths

**Files:**
- Modify: `.github/workflows/release.yml`
- Modify: `.github/workflows/reusable-release.yml`
- Modify: `setup-project` skill (all copies)

**Acceptance:**
- [x] Both workflows start from the previous same-environment tag
- [x] GitHub's generated notes are published if the script fails
- [x] `setup-project` writes a caller of `reusable-release.yml`
- [ ] First `-stg` release after merge shows described notes
- [ ] Reusable workflow exercised from a consumer repo

### Task 1.3: Authoring and docs

**Files:**
- Modify: `.github/pull_request_template.md`
- Modify: `pr` skill (all copies)
- Modify: `README.md`, `docs/DEPLOYMENT.md`, `docs/WORKFLOWS.md`

**Acceptance:**
- [x] New PRs are asked for a release note

## Decisions

- **No AI service in CI:** PR descriptions already hold the explanation, so no API key or generated wording is needed.
- **Reusable workflow declares no permissions:** declaring `pull-requests: read` would fail callers that grant only `contents`. Callers in private repos grant it themselves.
- **`release_notes_from_changelog` defaults to `false`:** a CHANGELOG section that is not updated repeats the same text on every release.
