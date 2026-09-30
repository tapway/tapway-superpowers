# Work Package Checklist — Hermes plugin install

**Branch:** `feat/hermes-plugin`
**PR:** https://github.com/tapway/tapway-superpowers/pull/39
**Status:** 🟢 Ready for review

## Packaging

- [x] `hermes/plugin/plugin.yaml` names the plugin `tapway-superpowers`
- [x] `register()` covers every `hermes/skills/*/SKILL.md`
- [x] `hermes/plugin/skills/` is a byte mirror of `hermes/skills/`
- [x] Plugin-guard scan of `hermes/plugin/` is not DANGEROUS

## Docs

- [x] Plan committed (`docs/plans/2026-09-30-hermes-plugin.md`)
- [x] Install command in `hermes/README.md`, `README.md`, `docs/DEPLOYMENT.md`
- [x] Workflow section in `docs/WORKFLOWS.md`

## Testing

- [x] RED first: `tests/test_hermes_plugin.py` failed before the plugin existed
- [x] GREEN: `python tests/test_hermes_plugin.py`
