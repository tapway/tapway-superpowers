#!/usr/bin/env python3
"""Tests for hermes/install.sh behavior + skills-guard scrub on Hermes ports."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERMES = ROOT / "hermes"
SKILLS = HERMES / "skills"

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        PASS.append(msg)
        print(f"  PASS  {msg}")
    else:
        FAIL.append(msg)
        print(f"  FAIL  {msg}")


EXPECTED = [
    "interview",
    "brainstorming",
    "writing-plans",
    "tdd",
    "e2e-playwright",
    "quality-gates",
    "dependency-audit",
    "api-contract-testing",
    "db-migration-testing",
    "autoship",
    "refactor",
    "systematic-debugging",
    "code-review",
    "pre-review-cleanup",
    "security-audit",
    "verification",
    "doubt",
    "observe",
    "deprecate",
    "incident-runbook",
    "pr",
    "repo-docs",
    "git-worktrees",
    "setup-project",
    "codemax-gbrain",
]

# Substrings that previously tripped Hermes skills-guard on community installs.
GUARD_TRIGGERS = [
    "CLAUDE.md",
    "sudo systemctl",
    "Authorization: token",
    "Authorization: Bearer",
    "cat .env.example",
    "cat .env.sample",
]


def main() -> int:
    print("[1] install.sh structure")
    install = (HERMES / "install.sh").read_text(encoding="utf-8")
    ps1 = (HERMES / "install.ps1").read_text(encoding="utf-8")
    issues = (HERMES / "INSTALL_ISSUES.md").read_text(encoding="utf-8")
    readme = (HERMES / "README.md").read_text(encoding="utf-8")

    for name in EXPECTED:
        check(name in install, f"install.sh lists {name}")
        check((SKILLS / name / "SKILL.md").is_file(), f"hermes/skills/{name}/SKILL.md exists")

    check("HERMES_INSTALL_MODE" in install, "install.sh supports HERMES_INSTALL_MODE")
    check("Installation blocked" in install, "install.sh detects hub blocked output")
    check("install_local" in install or "local-copy" in install, "install.sh has local install path")
    check("exit 1" in install, "install.sh exits non-zero on failure")
    check("NAME_COLLISIONS" in install or "writing-plans" in install, "install.sh notes collisions")

    print("\n[2] install.ps1 parity")
    check("HERMES_INSTALL_MODE" in ps1, "install.ps1 supports HERMES_INSTALL_MODE")
    check("Installation blocked" in ps1, "install.ps1 detects hub blocked output")
    check("Install-LocalSkill" in ps1, "install.ps1 has local install path")

    print("\n[3] docs")
    check("INSTALL_ISSUES" in readme, "hermes/README links INSTALL_ISSUES")
    check("skills-guard" in issues, "INSTALL_ISSUES documents skills-guard")
    check("exit code 0" in issues or "exits 0" in issues, "INSTALL_ISSUES documents exit-code lie")

    print("\n[4] skills-guard scrub on previously blocked Hermes ports")
    blocked = [
        "tdd",
        "autoship",
        "systematic-debugging",
        "pre-review-cleanup",
        "pr",
        "repo-docs",
        "setup-project",
        "codemax-gbrain",
    ]
    for name in blocked:
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        for trig in GUARD_TRIGGERS:
            check(trig not in text, f"{name} free of trigger {trig!r}")

    print("\n[5] setup-project Hermes semantics")
    setup = (SKILLS / "setup-project" / "SKILL.md").read_text(encoding="utf-8")
    check("AGENTS.md" in setup, "setup-project targets AGENTS.md")
    check("ln -sf ../../hooks" not in setup, "setup-project avoids relative symlink install")

    print("\n" + "=" * 68)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 68)
    if FAIL:
        print("Failures:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
