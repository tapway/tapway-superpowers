---
name: systematic-debugging
description: >
  Debug methodically — bug investigation, unexpected behavior, "works in
  staging but not prod", error messages, flaky or failing tests. Triggers
  include "debug", "why is X failing", "investigate this bug", "track down",
  "it works locally but not in prod".
---

# Skill: Systematic Debugging

**When to invoke:** Any bug investigation, unexpected behavior, "works in staging but not prod", error messages, failing tests.

> **Built-in alternatives:**
> - For code bugs with a clear repro: use the **`$bugfix`** skill (if available) — it enforces repro-first with a regression test and opens a PR automatically.
> - For production incidents needing a written root-cause report: use the **`$investigate`** skill (if available) — it runs parallel hypothesis subagents, adversarially refutes each, and produces a cited report.
>
> Use this skill when you want a guided, step-by-step debugging process without the automation of those built-ins.

---

## Protocol

### Step 1: Reproduce First (Non-Negotiable)

Before touching any code, reproduce the bug reliably.
- What exact steps trigger it?
- What is the expected behavior?
- What is the actual behavior?
- What is the exact error message / stack trace?

**Write a failing test that captures the bug before writing any fix.** This is the repro artifact — it proves the bug exists and will become the regression test.

```python
# Python: name it after the bug
def test_discount_returns_negative_when_percentage_exceeds_100():
    ...

# TypeScript
it('throws when discount percentage exceeds 100', () => { ... })
```

Confirm the test **fails** before continuing. If it passes, your repro is wrong — fix the test first.

### Step 2: Isolate
Narrow down where the bug lives:
- Is it frontend, backend, or the boundary between them?
- Add logging/print statements at key points to trace the execution path
- Check: does it happen with a minimal input? Which inputs trigger it vs don't?
- `git log --oneline -20` — when did this start? Use `git bisect` if the regression window is unclear.

**Name your confusion (Karpathy):** Before forming hypotheses, articulate what's unclear. What about this bug surprises you? What assumption are you making that might be wrong? Say it explicitly — don't skip to hypotheses.

### Step 3: Generate at Least 2 Hypotheses

For each hypothesis:
- What evidence supports it?
- What would disprove it?
- How would you test it?

Rank by likelihood. Test the most likely one first — don't test all of them speculatively.

If the bug is complex or in an unfamiliar system, generate hypotheses in parallel:
```
Hypothesis A: [state it]
  Evidence for: ...
  Evidence against: ...
  Test: ...

Hypothesis B: [state it]
  Evidence for: ...
  Evidence against: ...
  Test: ...
```
Adversarially check each — try to disprove your own most likely hypothesis before committing to it.

### Step 4: Test Hypotheses
- Add targeted logging
- Write a unit test that isolates the specific component
- Check git log — when did this start failing? (`git bisect` if needed)

### Step 5: Fix
Implement the minimal fix.
- The failing test from Step 1 must now pass
- Run the full test suite — no regressions
- **Surgical fix rule (Karpathy):** Touch only the code that causes the bug. No "while I'm here" improvements. The diff should tell a one-sentence story.
- Commit: `git commit -m "fix: [what was broken and how it's fixed]"`

The Step 1 test is now your **regression test** — it stays in the codebase permanently.

### Step 6: Post-mortem (for significant bugs)

For any bug that took >30 min or affected users in production:

```markdown
## Bug Post-mortem: [Bug title]
**Root cause:** [what caused it]
**Why it wasn't caught:** [what test/check was missing]
**Prevention:** [add test / update linting / update AGENTS.md convention]
**Regression test:** [test function name and file path]
```

Save to `docs/post-mortems/[date]-[slug].md` and commit it.

---

## Stack-Specific Debugging

### Python FastAPI
```bash
import logging
logger = logging.getLogger(__name__)
logger.debug("Value: %s", value)

uvicorn src.main:app --reload --log-level debug
```

### Next.js
```typescript
// Server Component
console.log('[DEBUG]', JSON.stringify(data, null, 2))
// Use React DevTools for component state
// Check Network tab for API response shapes
```

---

## When You're Stuck
- Re-read the error message literally — not your interpretation of it
- Check the most boring thing first (typos, wrong env var, wrong URL, stale cache)
- Ask: "What assumption am I making that might be wrong?"
- `git stash` and reproduce on a clean state
- If stuck after 2 hypothesis cycles: use `$investigate` for a fresh adversarial analysis