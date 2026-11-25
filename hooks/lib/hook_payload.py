#!/usr/bin/env python3
"""Normalise tool-call payloads from Claude Code, Codex and Hermes (B1).

Claude nests the arguments under ``tool_input``. Hermes' ``pre_tool_call``
sends ``{"tool_name": ..., "args": {...}}``. Codex sends a flatter shape. Every
gate reads one shape after this runs, so a payload change in one harness cannot
silently disable the gate in another.
"""

from __future__ import annotations

import json
import sys
from typing import Any

FLAT_KEYS = ("file_path", "path", "content", "new_string", "command")
NESTED_KEYS = ("tool_input", "args", "toolArgs", "input", "arguments")


def normalize(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"tool_name": "", "tool_input": {}}

    tool = ""
    for key in ("tool_name", "toolName", "tool", "name"):
        if isinstance(raw.get(key), str) and raw[key]:
            tool = raw[key]
            break

    tool_input: dict[str, Any] = {}
    for key in NESTED_KEYS:
        value = raw.get(key)
        if isinstance(value, dict):
            tool_input = dict(value)
            break

    for key in FLAT_KEYS:
        if key in raw and key not in tool_input:
            tool_input[key] = raw[key]

    merged = dict(raw)
    merged["tool_name"] = tool
    merged["tool_input"] = tool_input
    return merged


def main() -> int:
    try:
        raw = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raw = {}
    json.dump(normalize(raw), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())