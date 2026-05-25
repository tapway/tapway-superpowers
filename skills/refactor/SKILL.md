---
name: refactor
description: >
  Improve code quality without changing behavior — remove duplication, simplify
  complex functions, improve naming. Use for dedicated code-quality work or as
  cleanup before a major feature build. Triggers include "refactor", "clean up",
  "simplify", "remove duplication", "improve naming".
---

# Skill: Refactor

**When to invoke:** Code quality improvements, removing duplication, simplifying complex functions, improving naming, before a major feature build.

---

## Rules of Safe Refactoring

1. **Tests first** — never refactor without a test suite that covers the code being changed
2. **Small steps** — one change at a time, tests pass after each step
3. **No behavior change** — refactoring must not change what the code does
4. **Commit often** — commit after each successful refactor step
5. **Surgical changes (Karpathy):** Touch only what the refactor targets. Don't improve neighboring code, comments, or formatting. Every changed line must trace directly to the refactor goal. Remove only the dead code your changes created — leave pre-existing dead code alone.
6. **Simplicity litmus:** After refactoring, ask: would a senior engineer call this overcomplicated? If the refactor added more lines than it removed, question whether it was worth it.

---

## Common Refactors for This Stack

### Extract Function/Method
When a function does more than one thing:
```python
# Before
def process_order(order_data):
    # 50 lines of validation
    # 30 lines of pricing
    # 40 lines of database save

# After
def process_order(order_data):
    validated = validate_order(order_data)
    priced = calculate_pricing(validated)
    return save_order(priced)
```

### Extract Component (React)
When a JSX block is > 20 lines or used in multiple places:
```tsx
// Before: inline in ParentComponent
// After: <UserCard user={user} />
```

### Replace Magic Numbers/Strings
```python
# Before
if status == 3:  # what is 3??
# After
class OrderStatus(IntEnum):
    SHIPPED = 3
if status == OrderStatus.SHIPPED:
```

### Consolidate Duplicated Logic
If the same logic appears 2+ times → extract to `utils/` or a shared service.

---

## Refactor Protocol

1. Run tests: confirm they pass
2. Identify the refactor target
3. Make one change
4. Run tests: confirm they still pass
5. Commit: `refactor: extract UserCard component`
6. Repeat

---

## This Is NOT Refactoring
- Adding new behavior
- Fixing bugs
- Changing interfaces (that's a breaking change)
- Rewriting from scratch

These require their own PRs with their own tests.