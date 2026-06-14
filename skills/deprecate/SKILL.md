---
name: deprecate
description: >
  Safe removal of APIs, endpoints, feature flags, or internal modules with migration
  support. Requires a tested replacement before any removal, uses Strangler/Adapter/
  Feature-flag patterns, distinguishes advisory from compulsory deprecation, and
  verifies zero active usage before deleting anything. Triggers include "deprecate
  this", "remove this API", "sunset this feature", "migrate away from X",
  "clean up old code", "/deprecate".
---

# Skill: Deprecate

**When to invoke:** When removing an API endpoint, internal module, feature, or dependency. Also when addressing "zombie code" — unmaintained systems with active consumers and no owner.

---

## Core Principle

> Code is a liability, not an asset. Every line carries maintenance cost.

Keeping old code "just in case" accumulates silent debt: security patches, test coverage, onboarding confusion, and integration weight. This skill makes removal safe by enforcing that a tested replacement exists before anything is touched.

---

## Protocol

### Step 1 — Decision Gate

Before any deprecation work, answer these five questions:

```
1. Does this provide unique value no replacement can cover?  → If yes, stop.
2. How many consumers depend on it?
   grep -r "[name]" --include="*.py" --include="*.ts" --include="*.tsx" | grep -v test
3. Does a tested replacement already exist?                  → If no, build it first (Step 2).
4. What is the migration effort per consumer?                (minutes / hours / days)
5. What is the ongoing maintenance cost of keeping it?
```

If question 1 is yes, close the ticket. Everything else is negotiable.

### Step 2 — Build the Replacement First

**Never deprecate before the replacement is tested.**

Checklist before any deprecation signal goes out:
- [ ] Replacement exists and has test coverage (pytest / jest)
- [ ] Replacement satisfies the same contract as the original (inputs → outputs, error conditions)
- [ ] Migration path is documented (see Step 4)
- [ ] Replacement is deployed to staging

For internal functions or modules without tests, write characterization tests against the old code first (see `/refactor` Protocol B), then build the replacement to match.

### Step 3 — Choose Deprecation Type

| Type | When to use | Enforcement |
|---|---|---|
| **Advisory** | Consumers can migrate voluntarily; no security risk | Warnings + docs; old code keeps running |
| **Compulsory** | Security risk, unsustainable maintenance, or licensing issue | Hard removal date (min 2 sprints); block new consumers |

**Mark the code immediately:**

**Python — advisory:**
```python
import warnings

def old_endpoint():
    warnings.warn(
        "old_endpoint() is deprecated. Use new_endpoint() instead. "
        "Migration guide: docs/migrations/old-to-new.md",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_endpoint()
```

**FastAPI — compulsory (with Sunset header):**
```python
@router.get("/v1/payments", deprecated=True)
async def old_payments(response: Response):
    response.headers["Sunset"] = "Sat, 01 Jan 2027 00:00:00 GMT"
    response.headers["Link"] = '</v2/payments>; rel="successor-version"'
    return await new_payments()
```

**TypeScript — advisory:**
```typescript
/** @deprecated Use newFunction() instead. See docs/migrations/old-to-new.md */
export function oldFunction() {
  console.warn('oldFunction() is deprecated. Use newFunction() instead.');
  return newFunction();
}
```

### Step 4 — Write the Migration Guide

Write `docs/migrations/[old-name]-to-[new-name].md` before migrating any consumer:

```markdown
# Migration: old_endpoint → new_endpoint

## Why
[one sentence — why is the old one going away?]

## What Changed
[interface diff — inputs, outputs, error conditions, breaking changes]

## How to Migrate

Before:
\`\`\`python
result = old_endpoint(user_id, amount)
\`\`\`

After:
\`\`\`python
result = new_endpoint(user_id=user_id, amount_cents=amount)
\`\`\`

## Timeline
- Advisory since: [date]
- Compulsory removal date: [date or "none"]

## Questions
[Slack channel or GitHub issue link]
```

### Step 5 — Migrate Consumers Incrementally

Choose a migration pattern based on blast radius:

**Strangler Pattern — for endpoints/services (traffic-level migration)**
```
Old endpoint running → Route X% of traffic to new endpoint → Increase X% → Remove old
```
Use a feature flag or API gateway routing rule. Never flip to 100% without a monitoring window.

**Adapter Pattern — for internal modules (code-level migration)**
```python
# Adapter: translates old call signature to new implementation
def old_function(arg1, arg2):
    """Temporary adapter — remove once all callers are migrated."""
    return new_function(combined=f"{arg1}:{arg2}")
```
Migrate callers one by one. Remove the adapter only when grep returns zero hits.

**Feature Flag Pattern — for UI features or A/B scenarios**
```python
if feature_flags.is_enabled("use_new_payment_flow", user_id):
    return new_payment_flow()
return old_payment_flow()  # remove once flag is at 100% and stable
```

Never migrate all consumers at once. Staged migration means a rollback affects only the current batch.

### Step 6 — Verify Zero Usage Before Removal

Before deleting any code, verify no active consumers remain:

```bash
# Find all usages (excluding tests and the deprecated file itself)
grep -r "old_endpoint\|old_function\|/v1/old-path" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  | grep -v "__pycache__" | grep -v ".test." | grep -v "deprecated"

# For external APIs: check production logs
# Requirement: zero hits in the last 14 days, not just today
```

**Zero-usage bar:**
- Internal functions: zero grep hits is sufficient
- External API endpoints: zero production traffic for 14 consecutive days

### Step 7 — Remove and Document

Only after Step 6 passes:

```bash
git rm path/to/old_file.py
# OR delete the function/class from its file

git commit -m "chore: remove deprecated old_endpoint (replaced by new_endpoint since [date])"
```

Update `CHANGELOG.md`:
```markdown
### Removed
- `old_endpoint` — deprecated since [date], replaced by `new_endpoint` (see docs/migrations/)
```

Keep `docs/migrations/[name].md` for one sprint post-removal — teammates may be mid-migration. Delete it after that.

---

## Zombie Code Protocol

Zombie code = unmaintained with active consumers and no owner.

If you find zombie code:
1. Find the last owner: `git log --follow -p [file] | grep "^Author:" | head -3`
2. Either assign an owner or start compulsory deprecation immediately
3. Never leave zombie code without a resolution — "I'll deal with it later" is how it stays zombie for three years

---

## Checklist Before Removal

- [ ] Decision gate passed (unique value, consumer count, replacement exists)
- [ ] Replacement is tested and deployed to staging
- [ ] Deprecation warnings or Sunset headers in place
- [ ] Migration guide written at `docs/migrations/`
- [ ] All consumers migrated (zero grep hits or 14 days zero production traffic)
- [ ] `CHANGELOG.md` updated with `### Removed` entry
- [ ] Migration doc scheduled for deletion 1 sprint post-removal

---

## Hard Rules

- ❌ Never remove before the replacement is tested and deployed
- ❌ Never set a compulsory deadline shorter than 2 sprints
- ❌ Never skip the zero-usage verification step
- ❌ Never leave zombie code without an owner or active deprecation plan
- ❌ Never delete the migration doc at the same time as the code — keep for 1 sprint
