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