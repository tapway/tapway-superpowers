#!/usr/bin/env python3
"""
Quality-gates config-layer validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies the quality-gates skill exists in BOTH the Claude plugin (skills/)
and Hermes port (hermes/skills/), ships config templates for the Phase 1
config-layer gaps (coverage thresholds, type-strict, env validation,
CODEOWNERS/branch protection), and a CI quality-gate workflow (lint/format/
typecheck/coverage). Structural enforcement, not just documentation.
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


def main() -> int:
    print("=" * 68)
    print("QUALITY-GATES CONFIG-LAYER — VALIDATION SUITE")
    print("=" * 68)

    # --- 1. Skill file exists in both copies -------------------------------
    print("\n[1] Skill file present (Claude skills/ + Hermes hermes/skills/)")
    claude_skill = read("skills", "quality-gates", "SKILL.md")
    hermes_skill = read("hermes", "skills", "quality-gates", "SKILL.md")
    check(claude_skill is not None, "skills/quality-gates/SKILL.md exists")
    check(hermes_skill is not None, "hermes/skills/quality-gates/SKILL.md exists")

    # --- 2. Skill covers the 5 Phase-1 config categories ---------------------
    print("\n[2] quality-gates SKILL.md covers all 5 config-layer categories")
    for kw in ["coverage", "type-strict", "env", "CODEOWNERS", "branch protection",
               "lint", "format", "typecheck", "fail-under"]:
        check(claude_skill is not None and kw.lower() in claude_skill.lower(),
              f"Claude SKILL.md mentions '{kw}'")

    # --- 3. Config templates shipped ----------------------------------------
    print("\n[3] Config templates shipped")
    cov = read("skills", "quality-gates", "templates", "coverage-pyproject.toml")
    check(cov is not None, "coverage-pyproject.toml template exists")
    check(cov is not None and "fail_under" in cov, "coverage template has fail_under threshold")

    ts = read("skills", "quality-gates", "templates", "tsconfig.strict.json")
    check(ts is not None, "tsconfig.strict.json template exists")
    check(ts is not None and "noImplicitAny" in ts and "strict" in ts,
          "tsconfig strict template has strict + noImplicitAny")

    env = read("skills", "quality-gates", "templates", ".env.example")
    check(env is not None, ".env.example template exists")

    owners = read("skills", "quality-gates", "templates", "CODEOWNERS")
    check(owners is not None, "CODEOWNERS template exists")
    check(owners is not None and "@" in owners, "CODEOWNERS template has a team handle")

    # --- 4. CI quality-gate workflow ----------------------------------------
    print("\n[4] CI quality-gate workflow")
    ci = read(".github", "workflows", "quality.yml")
    check(ci is not None, ".github/workflows/quality.yml exists")
    check(ci is not None and "lint" in ci.lower(), "CI runs lint")
    check(ci is not None and "format" in ci.lower(), "CI runs format check")
    check(ci is not None and "typecheck" in ci.lower() or (ci and "tsc" in ci.lower()),
          "CI runs typecheck")
    check(ci is not None and "coverage" in ci.lower() or (ci and "fail-under" in ci.lower()),
          "CI runs coverage gate")
    check(ci is not None and "|| true" not in ci,
          "CI gates are enforced (no '|| true' that would make them advisory-only)")

    # --- 5. Wiring into setup-project ---------------------------------------
    print("\n[5] setup-project references quality-gates")
    setup = read("skills", "setup-project", "SKILL.md")
    check(setup is not None and "quality-gates" in setup, "setup-project references quality-gates")

    # --- 6. Hidden/guard files ----------------------------------------------
    print("\n[6] Guard config files")
    gitignore = read(".gitignore")
    check(gitignore is not None and ".coverage" in gitignore, ".gitignore excludes .coverage")
    check(gitignore is not None and "htmlcov" in gitignore, ".gitignore excludes htmlcov/")

    # --- 7. README + CHANGELOG ----------------------------------------------
    print("\n[7] README + CHANGELOG updated")
    readme = read("README.md")
    changelog = read("CHANGELOG.md")
    check(readme is not None and "quality-gates" in readme, "README references quality-gates")
    check(changelog is not None and "quality-gates" in changelog, "CHANGELOG notes quality-gates")

    print("\n" + "=" * 68)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 68)

    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
