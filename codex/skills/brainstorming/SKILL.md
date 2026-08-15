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

Explore the problem space thoroughly before committing to an approach. Generate multiple solutions, evaluate trade-offs, and arrive at the best path forward.

---

## Protocol

### 0. Deep Research (optional — unfamiliar domains only)

If the problem involves technology, services, or patterns your team hasn't used before, run the **`$deep-research`** skill first (if installed in your skills set):

```
$deep-research what are the best options for [job queues / auth providers / payment gateways / ...] in a FastAPI + Next.js stack?
```

It fans out across multiple sources, fact-checks claims, and returns a cited report. Use that report as input to Step 1 below — it gives you grounded options instead of guesses.

Skip this step if the domain is familiar.

### 1. Restate the Problem
Write out your understanding of what needs to be solved. Include:
- The user-facing goal
- Any constraints (performance, compatibility, team conventions)
- What "done" looks like

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
- **Pros:** What makes this good
- **Cons:** What makes this risky or limited
- **Complexity:** Low / Medium / High

### 4. Evaluate
Score each option on:
- **Simplicity** — would a senior engineer call this overcomplicated? (Karpathy litmus test)
- Fits team conventions (AGENTS.md)
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