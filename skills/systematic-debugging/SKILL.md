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

---

## Protocol

### Step 1: Reproduce
Before doing anything else, reproduce the bug reliably.
- What exact steps trigger it?
- What is the expected behavior?
- What is the actual behavior?
- What is the exact error message / stack trace?

Write a failing test that captures the bug **before** fixing it.

### Step 2: Isolate
Narrow down where the bug lives:
- Is it frontend, backend, or the boundary between them?
- Add logging/print statements at key points to trace the execution path
- Check: does it happen with a minimal input? Which inputs trigger it vs don't?

**Name your confusion (Karpathy):** Before forming hypotheses, articulate what's unclear. What about this bug surprises you? What assumption are you making that might be wrong? If something feels off, say so explicitly — don't just move to the next hypothesis.

### Step 3: Hypothesize
Form at least 2 hypotheses about the root cause. For each:
- What evidence supports this hypothesis?
- What would disprove it?
- How would you test it?

### Step 4: Test Hypotheses
Test the most likely hypothesis first:
- Add targeted logging
- Write a unit test that isolates the specific component
- Check git log — when did this start failing? (`git bisect` if needed)

### Step 5: Fix
Implement the minimal fix. Don't refactor while fixing.
- The failing test from Step 1 should now pass
- Run the full test suite — no regressions
- **Surgical fix rule (Karpathy):** Touch only the code that causes the bug. No "while I'm here" improvements to neighboring code. No error handling for states the fix doesn't introduce. The diff should tell a one-sentence story.

### Step 6: Post-mortem (for significant bugs)
For bugs that took >30 min or affected users:
- Root cause: [what caused it]
- Why it wasn't caught: [what test/check was missing]
- Prevention: [add test / update linting / update CLAUDE.md convention]

---

## Stack-Specific Debugging

### Python FastAPI
```bash
# Add debug logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Value: %s", value)

# Run with reload
uvicorn src.main:app --reload --log-level debug
```

### Next.js
```typescript
// Server Component debugging
console.log('[DEBUG]', JSON.stringify(data, null, 2))

// Check network tab for API responses
// Use React DevTools for component state
```

---

## When You're Stuck
- Take a step back — re-read the error message literally
- Check the most boring thing first (typos, wrong env var, wrong URL)
- Ask: "What assumption am I making that might be wrong?"
- `git stash` and reproduce on a clean state