# Checklist: flow drives the bot team  (v2)

**Branch:** `feat/flow-drives-bots`  **Status:** 🔴 not started
**Plan:** `docs/plans/2026-09-28-flow-bot-orchestration.md`
**Corrected premise:** `is_bot_mode_managed` = **True**; `ui_meta.hermes-bots` **present**; `Bot Chat` reachable from the CLI (`source=cli`).

## Scripts (live in the repo, not in `~` only) ⟨F16⟩
- [ ] ⬜ Range check: docs-only passes / code-touching **fails** / **two-commit range with code first fails** ⟨F4⟩
- [ ] ⬜ Seal check: present passes / absent fails / **quoted-seal STOP block fails** ⟨F6⟩
- [ ] ⬜ Seal check greps **no transcript** — the log carries the seal string from the start ⟨F6⟩
- [ ] ⬜ Preconditions refuse on: empty artifact · missing `BASE` · **ambiguous** phase skill (a duplicate name means neither copy loads) ⟨F3⟩ ⟨F14⟩
- [ ] ⬜ Genesis case: phase 1 accepted with a non-empty Confirmed Intent, no predecessor commit ⟨F5⟩
- [ ] ⬜ Re-entry guard: launch without `FLOW_ORCHESTRATED` refused; contract carries run-only-your-phase ⟨F12⟩
- [ ] ⬜ Provenance output names profile + session id; the word "author" appears nowhere ⟨F8⟩
- [ ] ⬜ Bound: 900 s is a single scripted value; a hanging phase is stopped and reported ⟨F13⟩

## Flow authoring
- [ ] ⬜ flow-decide: 4 Phase-A bots in order + refuse-not-launch; no "run it yourself" wording
- [ ] ⬜ flow-build: @builder + **range** verification; TDD/simplify/PR steps unchanged
- [ ] ⬜ Contracts documented + a task owns `docs/flow/<feature>/prompt-NN-<bot>.md` ⟨F11⟩
- [ ] ⬜ Prompts passed with `--query-file` (not `-q "$(cat …)"`) ⟨F16⟩
- [ ] ⬜ Stage exact paths only — no `git add docs/flow`

## Refuted claims removed from the flow skill
- [ ] ⬜ `peer messaging is CLOSED` absent ⟨F1⟩ ⟨F9⟩
- [ ] ⬜ `check whether the seal's commit author` absent — it contradicted this plan's own rule ⟨F9⟩

## Rehearsal (the part that proves it)
- [ ] ⬜ One real @architect phase driven by the runner; artifact verified by the verifier
- [ ] ⬜ Deliberate empty prompt **refused**
- [ ] ⬜ Full `/flow-decide` chain exercised through to the seal, **including the genesis phase** ⟨F5⟩

## Propagation + suites
- [ ] ⬜ All 7 pairs md5-identical; backups per tree ⟨F7⟩
- [ ] ⬜ `test_hermes_install.py` + `test_ponytail_pack.py` + `test_codex_port.py` + `test_quality_gates.py` all exit 0
- [ ] ⬜ `hermes-flow-pipeline` runbook replaced with the orchestrated version

## QA
- [ ] ⬜ No step claims role separation from commit metadata ⟨F8⟩
- [ ] ⬜ Fallback recorded if nested launches can't finish a phase in time
