> **⚠ SUPERSEDED FOR SCOPE — not sealed.** The chain design below is retained as the design record.
> The scope decision is `docs/plans/2026-09-28-flow-bot-orchestration-rescope.md`: one phase,
> driven by hand, supervisor text NOT propagated to worker profiles. Do not implement the chain
> from this document.

# Plan: One entry point — the flow drives the bot team

> **Revision v2 — post doubt-cycle-1.** v1 returned 16 findings, all Actionable; each fix is
> marked `⟨F#⟩`. Record: `docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`.

Implements `docs/brainstorming/flow-bot-orchestration.md` (Option A: subprocess room-runner).
**Procedure source:** `headless-bot-orchestration` skill + `references/headless-bot-run.md`.
**Corrected premise:** `is_bot_mode_managed` is **True** for all six profiles and `ui_meta.hermes-bots` is
**present** in every bot `profile.yaml` (nested inside `ui_meta` — a top-level key dump misses it). v1's
claim that the gate was closed, and that the key still needed flipping, was wrong. The `Bot Chat` title is
reachable from the CLI: decider's own session row reads `source=cli`.

## Goal

Make `/flow-decide` and `/flow-build`, invoked in the owner's own CLI, drive the five-bot team through
their phases, so the bots do the phase work and the owner never types into an individual bot's chat.

## Approach

codemax supervises. Per phase: write a contract, assert the precondition **or refuse to launch**, launch,
verify the **artifact**, then continue or stop.

1. **Pin the base before every launch.** `⟨F3⟩` `git rev-parse HEAD` is recorded as `BASE` before phase N. A
   phase that produces nothing leaves HEAD unchanged, and a HEAD-scoped check would then report the
   *previous* phase's commit as this phase's evidence.
2. **Verify a range, not a commit.** `⟨F4⟩` flow-build commits **per task**, so its evidence is
   `git diff --numstat BASE..HEAD`. **Phase A and Phase B both require a NON-EMPTY range**: Phase B additionally requires every changed path
   to be inside the plan's authorised set; Phase A additionally requires every changed path to be under
   `docs/`. An **empty** range satisfies "touches docs only" vacuously — measured: with no commit after
   `BASE`, `git diff --name-only "$BASE..HEAD" | grep -qv '^docs/'` is false and a naive docs-only check
   exits 0 — so a phase that produced nothing would be reported VERIFIED. The non-emptiness test comes
   first. `⟨F7-c2⟩`
3. **Genesis is a defined case.** `⟨F5⟩` Phase 1 has no predecessor: the precondition is that `BASE` exists and the **Confirmed Intent document at
   a pinned path** (`docs/flow/<feature>/intent.md`, written by the owner in the CLI — not produced by a
   headless phase) is non-empty. `⟨F2-c2⟩` **Design consequence:** `@decider` owns the Confirmed Intent and
   `/interview` is explicitly interactive, so a headless @decider cannot run it; the intent must exist
   *before* phase 1 launches, or the runner is refused rather than fed an invented one.
4. **Structured evidence only.** `⟨F6⟩` The gate verdict comes from the artifact and the phase's `state.db`
   row, **never** from grepping the transcript: the framework's own skill warns a run's log contains the
   literal gate-seal string from the moment it starts, so a log grep reports PASSED for every run,
   including a STOP.
5. **Provenance stated honestly.** `⟨F8⟩` A `sessions` row proves a session existed and how it was launched;
   it has **no author column**. So provenance is reported as *"the seal text is present in the artifact, and
   phase N ran as profile `<bot>` in session `<id>`"* — never as authorship. Commit metadata is never used
   (shared git identity).
6. **Re-entry guard.** `⟨F12⟩` Every launch sets `FLOW_ORCHESTRATED=1` and the contract carries an explicit
   *"run only your own phase; do not orchestrate"* clause. Without it, a worker reading its own propagated
   flow-decide text launches @decider/@architect recursively, and the parent's timeout does not bound the tree.
7. **Bounded.** `⟨F13⟩` **900 s per phase**, a single scripted value; on expiry the runner stops in-turn.
   Stall-vs-slow: if the log advanced within the last 120 s, extend once by 300 s, then stop.
8. **Contracts and scripts are real artifacts.** `⟨F11⟩` `⟨F16⟩` `docs/flow/<feature>/prompt-NN-<bot>.md` is
   a file-map entry with a task; the two runner scripts live **in the repo** (`hermes/scripts/`) so they are
   reviewable and backed up. Prompts use `--query-file`, which the framework documents as safe for arbitrary
   text — `-q "$(cat …)"` lets the shell interpret `$(...)` and backticks inside a contract.

## Files

| Path | What |
|---|---|
| `hermes/scripts/flow-run-phase.sh` | **CREATE** — precondition assert + launch + log capture; refuses on a false premise |
| `hermes/scripts/flow-verify-phase.sh` | **CREATE** — range / docs-only / status / seal / provenance |
| `docs/flow/<feature>/prompt-NN-<bot>.md` | **CREATE** — the contract per phase `⟨F11⟩` |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-decide/SKILL.md` | **MODIFY** — Phase A orchestration + refuse-not-launch |
| `~/.hermes/profiles/codemax/skills/openclaw-imports/flow-build/SKILL.md` | **MODIFY** — Phase B orchestration + range verification |
| the 5 profile pairs + the root pair | **MODIFY** — propagate, with the re-entry clause `⟨F7⟩` `⟨F12⟩` |
| `~/.hermes/profiles/codemax/skills/software-development/hermes-flow-pipeline/SKILL.md` | **MODIFY** — runbook replaced; **and** its refuted claims fixed: the "peer messaging is CLOSED" line and the "check the seal's commit author" line, which contradicts this plan's own rule `⟨F9⟩` |
| `docs/plans|checklists/2026-09-28-flow-bot-orchestration*.md` | **CREATE** |

**6 profiles + the root tree** (`~/.hermes/skills/` + `~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills/`) = the 7 skill trees

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **A weekday cron rewinds the working checkout** | `codemax-skills-sync.sh:50` runs `git reset -q --hard origin/master` in `~/tapway-superpowers` whenever master's tip moves. **This branch is not on origin/master**, so an unpushed commit is destroyed and the tree reverts. The plan set itself and (for the grounding plan) the repo-tree edits are exposed. Owner decision required: push/merge the branch, or exclude the repo from that cron. Until then the plan set is backed up outside the repo at `~/.hermes/profiles/codemax/backups/flow-plans-<ts>/`. |
| Launching on a false premise | `BASE` pinned per phase; the precondition prints and refuses `⟨F3⟩` |
| Trusting a phase's summary | Artifact/range verification is a required step with named commands |
| A docs-last commit hides code changes | Range check `BASE..HEAD`, not `HEAD` `⟨F4⟩` |
| A log grep reports a seal never issued | Structured evidence only `⟨F6⟩` |
| Recursive orchestration | `FLOW_ORCHESTRATED` guard + contract clause `⟨F12⟩` |
| Unbounded wait | 900 s bound + stall-vs-slow rule `⟨F13⟩` |
| Role separation claimed from `git log` | Forbidden; provenance is a launch record only `⟨F8⟩` |
| Over-broad `git add` | Exact paths; never `git add docs/flow` |
| Scripts unreviewable | They live in the repo `⟨F16⟩` |

## Tasks

| # | Task | Verifiable success criterion |
|---|---|---|
| 1 | Range check | a docs-only range exits 0; a range touching a `.py` exits **non-zero**; a **two-commit** range whose first commit touches code exits **non-zero** (the v1 `HEAD`-scoped check passes that case — proven able to fail) `⟨F4⟩` |
| 2 | Seal check | passes on `## Doubt Gate — PASSED`; fails when absent; **and** fails on a STOP block quoting the heading; **and** the script greps **no** transcript `⟨F6⟩` |
| 3 | Preconditions | refuses (non-zero + printed reason) on an empty artifact, on a missing `BASE`, and when the bot's phase skill is **ambiguous** (a duplicate name means neither copy loads, so a lone name grep still passes) `⟨F14⟩` |
| 4 | Genesis case | phase 1 runs with no predecessor; the runner accepts a non-empty Confirmed Intent instead of a commit `⟨F5⟩` |
| 5 | Re-entry guard | a phase launched without `FLOW_ORCHESTRATED` is refused; with it, the contract carries the run-only-your-phase clause `⟨F12⟩` |
| 6 | Provenance output | prints the profile + session id; the word "author" appears **nowhere** in its output `⟨F8⟩` |
| 7 | Bound | the max wait is a single scripted value; a deliberately hanging phase is stopped at 900 s and reported `⟨F13⟩` |
| 8 | Flow text | flow-decide names the 4 Phase-A bots in order + refuse-not-launch; flow-build names @builder + range verification. The preservation half is checked as `diff -u <backup> <new> \| grep -c '^-[^-]'` over the TDD/simplify/PR step headings = 0 **after a `test -f` preflight** `⟨F8-c2⟩` `⟨F15-c2⟩` |
| 8b | Scope the status check | `git status --porcelain` is run **only against the paths this phase was authorised to touch** — an unscoped status cannot tell this phase's stray file from a sibling run's, so both directions misreport `⟨F10⟩` |
| 8c | Condition survey freshness | every machine-state row the preconditions rely on is **re-measured immediately before the run** and the values recorded; the cycle-1 survey was already stale when written `⟨F15⟩` |
| 9 | Refuted claims removed | `peer messaging is CLOSED` and `check whether the seal's commit author` are **absent** from `hermes-flow-pipeline` `⟨F9⟩` |
| 10 | Propagate + verify | all 7 pairs md5-identical; 7 backups present `⟨F7⟩` |
| 11 | Repo suites still pass | `python3 tests/test_hermes_install.py`, `test_ponytail_pack.py`, `test_codex_port.py`, `test_quality_gates.py` all exit 0 — adding scripts must not move a declared count |
| 12 | **Live rehearsal** | one real @architect phase driven by the runner, artifact verified; a deliberately empty prompt **refused**; the whole `/flow-decide` chain exercised including the genesis case `⟨F5⟩` |

## Success criteria

1. `flow-verify-phase.sh` proven able to fail in **four** modes: code-touching range, missing seal,
   quoted-seal STOP block, multi-commit range with code in a non-final commit `⟨F4⟩`.
2. `flow-run-phase.sh` refuses on a false premise, a missing `BASE`, and an ambiguous phase skill — each
   refusal demonstrated `⟨F3⟩` `⟨F14⟩`.
3. The full chain runs from `/flow-decide` in codemax including the genesis phase, and stops at the seal,
   with the seal read from the artifact and not the log `⟨F5⟩` `⟨F6⟩`.
4. No output claims authorship; the provenance line names a session, never an author `⟨F8⟩`.
5. The 900 s bound is a single scripted value, demonstrated stopping a hanging phase `⟨F13⟩`.
6. All 7 pairs md5-identical with backups; the four repo suites exit 0 `⟨F7⟩`.

## Out of scope

- Flipping `ui_meta.hermes-bots` or AgentChat identities — **already present and open**; nothing to flip
  `⟨F1⟩`. Peer messaging is not the control channel because it is fire-and-forget and title-gated, so it
  cannot sequence a supervisor that gates each launch on a verified artifact `⟨F2⟩`.
- The desktop group room.
- Changing the gate's ownership rule.
- Running these three initiatives through the new orchestration (single-agent by design).
