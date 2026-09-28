# Doubt cycle 1 — reconciliation

**Date:** 2026-09-28 · **Gate:** flow-decide Step 4 · **Verdict: STOP — not sealed**

Three fresh-context reviewers (one per plan) returned **48 findings**: 17 against
`2026-09-28-ponytail-flow-assimilation`, 15 against `2026-09-28-platform-grounding-retrieval`, 16 against
`2026-09-28-flow-bot-orchestration`. Each received only ARTIFACT + CONTRACT, never the author's reasoning.

## Verification rule applied

A reviewer is a claim, not a verdict. Every load-bearing finding was re-checked by the author before
being accepted. **All spot-checks confirmed the reviewer was right**, including three findings that
refute the author's own survey:

| Check | Reviewer said | Re-measured | Result |
|---|---|---|---|
| `is_bot_mode_managed` | True (survey said False) | True for all 6 profiles + root | **reviewer right** |
| `hermes-bots` key | present in `ui_meta` | `ui_meta = {{'hermes-bots': {{}}}}` | **reviewer right** — earlier check read top-level keys only |
| `Bot Chat` title | reachable from CLI | decider's row is `source=cli` | **reviewer right** — "desktop-only" was false |
| `ponytail-gain` | forbids per-repo numbers | line 51 "NEVER print a per-repo savings number"; line 54 names `ponytail-debt` as the only per-repo figure | **reviewer right** — instrument mapping was inverted |
| sync script | dry-run + TARGETS includes decider/doubter | `APPLY=0`; `TARGETS="${TARGETS:-default decider architect planner doubter builder}"` | **reviewer right** |
| default tree + cron | fix would be clobbered | 3 bare command lines on the served copy; cron `9486afce96d1` enabled, reinstalls from repo source | **reviewer right** |
| log seal-grep | unsound | framework skill: "never substring matches on the transcript … the literal gate-seal string from the moment the run starts" | **reviewer right** |
| real catalogs | zero contracts | `provides: []` / `consumes: []` on every component | **reviewer right** |

No finding was discarded as a contract misread. Two were downgraded to trade-offs; the rest are
**Actionable**.

## Classification

### Actionable — plan 1 (ponytail assimilation)

| # | Finding | Sev | Fix |
|---|---|---|---|
| F1 | prescribed install command is dry-run, a no-op | high | add `--apply` |
| F2 | default TARGETS installs into decider+doubter, excludes codemax | high | pass `TARGETS="architect planner builder"` explicitly |
| F3 | removal criterion greps a string that never existed | high | target the real line-85 string |
| F4 | `ponytail-gain` cannot produce a per-repo number | high | Step 7 uses the **counted `ponytail:` ledger** (`ponytail-debt`); any `ponytail-gain` output must be labelled benchmark medians |
| F5 | fallback needed exactly where the pack is forbidden | high | scope Step 3's fallback to profiles that carry the pack; Phase B is @builder-only |
| F6 | `{{6 others}}` template expands to 5 paths | med | name all 7 trees explicitly |
| F7 | "minimum 3 options" is not in flow-decide and already 0 | med | move the guard to the file that owns the rule (`brainstorming`) |
| F8 | "byte-identical" names no baseline | med | back up codemax's pair first; hash before/after |
| F9 | task 4 criterion is prose | med | give the command + expected line |
| F10 | Step 6 lens in the brainstorm only | med | drop it or state it in all three twins |
| F11 | brainstorm contradicts itself on resolvability | med | one table row per profile, measured |
| F12 | "A3" is an undefined token | med | define the measurement or delete the reference |
| F13 | "0 on decider/doubter" cannot distinguish an exclusion from a broken probe | med | add a positive control (codemax must report 6) |
| F14 | backup criterion undecidable; codemax never backed up | med | name the directory + count |
| F15 | debt/help have no task | low | add tasks, or record them as deliberately unhomed |
| F16 | the surviving Step 3 text orders the opposite, and is false | med | rewrite the whole step, not the tail of it |
| F17 | criterion 6 has no file scope and is already true | low | name the paths |

### Actionable — plan 2 (grounding retrieval)

| # | Finding | Sev | Fix |
|---|---|---|---|
| F1 | `catalog:` can never appear in a pack | high | criterion becomes "the pack compiles and lists ADR ids + component roles" |
| F2 | installing the package DOES create a `codemax` console script | high | state the real protection: never activate or PATH that venv; assert the venv's bin content |
| F3 | the served copy is on the default tree and a cron reinstalls from repo source | high | add the default tree **and the 3 repo trees** to scope, or the fix is reverted weekly |
| F4 | task 7 criterion is prose | high | give the greps |
| F5 | the twin `check` command keeps the bare form | med | absence-check the whole `codemax platform-context` string |
| F6 | `TAPWAY_SPECS_DIR=` (empty) satisfies the criterion | med | require non-empty and equal to the clone path |
| F7 | "7 profiles" vs 6-profile globs | med | enumerate all 7 paths |
| F8 | "offline" is unfalsifiable; the network steps are unstated | med | run the build with the interface down; name the two network steps |
| F9 | benefit overstated — catalogs carry no contracts | med | narrow the claim to roles + ADR ids + constitution |
| F10 | plan and checklist disagree on work items | med | reconcile both directions |
| F11 | task 1 criterion too weak for tasks 3–4 | med | assert `platforms/<p>/catalog.yaml` |
| F12 | "gate stayed off" is vacuous | low | assert the hooks dir is absent too |
| F13 | `--help` exits 0 regardless; no ref pinned | low | pin the codemax SHA; assert the `platform-context` subgroup |
| F14 | venv would resolve `hermes-agent` 0.19.0 while the box runs 0.21.5 | med | record the drift and test the platform-context path only |
| F15 | "five UNKNOWN rows" is not true of the companion doc | low | state the real count |

### Actionable — plan 3 (orchestration)

| # | Finding | Sev | Fix |
|---|---|---|---|
| F1 | bot-mode survey is false | high | correct the survey; delete the "flip the key later" out-of-scope item |
| F2 | Option B's rejection reason is false | high | restate: B is *possible* from a CLI session titled `Bot Chat`; A is chosen for supervision semantics, not impossibility |
| F3 | no base SHA ⇒ "no commit" passes as "docs-only commit" | high | pin `git rev-parse HEAD` before each launch |
| F4 | `git show HEAD` can't see a multi-commit build phase | high | check the whole range base..HEAD; define a Phase B artifact check |
| F5 | criterion 5 unexercised; first-phase case undefined | high | define the genesis case; add a chain-level check |
| F6 | log seal-grep false-positives | high | structured evidence only; never grep the transcript for the seal |
| F7 | "7 pairs" vs 6 profiles | high | name the root pair |
| F8 | `state.db` has no author column | med | stop calling a session row authorship |
| F9 | flow skill still instructs the commit-author check the plan bans | med | include those lines in the edit |
| F10 | unscoped `git status` | med | scope to staged/authorised paths |
| F11 | `docs/flow/...` contract files have no task | med | add them to the file map + a task |
| F12 | propagated supervisor text lets a bot re-enter orchestration | med | add a depth guard and a re-entry task |
| F13 | no numeric bound | med | state seconds + the command that fails without it |
| F14 | "resolves its phase skills" passes on a shadowed name | med | add the ambiguity check |
| F15 | several criteria are prose; survey rows are stale | med | make each decidable; re-measure before the run |
| F16 | `-q "$(cat …)"` mangles arbitrary text; scripts unversioned | low | use `--query-file`; place the scripts in version control |

## Verdict

**STOP.** ~45 of 48 findings are Actionable, including three that contradict the authors' own survey and
one that invalidates a claimed measurement instrument. The three plans are **not sealable as written**;
they need a revision pass (cycle 2), after which the gate is re-run.

This is the gate working as designed: an unresolved Actionable finding at the plan stage is the cheapest
bug available, and three of these (the false bot-mode premise, the inverted gain/debt mapping, the
weekly cron that reverts the grounding fix) would each have cost more to discover in code.
