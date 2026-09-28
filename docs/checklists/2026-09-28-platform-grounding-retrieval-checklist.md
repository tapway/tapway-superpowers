# Checklist: Step 1.5 grounding — environment wiring  (v4)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-platform-grounding-retrieval.md` (v4 — supersedes v3)

> **Premise corrected.** v1–v3 planned to wire Step 1.5. It is already implemented on master
> (`docs/plans/2026-09-21-platform-grounding-g1-g6.md`, Status: implemented) and present in all three
> skill variants. This checklist covers **environment wiring only**. Do not rewrite Step 1.5.

## Criteria hygiene — both of these bit this plan set
- [ ] ⬜ No criterion uses `wc -l | grep -q '^N$'` — BSD/macOS pads (`"       1"`), so it never matches. Use `$(… | tr -d '[:space:]')`
- [ ] ⬜ No criterion runs `grep -c` unguarded under `set -e` — it exits 1 when the count is 0, i.e. it aborts in the passing state. Use `|| true` or `test "$(… || true)" -eq 0`

## Environment
- [ ] ⬜ `python3 -m venv ~/.hermes/venvs/codemax-cli`; `…/bin/python -c 'import sys;assert sys.version_info>=(3,11)'` exits 0 (box is 3.12.8)
- [ ] ⬜ Install with `…/bin/pip install ~/tapway-codemax` — isolation **on**. **Not** v3's `--no-build-isolation`: a fresh venv has no setuptools, so the backend is unavailable (`BackendUnavailable`)
- [ ] ⬜ Offline fallback, if needed: `…/bin/pip install -U setuptools` **then** the no-isolation form
- [ ] ⬜ `…/bin/python -c 'import codemax'` exits 0
- [ ] ⬜ **Never** bare `python -m codemax.cli` and never a `$PY` variable — v3 used undefined `$PY`, and the venv's `bin/` is deliberately off PATH
- [ ] ⬜ Clone `tapway/platform-specs` → `~/platform-specs-local` **read-only**; assert `constitution.md` **and** `platforms/samurai-v2/catalog.yaml`
- [ ] ⬜ `TAPWAY_SPECS_DIR` non-empty in each env file the skill reads — file list enumerated, not implied

## Prove it works
- [ ] ⬜ `…/bin/python -m codemax.cli platform-context --help` exits 0 (the subgroup)
- [ ] ⬜ Pack builds: output has ≥1 ADR id **and no `catalog:`** — both catalogs carry `provides: []`, so a catalog citation can never resolve
- [ ] ⬜ Checker passes an ADR-id-only doc; checker **fails** an ungrounded doc (both directions)
- [ ] ⬜ **`bash tests/e2e-platform-grounding.sh` → 0 failures** (currently 3; the same 3 on clean master, so pre-existing)
- [ ] ⬜ The `UNKNOWN row should pass` failure is **decided, not papered over**: the skill mandates `UNKNOWN (not retrieved: …)` rows, while `_resolve_ref` pushes exactly that text into `unresolved` → `passed=False`. State which side is the bug
- [ ] ⬜ No assertion was relaxed to reach green

## Skill text — read the anchor coupling first
- [ ] ⬜ `~/.hermes/scripts/tapway-v240-sync.sh` defines `ANCHOR_A` (84–86) and `ANCHOR_B` (91–93) and exits **3** on mismatch (98–100); its classifier keys on the literal phrase `Box reality` (142–144); it `rm -rf`s + `cp -a`s (175–179)
- [ ] ⬜ v3's "`codemax platform-context` must occur 0 times" **would zero ANCHOR_B and fail the script closed**, leaving the skill at upstream v1.3.0 — the version this plan exists to fix
- [ ] ⬜ So: keep the anchors, or update them in the same change
- [ ] ⬜ After editing, `bash ~/.hermes/scripts/tapway-v240-sync.sh` (**dry-run default**) classifies the skill **KEEP**, not FLAG
- [ ] ⬜ Note reads `retrieval is wired` ≥1 and `does not exist` = 0 per copy

## Decisions to record (not to act on)
- [ ] ⬜ *(guard)* `test ! -d ~/.hermes/agent-hooks` still true — the hook is **not** installed here; the gate is pilots-only and this repo is public. `hermes/config.hooks.yaml:34` still names it
- [ ] ⬜ *(guard)* `TAPWAY_BRAINSTORM_GATE` absent from all 7 env files
- [ ] ⬜ *(guard)* `shasum -a 256 ~/.local/bin/codemax` = `08f16040b18cd8c33a0edddb3df5d525d5eb80a0f5c7fe23bc846eef60230a54` — baseline now recorded, so this is decidable (v3's "unchanged" was not)
- [ ] ⬜ Wiring + gate-off decision recorded in `hermes-flow-pipeline/SKILL.md` in **all 7 trees** that carry it

## Ship
- [ ] ⬜ Committed **and merged** — `git ls-tree origin/master <edited path>` succeeds. `codemax-skills-sync.sh:50` hard-resets to `origin/master` on the weekday tick
- [ ] ⬜ PR body states which of the 3 e2e failures resolved and why the third was decided as it was
- [ ] ⬜ No write of any kind to `tapway/platform-specs`
