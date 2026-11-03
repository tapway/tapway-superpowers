---
name: interview
description: >-
  Requirements extraction through structured one-question-at-a-time interviewing
  before any planning or building begins. Surfaces the real goal behind the stated
  request — who benefits, why now, what success looks like, constraints, out-of-scope.
  Feeds directly into /brainstorming or /plan. Triggers include "interview me",
  "stress-test my thinking", "help me figure out requirements", "what should we
  build", "I'm not sure what I want", "/interview".
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [requirements, planning, discovery, interviewing]
    related_skills: [brainstorming, writing-plans]
---

# Skill: Interview

**When to invoke:** Before brainstorming or planning, when a request is underspecified — missing who benefits, why now, success criteria, or constraints. Also when the user says "stress-test my thinking" or explicitly asks to be interviewed.

> **Note (Hermes):** In Hermes you can invoke this as a skill, or just ask me to interview you. The protocol below is identical to the Claude Code plugin — Hermes runs the same skills (interview → brainstorming → writing-plans → tdd → review → pr) through its own skill system.

## Core Principle

> Build the right thing before building the thing right.

Requests diverge from intent. This skill closes that gap through targeted questioning before any code, spec, or plan is written. A confirmed intent statement costs ten minutes; a wrong implementation costs days.

## Protocol

### Step 1 — Hypothesize
State your best reading of the request in one sentence. Add an honest confidence score (0–100%) and name exactly what's still missing.

```
My reading: You want [X] so that [Y].
Confidence: 60% — I don't yet know [what's missing].
```

### Step 2 — Ask One Question
Ask one focused question, paired with your hypothesis for the answer. Then stop. Wait for the response before asking the next question.

```
Question: [single question]
My guess: [your hypothesis for their answer]
```

**Focus on the highest-uncertainty dimension first:**

| Dimension | What to ask |
|---|---|
| **Who** | Who actually uses this — end user, internal team, or API consumer? |
| **Why now** | What changed that makes this urgent? What unblocks if you build it? |
| **Success** | What does "done" look like in production? How would you know it worked? |
| **Constraint** | What can't change — deadline, budget, tech stack, integration? |
| **Out of scope** | What are you explicitly NOT building? |

Never ask two questions at once. Compound questions let users answer only the easier one.

### Step 3 — Listen for Drift Signals
Watch for answers that reveal the request means something different than it sounds:

- **"Should want" language** — "best practice", "the right way", "everyone does it like..." → they may want validation, not a decision
- **Convention-deferring** — "whatever you think is fine" → they're uncertain, not flexible
- **Sophistication signaling** — using technical terms loosely → probe what they actually mean by them

When you spot a drift signal, reflect it back before continuing:
```
It sounds like [restatement]. Is that right, or is the actual goal [alternative]?
```

### Step 4 — Test the Stop Condition
After each answer, ask yourself: *Can I predict the user's reaction to the next three questions I would ask?*

- **Yes** → you have enough. Move to Step 5.
- **No** → one more question. Return to Step 2.

If you still can't predict after 7–8 rounds, something foundational is missing. Name it directly:
```
I'm stuck on [X]. Until I understand that, any plan I write will carry a critical assumption.
Can you help me with that specifically?
```

### Step 5 — Confirm Intent
Restate the full intent in structured form and ask for explicit confirmation:

```
## Confirmed Intent

**Outcome:** [what will exist or change]
**User:** [who benefits and how]
**Why now:** [what's driving the timing]
**Success:** [how you'll measure it in production]
**Constraints:** [non-negotiables — tech, timeline, integration]
**Out of scope:** [explicitly excluded]

Does this capture it? Any corrections before I move to [/brainstorming / /plan]?
```

Do not proceed until the user says yes (or gives corrections that you restate and confirm again).

## Output
The confirmed intent statement feeds directly into:
- `brainstorming` — as the problem framing
- `writing-plans` — as the requirements section

Save it to `docs/plans/intent-[feature].md` if the project has a `docs/plans/` directory.

## Hard Rules
- ❌ Never ask two questions at once
- ❌ Never start planning or coding before the intent is confirmed
- ❌ Never accept "whatever you think" as an answer — probe the uncertainty
- ❌ Never skip the explicit confirmation step (Step 5)
- ❌ Never run more than 8 rounds without naming what's blocking you
