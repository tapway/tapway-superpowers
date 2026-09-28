# Checklist: Step 1.5 retrieval  (v3 — synced to plan)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-platform-grounding-retrieval.md`

## Infra
- [ ] ⬜ Clone `tapway/platform-specs` → `~/platform-specs-local`; assert `constitution.md` **and** `platforms/samurai-v2/catalog.yaml`
- [ ] ⬜ Clone `tapway/codemax` → `~/tapway-codemax`; **pin decidable**: `test "$(grep -c "$SHA" <plan>)" -ge 1` (running `rev-parse` alone cannot fail)
- [ ] ⬜ Venv `~/.hermes/venvs/codemax-cli`; **expect** `bin/codemax` — assert its presence, it is not a failure
- [ ] ⬜ Record the `hermes-agent` drift (PyPI 0.19.0 vs box 0.21.5+3840)

## Prove the CLI — every command uses the venv's own interpreter
- [ ] ⬜ `~/.hermes/venvs/codemax-cli/bin/python -m codemax.cli platform-context --help` exits 0 (the **subgroup**)
- [ ] ⬜ **NOT** bare `python -m codemax.cli` — it fails (`ModuleNotFoundError`), because the venv is never on PATH
- [ ] ⬜ Build with the network **probed and restored** around it (a build succeeding identically online proves nothing)
- [ ] ⬜ Task 4 shell-form: `test "$(printf '%s' "$OUT" | grep -c 'ADR-')" -ge 1` and `test "$(printf '%s' "$OUT" | grep -c 'catalog:')" -eq 0`
- [ ] ⬜ `check` passes a grounded doc (exit 0)
- [ ] ⬜ `check` **fails** an ungrounded doc (non-zero) ← fail-closed proven
- [ ] ⬜ **Pass-direction fixture uses an ADR-id-only doc** — a `catalog:<p>#<id>` citation can never resolve; and assert the checker's option-heading regex accepts the doc's headings

## Wiring
- [ ] ⬜ Non-empty `TAPWAY_SPECS_DIR` (equal to the clone path) in all **7** env files; `test "$(grep -c …)" -eq 1` (bare `grep -c` exits 1 when the count is 0, i.e. fails when correct)
- [ ] ⬜ **End-to-end**: a fresh shell runs the documented build with `$TAPWAY_SPECS_DIR` **read** from a profile `.env`, not typed — every other criterion is component-level
- [ ] ⬜ **Guard**: `TAPWAY_BRAINSTORM_GATE` absent from all 7 **and** `test ! -d ~/.hermes/agent-hooks` (both already true)
- [ ] ⬜ `~/.local/bin/codemax` sha256 unchanged

## Skill text — all copies a writer can serve
- [ ] ⬜ Both commands rewritten: `grep -c 'venvs/codemax-cli/bin/python -m codemax.cli'` ≥ 2; `grep -c 'codemax platform-context'` = **0** (as `test "$(…)" -eq 0`)
- [ ] ⬜ Note corrected: `retrieval is wired` present **and** zero `does not exist` — **and** the note must stop naming `codemax platform-context` at all, else task 7 and task 8 contradict
- [ ] ⬜ Also remove the note's other now-false statements: specs "not cloned" and `TAPWAY_SPECS_DIR` "is unset"
- [ ] ⬜ Edited in the repo trees **and** all 7 installed copies. **Only `hermes/skills` is distributed by the cron** — `skills/` and `codex/skills/` serve the Claude plugin and `codex/install.sh`
- [ ] ⬜ **CRITICAL**: the repo-tree edits only survive if **pushed/merged to master** — `codemax-skills-sync.sh:50` does `git reset --hard origin/master`, so unmerged branch edits are rewound
- [ ] ⬜ `hermes-flow-pipeline` updated in the **4 trees that carry it** (root, architect, codemax, doubter, planner as measured)
- [ ] ⬜ **NEVER** set a scratch `HERMES_HOME`: `resolve_hermes_home` ignores it and `install_local` `rm -rf`s the live 31 dirs. Use `HERMES_DRY_RUN=1` + assert on `hermes/skills/` directly

## QA
- [ ] ⬜ No write of any kind to `tapway/platform-specs`
- [ ] ⬜ Claim bounded to roles + ADR ids + constitution (both catalogs carry `provides: []`)
- [ ] ⬜ Fallbacks named: clone → `gh auth refresh -s repo`; install → `pip install --no-build-isolation ~/tapway-codemax`
- [ ] ⬜ Claude plugin clone named as out of scope
