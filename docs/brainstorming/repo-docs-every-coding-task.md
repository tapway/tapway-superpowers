# Brainstorm: Keep repo docs current on every coding task

**Status:** Recommended for discussion; no implementation or rollout approved.

## Problem and definition of done

Developers should not have to remember `/repo-docs` to keep shipped code and docs in sync. Every completed coding task should review its docs impact after the implementation is verified; every code PR should report the result, even if it was opened without Superpowers. Update only affected docs. A behavior-preserving refactor can legitimately leave the docs untouched, but it must say why. Read-only work and interim edits are not delivery events.

Two distinct guarantees are at issue: *the agent performed a docs review* and *a PR cannot merge without an explicit docs disposition*. A GitHub check can enforce the second; it cannot infer from Markdown whether an agent actually loaded a skill or whether prose is semantically correct. The proposed workflow should work for Claude Code (`/repo-docs`), Codex (`$repo-docs`), Hermes (`tapway-superpowers:repo-docs`), and people who use no agent.

## Platform context and routing

`tapway/platform-specs` at `bbb0f56` publishes `city-os` and `samurai-v2`. Both CodeMAX packs built (digests `4bff79a1bfbaefbd` and `54ab96fde221c50a`); neither lists `tapway/tapway-superpowers` or publishes a contract for this workflow. A targeted build for `tapway-superpowers` found no catalog. The [constitution](https://github.com/tapway/platform-specs/blob/bbb0f56/constitution.md) calls for one owner per interface, versioned consumer-facing contracts, and a spec before implementing changes across multiple components. Do not use a product ADR as a citation for shared developer tooling.

| Question | Evidence and consequence |
|---|---|
| Ownership and consumers | **Platform contract ID:** UNKNOWN (not retrieved: shared tooling is absent from both product catalogs). Superpowers owns `repo-docs` and the reusable workflow in this repo; project repos consume them. City Nexus already calls the shared workflow. |
| Existing capability | `/pr` and `/autoship` already require a docs pass; `/pr` already allows a no-change outcome. The balanced audit emits a warning for certain PRs and counts any `docs/` touch, not necessarily a relevant one. The reusable workflow checks plan issue frontmatter and brainstorm grounding, not docs impact. Reuse these surfaces rather than adding another standalone workflow. |
| Platform decisions | The constitution governs ownership and consumer contracts. UNKNOWN (not retrieved: no developer-tooling ADR was listed in either product pack). |
| Data model | The proposal uses Git diffs, repo-local docs, and PR metadata. It does not touch product entities, databases, or gbrain. UNKNOWN (not retrieved: no shared tooling data contract was published in either catalog). |
| Dependency direction | Existing code shows consuming repos call the reusable workflow; Superpowers should not import project code or write to product docs from CI. UNKNOWN (not retrieved: no catalog `consumes` edge covers this tooling integration). |

**Routing decision:** Extend the existing Superpowers skills and reusable workflow. Before implementation, specify the small docs-disposition contract and caller opt-in in a Superpowers design spec because the change has downstream consumers. Do not add a product catalog entry or a gbrain dependency merely to enable a docs gate.

## What remains unclear

Does “every coding work” mean every completed local task, even one never committed, or every change that can be merged? Assume a docs pass is expected at local completion and enforced at merge, not at each edit. If proof of review for unshipped local work is non-negotiable, that requires separate harness-level enforcement and a defined task boundary. The other open decision is rollout scope: pilot in Superpowers before enabling it in consuming repos.

## Option A — Make `repo-docs` part of coding-task completion

Give `repo-docs` an incremental review mode and make the standard verification workflow call it after code changes, before declaring the task complete. Keep `/pr` and `/autoship` as backstops; reuse an earlier review only if it covers the current change. Leave bootstrap mode for missing or outdated standard docs.

**Platform fit:** Keeps docs ownership in the changed repository and extends the existing skill rather than creating a competing one. The constitution's ownership principle applies; product catalog coverage does not extend here.

**Pros:** Small change; useful even before committing; no forced doc rewrites. **Cons:** An agent or developer can skip it; a direct PR still has no required docs outcome. **Complexity:** Low.

UNKNOWN (not retrieved: platform pack unavailable)

## Option B — Incremental task review plus a required PR docs check (recommended)

Use Option A for the authoring experience and add one outcome check to the existing reusable workflow, opt-in per consuming repo. For every PR whose diff includes maintained code or behavior-bearing configuration, require either `Docs: updated` with relevant docs paths changed in that PR, or `Docs: no impact` with a concrete reason for reviewers. `Not applicable` is derived by CI only for diffs outside the declared coding scope, not accepted from a checkbox as a bypass.

**Platform fit:** Preserves the consuming repo as owner of its docs and extends the existing caller/provider relationship. Treat the new input and PR format as a versioned shared workflow contract; no product data path changes.

**Pros:** Catches bare `gh pr create`, browser-created PRs, and human changes; produces evidence reviewers can inspect; no requirement for a meaningless doc diff. **Cons:** Needs protected-branch configuration, stable diff rules, PR metadata validation, and reviewer judgment for no-impact claims. Does not attest skill invocation. **Complexity:** Medium.

UNKNOWN (not retrieved: platform pack unavailable)

## Option C — Hard-stop each agent at local task completion

Add per-harness completion guards that require a docs-review result for the current worktree diff before allowing a coding turn to finish or a PR to open. That requires defining what ends a task, how the review is invalidated by further edits, how to avoid retry loops, and what happens after a restart or interrupted turn.

**Platform fit:** Extends Superpowers' harness integration rather than changing any product domain. The current plugin has pre/post-tool hooks; Hermes documents `post_llm_call` and `on_session_end` as observers, not portable controls that can resume a finished turn. A gate on PR commands alone cannot cover browser-created PRs.

**Pros:** Stronger feedback for local work where the harness can enforce it. **Cons:** Highest cross-harness maintenance; fails to cover humans and agents without installed hooks; still needs merge checks for repository-wide enforcement. **Complexity:** High.

UNKNOWN (not retrieved: platform pack unavailable)

## Evaluation

Scores are 1–5 (higher is better); platform fit reflects observed repo ownership and consumer direction, not an unpublished catalog contract.

| Option | Simplicity | Platform fit | Testability | Maintainability | Speed to implement |
|---|---:|---:|---:|---:|---:|
| A. Task workflow only | 5 | 4 | 3 | 5 | 5 |
| B. Task review + required PR check | 4 | 5 | 5 | 4 | 4 |
| C. Per-harness hard stop | 1 | 2 | 2 | 1 | 1 |

## Recommendation and acceptance checks

Choose **B**. Run the incremental review on the final task diff and reuse it at PR time only when still current. The canonical pass checks changes to public interfaces, major runtime behavior or error paths, schemas, configuration, deployment, and operator instructions; update the affected sections only. Do not run a full repo-docs regeneration on every bugfix, mark a plan/checklist edit as a docs update, or make success depend on a CodeMAX flag. Repo-local docs remain separate from GitHub Wiki and gbrain sync.

Pilot the shared check in Superpowers, initially as advisory to calibrate scope, then require that specific status on the branch where code first lands. Ensure docs-impact evaluation runs on the real PR diff and re-evaluates on code pushes and PR-description edits. Do not inherit the existing plan/brainstorm job's unconditional `base=master` skip for docs impact; any promotion exemption must depend on the actual protected merge path. Before rolling out to other repos, verify the specific required status and protect changes to the workflow and repository policy through review. A generic no-impact claim is not evidence; the reviewer checks the explanation against the current diff, with stale approvals dismissed on push. Do not imply that rerunning CI proves the author refreshed an earlier no-impact explanation.

Acceptance cases for implementation:

- A PR opened outside Superpowers with code changes and no disposition fails the required check.
- A behavior/config change with an affected canonical doc updated and named passes; a plan-only Markdown diff does not satisfy an `updated` disposition.
- A narrowly scoped internal fix with a specific `no impact` reason passes the mechanical check without a filler edit and remains subject to human review.
- A new commit re-runs the check on the new code diff and dismisses an approval for the old diff; editing the disposition also re-runs the check.
- A docs-only PR passes as not applicable; a relevant behavior-bearing config change does not skip review merely because no source extension changed.
- Claude Code, Codex, and Hermes expose the same incremental behavior by their native skill mechanism; routine completion does not regenerate unrelated docs or push to gbrain.

## Source trail

- [Superpowers `/pr` docs step](https://github.com/tapway/tapway-superpowers/blob/5714885/skills/pr/SKILL.md#L107-L125) and [`/autoship` docs step](https://github.com/tapway/tapway-superpowers/blob/5714885/skills/autoship/SKILL.md#L214-L224).
- [Balanced audit warning](https://github.com/tapway/tapway-superpowers/blob/5714885/.github/workflows/workflow-audit.yml#L124-L141), [shared workflow](https://github.com/tapway/tapway-superpowers/blob/5714885/.github/workflows/workflow-gate.yml), and [what its checker validates](https://github.com/tapway/tapway-superpowers/blob/5714885/scripts/workflow_gate.py#L1-L10).
- [City Nexus caller](https://github.com/tapway/city-nexus/commit/9aadf9770d1e0bc16dfe16d237e98d66037d3ae1), [platform catalog inventory](https://github.com/tapway/platform-specs/blob/bbb0f56/README.md), and [Hermes plugin hook contract](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks#plugin-hooks).
