#!/usr/bin/env python3
"""Hermes plugin package: installable subdirectory, mirrors hermes/skills.

Checks are written against the **real** Hermes plugin API where it is available
(``PluginContext.register_skill``, ``scan_plugin``, ``_serve_plugin_skill``).
A hand-rolled mock proves nothing about the contract the plugin actually meets.

Checks that need hermes-agent are reported as SKIP when it is not installed, so
this still runs in a checkout without it — but a developer machine is expected
to exercise all of them, and the plugin behaviour is only verified there.
"""
from __future__ import annotations

import filecmp
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "hermes" / "plugin"
SKILLS = ROOT / "hermes" / "skills"
SYNC_SCRIPT = ROOT / "scripts" / "sync-hermes-plugin-skills.sh"
INSTALL = "hermes plugins install tapway/tapway-superpowers/hermes/plugin --enable"

PASS: list[str] = []
FAIL: list[str] = []
SKIP: list[str] = []


def check(cond: bool, msg: str) -> None:
    (PASS if cond else FAIL).append(msg)
    print(f"  {'PASS' if cond else 'FAIL'}  {msg}")


def skip(msg: str) -> None:
    SKIP.append(msg)
    print(f"  SKIP  {msg}")


def _load_plugin_module(plugin_dir: Path = PLUGIN):
    init = plugin_dir / "__init__.py"
    if not init.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"tapway_hermes_plugin_{id(plugin_dir)}", init)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _hermes_api():
    """Import the real plugin API from a hermes-agent checkout, or return None."""
    for cand in (os.environ.get("HERMES_AGENT_PATH"), "/usr/local/lib/hermes-agent", str(Path.home() / "hermes-agent")):
        if cand and (Path(cand) / "hermes_cli" / "plugins.py").is_file():
            if cand not in sys.path:
                sys.path.insert(0, cand)
            break
    try:
        import yaml  # noqa: F401 - a Hermes install without PyYAML cannot parse config either

        from hermes_cli.plugins import PluginContext, PluginManager
        from hermes_cli.plugins_manifest import PluginManifest

        return PluginContext, PluginManager, PluginManifest
    except Exception:
        return None


def _real_context(plugin_dir: Path = PLUGIN):
    """A real ``PluginContext`` bound to a throwaway HERMES_HOME (no global state)."""
    api = _hermes_api()
    if api is None:
        return None
    PluginContext, PluginManager, PluginManifest = api
    os.environ["HERMES_HOME"] = tempfile.mkdtemp(prefix="tapway-plugin-home-")
    manager = PluginManager()
    manifest = PluginManifest(name="tapway-superpowers", path=str(plugin_dir))
    return PluginContext(manifest, manager), manager


def _copy_plugin() -> Path:
    target = Path(tempfile.mkdtemp(prefix="tapway-plugin-copy-")) / "plugin"
    shutil.copytree(PLUGIN, target, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def _manifest_version() -> str:
    match = re.search(r"^version:\s*(\S+)", (PLUGIN / "plugin.yaml").read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else ""


def _json_version() -> str:
    return str(json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version", ""))


def _changelog_version() -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return match.group(1) if match else ""


def section_manifest() -> None:
    print("[1] manifest")
    manifest = PLUGIN / "plugin.yaml"
    check(manifest.is_file(), "hermes/plugin/plugin.yaml exists")
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    check("name: tapway-superpowers" in text, "plugin name is tapway-superpowers")
    check(bool(_manifest_version()), "plugin.yaml has a version")
    check(
        _manifest_version() == _json_version() == _changelog_version(),
        "version matches .claude-plugin/plugin.json and CHANGELOG "
        f"({_manifest_version()} / {_json_version()} / {_changelog_version()})",
    )
    check(bool(re.search(r"^api_version:\s*[1-9]\d*", text, re.MULTILINE)), "api_version declares the plugin API generation")


def section_register_source() -> None:
    print("\n[2] register() source")
    init = PLUGIN / "__init__.py"
    check(init.is_file(), "hermes/plugin/__init__.py exists")
    body = init.read_text(encoding="utf-8") if init.is_file() else ""
    check("def register" in body, "defines register()")
    check("register_skill" in body, "calls ctx.register_skill")
    check("description=" in body, "passes the skill description to the registrar")
    check("frontmatter" in body, "passes frontmatter to the registrar")
    for bad in ("curl ", "sudo ", "python -c", "python3 -c"):
        check(bad not in body, f"__init__.py free of {bad!r}")


def section_fail_loud() -> None:
    print("\n[3] register() fails loudly instead of registering nothing")
    build = _real_context()
    if build is None:
        skip("real PluginContext unavailable — failure paths not exercised")
        return
    ctx, _manager = build

    no_skills = _copy_plugin()
    shutil.rmtree(no_skills / "skills")
    mod = _load_plugin_module(no_skills)
    try:
        mod.register(_real_context(no_skills)[0])
        check(False, "missing skills/ raises")
    except Exception as exc:  # noqa: BLE001 - any loud failure is the contract
        check(
            "skills" in str(exc).lower() or "SKILL.md" in str(exc),
            f"missing skills/ raises ({type(exc).__name__})",
        )

    partial = _copy_plugin()
    victim = sorted(p for p in (partial / "skills").iterdir() if p.is_dir())[0]
    (victim / "SKILL.md").unlink()
    try:
        _load_plugin_module(partial).register(_real_context(partial)[0])
        check(False, "a skill directory without SKILL.md raises")
    except Exception as exc:  # noqa: BLE001
        check(victim.name in str(exc), f"skill directory without SKILL.md raises ({victim.name})")


def section_mirror() -> None:
    print("\n[4] skill mirror")
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

    print("\n[5] mirror regeneration tooling")
    check(SYNC_SCRIPT.is_file(), "scripts/sync-hermes-plugin-skills.sh exists")
    if SYNC_SCRIPT.is_file():
        check(os.access(SYNC_SCRIPT, os.X_OK), "sync script is executable")
        proc = subprocess.run([str(SYNC_SCRIPT), "--check"], cwd=ROOT, capture_output=True, text=True, timeout=120)
        check(proc.returncode == 0, f"sync script --check reports no drift (exit {proc.returncode})")
    workflows = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
    check("sync-hermes-plugin-skills.sh" in workflows, "docs/WORKFLOWS.md documents the sync script")


def section_registration() -> None:
    print("\n[6] real registration")
    mod = _load_plugin_module()
    if mod is None:
        check(False, "cannot import register()")
        return
    build = _real_context()
    if build is None:
        skip("real PluginContext unavailable — registration contract not exercised")
        return
    ctx, manager = build
    try:
        mod.register(ctx)
    except Exception as exc:  # noqa: BLE001
        check(False, f"register() against the real PluginContext raised: {exc}")
        return

    registered = manager.list_plugin_skills("tapway-superpowers")
    expected = sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())
    check(registered == expected, f"registers every skill ({len(registered)}/{len(expected)})")

    metas = {m["name"]: m for m in manager.list_plugin_skill_metadata()}
    missing_desc = [name for name, meta in metas.items() if not str(meta.get("description", "")).strip()]
    check(not missing_desc, f"every skill has a non-empty description ({len(missing_desc)} empty)")
    missing_fm = [name for name, meta in metas.items() if not meta.get("frontmatter")]
    check(not missing_fm, f"every skill carries its frontmatter ({len(missing_fm)} empty)")

    incident = manager.find_plugin_skill("tapway-superpowers:incident-runbook")
    check(
        incident is not None and incident.is_file() and PLUGIN in incident.parents,
        "registered path points into hermes/plugin/skills",
    )

    print("\n[7] linked files resolve")
    if incident is None:
        check(False, "incident-runbook is not registered")
        return
    from tools.skills_tool_plugin import _serve_plugin_skill

    skill_dir = incident.parent
    support = sorted(
        p.relative_to(skill_dir).as_posix() for p in skill_dir.rglob("*") if p.is_file() and p.name != "SKILL.md"
    )
    if not support:
        check(False, "incident-runbook ships no linked files to resolve")
    else:
        rel = support[0]
        payload = json.loads(_serve_plugin_skill(incident, "tapway-superpowers", "incident-runbook", file_path=rel))
        check(payload.get("success") is True, f"skill_view(file_path={rel!r}) resolves")


def section_guard() -> None:
    print("\n[8] plugin-guard verdict")
    try:
        from tools.plugin_guard import scan_plugin, should_allow_plugin_install
    except Exception:
        skip("plugin-guard unavailable — install gate not exercised")
        return
    result = scan_plugin(PLUGIN)
    check(
        result.verdict == "safe",
        f"plugin-guard verdict is safe (got {result.verdict}, {len(result.findings)} findings)",
    )
    allowed, reason = should_allow_plugin_install(result)
    check(allowed is True, f"install is allowed without --force ({reason})")


def section_docs() -> None:
    print("\n[9] install command is documented")
    for rel in ("hermes/README.md", "README.md", "docs/DEPLOYMENT.md", "docs/WORKFLOWS.md"):
        doc = (ROOT / rel).read_text(encoding="utf-8")
        check(INSTALL in doc, f"{rel} documents `{INSTALL}`")


def section_newlines() -> None:
    print("\n[10] text files end with a newline")
    targets = [ROOT / "docs" / "WORKFLOWS.md", *(p for p in SKILLS.rglob("*") if p.is_file())]
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in targets
        if p.suffix in {".md", ".py", ".sh", ".yaml", ".yml", ".json"} and not p.read_bytes().endswith(b"\n")
    ]
    check(not offenders, f"no missing trailing newlines ({', '.join(offenders[:5]) or 'none'})")


def main() -> int:
    section_manifest()
    section_register_source()
    section_fail_loud()
    section_mirror()
    section_registration()
    section_guard()
    section_docs()
    section_newlines()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(SKIP)} skipped")
    return 1 if FAIL else 0


def test_hermes_plugin_suite() -> None:
    """pytest entry point, so `pytest tests/` collects this script too."""
    assert main() == 0, f"{len(FAIL)} check(s) failed"


if __name__ == "__main__":
    raise SystemExit(main())