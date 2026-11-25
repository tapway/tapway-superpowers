---
name: security-audit
description: >
  Audit code touching auth, payments, user data, file uploads, external APIs,
  admin functions, or database queries against the OWASP Top 10. Triggers
  include "security review", "audit auth", "check for vulnerabilities",
  "is this safe", "before we ship sensitive code".
---

# Skill: Security Audit

**When to invoke:** Any code touching auth, payments, user data, file uploads, external APIs, admin functions, or database queries.

> **Two review scopes — pick the right one:**
>
> | Scope | When to use |
> |---|---|
> | `$security-audit` on the current branch diff only | Pre-PR, fast, targeted — "does this change introduce a vulnerability?" |
> | `$security-audit` on the full codebase | Pre-launch, after major refactors, onboarding a new component — "is the whole system secure?" |
>
> Run a targeted review on the diff before every PR that touches sensitive code. Run `$security-audit` on the full system when you need confidence in the whole stack.

---

## OWASP Top 10 Checklist for This Stack

### A1 — Broken Access Control
- [ ] Every API route has explicit auth check (FastAPI `Depends(get_current_user)`)
- [ ] Role-based checks where applicable (`current_user.role == "admin"`)
- [ ] No direct object reference without ownership check (e.g., `WHERE user_id = current_user.id`)
- [ ] Next.js middleware protects all `/dashboard/*` routes

### A2 — Cryptographic Failures
- [ ] Passwords hashed with bcrypt / argon2 (never MD5/SHA1)
- [ ] JWTs signed with strong secret (≥ 256 bits), stored in httpOnly cookies
- [ ] No sensitive data in localStorage
- [ ] HTTPS enforced in production

### A3 — Injection
- [ ] All SQL uses parameterized queries or ORM (no f-strings in queries)
- [ ] User input never passed to `eval()`, `exec()`, `subprocess` unvalidated
- [ ] Template rendering uses auto-escaping (React handles this; Jinja2 use `|e`)

### A4 — Insecure Design
- [ ] Rate limiting on auth endpoints (`slowapi` for FastAPI)
- [ ] Account lockout after N failed logins
- [ ] Password reset tokens are single-use and expire

### A5 — Security Misconfiguration
- [ ] No debug mode in production (`DEBUG=False`)
- [ ] No default credentials
- [ ] CORS configured to specific origins (not `*` in production)
- [ ] Error responses don't expose stack traces to users

### A6 — Vulnerable Components
- [ ] `npm audit` passes / warnings reviewed
- [ ] `pip-audit` or `safety check` passes
- [ ] No pinned versions with known CVEs

### A7 — Auth Failures
- [ ] Session tokens invalidated on logout
- [ ] JWT expiry set (access: 15min, refresh: 7d)
- [ ] No auth tokens in URL parameters (use headers/cookies)

### A10 — SSRF
- [ ] URL parameters for external fetches are validated against an allowlist
- [ ] Internal services not reachable from user-supplied URLs

---

## Auth-Design Review (beyond OWASP items)

The OWASP checklist catches *checklist-level* auth mistakes. This section
catches **auth-design flaws** — the highest-severity real-world vulnerabilities
(IDOR, missing RBAC, weak OAuth flows) that a static checklist misses. Run this
when the audit touches auth, sessions, tokens, or permission logic.

### Design Questions

- [ ] **RBAC/ABAC matrix exists** — for every user role (admin, member, viewer…), is there an explicit matrix of which resources/actions each role can access? If the answer is "we don't have roles yet", that's a finding.
- [ ] **IDOR check** — every endpoint that takes an object ID must verify the user can access *that object* (not just "is logged in"). `GET /users/{id}` and `GET /projects/{id}` are classic IDOR sites.
- [ ] **Object-level vs function-level auth** — admin-only functions exist (*function-level*), but does a regular user's request to `POST /admin/...` get rejected? Every function-level check must also be enforced server-side, never hidden in the UI.
- [ ] **OAuth flow correctness** — state parameter on the auth-code flow (CSRF), PKCE required for public clients, redirect URIs validated against an allowlist, auth-code exchanged server-side only.
- [ ] **JWT design** — algorithm pinned (`alg: HS256` etc., `jwt.sign` with explicit algorithm, never `"alg": "none"`), expiry short (access 15min), refresh rotation, no sensitive claims in the payload.
- [ ] **Session design** — session ID entropy ≥ 128 bits, httpOnly + Secure cookies, SameSite policy, session fixation protection (new session ID after login), server-side invalidation on logout.
- [ ] **Permission re-check on nested resources** — can a user access `/projects/{pid}/tasks/{tid}` where the task belongs to a project the user can't see?
- [ ] **Default-deny** — is the default posture "deny unless explicitly allowed"? Missing annotations/attributes should fail closed, not open.

### Design-Flaw Finding Template

```markdown
[IDOR|Missing-RBAC|Weak-OAuth|JWT|Session|Default-Deny]
Path: [endpoint / file]
Flaw: [what a malicious user can do]
Severity: Critical/High/Med
Fix: [concrete fix — e.g. "add owner check in Service layer", "enforce PKCE"]
```

---

## Quick Scan Commands

```bash
# Python dependency vulnerabilities
pip install pip-audit && pip-audit

# Node dependency vulnerabilities
npm audit --audit-level=high

# Secrets in codebase
grep -rE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]{8,}" src/ --include="*.py" --include="*.ts"
```

---

## Output Format

```markdown
## Security Audit: [Component]

### Critical
- [Issue] at [file:line] — [Description and fix]

### High
- [Issue] at [file:line] — [Description and fix]

### Medium / Low
- [Issue] — [Description]

### Verdict
✅ Clear to ship / ❌ Must fix [N critical] before shipping
```