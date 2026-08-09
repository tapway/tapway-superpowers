#!/usr/bin/env python3
"""
E2E-Playwright skill validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies the e2e-playwright skill exists in BOTH the Claude plugin (skills/)
and Hermes port (hermes/skills/), is structurally wired into the tdd,
autoship, and verification skills, ships a CI template, and updates the
test-writer agent. Structural enforcement, not just documentation.
"""
import os
import sys
import re

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
print("E2E-PLAYWRIGHT SKILL — VALIDATION SUITE")
print("=" * 68)

# --- 1. Skill file exists in both copies -------------------------------
print("\n[1] Skill file present (Claude skills/ + Hermes hermes/skills/)")
claude_skill = read("skills", "e2e-playwright", "SKILL.md")
hermes_skill = read("hermes", "skills", "e2e-playwright", "SKILL.md")
check(claude_skill is not None, "skills/e2e-playwright/SKILL.md exists")
check(hermes_skill is not None, "hermes/skills/e2e-playwright/SKILL.md exists")

# --- 2. Required sections in Claude copy -------------------------------
print("\n[2] Claude SKILL.md required sections/frontmatter")
for sec in ["## Protocol", "## Verification / Gate", "## Hard Rules"]:
    check(claude_skill is not None and sec in claude_skill, f"Claude SKILL.md contains '{sec}'")
check(claude_skill is not None and "When to invoke" in claude_skill, "Claude SKILL.md has 'When to invoke'")
check(claude_skill is not None and "playwright" in claude_skill.lower(), "mentions playwright")
check(claude_skill is not None and "webServer" in claude_skill, "has webServer config guidance")
check(claude_skill is not None and "auth.setup" in claude_skill, "has auth.setup (storageState) guidance")
check(claude_skill is not None and "never by weakening assertions" in claude_skill.lower(),
      "enforces 'never weaken assertions' rule")

# --- 3. Hermes copy mirrors Claude copy --------------------------------
print("\n[3] Hermes SKILL.md mirrors + port notes")
check(hermes_skill is not None and "When to invoke" in hermes_skill, "Hermes SKILL.md has 'When to invoke'")
check(hermes_skill is not None and "delegate_task" in hermes_skill, "Hermes copy references delegate_task (port)")
check(hermes_skill is not None and hermes_skill.strip() != (claude_skill or "").strip(),
      "Hermes copy is not an exact byte-duplicate (adapted for Hermes)")

# --- 4. Wiring into tdd (both copies) ----------------------------------
print("\n[4] tdd skill wired to run E2E after unit GREEN")
claude_tdd = read("skills", "tdd", "SKILL.md")
hermes_tdd = read("hermes", "skills", "tdd", "SKILL.md")
check(claude_tdd is not None and "e2e-playwright" in claude_tdd, "Claude tdd references e2e-playwright")
check(hermes_tdd is not None and "e2e-playwright" in hermes_tdd, "Hermes tdd references e2e-playwright")

# --- 5. Wiring into autoship (default path, not just deploy mode) ------
print("\n[5] autoship makes E2E mandatory in DEFAULT path")
claude_auto = read("skills", "autoship", "SKILL.md")
hermes_auto = read("hermes", "skills", "autoship", "SKILL.md")
check(claude_auto is not None and "e2e-playwright" in claude_auto, "Claude autoship references e2e-playwright")
check(hermes_auto is not None and "e2e-playwright" in hermes_auto, "Hermes autoship references e2e-playwright")
# E2E must appear in the standard Phase 4 (Post-Implementation) — i.e. BEFORE the
# deploy-only Phase 4D — proving it's a default-path gate, not just deploy mode.
if claude_auto:
    phase4d_idx = claude_auto.find("### Phase 4D")
    prefix = claude_auto[:phase4d_idx] if phase4d_idx != -1 else claude_auto
    check("e2e-playwright" in prefix,
          "Claude autoship: E2E gate in standard Phase 4 (before deploy-only Phase 4D)")

# --- 6. Wiring into verification (both copies) -------------------------
print("\n[6] verification skill adds npx playwright test to checklist")
claude_ver = read("skills", "verification", "SKILL.md")
hermes_ver = read("hermes", "skills", "verification", "SKILL.md")
check(claude_ver is not None and "npx playwright test" in claude_ver, "Claude verification has 'npx playwright test'")
check(hermes_ver is not None and "npx playwright test" in hermes_ver, "Hermes verification has 'npx playwright test'")

# --- 7. CI template ----------------------------------------------------
print("\n[7] CI workflow template")
ci = read(".github", "workflows", "playwright.yml")
check(ci is not None, ".github/workflows/playwright.yml exists")
check(ci is not None and "playwright" in ci.lower(), "CI runs playwright")
check(ci is not None and "ubuntu-latest" in ci, "CI uses ubuntu-latest")
check(ci is not None and "npx playwright install --with-deps" in ci, "CI installs browser deps")
check(ci is not None and "blob-report" in ci.lower() or (ci and "artifact" in ci.lower()),
      "CI uploads artifacts (traces/blob-report)")

# --- 8. Test-writer agent -------------------------------------------------
print("\n[8] test-writer agent updated for E2E")
tw = read("agents", "test-writer", "AGENT.md")
check(tw is not None and "e2e" in tw.lower(), "test-writer agent mentions e2e layer")

# --- 9. README + CHANGELOG --------------------------------------------
print("\n[9] README + CHANGELOG updated")
readme = read("README.md")
changelog = read("CHANGELOG.md")
check(readme is not None and "e2e-playwright" in readme, "README references e2e-playwright skill")
check(changelog is not None and "e2e-playwright" in changelog, "CHANGELOG notes e2e-playwright addition")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)