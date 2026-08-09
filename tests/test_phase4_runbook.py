#!/usr/bin/env python3
"""
Phase 4 PR2 — incident-runbook + db-reviewer validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies:
1. incident-runbook skill exists in both Claude (skills/) and Hermes
   (hermes/skills/) copies, ships templates, and is wired into observe.
2. db-reviewer subagent exists (agents/db-reviewer/AGENT.md) and is wired into
   the pr/code-review pipeline.
"""
import os
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
print("PHASE 4 PR2 — RUNBOOK + DB-REVIEWER — VALIDATION SUITE")
print("=" * 68)

# --- 1. incident-runbook skill (both copies) ----------------------------
print("\n[1] incident-runbook skill present (both copies)")
for copy, label in [("skills", "Claude"), ("hermes/skills", "Hermes")]:
    s = read(copy, "incident-runbook", "SKILL.md")
    check(s is not None, f"{label} incident-runbook exists")
    check(s is not None and ("sev" in s.lower() or "severity" in s.lower()),
          f"{label} covers severity levels")
    check(s is not None and "runbook" in s.lower(), f"{label} is a runbook skill")
    check(s is not None and "postmortem" in s.lower(), f"{label} covers postmortem")
    check(s is not None and "blameless" in s.lower(), f"{label} is blameless")
    # C1 hardening: the Hermes copy, like the Claude copy, must SHIP its templates
    # (the skill references them; a missing templates dir is a real gap)
    tpl_dir = read(copy, "incident-runbook", "templates", "runbook.md")
    check(tpl_dir is not None, f"{label} runbook template SHIPPED in templates dir")

# --- 2. runbook templates -------------------------------------------------
print("\n[2] Runbook + postmortem templates")
tpl = read("skills", "incident-runbook", "templates", "runbook.md")
check(tpl is not None, "runbook.md template exists")
check(tpl is not None and "Symptom" in tpl, "runbook template has Symptom section")
check(tpl is not None and "Mitigation" in tpl, "runbook template has Mitigation")
check(tpl is not None and "Escalation" in tpl, "runbook template has Escalation")
pm = read("skills", "incident-runbook", "templates", "postmortem.md")
check(pm is not None, "postmortem.md template exists")
check(pm is not None and "Timeline" in pm, "postmortem template has Timeline")
check(pm is not None and "Root Cause" in pm, "postmortem template has Root Cause")
check(pm is not None and "Action Items" in pm, "postmortem template has Action Items")

# --- 3. wired into observe -------------------------------------------------
print("\n[3] observe links to incident-runbook")
obs = read("skills", "observe", "SKILL.md")
obs_h = read("hermes/skills", "observe", "SKILL.md")
check(obs is not None and "incident-runbook" in obs, "Claude observe references incident-runbook")
check(obs_h is not None and "incident-runbook" in obs_h, "Hermes observe references incident-runbook")

# --- 4. db-reviewer subagent ------------------------------------------------
print("\n[4] db-reviewer subagent exists")
dbr = read("agents", "db-reviewer", "AGENT.md")
check(dbr is not None, "agents/db-reviewer/AGENT.md exists")
check(dbr is not None and "N+1" in dbr, "db-reviewer covers N+1 detection")
check(dbr is not None and "index" in dbr.lower(), "db-reviewer covers indexing")
check(dbr is not None and "schema" in dbr.lower(), "db-reviewer covers schema review")
check(dbr is not None and "EXPLAIN" in dbr, "db-reviewer uses EXPLAIN ANALYZE")

# --- 5. db-reviewer wired into pipeline ------------------------------------
print("\n[5] db-reviewer wired into pr/code-review")
pr = read("skills", "pr", "SKILL.md")
cr = read("skills", "code-review", "SKILL.md")
check(pr is not None and "db-reviewer" in pr, "pr skill references db-reviewer")
check(cr is not None and ("db-reviewer" in cr or "database" in cr.lower()),
      "code-review references database review")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)