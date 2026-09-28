# Checklist: ponytail flow assimilation  (v2)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-ponytail-flow-assimilation.md`
**Baselines:** pack live in codemax + root only · `/simplify-code` live in `builder` only · sync script is
dry-run by default with `TARGETS` = `default decider architect planner doubter builder`

## Skills / Config
- [ ] ⬜ `TARGETS="architect planner builder" bash ~/.hermes/scripts/tapway-v240-sync.sh --apply --ponytail` — **`--apply` is required, the default is a dry run** ⟨F1⟩
- [ ] ⬜ `TARGETS` set explicitly — the script default would install into decider + doubter and skip codemax ⟨F2⟩
- [ ] ⬜ `test -d ~/.hermes/profiles/architect/skills/tapway/ponytail` (a created path, not an exit code)
- [ ] ⬜ Counts: architect/planner/builder = 6 · codemax = 6 (**positive control**) · decider + doubter = 0 ⟨F13⟩

## Backups (the baseline that makes "byte-identical" falsifiable)
- [ ] ⬜ 7 pre-change flow pairs backed up; `find ~/.hermes -path '*backups/flow-pairs-*' -name 'flow-decide*' | wc -l` = 7 ⟨F8⟩ ⟨F14⟩

## Flow authoring
- [ ] ⬜ **Whole** Step 3 rewritten, not its tail ⟨F16⟩
- [ ] ⬜ Absent: `run a manual simplification pass over your own diff` ⟨F3⟩
- [ ] ⬜ Absent: the false `/simplify-code` location claim (`exists only on the` + `default` in one paragraph) ⟨F16⟩
- [ ] ⬜ Absent: the `cp -R` copy-it-in-first instruction (it ordered the opposite of the rule) ⟨F16⟩
- [ ] ⬜ Present: `ponytail-review` as the fallback, scoped *where the pack is present* ⟨F5⟩
- [ ] ⬜ Step 1 gate precedence added; `diff <backup> <new>` removes **no line** from the TDD gate block ⟨F8⟩
- [ ] ⬜ Step 7 carries the counted `ponytail:` ledger, names `ponytail-debt`; `ponytail-gain` only with a "benchmark medians" qualifier ⟨F4⟩ ⟨F9⟩
- [ ] ⬜ flow-decide Steps 2–3 name the YAGNI bullet; the "minimum 3 options" guard asserted on `brainstorming/SKILL.md`, not flow-decide ⟨F7⟩
- [ ] ⬜ Step 6 recorded as **not adopted** in plan + brainstorm + checklist ⟨F10⟩
- [ ] ⬜ `ponytail-audit` in no flow step — grep scoped to the two flow files only ⟨F17⟩
- [ ] ⬜ debt/help accounted for: ≥1 marker harvested or an intentionally empty ledger ⟨F15⟩

## Propagation
- [ ] ⬜ All 7 pairs md5-identical to codemax's ⟨F6⟩
- [ ] ⬜ `hermes-flow-pipeline` records the map + unplugged-audit + not-adopted-Step-6

## QA
- [ ] ⬜ No criterion permits a per-repo number from `ponytail-gain` ⟨F4⟩
- [ ] ⬜ Reviewer question: does any wording let ponytail past a gate?
