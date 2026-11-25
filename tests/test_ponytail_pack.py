#!/usr/bin/env python3
"""Tests for the vendored ponytail skill pack.

Upstream: https://github.com/dietrichgebert/ponytail (MIT, (c) 2026 DietrichGebert)

The pack is vendored verbatim into all three host trees (Claude `skills/`,
`hermes/skills/`, `codex/skills/`). These tests exist because the two ways this
integration can silently rot are:

  1. Rule text getting rewritten/lost while porting to a host tree -- which
     would quietly change agent behaviour from the behaviour that was measured.
  2. Skill counts drifting out of sync across the four places that declare them
     (plugin.json, install.sh x2, README, tests).

So the tests assert (a) no canonical rule line is missing from any host port and
(b) every declared count agrees with the filesystem.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACK = [
    "ponytail",
    "ponytail-review",
    "ponytail-audit",
    "ponytail-debt",
    "ponytail-gain",
    "ponytail-help",
]

UPSTREAM_REPO = "github.com/dietrichgebert/ponytail"
UPSTREAM_COMMIT = "e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156"
UPSTREAM_AUTHOR = "DietrichGebert"

# Substrings that trip the Hermes skills-guard on community installs.
GUARD_TRIGGERS = [
    "CLAUDE.md",
    "sudo systemctl",
    "cat .env.example",
    "cat .env.sample",
]

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        PASS.append(msg)
        print(f"  PASS  {msg}")
    else:
        FAIL.append(msg)
        print(f"  FAIL  {msg}")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body) for a YAML-frontmatter markdown file."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def body_lines(text: str) -> list[str]:
    _, body = split_frontmatter(text)
    return [ln.strip() for ln in body.splitlines() if ln.strip()]


def skill_dirs(path: Path) -> list[str]:
    if not path.is_dir():
        return []
    return sorted(p.name for p in path.iterdir() if (p / "SKILL.md").is_file())


def count_bash_array(text: str, var: str) -> int | None:
    """Count entries in a bash `NAME=( ... )` array."""
    m = re.search(rf"^{var}=\(\n(.*?)^\)", text, re.S | re.M)
    if not m:
        return None
    entries = [ln for ln in m.group(1).splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return len(entries)


def main() -> int:
    print("[1] vendored in all three host trees")
    for name in PACK:
        for tree in ("skills", "hermes/skills", "codex/skills"):
            p = ROOT / tree / name / "SKILL.md"
            check(p.is_file(), f"{tree}/{name}/SKILL.md exists")

    print("\n[2] rule text preserved (no canonical line lost in porting)")
    for name in PACK:
        canon = (ROOT / "skills" / name / "SKILL.md")
        if not canon.is_file():
            check(False, f"{name}: canonical SKILL.md readable")
            continue
        canon_lines = body_lines(canon.read_text(encoding="utf-8"))
        for tree in ("hermes/skills", "codex/skills"):
            port = ROOT / tree / name / "SKILL.md"
            if not port.is_file():
                check(False, f"{name}: {tree} port readable")
                continue
            port_text = port.read_text(encoding="utf-8")
            missing = [ln for ln in canon_lines if ln not in port_text]
            check(
                not missing,
                f"{name}: {tree} carries all {len(canon_lines)} rule lines"
                + (f" (missing {len(missing)}: {missing[0][:48]!r}...)" if missing else ""),
            )

    print("\n[3] upstream provenance + MIT attribution")
    lic = ROOT / "skills" / "ponytail" / "LICENSE"
    check(lic.is_file(), "skills/ponytail/LICENSE vendored")
    if lic.is_file():
        lic_text = lic.read_text(encoding="utf-8")
        check("MIT License" in lic_text, "LICENSE is MIT")
        check(UPSTREAM_AUTHOR in lic_text, f"LICENSE credits {UPSTREAM_AUTHOR}")

    for name in PACK:
        p = ROOT / "skills" / name / "SKILL.md"
        if not p.is_file():
            check(False, f"{name}: canonical readable for provenance")
            continue
        fm, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        check("license: MIT" in fm, f"{name}: frontmatter declares license: MIT")
        check(UPSTREAM_REPO in fm, f"{name}: frontmatter records upstream repo")
        check(UPSTREAM_COMMIT in fm, f"{name}: frontmatter pins upstream commit")

    print("\n[4] declared counts agree with the filesystem")
    canon_count = len(skill_dirs(ROOT / "skills"))
    hermes_count = len(skill_dirs(ROOT / "hermes" / "skills"))
    codex_count = len(skill_dirs(ROOT / "codex" / "skills"))
    check(canon_count >= len(PACK), f"canonical skills/ has {canon_count} skills")

    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(
        len(plugin["skills"]) == canon_count,
        f"plugin.json skills ({len(plugin['skills'])}) == canonical dirs ({canon_count})",
    )
    for name in PACK:
        check(f"./skills/{name}" in plugin["skills"], f"plugin.json registers {name}")

    hermes_install = (ROOT / "hermes" / "install.sh").read_text(encoding="utf-8")
    codex_install = (ROOT / "codex" / "install.sh").read_text(encoding="utf-8")
    for name in PACK:
        check(name in hermes_install, f"hermes/install.sh lists {name}")
        check(name in codex_install, f"codex/install.sh lists {name}")

    h_n = count_bash_array(hermes_install, "SKILLS")
    c_n = count_bash_array(codex_install, "SKILLS")
    check(h_n == hermes_count, f"hermes install.sh SKILLS ({h_n}) == hermes dirs ({hermes_count})")
    # Codex splits its set across SKILLS=(...) plus a single-line UMBRELLA=(tapway).
    m_umb = re.search(r"^UMBRELLA=\(([^)]*)\)", codex_install, re.M)
    c_u = len([x for x in (m_umb.group(1).split() if m_umb else []) if x])
    check(
        c_n is not None and c_n + c_u == codex_count,
        f"codex install.sh SKILLS+UMBRELLA ({c_n}+{c_u}) == codex dirs ({codex_count})",
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"^### (\d+) Skills", readme, re.M)
    check(m is not None, "README declares a skill count")
    if m:
        check(
            int(m.group(1)) == canon_count,
            f"README '### {m.group(1)} Skills' == canonical dirs ({canon_count})",
        )
    for name in PACK:
        check(f"`{name}`" in readme, f"README documents {name}")

    print("\n[5] hermes ports pass the skills-guard scrub")
    for name in PACK:
        p = ROOT / "hermes" / "skills" / name / "SKILL.md"
        if not p.is_file():
            check(False, f"{name}: hermes port readable")
            continue
        text = p.read_text(encoding="utf-8")
        for trig in GUARD_TRIGGERS:
            check(trig not in text, f"hermes {name} free of trigger {trig!r}")

    print("\n[6] ponytail is auto-triggering, not inert")
    # A pack that never fires saves nothing; the description must carry the
    # coding-task triggers that produced the measured result.
    core = (ROOT / "skills" / "ponytail" / "SKILL.md")
    if core.is_file():
        fm, _ = split_frontmatter(core.read_text(encoding="utf-8"))
        for trig in ("coding task", "laziest", "yagni"):
            check(trig in fm.lower(), f"ponytail description carries trigger {trig!r}")
        check("Do NOT" in fm, "ponytail description scopes out non-coding requests")

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