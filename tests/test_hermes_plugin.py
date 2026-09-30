#!/usr/bin/env python3
"""Hermes plugin package: installable subdirectory, mirrors hermes/skills."""
from __future__ import annotations

import filecmp
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "hermes" / "plugin"
SKILLS = ROOT / "hermes" / "skills"
INSTALL = "hermes plugins install tapway/tapway-superpowers/hermes/plugin"

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, msg: str) -> None:
    (PASS if cond else FAIL).append(msg)
    print(f"  {'PASS' if cond else 'FAIL'}  {msg}")


class _Ctx:
    def __init__(self) -> None:
        self.skills: list[tuple[str, Path]] = []

    def register_skill(self, name: str, path, description: str = "", frontmatter=None) -> None:
        self.skills.append((name, Path(path)))


def main() -> int:
    print("[1] manifest")
    manifest = PLUGIN / "plugin.yaml"
    check(manifest.is_file(), "hermes/plugin/plugin.yaml exists")
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    check("name: tapway-superpowers" in text, "plugin name is tapway-superpowers")
    check("version:" in text, "plugin.yaml has a version")

    print("\n[2] register()")
    init = PLUGIN / "__init__.py"
    check(init.is_file(), "hermes/plugin/__init__.py exists")
    body = init.read_text(encoding="utf-8") if init.is_file() else ""
    check("def register" in body, "defines register()")
    check("register_skill" in body, "calls ctx.register_skill")
    for bad in ("curl ", "sudo ", "python -c", "python3 -c"):
        check(bad not in body, f"__init__.py free of {bad!r}")

    print("\n[3] skill mirror")
    plugin_skills = PLUGIN / "skills"
    src = sorted(p.relative_to(SKILLS).as_posix() for p in SKILLS.rglob("*") if p.is_file())
    dst = (
        sorted(p.relative_to(plugin_skills).as_posix() for p in plugin_skills.rglob("*") if p.is_file())
        if plugin_skills.is_dir()
        else []
    )
    check(src == dst, f"plugin skills file list matches hermes/skills ({len(src)} files)")
    for rel in src:
        left, right = SKILLS / rel, plugin_skills / rel
        check(right.is_file() and filecmp.cmp(left, right, shallow=False), f"byte match {rel}")

    print("\n[4] registration covers every skill")
    if init.is_file():
        spec = importlib.util.spec_from_file_location("tapway_hermes_plugin", init)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        ctx = _Ctx()
        mod.register(ctx)
        registered = {name: path for name, path in ctx.skills}
        for skill_dir in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()):
            path = registered.get(skill_dir.name)
            check(path is not None and path.is_file() and path.name == "SKILL.md", f"registers {skill_dir.name}")
    else:
        check(False, "cannot import register()")

    print("\n[5] install command is documented")
    for rel in ("hermes/README.md", "README.md", "docs/DEPLOYMENT.md"):
        doc = (ROOT / rel).read_text(encoding="utf-8")
        check(INSTALL in doc, f"{rel} documents `{INSTALL}`")

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
