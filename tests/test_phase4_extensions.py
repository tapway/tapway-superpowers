#!/usr/bin/env python3
"""
Phase 4 — extensions validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies the three extend-in-place extensions exist in BOTH the Claude plugin
(skills/) and Hermes port (hermes/skills/):
1. a11y (axe-core) inside e2e-playwright
2. performance/benchmark inside verification
3. auth-design review inside security-audit
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = []
FAIL = []


def check(cond, label):
    if cond:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(label)
        print(f"  FAIL  {label}")


def read(*rel):
    p = os.path.join(ROOT, *rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


print("=" * 68)
print("PHASE 4 — EXTENSIONS — VALIDATION SUITE")
print("=" * 68)

# --- 1. e2e-playwright: a11y (axe-core) extension ------------------------
print("\n[1] e2e-playwright has axe-core a11y step (both copies)")
for copy, label in [("skills", "Claude"), ("hermes/skills", "Hermes")]:
    s = read(copy, "e2e-playwright", "SKILL.md")
    check(s is not None, f"{label} e2e-playwright exists")
    check(s is not None and "axe" in s.lower(), f"{label} e2e mentions axe")
    check(s is not None and "@axe-core/playwright" in s, f"{label} e2e references @axe-core/playwright")
    check(s is not None and "AxeBuilder" in s, f"{label} e2e uses AxeBuilder")
    check(s is not None and "wcag" in s.lower(), f"{label} e2e references WCAG")
    check(s is not None and "accessib" in s.lower(), f"{label} e2e mentions accessibility")

# --- 2. verification: perf/benchmark extension ---------------------------
print("\n[2] verification has performance/benchmark step (both copies)")
for copy, label in [("skills", "Claude"), ("hermes/skills", "Hermes")]:
    s = read(copy, "verification", "SKILL.md")
    check(s is not None, f"{label} verification exists")
    check(s is not None and "performance" in s.lower(), f"{label} verification mentions performance")
    check(s is not None and "benchmark" in s.lower(), f"{label} verification has benchmark step")
    check(s is not None and "latency" in s.lower(), f"{label} verification covers latency")
    check(s is not None and ("query count" in s.lower() or "throughput" in s.lower()),
          f"{label} verification covers query count / throughput")

# --- 3. security-audit: auth-design extension ----------------------------
print("\n[3] security-audit has auth-design review section (both copies)")
for copy, label in [("skills", "Claude"), ("hermes/skills", "Hermes")]:
    s = read(copy, "security-audit", "SKILL.md")
    check(s is not None, f"{label} security-audit exists")
    check(s is not None and "auth-design" in s.lower(), f"{label} security-audit has auth-design section")
    check(s is not None and "rbac" in s.lower(), f"{label} covers RBAC")
    check(s is not None and "idor" in s.lower(), f"{label} covers IDOR")
    check(s is not None and "pkce" in s.lower(), f"{label} covers OAuth PKCE")

# --- 4. Wiring: a11y wired into the E2E playbook (as a STEP, not a mention) ---
print("\n[4] a11y wired into the E2E playbook")
claude_e2e = read("skills", "e2e-playwright", "SKILL.md")
hermes_e2e = read("hermes/skills", "e2e-playwright", "SKILL.md")
# The a11y step must be a real numbered step (### Step D2), which proves it's
# part of the playbook — not just a keyword mention somewhere.
for label, s in [("Claude", claude_e2e), ("Hermes", hermes_e2e)]:
    check(s is not None and "### Step D2" in s,
          f"{label} a11y is a numbered playbook step (### Step D2), not just a mention")
    check(s is not None and "axe" in s.lower(),
          f"{label} a11y step mentions axe")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)