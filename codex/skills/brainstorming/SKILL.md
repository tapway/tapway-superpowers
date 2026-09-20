---
name: brainstorming
description: >
  Explore approaches before writing code for a new feature, architecture decision,
  or complex bug. Use when there is even a 1% chance multiple approaches exist.
  Triggers include "let's brainstorm", "how should we approach", "what are the
  options for", "before we code", or any exploratory design question.
---

# Skill: Brainstorming

**When to invoke:** Before writing any code for a new feature, architecture decision, or complex bug. If there's even a 1% chance this applies, invoke it.

---

## Purpose

Explore the problem space thoroughly before committing to an approach. Generate multiple solutions, evaluate trade-offs, and arrive at the best path forward — **grounded in the platform-wide design, not just this repo**.

---

## Protocol

### 0. Deep Research (optional — unfamiliar domains only)

If the problem involves technology, services, or patterns your team hasn't used before, use Codex web search tools first to gather grounded options instead of guesses.

Skip this step if the domain is familiar.

### 1. Restate the Problem

Write out your understanding of what needs to be solved. Include:
- The user-facing goal
- Any constraints (performance, compatibility, team conventions)
- What "done" looks like

### Step 1.5 — Platform Context (MANDATORY, fail-closed)

Before generating ANY option, retrieve the platform-wide design context. This step is enforced — `codemax platform-context check` will fail the document (and the write hook will block it) if options exist without grounding.

**How:** run the platform context builder for the platform this repo belongs to:

```bash
codemax platform-context build --specs-dir "$TAPWAY_SPECS_DIR" --platform <platform>
```

That emits a deterministic, index-first pack (≈4,000 chars — an index, never the full docs; details are fetch-on-demand from the specs repo `tapway/platform-specs`).

**Then answer, per candidate area (cite the pack or the catalog for each):**

1. **Ownership & contracts** — which component owns the interface/symbol being touched? What contracts does it publish (`catalog:<platform>#<contract-id>`), and who consumes them?
2. **Existing capability** — does a component/service/ADR already cover this need? (This is the duplicate-killer.)
3. **Platform decisions** — which platform ADRs (ADR ids from the pack) constrain this area?
4. **Data model** — which existing entities/stores does this touch, and which repo owns them?
5. **Dependency direction** — what may call/import what, per the catalog's `consumes` edges?

**Routing decision before designing** (write it down):
- extend an existing platform spec → find it in the pack and cite it
- implement directly against an existing contract → cite the contract id
- create one new spec → say so explicitly
- decompose across multiple components → name each component from the catalog

Unanswered items are recorded as **`UNKNOWN (not retrieved: <what you tried>)`** — an explicit hole beats a silent assumption. Do NOT guess.

If the specs repo or the pack is unavailable, every option in the doc must carry an `UNKNOWN (not retrieved: platform pack unavailable)` row — the gate fails closed on missing grounding, not on missing infrastructure.

### 2. Name Your Confusion

Before generating solutions, articulate what's unclear:
- What assumptions are you making that might be wrong?
- What would you ask the user if you could ask one clarifying question?
- Is there anything about this problem that feels off or contradictory?

If you're confused about something, **say so explicitly.** Don't hide uncertainty behind confident-sounding options.

### 3. Generate Options (minimum 3)

For each approach:
- **Name** the approach clearly
- **Describe** how it works in 2-3 sentences
- **Platform Fit** — how it aligns with the platform context from Step 1.5 (citing contract ids / ADR ids / components), or `UNKNOWN (not retrieved: …)`
- **Pros:** What makes this good
- **Cons:** What makes this risky or limited
- **Complexity:** Low / Medium / High
- **Grounding:** `catalog:<platform>#<id>, ADR-…` (resolvable refs) — this line is what the gate parses

Options that would violate a platform contract or duplicate an existing capability MUST be listed with a **Rejected because platform:** line (cite the contract/ADR) — rejecting them explicitly is part of the record.

### 4. Evaluate

Score each option on:
- **Simplicity** — would a senior engineer call this overcomplicated? (Karpathy litmus test)
- **Platform fit** — does it align with the catalog's ownership and dependency direction?
- Fits team conventions (AGENTS.md / repo conventions)
- Testability
- Maintainability
- Speed to implement

### 5. Recommend

State the recommended approach and why. Flag any assumptions that, if wrong, would change the recommendation.

**Push back if warranted.** If the user's implied direction is more complex than necessary, say so. Propose the simpler alternative even if it wasn't one of the requested approaches.

### 6. Save Output

Save the full brainstorming session to:
```
docs/brainstorming/[topic-slug].md
```
Use kebab-case for the filename (e.g. `auth-flow-options.md`, `payment-provider-comparison.md`). This file is the team's record of why the chosen approach was selected — it must exist before moving to planning.

**Gate before commit** (fail-closed when `TAPWAY_BRAINSTORM_GATE=1`):
```bash
codemax platform-context check --specs-dir "$TAPWAY_SPECS_DIR" --platform <platform> --doc docs/brainstorming/[topic-slug].md
```
Every `## Option` section must carry a `Grounding:` line with resolvable citations or an explicit `UNKNOWN (not retrieved: …)` row. Fix the doc, not the gate.

Commit it immediately so the whole team can see it:
```bash
git add docs/brainstorming/[topic-slug].md
git commit -m "docs: add brainstorming output for [topic]"
```

### 7. Hand off

If proceeding, invoke the `writing-plans` skill next to turn the recommendation into an implementation plan.

---

## Red Flags (you're skipping brainstorming when you shouldn't)

- "This is obviously a simple X" — simple problems often have subtle gotchas
- "I've done this before" — past solutions may not fit this context
- "The user already told me what to do" — confirm you understand the *why*, not just the *what*
- "I know the platform from memory" — you don't; read the pack. Facts are recorded, not remembered.
