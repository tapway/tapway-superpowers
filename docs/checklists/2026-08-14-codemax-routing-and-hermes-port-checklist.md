# Work Package Checklist — Codemax-gbrain Hermes port + wiki/repo routing

**Branch:** `feat/hermes-codemax-gbrain-port`
**PR:** #27
**Status:** 🟢 In review (CI gate pending: commits plan + checklist)

## Docs & Skills

- [x] ✅ Hermes port of `codemax-gbrain` skill (`hermes/skills/codemax-gbrain/SKILL.md`)
- [x] ✅ `writing-plans` step 7c — wiki-vs-repo routing (Claude + Hermes copies)
- [x] ✅ `writing-plans` step 7b — GitHub issue after plan (Claude copy; Hermes had it)
- [x] ✅ `codemax-gbrain` "route before you sync" push pointer (both copies)
- [ ] 🟢 Plan committed (`docs/plans/2026-08-14-codemax-routing-and-hermes-port.md`)
- [ ] 🟢 Checklist committed (this file)

## Install / Packaging

- [x] ✅ `hermes/install.sh` + `hermes/install.ps1` list `codemax-gbrain` (25 skills)
- [x] ✅ Skill counters updated: `README.md`, `hermes/README.md`

## Testing (TDD)

- [x] ✅ `tests/test_wiki_repo_routing.py` — RED 14 fail → GREEN 24 pass
- [x] ✅ `tests/test_hermes_install.py` — 105 passed
- [x] ✅ `bash -n hermes/install.sh` — OK
- [x] ✅ Full standalone suite green (one pre-existing `test_phase3_hooks` clean-tree failure unrelated to this PR)

## Definition of Done

- [ ] 🟢 PR #27 merged
- [ ] 🟢 No release (per instruction)
- [ ] 🟡 Optional follow-ups: fix pre-existing `plugin.json` `"hooks": []` stale field; mirror routing step into `codex/` port when it lands