#!/usr/bin/env python3
"""Tests for the codex/ port of Tapway Superpowers to OpenAI Codex.

Mirrors test_hermes_install.py: asserts the structure, skill set, hook
adaptation (Codex stdin-JSON payloads), installer wiring, and guard-scrub of
Claude/Hermes-specific verbs that must be normalized away in the Codex copies.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / "codex"
SKILLS = CODEX / "skills"
HOOKS = CODEX / "hooks"
TEMPLATES = CODEX / "templates"

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        PASS.append(msg)
        print(f"  PASS  {msg}")
    else:
        FAIL.append(msg)
        print(f"  FAIL  {msg}")


# The 24 Claude-source skills to port. dependency-audit is deliberately excluded
# as a skill (it stays a hook, exactly as in Claude). $tapway umbrella is #25.
EXPECTED = [
    "interview",
    "brainstorming",
    "writing-plans",
    "tdd",
    "e2e-playwright",
    "quality-gates",
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

# Verbs/tokens that must NOT survive into a Codex skill (Claude/Hermes-native).
GUARD_TRIGGERS = ["CLAUDE.md", "delegate_task", "hermes skills", "hermes bundles"]


def main() -> int:
    print("[1] codex/ tree structure")
    check(CODEX.is_dir(), "codex/ exists")
    check(SKILLS.is_dir(), "codex/skills/ exists")
    check(HOOKS.is_dir(), "codex/hooks/ exists")
    check(TEMPLATES.is_dir(), "codex/templates/ exists")

    print("\n[2] 24 pipeline skills + $tapway umbrella")
    check((SKILLS / "tapway" / "SKILL.md").is_file(), "codex/skills/tapway/SKILL.md ($tapway umbrella) exists")
    for name in EXPECTED:
        check((SKILLS / name / "SKILL.md").is_file(), f"codex/skills/{name}/SKILL.md exists")
    # dependency-audit must NOT be a codex skill (planned exclusion).
    check(not (SKILLS / "dependency-audit").exists(), "dependency-audit is NOT a codex skill (stays a hook)")

    print("\n[3] frontmatter (name + description required by Codex)")
    for name in EXPECTED + ["tapway"]:
        skill = (SKILLS / name / "SKILL.md")
        if skill.is_file():
            text = skill.read_text(encoding="utf-8")
            fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            has_fm = bool(fm)
            has_name = has_fm and re.search(r"^name:\s*\S+", fm.group(1), re.M)
            has_desc = has_fm and re.search(r"^description:", fm.group(1), re.M)
            check(bool(has_fm), f"{name} has frontmatter")
            check(has_name is not None, f"{name} frontmatter has name:")
            check(has_desc is not None, f"{name} frontmatter has description:")
        else:
            check(False, f"{name} SKILL.md missing (frontmatter NA)")

    print("\n[4] guard-scrub: no Claude/Hermes verbs in codex skills")
    for name in EXPECTED + ["tapway"]:
        skill = (SKILLS / name / "SKILL.md")
        if skill.is_file():
            text = skill.read_text(encoding="utf-8")
            for trig in GUARD_TRIGGERS:
                check(trig not in text, f"{name} free of {trig!r}")

    print("\n[5] codemax-gbrain env-gated in codex port")
    gbrain = (SKILLS / "codemax-gbrain" / "SKILL.md")
    if gbrain.is_file():
        text = gbrain.read_text(encoding="utf-8")
        check("CODEMAX_ENABLED" in text, "codemax-gbrain carries CODEMAX_ENABLED gate")
        check("CODEMAX_WIKI_DIR" in text and "CODEMAX_GBRAIN_DIR" in text,
              "codemax-gbrain carries CODEMAX_WIKI_DIR / CODEMAX_GBRAIN_DIR behavior")
        check("mcp_servers.gbrain" in text, "codemax-gbrain registers Codex gbrain MCP (config.toml)")

    print("\n[6] hooks: stdin-JSON parsing (Codex payload via stdin, not $1)")
    expected_hooks = [
        "pre-bash-safety.sh",
        "pre-commit-secrets.sh",
        "pre-commit-gate.sh",
        "dependency-audit.sh",
        "post-write-lint.sh",
        "post-commit-release-note.sh",
        "session-start.sh",
        "pre-execute-github-issue-check.sh",
        "pre-execute-github-issue-create.sh",
    ]
    for name in expected_hooks:
        hook = (HOOKS / name)
        check(hook.is_file(), f"codex/hooks/{name} exists")
        if hook.is_file():
            text = hook.read_text(encoding="utf-8")
            # Must read the command/file from Codex's stdin JSON payload,
            # not from $1 like the Claude hook did.
            check("json.load" in text, f"{name} parses stdin JSON (json.load)")
            check("tool_input" in text, f"{name} reads tool_input from payload")

    print("\n[7] hooks.json.template (Codex event model)")
    hj = (CODEX / "hooks.json.template")
    check(hj.is_file(), "codex/hooks.json.template exists")
    if hj.is_file():
        text = hj.read_text(encoding="utf-8")
        check("SessionStart" in text, "hooks maps SessionStart")
        check("PreToolUse" in text, "hooks maps PreToolUse")
        check("PostToolUse" in text, "hooks maps PostToolUse")
        check("apply_patch" in text, "PostToolUse matcher uses apply_patch (Codex tool name)")
        check("matcher" in text, "hooks uses matcher (Codex hook model)")

    print("\n[8] AGENTS.md template (pipeline as background discipline)")
    agents = (TEMPLATES / "AGENTS.md")
    check(agents.is_file(), "codex/templates/AGENTS.md exists")
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        check("$tapway" in text, "AGENTS.md invokes $tapway")
        check("TDD" in text or "tdd" in text, "AGENTS.md enforces TDD")
        check("PR" in text, "AGENTS.md enforces PR exit gate")

    print("\n[9] installer wiring")
    install = (CODEX / "install.sh")
    ps1 = (CODEX / "install.ps1")
    readme = (CODEX / "README.md")
    check(install.is_file(), "codex/install.sh exists")
    check(ps1.is_file(), "codex/install.ps1 exists")
    check(readme.is_file(), "codex/README.md exists")
    if install.is_file():
        text = install.read_text(encoding="utf-8")
        for name in EXPECTED:
            check(name in text, f"install.sh lists {name}")
        check("-agents/skills" in text or ".agents/skills" in text, "install.sh targets .agents/skills (Codex skill dir)")
        check("AGENTS.md" in text, "install.sh writes AGENTS.md into consuming repo")
        check("hooks.json" in text, "install.sh wires .codex/hooks.json")
        check("trust" in text.lower(), "install.sh notes hooks trust review")

    print("\n[10] README mapping")
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        check("$tapway" in text, "README documents $tapway umbrella")
        check("AGENTS.md" in text, "README documents AGENTS.md")
        check("trust" in text.lower(), "README documents hooks trust review")
        check("plugin" in text.lower(), "README leaves a plugin runbook (Option C path)")
        check("$skill" in text, "README documents $skill invocation (no custom slash cmds)")

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