# Brainstorm: Assimilating the ponytail pack into the flow pipeline

- **Date:** 2026-09-28
- **Status:** Proposed (awaiting plan)
- **Author:** flow-decide run, codemax profile
- **Companion docs:** `docs/plans/2026-09-24-ponytail-skill-pack-adoption.md` (vendoring — this doc does
  not revisit how the pack ships, only where it fires)

## 1. Problem restated

The pack was **vendored and installed** (v2.4.0) but **no flow phase references it**. Nothing in
`flow-decide` or `flow-build` names ponytail, so "adoption" currently means "six skills sit on disk and
fire by description match in whatever profile happens to hold them". The owner's question is precise:
*where does each of the six skills belong in the two phases?*

**User-facing goal:** every one of the six ponytail skills has either a **named phase, a trigger, and a
declared output**, or an explicit recorded decision that it has no home in this pipeline — so the next
person reading the flow knows where it fires and why.

**Scope locked via interview:**
- Install set is **@architect (brainstorming) + @planner (writing-plans) + @builder (build)** —
  deliberately **not** @decider (orchestrator) or @doubter (judge); neither writes code, so an
  auto-triggering coding persona is noise there and would muddy artifact-only review.
- `ponytail-audit` is **left unplugged in the pipeline** on purpose (see §3 D).
- **Ponytail never overrides a gate.** The port says it itself: *"Never a reason to skip gates: the
  Tapway pipeline (tdd, quality-gates, verification) still governs whether work is done."*

## 2. Current state (grounded survey)

| Fact | Measured value |
|---|---|
| Pack installed where | codemax 6/6, default 6/6, **decider/architect/planner/doubter/builder 0/6** |
| `/ponytail` resolves | yes in codemax + default; absent in all five bots |
| `/simplify-code` (flow-build Step 3) | live in **1 of 7 trees only** (`builder`); archived on the other six, including the root/default tree — measured per tree in doubt cycle 1 |
| Steps named by the flow | A: interview, brainstorming, writing-plans, doubt · B: tdd, verification, simplify, observe, security-audit, code-review, pr |
| Phase skills resolvable per bot | all five resolve every skill their phase names (truncation-proof re-check) |

**The gap, stated accurately (corrected in doubt cycle 1):** flow-build Step 3 already carries three
dated local corrections, and its fallback is *not* undefined — it is a **one-clause pass with no
procedure**: *"run a manual simplification pass over your own diff (dead code, duplication, speculative
abstraction) reported as `Simplify: manual pass (/simplify-code absent)`"*. What is missing is any
method. `ponytail-review` supplies the method (a defined, diff-scoped over-engineering review), so it
**replaces the fallback's procedure** — it does not invent the fallback. The same step also contains a
claim that is **false on this machine** (see §8), and its surviving text tells the operator to *make*
`/simplify-code` resolve by copying it in — the opposite order to this doc's rule.

## 3. Options

### A. Core rule only
Install `ponytail` in the three profiles; no reviewer, no ledger, no scoreboard.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** cheapest; one rule to reason about; nothing new in any phase's transcript.
- **Cons:** leaves the fallback's *procedure* undefined (see the corrected §2) — the defect goes unfixed; no stated
  way to *measure* whether it helped.
- **Complexity:** Low.

### B. Assimilate all six, each with a named home (recommended)
`ponytail` core as the standing rule in architect/planner/builder; `ponytail-review` as the defined
over-engineering pass at **Step 3 simplify** (and an optional second lens at Step 6); `ponytail-debt`
as the **per-repo counted ledger** — the only per-repo figure the pack itself authorises
(`grep -rnE '(#|//) ?ponytail:' .`) — surfaced in the Step 7 report; `ponytail-gain` as a
**benchmark card** that may be displayed but never presented as this-repo savings; `ponytail-audit` explicitly unplugged; `ponytail-help` as operator reference. **Step 6 is NOT adopted:**
the optional second lens floated earlier in this section is withdrawn — the over-engineering pass lives at
Step 3 only, so `/code-review` at Step 6 is unchanged `⟨F-c2⟩`.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** every skill lands somewhere accountable; gives the fallback a procedure; the measurement problem
  becomes tractable via the **counted ledger** (`ponytail-debt`) instead of asserted.
- **Cons:** more moving parts to keep coherent; needs an explicit ordering rule so `/simplify-code` (where
  present) still runs first and ponytail-review is the fallback, not a parallel duplicate.
- **Complexity:** Medium.

### C. Maximal — all five bots, audit as a gate
Install everywhere, run `ponytail-audit` over the repo on every feature.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** maximum coverage; audit results are genuinely repo-wide.
- **Cons:** a whole-repo audit per feature is ceremony that burns budget for nothing (this is exactly what
  the core rule's own rung-1 YAGNI test rejects); installing in the orchestrator/judge is noise.
- **Complexity:** High.

### D. No assimilation (status quo)
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** zero work; nothing changes.
- **Cons:** the pack fires or doesn't depending on which profile you happen to be in — non-deterministic
  behaviour, which is worse than either extreme.
- **Complexity:** None.

**Rejected because over-engineering:** `ponytail-audit` as a per-feature gate (option C). Its own rung-1
test fails it: a repo-wide audit on every feature does not need to exist. Its home is on-demand/scheduled
hygiene, recorded here rather than invented as a gate.
**Rejected because role conflict:** ponytail in @doubter. The doubt gate's value is artifact-only
adversarial review, unmuddied by the author's frame. Adding a code-writing persona to the judge trades
that away for nothing.
**Cycle-1 caveat:** the Step 3 fallback is needed in exactly the profiles the install set excludes, so the
fallback must be written as *"where the pack is present"*, and Phase B scoped to @builder — otherwise the
exclusion criterion and the fallback criterion contradict each other.
**Rejected because no artifact:** `ponytail-review`/`-audit` in Phase A. There is no diff and no repo
audit target at plan time — they review code, and at Step 2 the artifact is an option set.

## 4. Evaluation

| Option | Simplicity | Fixes the real defect | Measurable | Risk to gates |
|---|---|---|---|---|
| A | High | No | No | Low |
| **B** | Medium | **Yes** | **Yes** (counted `ponytail:` ledger, *not* `ponytail-gain`) | Low, with the ordering rule |
| C | Low | Partly | Yes | Medium (ceremony) |
| D | High | No | No | Low |

## 5. Recommendation

**Option B**, with two explicit rules written into the plan:

1. **Gate precedence:** where `/simplify-code` resolves, it runs and ponytail-review does not duplicate
   it; ponytail-review is the fallback that *defines* the manual pass. TDD's RED gate always precedes
   any ladder-climbing in Step 1.
2. **Measurement — corrected in doubt cycle 1.** `ponytail-gain` is a *fixed benchmark card*; its own text
   says "These are benchmark medians, not this repo. NEVER print a per-repo savings number … there is no
   real baseline to subtract from in a live repo", and it names `/ponytail-debt` as "the only real per-repo
   figures". So the Step 7 report gains the **counted ledger** (the `ponytail:` harvest), and any
   `ponytail-gain` output shown must be **labelled benchmark medians, never this-repo savings**.

**Assumptions that would change this recommendation:**
- If the measured builder A/B shows the RED gate degrading, the install set narrows to architect/planner
  only and the builder is reverted.
- If `ponytail-debt` turns out to have no writer in practice (nobody adds `ponytail:` markers), it is
  **carried with a decidable criterion** instead (plan task 10: >=1 real marker in a named target repo, or an
empty ledger whose command output is pasted). This supersedes v1's "drop it": the instrument's own text
(`ponytail-debt` line 48) says an empty ledger is a legitimate outcome, so carrying it is free while removing
it would discard the only per-repo figure the pack authorises `⟨F-c2⟩`.

## 6. Save output

This file. Committed with the plan and checklist as one docs commit.

## 7. Hand off

`writing-plans` → `docs/plans/2026-09-28-ponytail-flow-assimilation.md`.

## Red flags

- ❌ Putting ponytail in the doubt path, where it can launder an over-engineered plan past the gate
- ❌ Treating ponytail's "one small check" as a substitute for TDD's failing-test gate
- ❌ Running `ponytail-audit` per feature and calling the cost "quality"
- ❌ Presenting `ponytail-gain`'s benchmark medians as this-repo savings (the pack forbids it in writing)
- ❌ Editing only the tail of Step 3 while its surviving text still orders the operator to copy `/simplify-code` in

## 8. Doubt cycle 1 corrections

Revised after the Step 4 gate returned 48 findings across the three plans
(`docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`). Changes here are limited to statements that
were **false on this machine** or that inverted the pack's own rules; each was re-measured before it was
written. Findings that are plan-level (criteria shape, scope, ordering) are fixed in the plan, not here.
