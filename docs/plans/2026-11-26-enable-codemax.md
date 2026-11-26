---
issue: 106
title: Enable the CodeMAX workflow in tapway-superpowers
date: 2026-11-26
---

# Enable the CodeMAX workflow in tapway-superpowers — Implementation Plan

**Goal:** The plan → issue → kanban flow applies to everyone working in this repo, not only to people who set an environment variable.

**Problem:** The repo has no `.codemax.yml`, so the hooks create issues only when `CODEMAX_ENABLED=1` or `CODEMAX_WORKFLOW=1` is set. Plans were written here and their issues had to be created by hand, without the `codemax` label.

**Out of scope:** Adding the file to other repos.

## Branch 1: chore/enable-codemax

### Task 1.1: Mark the repo as CodeMAX-enabled

**Objective:** Add the marker file the hooks look for.

**Files:**
- Create: `.codemax.yml`

**Acceptance:**
- [ ] `plan_issue.codemax_repo` returns true for the repo root without any environment variable
- [ ] Saving a new plan on a feature branch creates a `codemax` issue
- [ ] The brainstorm grounding gate is on by default in this repo
