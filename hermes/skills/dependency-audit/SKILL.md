---
name: dependency-audit
description: >
  Audit and remediate supply-chain vulnerabilities in project dependencies.
  Scans lockfiles with osv-scanner (multi-ecosystem), npm audit (Node), and
  pip-audit (Python); interprets findings, upgrades vulnerable packages, and
  verifies the fix. Runs at commit time via the quality/dependency hooks and in
  CI, and on demand to remediate reported vulnerabilities. Triggers include
  "dependency audit", "audit dependencies", "osv-scanner", "npm audit",
  "pip-audit", "vulnerable package", "supply chain", "update dependencies",
  "fix vulnerabilities".
---

# Skill: Dependency Audit & Remediation

**When to invoke:** When a dependency scan (pre-commit hook, CI, or on-demand) reports
vulnerable packages, or when adding/updating dependencies in a project. This skill
remediates the two most common supply-chain gaps: vulnerable transitive dependencies
and unpatched lockfiles.

> **Why it matters:** A single outdated transitive dependency can expose the whole app.
> OWASP covers application code; dependency audits cover the third-party packages that
> ship with it — the #1 real-world exploit vector.

---

## Core Concept

> Scan → interpret → upgrade → verify.

Three scanners, complementary coverage:

| Tool | Ecosystem | When |
|---|---|---|
| `osv-scanner` | All (19+ lockfile formats) | Primary, multi-ecosystem |
| `npm audit` | Node/JS | Node-specific advisory DB |
| `pip-audit` | Python | PyPI advisory DB |

---

## Protocol

### Step 0 — Run the Scan

```bash
# Full repo scan (multi-ecosystem)
osv-scanner .

# Ecosystem-specific
npm audit          # in a Node/frontend dir
pip-audit          # in a Python/backend dir
```

Install if missing: `go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest`, `pip install pip-audit`, `npm i -g` (npm audit is built in).

### Step 1 — Interpret the Findings

For each vulnerability report, capture:
- **Package** and **ecosystem**
- **Installed version** vs **fixed version** (the lockfile constraint)
- **Severity** (critical / high / medium)
- **CVE/OSV ID** (for the changelog and tracking)

Example output reading:
```
osv-scanner:
  Package: lodash@4.17.20 → fixed in 4.17.21  [HIGH]  CVE-2021-23337
  Package: urllib3@1.26.5 → fixed in 1.26.19   [CRITICAL]  GHSA-...
```

### Step 2 — Upgrade (fix the lockfile, not the manifest only)

Upgrade the vulnerable package and its dependents to the fixed version:

```bash
# Node
npm audit fix        # safe upgrades
npm audit fix --force  # only if a direct dep blocks; review before using
npm update <package> --save

# Python
pip-audit fix        # or:
pip install --upgrade <package>

# Direct/manual
# Upgrade the package constraint in pyproject.toml / package.json, then re-lock:
#   pip install -e . && pip freeze > requirements.lock   (or: uv lock / npm install)
```

**Rules:**
- Upgrade **minimum versions** that satisfy the advisory — don't jump to the latest if a smaller bump patches the CVE (avoids breaking changes)
- After changing constraints, **re-lock** (`npm install` / `uv lock` / `pip install -e .`) so the lockfile reflects the fix
- Prefer `npm audit fix` (safe) over `--force`; examine forced changes for breaking changes

### Step 3 — Verify

```bash
# Re-scan confirms the vuln is gone
osv-scanner . ; npm audit ; pip-audit

# Full test suite still passes
pytest -q          # backend
npm test           # frontend
```

- [ ] Vulnerable package no longer reported by all applicable scanners
- [ ] Full test suite passes (no regressions from the upgrade)
- [ ] Lockfile updated and committed (not just the manifest)

### Step 4 — Record

Add a CHANGELOG entry noting the package, CVE/OSV ID, and fixed version, and reference it in the PR.

---

## Verification / Gate

This skill is done when:

- [ ] `osv-scanner .`, `npm audit`, and `pip-audit` all report **zero** critical/high vulnerabilities for changed deps
- [ ] Vulnerable packages upgraded to fixed versions in the **lockfile**
- [ ] Full test suite passes
- [ ] CHANGELOG notes the CVE/OSV and fix

If a scan still reports the vulnerability after upgrade, either the fixed version isn't released or the constraint can't satisfy it — document and escalate, do not claim fixed.

---

## Hard Rules

- ❌ Never claim a dependency is "fixed" without re-running the scanner and seeing it clear
- ❌ Never commit a version bump without re-locking (`npm install` / `uv lock` / re-freeze)
- ❌ Never use `npm audit fix --force` without reviewing what changed (can introduce breaking changes)
- ❌ Never ignore a critical vulnerability in a production dependency — escalate instead
- ❌ Never add a dependency without running the dep-audit gate