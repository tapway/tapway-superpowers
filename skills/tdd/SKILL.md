---
name: tdd
description: >
  Test-Driven Development — write a failing test before any production code.
  Use for every new feature, bug fix, refactor, or behavior change. The iron
  law of this project. Triggers include "TDD", "write a test first", "new
  feature", "bug fix", "behavior change".
---

# Skill: Test-Driven Development (TDD)

**When to invoke:** Any new feature, bug fix, refactor, or behavior change. The iron law: no production code without a failing test first.

---

## The Cycle: Red → Green → Refactor

```
RED    → Write a minimal test that describes the desired behavior. Run it. See it FAIL.
GREEN  → Write the simplest code that makes the test pass. Run it. See it PASS.
REFACTOR → Improve the code without changing behavior. Tests must still pass.
```

---

## Protocol

### RED Phase
1. Write one test that describes exactly what the code should do
2. Test name format: `test_[function]_[condition]_[expected_outcome]`
   - Python: `def test_create_user_with_duplicate_email_raises_error():`
   - TypeScript: `it('createUser throws when email already exists', ...)`
3. **Run the test. Confirm it fails with the right error** (not a syntax error — an assertion error or `NotImplementedError`)
4. If it passes before writing code — the test is wrong. Fix it.

### GREEN Phase
1. Write the **minimum** code to make the test pass
2. No gold-plating. No "while I'm here" additions.
3. **Simplicity rules (Karpathy):**
   - If the test doesn't need it, don't write it
   - No error handling for states that cannot occur
   - No abstractions for single-use code — extract only on the second duplication
   - **Litmus test:** would a senior engineer call this overcomplicated? If yes, simplify
4. Run the test. Confirm it passes.
5. Run the full test suite. Confirm no regressions.

### REFACTOR Phase
1. Is the code readable? Are names clear?
2. Is there duplication that can be removed?
3. Does it follow project conventions (CLAUDE.md)?
4. Run tests again after every refactor step.

### Commit
```bash
git add [files]
git commit -m "feat: [what behavior was added]"
```

---

## Stack-Specific Notes

### Python (pytest)
```python
# backend/tests/unit/test_user_service.py
import pytest
from src.services.user_service import UserService

def test_create_user_with_valid_data_returns_user():
    service = UserService()
    user = service.create(email="test@example.com", name="Test")
    assert user.id is not None
    assert user.email == "test@example.com"
```

### TypeScript (Jest + RTL)
```typescript
// frontend/src/services/__tests__/auth.test.ts
import { login } from '../auth'

it('login returns token on valid credentials', async () => {
  const result = await login({ email: 'test@example.com', password: 'valid' })
  expect(result.token).toBeDefined()
})
```

---

## The Iron Law
> If you wrote production code before the test, delete that code. Start with the test.

Keeping "reference code" while writing tests is a violation. It defeats the purpose of TDD.

---

## Exceptions (require explicit approval)
- Throwaway prototypes / spike branches
- Auto-generated code (migrations, types from OpenAPI spec)
- Pure configuration files (tailwind.config.ts, alembic.ini)