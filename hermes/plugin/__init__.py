"""Register Tapway Superpowers skills into the installing Hermes profile.

Skills load as ``tapway-superpowers:<name>`` via ``skill_view``. They are not
copied into the skills directory and do not become bare ``/<name>`` commands.
"""
from pathlib import Path


def register(ctx):
    skills_dir = Path(__file__).parent / "skills"
    if not skills_dir.is_dir():
        return
    for child in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = child / "SKILL.md"
        if skill_md.is_file():
            ctx.register_skill(child.name, skill_md)
