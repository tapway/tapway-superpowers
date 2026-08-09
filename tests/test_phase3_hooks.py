#!/usr/bin/env python3
"""
Phase 3 — Enforceable Hooks validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies the hooks repair + the two new gates (progress quality + dependency
audit) with correct per-platform enforcement:
- Claude: plugin.json wires all hooks; blocking hooks use exit 2 (not 1)
- Hermes: shell-hook config exists with pre_tool_call blocking JSON protocol
- Both: git pre-commit backstop hook committed
- CI: dependency-audit step in quality.yml
"""
import json
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


def load_json(*rel):
    content = read(*rel)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


print("=" * 68)
print("PHASE 3 — ENFORCEABLE HOOKS — VALIDATION SUITE")
print("=" * 68)

# --- 1. Claude plugin manifest + hooks/hooks.json wiring -----------------
print("\n[1] Claude plugin hooks wiring (official auto-discovery)")
plugin = load_json(".claude-plugin", "plugin.json")
check(plugin is not None, ".claude-plugin/plugin.json parses")

# Official Claude Code discovers plugin hooks at hooks/hooks.json (no
# plugin.json field needed — official plugins don't declare one). Fix the
# broken behavior: plugin.json must not contain a stale/broken empty hooks
# structure, and hooks/hooks.json must reference the real scripts with the
# correct lifecycle semantics.
hjson = load_json("hooks", "hooks.json")
check(hjson is not None, "hooks/hooks.json parses")
check(hjson is not None and isinstance(hjson.get("hooks"), dict), "hooks/hooks.json has hooks dict")

hook_scripts = read("hooks", "hooks.json") or ""
for name in ["pre-bash-safety", "pre-commit-secrets", "pre-commit-gate",
             "post-write-lint", "post-commit-release-note", "session-start"]:
    check(name in hook_scripts, f"hooks.json references {name} script")

# The commit-related hooks must use the official colon matcher form
check("Bash(git commit:*)" in hook_scripts, "commit hooks use official 'Bash(git commit:*)' matcher (not space form)")
check("Bash(git commit *)" not in hook_scripts, "no legacy space-form matcher 'Bash(git commit *)'")

# plugin.json must not carry the broken empty hooks array as a manifest field
# (not part of the official schema — hooks auto-discover from hooks/hooks.json)
if plugin is not None:
    check("hooks" not in plugin or plugin.get("hooks") == [] or isinstance(plugin.get("hooks"), list),
          "plugin.json does not incorrectly gate hooks registration")
    check(plugin.get("hooks") != [] or "hooks" not in plugin,
          "plugin.json no longer has stale 'hooks': [] (official plugins omit the field)")

# --- 2. Blocking hooks use exit 2 (not 1) --------------------------------
print("\n[2] PreToolUse blocking hooks use exit 2 (Claude Code semantics)")
manual = read("hooks", "pre-bash-safety", "pre-bash-safety.sh")
secrets = read("hooks", "pre-commit-secrets", "pre-commit-secrets.sh")
gate = read("hooks", "pre-commit-gate", "pre-commit-gate.sh")
check(manual is not None and "exit 2" in manual, "pre-bash-safety uses exit 2 (not 1)")
check(secrets is not None and "exit 2" in secrets, "pre-commit-secrets uses exit 2 (not 1)")
check(gate is not None and "exit 2" in gate, "pre-commit-gate uses exit 2 to block")
# 'exit 1' only appears in explanatory comments, never as an executable statement
import re
gate_exits_1 = re.findall(r'^\s*exit 1\s*$', gate, flags=re.M) if gate else []
check(gate is not None and not gate_exits_1, "pre-commit-gate has no stray exit 1 (comments only)")

# --- 3. New hooks exist --------------------------------------------------
print("\n[3] New hook scripts exist")
gate_script = read("hooks", "pre-commit-gate", "pre-commit-gate.sh")
dep_script = read("hooks", "dependency-audit", "dependency-audit.sh")
git_script = read("hooks", "pre-commit", "git-pre-commit.sh")
check(gate_script is not None, "hooks/pre-commit-gate/pre-commit-gate.sh exists")
check(dep_script is not None, "hooks/dependency-audit/dependency-audit.sh exists")
check(git_script is not None, "hooks/pre-commit/git-pre-commit.sh exists")
# Gate script runs the quality checks
for kw in ["lint", "format", "typecheck", "coverage"]:
    check(gate_script is not None and (kw in gate_script or kw in (gate_script or "").lower()),
          f"pre-commit-gate runs {kw}")
# Dependency script references the scanners
for kw in ["osv-scanner", "npm audit", "pip-audit"]:
    check(dep_script is not None and kw in dep_script, f"dependency-audit uses {kw}")
# Git pre-commit backstop is executable-installable and blocks
check(git_script is not None and "exit 1" in git_script, "git-pre-commit backstop blocks (exit 1 is correct for git hooks)")

# --- 4. Hermes shell-hook config ----------------------------------------
print("\n[4] Hermes shell-hook config + dependency-audit skill")
hconfig = read("hermes", "config.hooks.yaml")
check(hconfig is not None, "hermes/config.hooks.yaml exists")
check(hconfig is not None and "pre_tool_call" in hconfig, "Hermes config has pre_tool_call hook")
check(hconfig is not None and "terminal" in hconfig, "Hermes config matches terminal tool")
check(hconfig is not None and "block" in hconfig, "Hermes config uses block decision")
hdep = read("hermes", "skills", "dependency-audit", "SKILL.md")
check(hdep is not None, "hermes/skills/dependency-audit/SKILL.md exists")
check(hdep is not None and "osv-scanner" in hdep, "Hermes dependency-audit skill mentions osv-scanner")

# Review hardening: the Hermes gate must NOT have the &&/|| precedence bug
# (A || B || C && D parses as A || B || (C && D), so HAS_BACKEND never set)
hgate = read("hermes", "agent-hooks", "tapway-pre-commit-gate.sh")
check(hgate is not None and "if [ -d backend ] || [ -f pyproject.toml ] || [ -f requirements.txt ]; then" in hgate
      or (hgate and "\nif [ -d backend ]" in hgate),
      "Hermes gate uses separate if statements (no &&/|| precedence bug)")

# --- 5. Skill gates wired -------------------------------------------------
print("\n[5] Skill gates wired (Hermes verification + pr)")
hver = read("hermes", "skills", "verification", "SKILL.md")
hpr = read("hermes", "skills", "pr", "SKILL.md")
check(hver is not None and "pre-commit" in hver or (hver and "commit-gate" in hver),
      "Hermes verification has commit-gate step")
check(hpr is not None and "pre-commit" in hpr or (hpr and "verification" in hpr),
      "Hermes pr references verification-before-commit")
check(hver is not None and "dependency" in hver.lower(), "Hermes verification mentions dependency audit")

# --- 6. CI dependency audit step ----------------------------------------
print("\n[6] CI quality.yml has dependency audit")
ci = read(".github", "workflows", "quality.yml")
check(ci is not None and "osv-scanner" in ci, "quality.yml runs osv-scanner")
check(ci is not None and "npm audit" in ci, "quality.yml runs npm audit")
check(ci is not None and "pip-audit" in ci, "quality.yml runs pip-audit")

# --- 7. setup-project installs the git backstop --------------------------
print("\n[7] setup-project installs git pre-commit hook")
setup = read("skills", "setup-project", "SKILL.md")
check(setup is not None and "pre-commit" in setup or (setup and "git-pre-commit" in setup),
      "setup-project references git pre-commit hook install")

# --- 8. README + CHANGELOG -----------------------------------------------
print("\n[8] README + CHANGELOG updated")
readme = read("README.md")
changelog = read("CHANGELOG.md")
check(readme is not None and "dependency-audit" in readme, "README references dependency-audit")
check(changelog is not None and "hooks" in changelog.lower(), "CHANGELOG notes hook changes")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)