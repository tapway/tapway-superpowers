# Plan: Assimilate the ponytail pack into the flow pipeline

> **Revision v2 — post doubt-cycle-1.** v1 returned 17 findings, all Actionable; each fix is marked `⟨F#⟩`. Record: `docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`.

Implements `docs/brainstorming/ponytail-flow-assimilation.md` (Option B).
**Verified baselines (measured 2026-09-28):** pack live in codemax + the root tree only; `hermes -p <p>
skills list | grep -c '│ ponytail'` = 6 for codemax, 0 for the other five; `/simplify-code` live in the
**builder** tree only; the sync script is **dry-run by default** with `TARGETS` defaulting to
`default decider architect planner doubter builder`.

## Goal

Give each of the six ponytail skills a named home in `flow-decide`/`flow-build` — or a recorded decision
that it has none — and give flow-build Step 3's fallback **a procedure**, without letting ponytail override
any existing gate.

## Approach

1. **Install set — explicit, never a default.** `@architect`, `@planner`, `@builder` only. `⟨F2⟩` `TARGETS`
   must be set explicitly: the script's default installs into **@decider and @doubter** (the two profiles
   this plan excludes) and **omits codemax**. `⟨F1⟩` `--apply` is required: it is dry-run by default and
   otherwise reports success having written nothing.
2. **Step 3 gets a procedure — the whole step is rewritten.** `⟨F16⟩` Not just its tail: the surviving text
   tells the operator to `cp -R` `/simplify-code` in *first* (the opposite order to this plan's rule) and
   asserts something **false here** ("exists only on the `default` profile, and neither `codemax` nor any
   bot profile ships it" — measured: live in the **builder** tree, archived on the root tree).
   Rewritten rule: use `/simplify-code` where it resolves; otherwise run `ponytail-review` over the diff as
   the defined pass, reported as `Simplify: ponytail-review (fallback)`.
3. **The fallback is scoped to the pack.** `⟨F5⟩` It applies *where the pack is present*
   (architect/planner/builder). Flow-build is a Phase B / @builder artifact, so the operative instruction
   lives on the builder path; the other copies carry the same text with the "where present" qualifier.
4. **Measurement uses the counted ledger, not the benchmark card.** `⟨F4⟩` `ponytail-gain` says *"These are
   benchmark medians, not this repo. NEVER print a per-repo savings number … there is no real baseline to
   subtract from in a live repo"* and names `/ponytail-debt` as *"the only real per-repo figures"*. Step 7's
   report carries the **`ponytail:` ledger** (`grep -rnE '(#|//) ?ponytail:'` with ceiling/upgrade-path
   columns). `ponytail-gain` output may appear **only** labelled as benchmark medians.
5. **Step 6 is explicitly not adopted.** `⟨F10⟩` v1's brainstorm floated an optional Step 6 lens; plan and
   checklist were silent. Decision: **not adopted** — the over-engineering pass lives at Step 3 only.
   Recorded in all three twins.
6. **`ponytail-audit` deliberately unplugged; `ponytail-help` is operator reference, no phase.** `⟨F15⟩`

## Per-profile Step 3 path (measured, so the deliverable is auditable)

| Tree | `/simplify-code` | Step 3 path taken |
|---|---|---|
| `builder` | live | `/simplify-code`, unchanged |
| root, architect, planner, codemax, decider, doubter | archived only | `ponytail-review` fallback **in the three pack profiles**; the other three report `/simplify-code absent` as today |

`⟨F11⟩`

## Files

| Path | What |
|---|---|
| **the root tree** `~/.hermes/skills/` **plus** `~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills/` (6 profiles + root = the 7 skill trees) | **MODIFY** — repo-relative `skills/tapway/ponytail{,-review,-audit,-debt,-gain,-help}/` created in **architect, planner, builder only**, via `TARGETS="architect planner builder" … --apply --ponytail` |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-build/SKILL.md` | **MODIFY** — Step 3 rewritten (§Approach 2); Step 7 ledger line; gate-precedence note |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-decide/SKILL.md` | **MODIFY** — Step 2 gains the YAGNI bullet (an option set must include "do nothing" / "the smallest thing"); Step 3 gains a task-cut note |
| the 5 profile pairs + the root pair | **MODIFY** — propagate (back up all 7 first) `⟨F6⟩` `⟨F14⟩` |
| `~/.hermes/profiles/codemax/skills/software-development/hermes-flow-pipeline/SKILL.md` | **MODIFY** — the map + unplugged-audit + not-adopted-Step-6 |
| `docs/plans|checklists/2026-09-28-ponytail-flow-assimilation*.md` | **CREATE** — this plan + checklist |
| `~/.hermes/profiles/codemax/backups/flow-pairs-<ts>/` | **CREATE** — the 7 pre-change backups that make "byte-identical" falsifiable `⟨F8⟩` |

**Known limitation (accepted):** the flow pair is unversioned profile config; the backup is the substitute
for a diff.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| ponytail degrades the RED gate in @builder | Gate precedence in Step 1; evidence = counted ledger + ≥3 logged builder runs; revert = delete 6 dirs |
| Step 3 runs both the skill and the fallback | The fallback runs **only** where `/simplify-code` does not resolve `⟨F5⟩` |
| The install command silently does nothing | `--apply` required; the criterion asserts a **created directory** `⟨F1⟩` |
| The pack lands in the excluded bots via the script default | `TARGETS` set explicitly; criterion asserts 0 in decider/doubter **with a positive control** `⟨F2⟩` `⟨F13⟩` |
| A savings claim is invented | Only the counted ledger may be reported as a repo figure `⟨F4⟩` |
| `ponytail-debt` has no writer | It is load-bearing: a task asserts ≥1 marker, or records the ledger as intentionally empty `⟨F15⟩` |
| Unversioned edits drift across 7 trees | Propagate from codemax; md5 all 7; 7 backups asserted by count `⟨F14⟩` |

## Tasks

| # | Task | Verifiable success criterion |
|---|---|---|
| 1 | Install into the 3 profiles | `TARGETS="architect planner builder" bash ~/.hermes/scripts/tapway-v240-sync.sh --apply --ponytail`; then `test -d ~/.hermes/profiles/architect/skills/tapway/ponytail` (a **created path**) `⟨F1⟩` |
| 2 | Prove the install set | architect/planner/builder → `grep -c '│ ponytail'` = 6; **positive control** codemax = 6; decider + doubter = 0 `⟨F13⟩` |
| 3 | Back up all 7 pairs | `find ~/.hermes -path '*backups/flow-pairs-*' -name 'flow-decide*' | wc -l` = 7 `⟨F14⟩` |
| 4 | Rewrite the whole Step 3 | contains `ponytail-review`; **absent**: `run a manual simplification pass over your own diff`, `exists only on the` … `default` in the same paragraph, and the `cp -R` copy-in instruction `⟨F3⟩` `⟨F16⟩` — each grep proven to fail on the v1 fixture |
| 5 | Gate precedence in Step 1 | the ordering sentence is present; `diff <backup> <new>` removes **no line** from the TDD gate block `⟨F8⟩` — a **labelled regression guard**: green by design, because it asserts that an untouched block stayed untouched. It is not RED evidence and must not be counted as such. |
| 6 | Step 7 ledger line | the fenced Report block contains a `ponytail:` ledger line; the step names `ponytail-debt`; `ponytail-gain` appears only with a "benchmark medians" qualifier `⟨F4⟩` `⟨F9⟩` |
| 7 | flow-decide Steps 2–3 | flow-decide names the YAGNI bullet; the "minimum 3 options" guard is asserted on **`skills/tapway/brainstorming/SKILL.md`** (the file that owns it), not on flow-decide `⟨F7⟩` |
| 8 | Step 6 recorded as not adopted | the not-adopted sentence appears in plan + brainstorm + checklist `⟨F10⟩` |
| 9 | Propagate + verify | all 7 pairs md5-identical to codemax's; 7 backups present `⟨F6⟩` |
| 10 | debt/help accounted for | ≥1 `ponytail:` marker harvested, or an empty ledger recorded as intended; `ponytail-help` named as operator reference `⟨F15⟩` |
| 11 | Record in the flow skill | `hermes-flow-pipeline` contains the map + unplugged-audit + not-adopted-Step-6 |

## Success criteria

1. `grep -c '│ ponytail'` = 6 for architect/planner/builder, 0 for decider/doubter, **with codemax asserted
   at 6 as a positive control** so a broken probe cannot read as a clean exclusion `⟨F13⟩`.
2. Step 3 contains a procedure and none of the three v1 strings, each grep proven able to fail.
3. No line removed from the TDD gate block, proven against the pre-change backup by diff `⟨F8⟩` (*labelled regression guard — green on write by design; the other six criteria are the RED evidence*).
4. All 7 pairs md5-identical; the backup **count** is asserted, not assumed `⟨F14⟩`.
5. Step 7's report carries the counted ledger; **no** criterion permits a per-repo number from
   `ponytail-gain` `⟨F4⟩`.
6. `ponytail-audit` appears in **no** flow step — grep scoped to **both flow files**, not the whole skill
   tree where `ponytail-help` legitimately names it `⟨F17⟩`.
7. Step 6 is recorded as not adopted in all three twins `⟨F10⟩`.

## Out of scope

- Moving the flow pair into the repo (a distribution change).
- Resurrecting `/simplify-code` from `.archive/` on any profile — the prune is deliberate.
- Any change to ponytail rule text; a higher-n A/B re-run.
- Wiring `ponytail-audit` as a gate `⟨F15⟩`.
- The bot handoff mechanism (`2026-09-28-flow-bot-orchestration.md`).
