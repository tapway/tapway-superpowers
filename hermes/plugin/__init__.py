"""Register Tapway Superpowers skills into the installing Hermes profile.

Skills load as ``tapway-superpowers:<name>`` via ``skill_view``. They are not
copied into the skills directory and do not become bare ``/<name>`` commands.

Registration is deliberately loud on a broken tree: a plugin that silently
registers zero skills is indistinguishable from a working one until someone
tries to load a skill.
"""
from pathlib import Path


def _frontmatter(skill_md: Path) -> dict:
    """Parse the YAML frontmatter block of a SKILL.md (``{}`` when absent).

    Hermes lists a plugin skill with the description passed to ``register_skill``
    — it does not re-read the file for the tier-1 listing — so the description and
    frontmatter have to come from here or they arrive empty.

    Inside Hermes this uses the runtime's own ``parse_frontmatter``
    (``hermes_yaml``). The bundled Hermes interpreter does **not** ship PyYAML, so
    importing ``yaml`` here would fail plugin registration outright — PyYAML is
    only a fallback for running this module outside Hermes (tests, tooling).
    """
    text = skill_md.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}

    try:  # the parser Hermes itself uses for every SKILL.md
        from agent.skill_utils import parse_frontmatter
    except Exception:
        parse_frontmatter = None
    if parse_frontmatter is not None:
        data, _body = parse_frontmatter(text)
        return data if isinstance(data, dict) else {}

    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        import yaml
    except ImportError:
        raise RuntimeError(
            f"{skill_md}: cannot parse frontmatter — no YAML parser available "
            "(expected Hermes' agent.skill_utils)"
        ) from None
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError as exc:
        raise RuntimeError(f"{skill_md}: invalid YAML frontmatter: {exc}") from exc
    return data if isinstance(data, dict) else {}


def register(ctx):
    # Hermes-side gates (B6): run even when the shell hooks are not installed.
    # A hook that raises would take the tool call down with it, so the gate is
    # loaded defensively and never blocks on its own failure mode except when
    # the payload is a brainstorm write it cannot evaluate.
    if hasattr(ctx, "register_hook"):
        try:
            from . import gates

            ctx.register_hook("pre_tool_call", gates.on_pre_tool_call)
        except Exception as exc:  # noqa: BLE001 - a missing hook must not break skills
            import logging

            logging.getLogger(__name__).warning("tapway-superpowers gates not registered: %s", exc)

    skills_dir = Path(__file__).parent / "skills"
    if not skills_dir.is_dir():
        raise RuntimeError(
            f"tapway-superpowers plugin is incomplete: {skills_dir} is missing. "
            "Reinstall it with: hermes plugins install tapway/tapway-superpowers/hermes/plugin --enable"
        )
    children = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not children:
        raise RuntimeError(f"tapway-superpowers plugin has no skills: {skills_dir} is empty")

    for child in children:
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            raise RuntimeError(f"tapway-superpowers skill '{child.name}' has no SKILL.md ({skill_md})")
        frontmatter = _frontmatter(skill_md)
        ctx.register_skill(
            child.name,
            skill_md,
            description=str(frontmatter.get("description") or ""),
            frontmatter=frontmatter,
        )