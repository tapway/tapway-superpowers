---
issue: 65
title: Repo docs impact pilot
---

## Plan: Repo docs impact pilot

**Goal:** Review docs at coding-task completion and expose a docs-impact check on Tapway Superpowers PRs before making it a required check.

**Tech stack:** Python standard library, Git, GitHub Actions, Markdown skills.

**Related skills:** tdd, repo-docs, verification, pr. **Estimated tasks:** 3.

**Decision:** [Option B](../brainstorming/repo-docs-every-coding-task.md). Use the existing reusable workflow, not separate per-agent hooks or a new mandatory workflow. The docs outcome is evidence for reviewers, not proof an agent skill ran.

### Assumptions

- Pilot on `tapway/tapway-superpowers` only; recent feature PRs target `master`. Do not edit branch rules or activate downstream callers during the pilot.
- Missing/invalid docs dispositions should warn during the pilot. A compatible, default-off boolean input `enforce_docs_impact` is the opt-in for a failing status; making that status required is a separate repo settings decision.
- The docs protocol and supported skill behavior are version-locked to Superpowers and belong in this repo. No product catalog, wiki, database, or gbrain changes.

### Tasks

1. **Build the checker** (`tests/test_docs_impact.py`, `scripts/docs_impact.py`). First exercise a Git diff with a runtime/config change, docs-only diff, missing/duplicate/malformed declaration, no-impact reason, updated paths not in the diff, planning-only and deleted docs. Then implement a CLI taking the PR event path and `--advisory`; use validated base/head SHAs with `git diff --name-status --no-renames -z base...head`. Accept a single plain `Docs: updated — <comma-separated paths>` listing added/modified maintained docs, or `Docs: no impact — <specific reason>`. CI derives not applicable from the diff. Default to treating unknown non-docs paths and skill instructions as coding changes. An unreadable event or failed diff is an operational failure, not a pass.
2. **Wire the advisory job and instructions** (`.github/workflows/workflow-gate.yml`, `.github/workflows/skills-tests.yml`, `.github/pull_request_template.md`, `docs/WORKFLOWS.md`). Trigger on open, push, reopen, and edit; use a standalone docs-impact job in the existing workflow that does not inherit plan/brainstorm promotion skips. Verify event and mode on a real Git repository fixture, workflow syntax, compatibility with opt-out callers, and that the check cannot execute PR text. Document rollback: remove advisory opt-in/self enablement; no existing contract check changes.
3. **Make docs review part of workflow completion** (`{skills,codex/skills,hermes/skills,hermes/plugin/skills}/{repo-docs,verification,pr,autoship}/SKILL.md` where applicable). Put one incremental procedure in `repo-docs` per harness; invoke it from verification for completed coding tasks and reuse the decision or review again in shipping workflows when the scope changes. Check that bootstrap remains available, unchanged docs do not get regenerated, PR instructions emit the declared format, and the Hermes skill package exactly mirrors its source.

### Pilot exit criteria

Verify the opening PR's advisory check directly and evaluate a PR without a docs declaration and one updated by editing the body. After reviewers have seen representative code and docs-only PRs, decide whether to turn on enforcement and require the status; do not do either as part of this pilot.
