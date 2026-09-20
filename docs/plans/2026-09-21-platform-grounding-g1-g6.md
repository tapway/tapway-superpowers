# Plan: Platform Grounding (G1–G6) for tapway-superpowers

Date: 2026-09-21
Status: implemented
Companion plan (code side): `tapway/codemax` — `docs/research/platform-context-grounding-for-brainstorming.md` (design report) and PR #104 (G4/G5 implementation).

## Goal

Make the enforced pipeline's `brainstorming` step reason from the platform-wide design (contracts, ownership, ADRs across sibling repos) instead of the one repo the agent sits in — and enforce it fail-closed.

## Non-goals

- No changes to app code or other skills.
- No LLM-judge verification (deterministic checks only; LLM evals are phase 2).
- Gate stays OFF by default in this public repo (`TAPWAY_BRAINSTORM_GATE=1` enables; per-repo adapters enable it for pilots).

## Design decisions (from the research report)

1. **Fail closed on every brainstorm doc** — decided by CH Lim (2026-09-21).
2. **All platforms at once, samurai-v2 + city-os first** — decided by CH Lim.
3. **Dedicated spec repo** (`tapway/platform-specs`) as the single writeable source of truth, referenced read-only — decided by CH Lim.

## Changes

### G1 — `brainstorming` skill: Step 1.5 "Platform Context"
Mandatory retrieval BEFORE options: ownership & contracts, existing capability, platform ADRs, data model, dependency direction; routing decision (extend / direct / new spec / decompose); unresolved items as `UNKNOWN (not retrieved: …)`. All three variants (skills/, hermes/skills/, codex/skills/) kept in sync.

### G2 — grounded option rows
`Platform Fit`, `Grounding:` (`catalog:<platform>#<contract-id>`, ADR ids), `Rejected because platform:`.

### G3 — fail-closed gate, three harnesses
`hooks/pre-brainstorm-ground/` (adapter + shared lib + `extract-post-text.py`), wired for Claude Code (`hooks/hooks.json` PreToolUse Write|Edit), Codex (`codex/hooks.json.template`), Hermes (`hermes/config.hooks.yaml`, matcher `terminal|write_file|patch`). Gate validates the POST-write text; bullet/bold `Grounding:` rows accepted; nested paths gated; fails closed when python3 is missing.

### G6 — index-first budget
Platform pack = ~4k-char index with fetch-on-demand (context-rot defense). Enforced in the skill text.

### Release workflow fixes (root-cause)
- `release.yml`: tag + GitHub release publish before (independent of) the plugin-manifest sync, which is now non-fatal — Auto Release had failed on every master push since the ruleset landed (bot push rejected by protected branch).
- `workflow-audit.yml`: diffs against the PR base ref instead of hardcoded `origin/main` (which doesn't exist; default is master) — the audit had failed on every PR since 2026-08-20.

## Tests

- `tests/test-phase-g.sh` (TDD: written RED first): Step 1.5 in all variants, template-form docs, creation-flow gating, heading-dodge, no-python3 fail-closed, md5 copy-drift guard.
- `tests/e2e-platform-grounding.sh`: full chain — spec repo → pack build → CLI check → hook.
- All 11 existing suites re-run: no regressions.
- Adversarial review: 16 findings (2 critical), all fixed with regression tests.

## Rollout

Pilots (gate ON, env baked in): samurai-inspector#52 (samurai-v2), city-terra#204 (city-os). Fleet-wide enablement after pilot feedback.

## Version

2.3.0 (feat → MINOR). CHANGELOG entry + manifest bumps included; Auto Release tags v2.3.0 and publishes the changelog section as release notes on merge.
