"""Hermes pre_tool_call gates (B6).

Runs in-process, so it works even when the shell hooks are not installed. It
mirrors hooks/pre-brainstorm-ground: a write to ``docs/brainstorming/*.md`` must
carry a ``Grounding:`` line for every option section, or an explicit
``UNKNOWN (not retrieved: …)`` row.

Returning ``{"action": "block", "message": …}`` is the Hermes hook contract;
returning ``None`` lets the tool run.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

BRAINSTORM_PREFIX = "docs/brainstorming/"
WRITE_TOOLS = {
    "write_file",
    "patch",
    "edit",
    "apply_patch",
    "Write",
    "Edit",
    "MultiEdit",
}
OPTION_RE = re.compile(r"^#{2,3}\s+(?:Option|Approach|Alternative|Proposal)\b.*$", re.MULTILINE | re.IGNORECASE)
GROUNDING_RE = re.compile(r"Grounding:\s*\S|UNKNOWN \(not retrieved", re.IGNORECASE)


def enabled() -> bool:
    """Explicit env wins; otherwise on under CodeMAX, off elsewhere (public repo)."""
    value = os.environ.get("TAPWAY_BRAINSTORM_GATE")
    if value is not None:
        return value == "1"
    return os.environ.get("CODEMAX_WORKFLOW") == "1" or Path(".codemax.yml").is_file()


def _target(args: dict[str, Any]) -> tuple[str, str]:
    path = ""
    for key in ("file_path", "path"):
        if isinstance(args.get(key), str):
            path = args[key]
            break
    text = ""
    for key in ("content", "new_string"):
        if isinstance(args.get(key), str):
            text = args[key]
            break
    return path, text


def _normalise(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def check_doc(path: str, text: str) -> list[str]:
    """Return one finding per ungrounded option section (empty = allowed)."""
    if not _normalise(path).startswith(BRAINSTORM_PREFIX):
        return []
    if not text.strip():
        return []

    matches = list(OPTION_RE.finditer(text))
    if not matches:
        return ["no '## Option / Approach / Alternative / Proposal' section — a brainstorm needs at least one"]

    findings: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.end() : end]
        if not GROUNDING_RE.search(section):
            findings.append(f"{match.group(0).strip()} has no 'Grounding:' line")
    return findings


def on_pre_tool_call(tool_name: str = "", args: Any = None, **_: Any) -> dict[str, str] | None:
    if tool_name not in WRITE_TOOLS:
        return None
    if not enabled():
        return None
    if not isinstance(args, dict):
        return None

    path, text = _target(args)
    if not path:
        return None

    findings = check_doc(path, text)
    if not findings:
        return None
    return {
        "action": "block",
        "message": (
            "tapway-superpowers refused this brainstorm write — every option must cite "
            "the brain with a 'Grounding: <wiki/...>' line (or an explicit "
            "'UNKNOWN (not retrieved: <reason>)').\n\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\nTo override for one run, set TAPWAY_BRAINSTORM_GATE=0."
        ),
    }