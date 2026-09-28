# Brainstorm: One entry point — the flow drives the bot team

- **Date:** 2026-09-28
- **Status:** Proposed (awaiting plan)
- **Author:** flow-decide run, codemax profile
- **Companion docs:** `headless-bot-orchestration` skill (procedure), `hermes-flow-pipeline` skill
  (current wiring)

## 1. Problem restated

`/flow-decide` and `/flow-build` and the five-bot team **duplicate the same purpose with no connection
between them**. Today the two systems are parallel: typing `/flow-decide` in any chat makes *that*
profile run the whole phase itself, while the team's delegation protocol cannot fire because no bot holds
`message_agent`. The owner's stated intent: **one entry point in his own CLI — `/flow-decide` in codemax
starts the team; he never types into an individual bot's chat.**

**User-facing goal:** `/flow-decide` typed in codemax drives Phase A across @decider → @architect →
@planner → @doubter and stops at a sealed plan; `/flow-build` drives Phase B in @builder. codemax
supervises and verifies; the bots do the phase work.

**Scope locked via interview:**
- **Architecture: subprocess room-runner** (option A).
- **These three initiatives are exempt from their own feature** — they run single-agent, because the
  orchestration does not exist yet (chicken-and-egg; stated, not glossed).

## 2. Current state (grounded survey)

| Fact | Measured value |
|---|---|
| `is_bot_mode_managed` | **True** — all six profiles + the root tree (sanctioned probe). *Corrected after doubt cycle 1: an earlier reading of "False" came from reading only top-level `profile.yaml` keys.* |
| Bot `profile.yaml` | `ui_meta = {'hermes-bots': {}}` — **the key is present**; it is nested inside `ui_meta`, which is why a top-level key dump missed it |
| `message_agent` eligibility | **the gate is open**: both conditions are met (a `hermes-bots` key exists, and a `Bot Chat`-titled session exists per profile) |
| `Bot Chat` session provenance | decider's row is **`source=cli`** — the title is reachable from the command line, *not* desktop-only |
| agentchat plugin | codemax yes; **decider/builder no** |
| Canonical `Bot Chat` sessions | decider, architect, planner, doubter, builder, **and codemax** have one |
| Bot cron jobs | none · Gateway | **default only** (PID 17283) · Desktop | **not running** |
| `bot_relay/roster.json` | `{"agents": []}` — wired, unused |
| Bot phase skills | all five resolve every skill their phase names |
| Headless invocation | `hermes -p <bot> chat -q "<prompt>" --oneshot` / `-Q` available |
| Authorship | all profiles share the box's git identity — **commit metadata cannot prove who wrote a seal** |

**The gate, precisely (re-measured).** `message_agent` is injected when (1) the **sending** session's
title is exactly `Bot Chat`, **and** (2) at least one profile carries a `hermes-bots` key. **Both hold on
this box today.** The CLI transport creates exactly that title
(`hermes -p <name> chat -c "Bot Chat" --create-if-missing -Q`), and decider's own row carries
`source=cli`. So the native path is *open*, and the earlier claim that it is closed was wrong.

## 3. Options

### A. codemax as subprocess room-runner (recommended, chosen)
codemax's flow skills become orchestrators: write prompt contracts (`docs/flow/<feature>/prompt-NN-<bot>.md`),
launch each phase as a fresh process (`hermes -p <bot> chat -q "$(cat …)" --oneshot`), verify the artifact
before launching the next, stop at the seal.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** delivers exactly the requested UX from the CLI; **works today with zero config change**; no
  `message_agent`, no Bot Chat, no gateway, no public identities; each phase is a fresh process so it
  always reads current disk state; the handoff is a file contract, which is auditable and survives
  context compression.
- **Cons:** codemax's context carries the orchestration overhead and must do the verification; a phase
  that stalls must be triaged by codemax (stall-vs-slow); nesting agent processes is heavier than a
  single session.
- **Complexity:** Medium-High.

### B. Bot Mode peer messaging (the native path)
Add `ui_meta.hermes-bots: {}` to each bot's `profile.yaml`; restart the gateway (the protocol section is
cached for the process lifetime); bots then hold `message_agent`.
- **Pros:** the framework-native channel; attribution and delivery receipts come free.
- **Cons (corrected in doubt cycle 1 — the earlier reason was refuted):** it is **not** unreachable from
  the CLI. The gate keys on a session *title*, and `hermes -p <name> chat -c "Bot Chat" --create-if-missing`
  produces one from the command line. The real objections are different and narrower: (a) the entry point
  the owner asked for is his **everyday** CLI session, not a specially-titled one, so B still asks him to
  work in a different surface; (b) `message_agent` is **fire-and-forget** — it never returns the reply,
  which arrives later as a background completion — so a supervisor that must verify each artifact *before*
  launching the next phase cannot use it as its control channel; (c) the delivery layer holds one surface
  per Bot Chat, so a bot mid-turn refuses inbound DMs with `target_busy`, and a verification loop that
  messages a bot it is simultaneously driving manufactures a false "reply failed".
- **Complexity:** Medium (config) + High (correct usage).

### C. Desktop group room
- **Pros:** the one multi-bot channel that needs no `message_agent`; the desktop drives each turn.
- **Cons:** desktop-only — the opposite of "type it in my CLI"; needs the desktop app running and the
  hosted-room service; `hosted_room_events = 0` records it as never used.
- **Complexity:** Low-Medium.

### D. Status quo (type into each bot's chat)
- **Pros:** zero work; both halves already work in isolation.
- **Cons:** the redundancy the owner rejected; the team's SOUL-level delegation protocol stays a fiction.
- **Complexity:** None.

**Rejected because it fails the requirement — restated honestly:** option B as the *primary* mechanism,
because the control channel it offers is fire-and-forget and title-gated. It is **reachable** from a CLI
session (see above); what it cannot do is sequence a supervisor that must gate each launch on the
previous phase's verified artifact. The decision stands, the stated reason is corrected.
**Rejected because it is the wrong surface:** option C — a desktop feature cannot satisfy "one entry
point in my CLI".
**Not deferred — already done:** the `hermes-bots` key is **already present** on every bot profile
(measured, mtime 2026-09-21), so there is nothing left to flip. The earlier "flip it later" item is
deleted as factually empty.

## 4. Evaluation

| Option | Delivers CLI UX | Works today | Verifiable handoff | Risk |
|---|---|---|---|---|
| **A** | **Yes** | **Yes** | Yes (file contracts + per-phase logs) | Medium |
| B | No | No (config needed) | Yes | High (misuse) |
| C | No | No | Partly | Low |
| D | No | Yes | No | Low |

## 5. Recommendation

**Option A.** Written into the plan as hard requirements:

1. **Preconditions, not promises.** Before each launch, assert the precondition and print a
   refuse-not-launch line: the previous phase's commit exists and is docs-only, the consumed artifact is
   non-empty (`test -s`), and the bot resolves its phase skills. A launch on a false premise burns a
   whole cycle.
2. **Verify the artifact, never the summary.** A bot's final message is a claim. After each phase:
   `git show --numstat HEAD` (right files, docs only), `git status`, and whether the seal heading exists.
   Spot-check two or three load-bearing `file:line` claims against the tree.
3. **Provenance, not commit metadata.** Because every profile shares the box's git identity, the seal's
   authorship must be proven from the per-phase log or the session row in that profile's `state.db`.
4. **Stage exact paths.** Never `git add docs/flow` — an over-broad add fabricates an audit trail by
   sweeping another run's files.
5. **Bounded.** Per-phase timeout and a stall-vs-slow triage rule; on exhaustion, stop in-turn.

**Assumptions that would change this recommendation:**
- If nested `hermes -p <bot>` launches cannot complete a phase inside a sane timeout, the design moves to
  a shell runner script invoked once per phase (same contracts, human between phases).
- If the owner later wants the desktop Bots-tab experience, option B is additive — but it will still not
  be the CLI entry point.

## 6. Save output

This file.

## 7. Hand off

`writing-plans` → `docs/plans/2026-09-28-flow-bot-orchestration.md`.

## Red flags

- ❌ Launching the next phase on the previous phase's prose rather than its artifact
- ❌ Reporting "role separation verified" from a clean `git log` (shared git identity proves nothing)
- ❌ An unbounded per-phase wait with no stall-vs-slow triage
- ❌ `git add` on a directory that may hold another run's files
- ❌ Letting the flow's own decide phase depend on orchestration that does not exist yet

## 8. Doubt cycle 1 corrections

Revised after the Step 4 gate returned 48 findings across the three plans
(`docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`). Changes here are limited to statements that
were **false on this machine** or that inverted the pack's own rules; each was re-measured before it was
written. Findings that are plan-level (criteria shape, scope, ordering) are fixed in the plan, not here.
