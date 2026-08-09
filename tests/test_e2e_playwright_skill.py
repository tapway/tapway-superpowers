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
check(claude_skill is not None and "weakening" in claude_skill.lower() and "assertion" in claude_skill.lower(),
      "enforces 'never weaken assertions' rule")
check(claude_skill is not None and "git diff --name-only" in claude_skill,
      "has concrete frontend-detection step (git diff --name-only)")
check(claude_skill is not None and "SKIPPED" in claude_skill,
      "explicitly defines skip-for-backend-only behavior")
check(claude_skill is not None and "testIgnore" not in claude_skill,
      "no broken testIgnore: /.*/ in setup project config")
check(claude_skill is not None and "pytest" in claude_skill.lower(),
      "covers backend E2E (pytest integration/e2e)")
check(claude_skill is not None and "tests/integration" in claude_skill,
      "references backend tests/integration/ directory")
check(claude_skill is not None and "tests/e2e" in claude_skill,
      "references backend tests/e2e/ directory")
check(claude_skill is not None and "backend-only" in claude_skill.lower() or "backend" in (claude_skill or ""),
      "defines backend E2E as mandated for backend changes")
check(claude_skill is not None and "backend" in claude_skill[:500].lower(),
      "frontmatter description mentions backend (not frontend-only)")

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
check(claude_auto is not None and "docs-only" in claude_auto, "Claude autoship defines docs-only skip behavior")
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
check(claude_ver is not None and "pytest" in claude_ver and ("integration" in claude_ver.lower() or "e2e" in claude_ver.lower()),
      "Claude verification has backend pytest integration/E2E check")
check(hermes_ver is not None and "pytest" in hermes_ver and ("integration" in hermes_ver.lower() or "e2e" in hermes_ver.lower()),
      "Hermes verification has backend pytest integration/E2E check")

# --- 7. CI template ----------------------------------------------------
print("\n[7] CI workflow template")
ci = read(".github", "workflows", "playwright.yml")
check(ci is not None, ".github/workflows/playwright.yml exists")
check(ci is not None and "playwright" in ci.lower(), "CI runs playwright")
check(ci is not None and "ubuntu-latest" in ci, "CI uses ubuntu-latest")
check(ci is not None and "npx playwright install --with-deps" in ci, "CI installs browser deps")
check(ci is not None and "blob-report" in ci.lower() or (ci and "artifact" in ci.lower()),
      "CI uploads artifacts (traces/blob-report)")
check(ci is not None and "paths:" in ci,
      "CI has path filters (only runs on frontend changes)")
check(ci is not None and "frontend" in ci,
      "CI references frontend directory")
check(ci is not None and "pytest" in ci,
      "CI runs backend pytest integration/E2E tests")
check(ci is not None and "backend" in ci,
      "CI references backend directory")

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

# --- 10. .gitignore ----------------------------------------------------
print("\n[10] .gitignore covers Playwright artifacts")
gitignore = read(".gitignore")
check(gitignore is not None, ".gitignore exists")
check(gitignore is not None and "playwright-report" in gitignore, ".gitignore excludes playwright-report/")
check(gitignore is not None and "test-results" in gitignore, ".gitignore excludes test-results/")
check(gitignore is not None and ".auth" in gitignore, ".gitignore excludes e2e/.auth/")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)
