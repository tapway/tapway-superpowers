# Re-scope decision: flow-drives-the-bots

**Date:** 2026-09-28 · **Status:** supersedes the chain scope of `2026-09-28-flow-bot-orchestration.md`
**Decided by:** owner ("proceed with the recommendations"), on the doubt gate's evidence.

## Why this is re-scoped rather than pushed through another cycle

The orchestration plan took 16 findings in cycle 1 and 21 in cycle 2, and the surviving items are
**design-level**, not criteria-shape. Fixing criteria does not close them:

| Gap | Why a fix does not close it |
|---|---|
| **Genesis is circular** | `@decider` owns the Confirmed Intent, but `/interview` is explicitly *interactive* and cannot run headless. A phase-1 precondition of "a non-empty intent document" cannot be satisfied by the pipeline that needs it. |
| **The re-entry guard cannot work as specified** | `FLOW_ORCHESTRATED=1` is **inherited** by child processes (measured), so it cannot distinguish a nested launch from the top-level one — it either refuses the legitimate entry point or refuses every child. |
| **The structured evidence does not exist** | `state.db`'s `sessions` table has no gate/seal/phase column (schema inspected). The only structured signal the framework documents is a `messages` query — i.e. the transcript, which the plan forbids. |
| **Unbounded tree** | The plan asserts a timeout bounds the work, but nothing kills a process *group*; a nested grandchild outlives the parent's bound. Untested either way. |
| **Interactive phases** | `/interview` is interactive; a headless bot cannot ask the owner anything, so it would invent a Confirmed Intent — the exact failure the flow's own red flags name. |

The background literature in the loaded skills is explicit that multi-agent teams do **not** beat a single
strong model on one-shot work, and the only durable wins are cost-splitting, enforced role separation, and
per-role memory. Two cycles of evidence say this design keeps acquiring risk in new places rather than
converging.

## The re-scoped increment (smallest thing that can actually be verified)

**One phase, driven by hand, with the human between phases.** No chain automation until a single phase is
proven end to end.

Kept:
- **File contracts** — `docs/flow/<feature>/prompt-NN-<bot>.md`, with sentinel lines, owned by a real task.
- **Range verification** — `BASE` pinned by `git rev-parse HEAD` before the launch; the evidence is
  `git diff --numstat BASE..HEAD`, **non-empty** for both phases (an empty range is not "docs only", it is
  "nothing happened"), Phase A additionally docs-only, Phase B additionally within the authorised file set.
- **Artifact verification over summaries** — the bot's final message is a claim, never the evidence.
- **`--query-file`**, not `-q "$(cat …)"`, so a contract containing `$(...)` or backticks is not
  shell-interpreted.
- **A bound** — one scripted value, with stall-vs-slow triage.

Dropped or deferred:
- **The 4-phase chain**, and with it the genesis problem: the owner authors `docs/flow/<feature>/intent.md`
  in the CLI *before* any launch, so no headless phase needs to run `/interview`.
- **The re-entry guard — made moot instead of fixed.** The supervisor text is **not propagated into the bot
  profiles**. The bots keep their own flow skills; only codemax carries the orchestration runbook. A worker
  therefore has no orchestration text to re-enter, which removes the hazard at its source rather than
  guarding against it. This also removes the "7 pairs md5-identical" requirement, which was the mechanism
  that forced the supervisor text into the workers.
- **Peer messaging** (`message_agent`) — reachable from a CLI session titled `Bot Chat`, but fire-and-forget,
  so it cannot sequence a supervisor that gates each launch on a verified artifact. Unchanged decision,
  corrected reason.
- **Any edit to the bots' `SOUL.md`** delegation language.

## Consequence for the doubt gate

`2026-09-28-flow-bot-orchestration.md` is retained as the **design record** and is not sealed. Sealing is
sought only for the two initiatives whose remaining findings are criteria-shape
(`2026-09-28-ponytail-flow-assimilation.md`, `2026-09-28-platform-grounding-retrieval.md`). This re-scope
is itself the deliverable for initiative 3 at this stage; the chain can be re-planned from it once one
phase has been rehearsed against real bots.
