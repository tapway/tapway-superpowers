---
name: code-review
description: >-
  Three-tier code review (Critical/Warning/Suggestion) (Hermes port of tapway-superpowers code-review skill).
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["code-review", "quality", "pull-request"]
    related_skills: [interview, brainstorming, writing-plans, tdd, pr]
---


# Skill: Code Review

**When to invoke:** Before opening a PR, when asked to review code, when reviewing your own changes before committing.

---

## Two Modes

### Requesting a Review (self-review before PR)
1. Run `git diff main...HEAD` to see all changes
2. Apply the checklist below
3. Fix all Critical and Warning issues before opening PR
4. Open PR with the template from `.github/pull_request_template.md`

### Receiving a Review (responding to reviewer feedback)
1. Read every comment — don't skim
2. For each comment: Acknowledge, Fix, or Discuss (never silently ignore)
3. Re-run tests after all fixes
4. Request re-review only when all items are resolved

---

## Review Checklist

### 🔴 Critical (block merge)
- [ ] No secrets, credentials, or API keys in code
- [ ] No SQL string interpolation (use parameterized queries)
- [ ] All user inputs validated (Zod on frontend, Pydantic on backend)
- [ ] Auth/authorization checks on all non-public endpoints
- [ ] No `console.log` / `print` with sensitive data in production paths
- [ ] No `any` type in TypeScript (unless explicitly annotated with reason)

### 🟡 Warnings (should fix, discuss if not)
- [ ] Error cases all handled (no silent failures)
- [ ] No N+1 queries (use `.select_related()` / eager loading)
- [ ] Functions < 50 lines; files < 300 lines
- [ ] Tests cover the happy path AND the key error paths
- [ ] Naming is clear — no abbreviations, no `data`, `stuff`, `temp`
- [ ] **No scope creep (Karpathy):** Every changed line traces to the stated goal. Flag changes to files or logic outside the PR's scope — even if they seem like improvements
- [ ] **No unnecessary abstractions:** Don't extract single-use code into helpers, don't add flexibility that isn't needed yet

### 🔵 Suggestions (nice to have)
- [ ] **Simplicity check:** Could this be shorter? If 200 lines can become 50, say so
- [ ] Is there a reusable utility here?
- [ ] Missing docstring on public function?
- [ ] Would a type alias make this more readable?

---

## Output Format

```markdown
## Code Review

### Summary
[1-2 sentence overview of what the change does]

### Issues

**Critical**
- [ ] `src/api/auth.py:42` — SQL query uses string interpolation → use `db.execute(text(...), {"param": value})`

**Warnings**
- [ ] `UserService.create()` doesn't handle duplicate email → add try/except for `IntegrityError`

**Suggestions**
- [ ] Extract the token validation into a shared `verify_token()` utility

### Verdict
❌ Request Changes / ✅ Approve
```