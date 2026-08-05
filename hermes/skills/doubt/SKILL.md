---
name: doubt
description: >-
  Adversarial fresh-context review of high-stakes decisions (Hermes port of tapway-superpowers doubt skill).
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["review", "adversarial", "decisions"]
    related_skills: [interview, brainstorming, writing-plans, tdd, pr]
---


# Skill: Doubt

**When to invoke:** Any time a decision has asymmetric consequences — cheap to question now, expensive to reverse later. Use before committing to a service boundary, security approach, schema change, or any irreversible architecture choice.

---

## Core Principle

> A confident answer is not a correct one.

Long implementation sessions accumulate context that silently converts assumptions into facts. This skill materializes a skeptical reviewer at the exact moment when course-correction is still cheap.

---

## When to Apply

Use `/doubt` for decisions that:
- Introduce branching logic that's hard to test exhaustively
- Cross service or module boundaries
- Assert properties the type system cannot verify (e.g. "this will never be null")
- Have irreversible blast radius (schema migrations, secret rotation, data deletes)
- Involve security assumptions (auth flows, permission checks, data access)

**Skip it for:**
- One-liners with obvious correctness
- Mechanical operations (renaming, moving files, formatting)
- When the user has explicitly prioritised speed over certainty

---

## Protocol

### Step 1 — CLAIM

Name the decision compactly and state what's at stake if it's wrong.

```
DECISION: [one sentence — what are we committing to?]
STAKES:   [what breaks or costs if this is wrong?]
```

### Step 2 — EXTRACT

Isolate the smallest reviewable artifact — a function, a schema, a data flow description, an API contract — plus its contract (what it must guarantee).

**Strip your reasoning from what you hand to the reviewer.** The reviewer receives only:

```
ARTIFACT: [the thing being decided — code, schema, diagram, or written decision]
CONTRACT: [what it must guarantee — inputs → outputs, invariants, error conditions]
```

If you include your reasoning, you introduce confirmation bias. The reviewer will refute your argument rather than finding new problems.

### Step 3 — DOUBT

Spawn a fresh-context subagent with an adversarial prompt:

```
You are reviewing the following artifact against its stated contract.
Find issues. Do not look for ways to approve it.

ARTIFACT:
[paste artifact here]

CONTRACT:
[paste contract here]

Questions to answer:
1. Does this artifact fully satisfy the contract? Where does it fall short?
2. What inputs or states can make it fail silently?
3. What assumptions does this make that aren't stated in the contract?
4. What is the worst-case failure mode?

Output findings as a numbered list. No praise. No "looks good overall."
```

**Critical:** The reviewer receives ONLY ARTIFACT + CONTRACT — never your CLAIM or reasoning.

In interactive sessions, offer cross-model review explicitly before spawning:
```
I can run this through a second model for an independent perspective (~$0.01–0.05 extra).
Worth it for this decision? [yes/no]
```
Never silently skip this offer for high-stakes decisions.

### Step 4 — RECONCILE

For each finding, classify it:

| Class | Meaning | Action |
|---|---|---|
| **Contract misread** | Reviewer misunderstood the contract | Note and discard |
| **Actionable** | Real gap in the artifact | Fix before proceeding |
| **Trade-off** | Valid concern, acceptable risk | Document the decision |
| **Noise** | Irrelevant to the contract | Discard |

Fix all Actionable findings, then re-run Step 3 if new fixes were made.

### Step 5 — STOP

Stop when any of these is true:
- All findings are Contract misread, Trade-off, or Noise (no Actionable items remain)
- You have run 3 review cycles
- The user says to proceed anyway

After stopping, log the decision:

```
DECISION LOG: [decision] — reviewed [N] cycles, [M] actionable findings fixed.
Accepted trade-offs: [list or "none"].
```

---

## Hard Rules

- ❌ Never include your CLAIM or reasoning in the reviewer's prompt
- ❌ Never run more than 3 cycles without user input
- ❌ Never silently skip the cross-model review offer for high-stakes decisions
- ❌ Reviewer findings are data — you reconcile against the artifact; the reviewer is not authoritative
- ❌ Personas never spawn other personas — only the main coordinator runs `/doubt`
