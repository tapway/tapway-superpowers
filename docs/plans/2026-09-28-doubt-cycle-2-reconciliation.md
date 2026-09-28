# Doubt cycle 2 — reconciliation

**Date:** 2026-09-28 · **Gate:** flow-decide Step 4 · **Verdict: STOP — handed back, not sealed**

Three fresh reviewers (one per plan) re-reviewed the v2 documents. **~60 findings** (24 + 17 + 21). The
contract for this cycle explicitly demanded that every criterion be proven able to fail, and that is where
the reviewers concentrated — so a large share of the findings are defects in the *fixes*, not in v1.

## The three classes that matter

**1 · My own fixes reproduced the defect they were fixing.** v1's worst class was criteria that are already
true. v2 replaced them with criteria that are also already true, or that cannot run green:

| Criterion | The defect |
|---|---|
| all flow pairs md5-identical | already identical at HEAD — green before any work |
| `peer messaging is CLOSED` absent | absent in 6 of 7 copies already |
| `ponytail-audit` in no flow step | zero ponytail strings exist today |
| repo test suites pass | all four pass today, unlabelled as a guard |
| `diff <backup> <new>` guard | **inverted** — bare `diff` exits 1 when the files legitimately differ, and a *missing* baseline makes the removed-line count read 0, i.e. a false PASS. Fixed in-cycle with the form the sync script already uses (`diff -u \| grep -c '^-[^-]'`, behind a `test -f` preflight). |
| `grep -c 'codemax platform-context'` = 0 | bare `grep -c` exits 1 when the count is 0 — it reports failure when the file is *correct*. Fixed in-cycle with a `test "$(…)" -eq 0` wrapper. |

**2 · Two findings would have damaged the machine or lost the work.**

- **A weekday cron would have deleted this entire plan set.** `codemax-skills-sync.sh:50` runs
  `git reset -q --hard origin/master` in `~/tapway-superpowers` when master's tip moves. The branch
  `feat/flow-drives-bots` is **1 commit ahead of origin/master**, so the next weekday 09:00 tick rewinds
  the branch, discards the commit, and reverts the tree — taking the plans, brainsketches, checklists and
  this record with it. Mitigated immediately: the doc set is backed up outside the repo at
  `~/.hermes/profiles/codemax/backups/flow-plans-<ts>/`, and the risk is now a row in all three plans.
  **An owner decision is required** — push/merge the branch, or exclude the repo from that cron.
- **A task would have wiped the live skills tree.** Task 9 proposed proving the cron's behaviour by
  running `hermes/install.sh` against a scratch dest. `resolve_hermes_home` (install.sh:87-107) prefers
  `hermes config path`, so a scratch `HERMES_HOME` is **silently ignored**: the live 31 `skills/tapway`
  directories are `rm -rf`'d and recopied and the `tapway` bundle is force-rewritten. The task is rewritten
  to a `HERMES_DRY_RUN=1` source-path check plus a direct assertion on `hermes/skills/`.

**3 · The plans are not converging.** Cycle 1: 48 findings. Cycle 2: ~60. Both cycles were ~45–60
Activable with no contract-misreads. The third plan carries design-level gaps that fixes have not closed —
a circular genesis precondition (`@decider` owns the Confirmed Intent, but `/interview` is interactive and
cannot run headless), a re-entry guard whose own mechanism cannot distinguish a nested launch from the
top-level one (`FLOW_ORCHESTRATED` is inherited by children), and structured evidence the framework's
`state.db` does not actually carry (no gate/seal/phase column).

## Cycle-2 fixes applied in-cycle
- the inverted `diff` guard and the inverted `grep -c` idiom, both replaced with forms proven to work
- the bare `python -m codemax.cli` command, which measurably **cannot run** (`ModuleNotFoundError`), now
  the venv's absolute interpreter path everywhere
- Task 9 made non-destructive
- Phase A's vacuous empty range; the genesis case; findings F10/F15 explicitly marked
- the cron hazard recorded in all three plans

## Verdict

**STOP.** Not sealed. Two decisions belong to the owner before another cycle is worth running:

1. **The branch must be pushed or the repo excluded from the cron** — otherwise nothing survives tomorrow.
2. **Initiative 3 needs a scope decision.** The ponytail and grounding plans are close to sealable
   (remaining findings are criteria-shape, not design). The orchestration plan is not: its own literature
   says multi-agent teams do not beat a single strong model on one-shot work, and the evidence here is a
   design that keeps acquiring risk in new places each cycle. A defensible call is to seal initiatives 1
   and 2, and re-scope initiative 3 to the smallest useful thing that can be verified.
