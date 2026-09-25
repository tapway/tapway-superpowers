#!/usr/bin/env python3
"""Verify doc/plugin count consistency after the repo-docs overhaul."""
import json
import os

checks = []

d = json.load(open(".claude-plugin/plugin.json"))
checks.append(("plugin.json skills=30", len(d["skills"]) == 30, len(d["skills"])))
checks.append(("plugin.json agents=5", len(d["agents"]) == 5, len(d["agents"])))

readme = open("README.md").read()
checks.append(("README '### 30 Skills'", "### 30 Skills" in readme, "present" if "### 30 Skills" in readme else "missing"))
checks.append(("README '### 8 Guardrail'", "### 8 Guardrail Hooks" in readme, "present" if "### 8 Guardrail Hooks" in readme else "missing"))
checks.append(("README '### 5 Specialized'", "### 5 Specialized Agents" in readme, "present" if "### 5 Specialized Agents" in readme else "missing"))
checks.append(("README no stale 13 Skills ToC", "  - [13 Skills]" not in readme, "clean" if "  - [13 Skills]" not in readme else "STALE"))
checks.append(("README Documentation index", "docs/ARCHITECTURE.md" in readme, "present" if "docs/ARCHITECTURE.md" in readme else "missing"))

h = open("hermes/README.md").read()
checks.append(("hermes/README 'All **31**'", "All **31**" in h, "present" if "All **31**" in h else "missing"))

checks.append(("skills/ count=30", len(os.listdir("skills")) == 30, len(os.listdir("skills"))))
checks.append(("hermes/skills/ count=31", len(os.listdir("hermes/skills")) == 31, len(os.listdir("hermes/skills"))))
checks.append(("agents/ count=5", len(os.listdir("agents")) == 5, len(os.listdir("agents"))))
hook_dirs = [x for x in os.listdir("hooks") if os.path.isdir(f"hooks/{x}")]
checks.append(("hooks dirs=10 (+hooks.json)", len(hook_dirs) == 10, len(hook_dirs)))

allok = True
for label, ok, val in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {label} (got {val})")
    allok = allok and ok
print("CONSISTENCY:", "ALL PASS" if allok else "FAILURES")
raise SystemExit(0 if allok else 1)