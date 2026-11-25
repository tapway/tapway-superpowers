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