# Checklist: Step 1.5 retrieval  (v2)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-platform-grounding-retrieval.md`

## Infra
- [ ] ⬜ Clone `tapway/platform-specs` → `~/platform-specs-local`; assert `constitution.md` **and** `platforms/samurai-v2/catalog.yaml` ⟨F11⟩
- [ ] ⬜ Clone `tapway/codemax` → `~/tapway-codemax`; record `rev-parse HEAD` as evidence ⟨F13⟩
- [ ] ⬜ Venv `~/.hermes/venvs/codemax-cli`; **expect** `bin/codemax` to be created — assert its presence, don't treat it as failure ⟨F2⟩
- [ ] ⬜ Record resolved versions; note the `hermes-agent` drift (PyPI 0.19.0 vs box 0.21.5+3840) ⟨F14⟩

## Prove the CLI (offline, subgroup-level)
- [ ] ⬜ `… python -m codemax.cli platform-context --help` exits 0 — the **subgroup**, not the top level ⟨F13⟩
- [ ] ⬜ Build **with the network interface down**; assert ADR ids + component roles present **and** `'catalog:' in idx` is False ⟨F1⟩ ⟨F8⟩
- [ ] ⬜ `check` passes a grounded doc (exit 0)
- [ ] ⬜ `check` **fails** an ungrounded doc (non-zero) ← fail-closed proven

## Wiring
- [ ] ⬜ Non-empty `TAPWAY_SPECS_DIR` (equal to the clone path) in all **7** env files ⟨F6⟩
- [ ] ⬜ `TAPWAY_BRAINSTORM_GATE` absent from all 7 **and** `test ! -d ~/.hermes/agent-hooks` ⟨F12⟩
- [ ] ⬜ `~/.local/bin/codemax` sha256 unchanged ⟨F2⟩

## Skill text — all copies a writer can serve
- [ ] ⬜ Both commands rewritten: `grep -c 'python -m codemax.cli'` ≥ 2; `grep -c 'codemax platform-context'` = **0** (catches the `check` twin) ⟨F5⟩
- [ ] ⬜ Note corrected, decidably: `grep -q 'retrieval is wired'` **and** `! grep -q 'does not exist'` ⟨F4⟩
- [ ] ⬜ Edited in the 3 **repo** trees as well as the 7 installed copies — else the weekday cron reverts it ⟨F3⟩
- [ ] ⬜ Simulated `install.sh` run against a scratch dest shows the corrected text arriving ⟨F3⟩

## QA
- [ ] ⬜ No write of any kind to `tapway/platform-specs`
- [ ] ⬜ Claim bounded to roles + ADR ids + constitution (not contracts/ownership) ⟨F9⟩
