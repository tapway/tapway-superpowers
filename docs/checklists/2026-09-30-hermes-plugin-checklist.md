# Work Package Checklist — Hermes plugin install

**Branch:** `feat/hermes-plugin`
**PR:** https://github.com/tapway/tapway-superpowers/pull/39
**Status:** 🟢 Ready for review

## Packaging

- [x] `hermes/plugin/plugin.yaml` names the plugin `tapway-superpowers`
- [x] `register()` covers every `hermes/skills/*/SKILL.md`
- [x] `hermes/plugin/skills/` is a byte mirror of `hermes/skills/`
- [x] Plugin-guard scan of `hermes/plugin/` is **safe** — asserted by
      `tests/test_hermes_plugin.py`, not a manual tick
- [x] `plugin.yaml` version agrees with `.claude-plugin/plugin.json` and the top
      `CHANGELOG.md` entry
- [x] `api_version: 1` declares the plugin API generation

## Docs

- [x] Plan committed (`docs/plans/2026-09-30-hermes-plugin.md`)
- [x] Install command in `hermes/README.md`, `README.md`, `docs/DEPLOYMENT.md`
- [x] Workflow section in `docs/WORKFLOWS.md`
- [x] Mirror regeneration documented (`scripts/sync-hermes-plugin-skills.sh`)

## Testing

- [x] RED first: `tests/test_hermes_plugin.py` failed before the plugin existed
- [x] GREEN: `python tests/test_hermes_plugin.py` — 59 passed, 2 skipped
      (Hermes-only checks) without hermes-agent
- [x] Full run with hermes-agent present: **66 passed, 0 skipped**
- [x] `python tests/test_hermes_install.py` — 159 passed
- [x] `python tests/check_docs_consistency.py` — ALL PASS
- [x] CI: `.github/workflows/skills-tests.yml` runs all three scripts on every PR

## MoA review follow-up (#39)

- [x] **Critical — unverified `ctx.register_skill` contract.** The test no longer
      mocks the context: it builds a real `PluginContext` + `PluginManager` from
      hermes-agent and registers into it. Verified separately by a real
      `hermes plugins install` into a throwaway `HERMES_HOME`: 31/31 skills
      registered, 0 empty descriptions/frontmatter.
- [x] **Critical — plugin-guard claim was a hand-ticked box.** Now a test calls
      the real `scan_plugin()` and asserts `verdict == "safe"` plus
      `should_allow_plugin_install(...) is True`. The repo root remains
      DANGEROUS (304 findings, 18 critical) — that is why the subdirectory ships.
- [x] **Warning — silent no-op on a broken tree.** `register()` raises with the
      missing path; a skill directory without `SKILL.md` raises with its name.
      Both failure paths are tested.
- [x] **Warning — pytest collected nothing.** Added a `test_hermes_plugin_suite()`
      entry point (pytest collects it) and pinned the script in CI.
- [x] **Warning — hardcoded plugin version.** Test asserts plugin.yaml ==
      `.claude-plugin/plugin.json` == top `CHANGELOG.md` release.
- [x] **Warning — linked files unproven.** Test resolves
      `skill_view(file_path="templates/…")` against the registered plugin copy.
- [x] **Warning — install command check omitted `--enable`.** The constant now
      carries the full documented command and four docs are checked.
- [x] **Suggestion — no mirror regeneration tooling.**
      `scripts/sync-hermes-plugin-skills.sh` (with `--check`) + docs.
- [x] **Suggestion — API generation unguarded.** `api_version: 1` in the manifest.
- [x] **Suggestion — missing trailing newlines.** Fixed in the skill sources and
      `docs/WORKFLOWS.md`; the test now enforces it.