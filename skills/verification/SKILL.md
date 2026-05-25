---
name: verification
description: >
  Verify a task is actually complete before declaring done — no exceptions.
  Run the relevant tests, lint, type-checks, and feature checks. Triggers
  include "is this done", "verify", "before I mark complete", "final check",
  "ready to ship".
---

# Skill: Verification Before Completion

**When to invoke:** Before declaring ANY task complete. No exceptions.

---

## The Rule

> A task is not done when the code is written. A task is done when it is verified.
>
> **Loop until green (Karpathy):** If verification fails, fix the issues and re-verify. Don't just report failure — resolve it. Strong success criteria let you loop independently without asking the user "now what?"

---

## Verification Checklist

### Functional Verification
- [ ] All tests pass: `make test` / `npm run test`
- [ ] The specific behavior requested works end-to-end (manual test if needed)
- [ ] No regressions — the full test suite passes, not just the new tests
- [ ] Edge cases tested: empty input, null values, max/min boundaries, unauthorized access

### Code Quality Verification
- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] Python type checks: `mypy src/`
- [ ] Linting passes: `ruff check src/` / `npm run lint`
- [ ] No dead code left behind (commented-out blocks, unused imports)

### Spec Verification
- [ ] Re-read the original requirement
- [ ] Every bullet point in the requirement is implemented
- [ ] No features were silently dropped ("I'll do that in a follow-up")
- [ ] The implementation matches what was planned (or the plan was updated)

### Security Spot-Check
- [ ] No secrets in code
- [ ] User inputs validated at the API boundary
- [ ] Auth required on all non-public endpoints

---

## Verification Report

After completing verification, output:
```
## Verification Report
- Tests: ✅ N passing, 0 failing
- Type checks: ✅ No errors
- Lint: ✅ No issues
- Spec coverage: ✅ All requirements met
- Security: ✅ No issues found

Status: COMPLETE ✅
```

If anything fails:
```
Status: INCOMPLETE ❌
Blockers: [list what failed and why]
Next: [specific fix for each blocker — then re-verify]
```

---

## Red Flags (you're skipping verification when you shouldn't)
- "It worked in my quick test" — quick tests miss edge cases
- "The tests should pass" — run them, don't assume
- "I'll fix the lint later" — later never comes
- "That requirement wasn't important" — it was, you just didn't do it