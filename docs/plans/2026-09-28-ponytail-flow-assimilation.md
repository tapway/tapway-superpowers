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
| `builder` | live | `/simplify-code`, unchanged — **and the fallback is inert here by design** |
| root, architect, planner, codemax, decider, doubter | archived only | `ponytail-review` fallback **in the three pack profiles**; codemax/decider/doubter carry no pack, so Step 3 reports `/simplify-code absent` as today. **The fallback is therefore live in exactly architect + planner; in builder it is inert because `/simplify-code` resolves.** One table, measured per tree — the earlier v2 text named two different triples `⟨F-c2⟩` |

`⟨F11⟩`

## Files

| Path | What |
|---|---|
| **the root tree** `~/.hermes/skills/` **plus** `~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills/` (6 profiles + root = the 7 skill trees) | **MODIFY** — repo-relative `skills/tapway/ponytail{,-review,-audit,-debt,-gain,-help}/` created in **architect, planner, builder only**, via `TARGETS="architect planner builder" … --apply --ponytail` |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-build/SKILL.md` | **MODIFY** — Step 3 rewritten (§Approach 2); Step 7 ledger line; gate-precedence note |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-decide/SKILL.md` | **MODIFY** — Step 2 gains the YAGNI bullet (an option set must include "do nothing" / "the smallest thing"); Step 3 gains a task-cut note |
| the 5 profile pairs + the root pair | **MODIFY** — propagate (back up all 7 first) `⟨F6⟩` `⟨F14⟩` |
| `hermes-flow-pipeline/SKILL.md` — **all 7 trees** (`~/.hermes/skills/` + 6 profiles), not codemax alone: 6 of the 7 already differ from codemax's (measured: codemax `d0a2c705…` vs `36440a43…` ×6), so a codemax-only edit reaches no bot | **MODIFY** — the map + unplugged-audit + not-adopted-Step-6 |
| `docs/plans|checklists/2026-09-28-ponytail-flow-assimilation*.md` | **CREATE** — this plan + checklist |
| `~/.hermes/profiles/codemax/backups/flow-pairs-<ts>/` | **CREATE** — the 7 pre-change backups that make "byte-identical" falsifiable `⟨F8⟩` |

**Known limitation (accepted):** the flow pair is unversioned profile config; the backup is the substitute
for a diff.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **A weekday cron rewinds the working checkout** | `codemax-skills-sync.sh:50` runs `git reset -q --hard origin/master` in `~/tapway-superpowers` whenever master's tip moves. **This branch is not on origin/master**, so an unpushed commit is destroyed and the tree reverts. The plan set itself and (for the grounding plan) the repo-tree edits are exposed. Owner decision required: push/merge the branch, or exclude the repo from that cron. Until then the plan set is backed up outside the repo at `~/.hermes/profiles/codemax/backups/flow-plans-<ts>/`. |
| ponytail degrades the RED gate in @builder | Gate precedence in Step 1; evidence = counted ledger + **≥3 builder runs logged** — a criterion task 12 now owns (`ls` the run logs and
assert the count, and that each shows the RED gate observed) — plus **revert = `rm -rf` the 6 pack dirs in
the 3 target profiles**, also asserted in task 12 `⟨F-c2⟩`. (v2 named this evidence and tasked nothing.) |
| Step 3 runs both the skill and the fallback | The fallback runs **only** where `/simplify-code` does not resolve `⟨F5⟩` |
| The install command silently does nothing | `--apply` required; the criterion asserts a **created directory** `⟨F1⟩` |
| The pack lands in the excluded bots via the script default | `TARGETS` set explicitly; criterion asserts 0 in decider/doubter **with a positive control** `⟨F2⟩` `⟨F13⟩` |
| A savings claim is invented | Only the counted ledger may be reported as a repo figure `⟨F4⟩` |
| `ponytail-debt` has no writer | It is load-bearing: a task asserts ≥1 marker, or records the ledger as intentionally empty `⟨F15⟩` |
| Unversioned edits drift across 7 trees | Propagate from codemax; md5 all 7; backups asserted **per tree** `⟨F14⟩` |
| **A pack-category writer resolves its own destination** | `hermes/install.sh:87-107` sets `DEST_ROOT` from `hermes config path`/`HERMES_HOME`, and `install_local` does `rm -rf` then `cp -a` — so pack edits in whichever tree it resolves to are temporary. The plan records which tree that is before editing, rather than assuming the 7 are static `⟨F-c2⟩` |

## Tasks

| # | Task | Verifiable success criterion |
|---|---|---|
| 1 | Install into the 3 profiles | `TARGETS="architect planner builder" bash ~/.hermes/scripts/tapway-v240-sync.sh --apply --ponytail`; then `test -d ~/.hermes/profiles/architect/skills/tapway/ponytail` (a **created path**) `⟨F1⟩` |
| 2 | Prove the install set | architect/planner/builder → `grep -c '│ ponytail'` = 6; **positive control** codemax = 6; decider + doubter = 0 `⟨F13⟩` |
| **0** | **Back up all 7 pairs BEFORE any write** | 7 backup dirs, one **per tree** — assert distinct parents, not a bare count: `for t in ~/.hermes/skills ~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills; do test -f "$t/backups/flow-pairs-<ts>/flow-build.SKILL.md" \|\| echo "MISSING: $t"; done` prints nothing. A single directory holding 7 files satisfies a bare `\| wc -l` = 7 and proves nothing `⟨F14⟩` `⟨F-c2⟩`. **Moved to task 0 because task 1's own command re-syncs flow wrappers as a side effect** — run in the written order, the "pre-change" baseline would be captured after the change |
| 4 | Rewrite the whole Step 3 | contains `ponytail-review`; **absent**: `run a manual simplification pass over your own diff`, `exists only on the` … `default` in the same paragraph, and the `cp -R` copy-in instruction `⟨F3⟩` `⟨F16⟩` — each grep proven to fail on the v1 fixture |
| 5 | Gate precedence in Step 1 | the ordering sentence is present; the concrete paths are `BK=~/.hermes/profiles/codemax/backups/flow-pairs-<ts>/flow-build.SKILL.md` and
`NEW=~/.hermes/profiles/codemax/skills/openclaw-imports/flow-build/SKILL.md`; the guard form is
`test -f "$BK" && test -f "$NEW"` || { echo 'REFUSE: baseline missing'; exit 1; }` then
`diff -u "$BK" "$NEW" | grep -c '^-[^-]'` must be **0** for the TDD gate block `⟨F8⟩`.
**Do not use bare `diff`**: it exits **1** when the two files legitimately differ (they must differ after
task 4), and when the baseline is missing the removed-line count reads `0` — a **false PASS**. The proven
idiom already exists at `~/.hermes/scripts/tapway-v240-sync.sh:64-72`; this criterion was measured to
fail-open without it. Labelled regression guard, but now one that can actually run. |
| 6 | Step 7 ledger line | the fenced Report block contains a `ponytail:` ledger line; the step names `ponytail-debt`; `ponytail-gain` appears only with a "benchmark medians" qualifier `⟨F4⟩` `⟨F9⟩` |
| 7 | flow-decide Steps 2–3 | flow-decide names the YAGNI bullet (failable: the string is absent today). The "minimum 3 options" rule is **not** re-asserted here: it already holds in all 7 trees of `brainstorming/SKILL.md` and no task touches that file, so it would be a pre-satisfied check — it is recorded below as a **labelled regression guard** instead `⟨F7⟩` `⟨F-c2⟩` |
| 8 | Step 6 recorded as not adopted | the not-adopted sentence appears in plan + brainstorm + checklist `⟨F10⟩` |
| 9 | Propagate + verify | **failable half:** for each of the 6 non-codemax trees, `diff -u <backup> <new> \| grep -c '^-[^-]'` ≥ 1 on the Step 3 region — i.e. the rewrite actually reached that tree. **Guard half:** all 7 pairs md5-identical *after* propagation (identical at HEAD today, so this alone can never fail) `⟨F6⟩` `⟨F-c2⟩` |
| 10 | debt/help accounted for | run the instrument's **own** scan against a **named target repo** (`TARGET=<repo>`): `grep -rnE '(#\|//) ?ponytail:' "$TARGET" --exclude-dir={node_modules,.git,build,dist} \| grep -v '/skills/ponytail'`. Pass with **either** ≥1 real marker **or** an empty result whose command output is pasted into the report — the disjunction is what the instrument's own text permits (`ponytail-debt` line 48: an empty ledger is legitimate). The plan's earlier bare idiom was rejected because it matches prose *inside the vendored pack itself* (3 hits measured in `tapway-superpowers`) and lacks the instrument's exclusions `⟨F15⟩` `⟨F-c2⟩`. `ponytail-help` named as operator reference |
| 11 | Record in the flow skill | `hermes-flow-pipeline` contains the map + unplugged-audit + not-adopted-Step-6, **in all 7 trees** (grep each) |
| 12 | **Gate-health evidence** | ≥3 builder runs logged after the pack lands: `ls <run-log-dir> \| grep -c builder` ≥ 3 **and** each log shows the RED gate observed. Also assert the documented revert: the 6 pack dirs exist before and are gone after `rm -rf` in a scratch copy |
| 13 | Record the writer's destination | `hermes config path` output recorded in this plan before any pack edit, so the tree the recurring writer refreshes is known rather than assumed |

## Success criteria

1. `grep -c '│ ponytail'` = 6 for architect/planner/builder, 0 for decider/doubter, **with codemax asserted
   at 6 as a positive control** so a broken probe cannot read as a clean exclusion `⟨F13⟩`.
2. Step 3 contains a procedure and none of the three v1 strings, each grep proven able to fail.
3. No line removed from the TDD gate block, proven with `diff -u | grep -c '^-[^-]'` = 0 **after a
   `test -f` preflight on both paths** — the preflight is required because a missing baseline otherwise
   reads as a PASS. (*labelled regression guard; the other criteria are the RED evidence*) `⟨F8⟩`
4. All 7 pairs md5-identical *(guard)* **and** each of the 6 non-codemax trees proven changed against its
   own backup *(failable)*; backups asserted **per tree**, not by count `⟨F14⟩` `⟨F-c2⟩`.
5. Step 7's report carries the counted ledger; **no** criterion permits a per-repo number from
   `ponytail-gain` `⟨F4⟩`.
6. *(labelled regression guard — zero ponytail strings exist in both flow files today, so this cannot fail
   from the work)* `ponytail-audit` appears in **no** flow step — grep scoped to **both flow files**, not the
   whole skill tree where `ponytail-help` legitimately names it `⟨F17⟩`.
7. Step 6 is recorded as not adopted in all three twins `⟨F10⟩`.

## Out of scope

- Moving the flow pair into the repo (a distribution change).
- Resurrecting `/simplify-code` from `.archive/` on any profile — the prune is deliberate.
- Any change to ponytail rule text; a higher-n A/B re-run.
- `~/.claude/skills/flow-{decide,build}/` — a **third** copy of the flow pair, outside `~/.hermes`, stale
  and unmentioned by v2 (measured md5 differs from codemax's). Explicitly out of scope here, so the
  "7 trees" claim is not mistaken for "every copy on the machine" `⟨F-c2⟩`.
- Wiring `ponytail-audit` as a gate `⟨F15⟩`.
- The bot handoff mechanism (`2026-09-28-flow-bot-orchestration.md`).
