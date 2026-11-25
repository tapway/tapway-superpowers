# Plan: Balanced Workflow-Audit Gate

## Goal
Make the tapway-superpowers workflow discipline **server-side mandatory** so it cannot be bypassed by skipping client hooks. Devs who modify code on their laptop and open a PR without the workflow's observable artifacts (plan, checklist, conventional commits) get their PR blocked.

## Approach
A GitHub Action (`workflow-audit.yml`) that runs on every PR and gates the merge on the workflow's fingerprints.

## Tiers (balanced profile)
| Check | Tier | Enforcement |
|---|---|---|
| Conventional commits | 🔴 BLOCK | exit 1 on any non-conventional commit |
| Secret scan | 🔴 BLOCK | exit 1 on secret pattern in diff |
| Plan doc (feat/refactor) | 🔴 BLOCK | exit 1 if feat/refactor PR lacks `docs/plans/*.md` |
| Checklist | 🟡 WARNING | PR comment, non-blocking |
| Docs touched | 🟡 WARNING | PR comment, non-blocking |

## Success criteria
1. A `feat:` PR with no plan doc → build fails (verified).
2. A clean conventional-commit PR with a plan doc → build passes.
3. No false failure on clean PRs (secret scan fixed for `set -e` + grep-exit-1).

## Files
- `.github/workflows/workflow-audit.yml` — the gate.
- This plan doc satisfies the gate's own plan requirement.