# Work Package Checklist — ponytail skill pack (vendored)

**Branch:** `feat/ponytail-skill-pack`
**PR:** (this PR)
**Status:** 🟢 Ready for review — tests green

## Docs & Skills

- [x] ✅ Canonical skills vendored verbatim (`skills/ponytail{,-review,-audit,-debt,-gain,-help}/SKILL.md`)
- [x] ✅ Hermes ports (`hermes/skills/...`) — frontmatter + host notes only, rule text untouched
- [x] ✅ Codex ports (`codex/skills/...`) — frontmatter + host notes only, rule text untouched
- [x] ✅ Upstream MIT licence retained (`skills/ponytail/LICENSE`)
- [x] ✅ Upstream repo + commit pinned in every vendored skill's frontmatter
- [x] ✅ Plan committed (`docs/plans/2026-09-24-ponytail-skill-pack-adoption.md`)
- [x] ✅ Checklist committed (this file)

## Install / Packaging

- [x] ✅ `hermes/install.sh` lists all 6 (SKILLS 25 → 31)
- [x] ✅ `codex/install.sh` lists all 6 (SKILLS 24 → 30, + `$tapway` umbrella)
- [x] ✅ `.claude-plugin/plugin.json` registers all 6 (skills 24 → 30)
- [x] ✅ Version bumped 2.3.0 → 2.4.0 (`plugin.json`, `marketplace.json`)
- [x] ✅ Stale marketplace counts corrected (19 skills / 4 agents → 30 skills / 5 agents)
- [x] ✅ Skill counters updated: `README.md`, `hermes/README.md`, `codex/README.md`

## Testing (TDD)

- [x] ✅ RED first: `tests/test_ponytail_pack.py` failed before the pack existed
- [x] ✅ GREEN: parity (no canonical rule line lost), provenance, count-drift, guard-trigger scrub
- [x] ✅ `tests/test_hermes_install.py` extended (`EXPECTED` + `blocked`) and green
- [x] ✅ Full local suite run — no regressions

## Review

- [x] ✅ Attribution visible in README + CHANGELOG (not presented as Tapway-authored)
- [x] ✅ Measured impact stated with the honest n=3 caveat
- [ ] 🟢 Reviewer: confirm vendoring (vs the `externalSkills` documentation precedent) is wanted
