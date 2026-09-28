# Checklist: ponytail flow assimilation  (v3 — synced to plan)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-ponytail-flow-assimilation.md`
**Baselines:** pack live in codemax + root only · `/simplify-code` live in the **builder** tree only
(v2 said "codemax/decider" in one place and "architect/planner/builder" in another — resolved: the fallback
is live in **architect + planner**, inert in builder because `/simplify-code` resolves there)

## Task 0 — BACKUP FIRST (before any write)
- [ ] ⬜ 7 backups, **one per tree**: `for t in ~/.hermes/skills ~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills; do test -f "$t/backups/flow-pairs-<ts>/flow-build.SKILL.md" || echo "MISSING: $t"; done` prints nothing
- [ ] ⬜ A bare `find … | wc -l` = 7 is **not** acceptable — one directory holding 7 files passes it and proves nothing

## Skills / Config
- [ ] ⬜ `TARGETS="architect planner builder" bash ~/.hermes/scripts/tapway-v240-sync.sh --apply --ponytail` — **`--apply` required** (default is a dry run that writes nothing)
- [ ] ⬜ `TARGETS` set explicitly — the script default installs into decider + doubter and skips codemax
- [ ] ⬜ `test -d ~/.hermes/profiles/architect/skills/tapway/ponytail` (a **created path**, not an exit code)
- [ ] ⬜ Counts 6/6/6 for architect/planner/builder, **positive control** codemax = 6, decider + doubter = 0
- [ ] ⬜ Record `hermes config path` — the pack-category writer `rm -rf`s whichever tree it resolves to

## Flow authoring
- [ ] ⬜ **Whole** Step 3 rewritten, not its tail
- [ ] ⬜ Absent: `run a manual simplification pass over your own diff`
- [ ] ⬜ Absent: the false `/simplify-code` location claim (`exists only on the` + `default` in one paragraph)
- [ ] ⬜ Absent: the `cp -R` copy-it-in-first instruction (it ordered the opposite of the rule)
- [ ] ⬜ Present: `ponytail-review` as the fallback, scoped *where the pack is present*
- [ ] ⬜ Step 1 gate precedence added; **guard**: `diff -u "$BK" "$NEW" | grep -c '^-[^-]'` = 0 over the TDD gate block, behind a `test -f` preflight (bare `diff` is inverted and fails open)
- [ ] ⬜ Step 7 carries the counted `ponytail:` ledger; `ponytail-gain` only with a "benchmark medians" qualifier
- [ ] ⬜ flow-decide Steps 2–3 name the YAGNI bullet. *"minimum 3 options" is a **labelled regression guard** (already true in all 7 trees) — not RED evidence*
- [ ] ⬜ Step 6 recorded as **not adopted** in plan + brainstorm + checklist
- [ ] ⬜ **Guard**: `ponytail-audit` in no flow step (zero ponytail strings exist there today)
- [ ] ⬜ Task 10 decidable: `grep -rnE '(#|//) ?ponytail:' "$TARGET" --exclude-dir={node_modules,.git,build,dist} | grep -v '/skills/ponytail'` → ≥1 real marker **or** an empty result with pasted output

## Propagation
- [ ] ⬜ **Failable**: for each of the 6 non-codemax trees, `diff -u <backup> <new> | grep -c '^-[^-]'` ≥ 1 on the Step 3 region
- [ ] ⬜ **Guard**: all 7 pairs md5-identical (already identical today)
- [ ] ⬜ `hermes-flow-pipeline` updated in **all 7 trees** (6 of 7 already differ from codemax's)

## Gate health (the top risk, which v2 named but no task owned)
- [ ] ⬜ ≥3 builder runs logged after the pack lands, each showing the RED gate observed
- [ ] ⬜ Revert demonstrated: the 6 pack dirs exist, then are gone after `rm -rf` in a scratch copy

## QA
- [ ] ⬜ No criterion permits a per-repo number from `ponytail-gain`
- [ ] ⬜ `~/.claude/skills/flow-*` named as out of scope (a third copy, outside `~/.hermes`, stale)
- [ ] ⬜ Reviewer question: does any wording let ponytail past a gate?
