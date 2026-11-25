"""TDD for the payload adapter and the Hermes in-process gate (B1/B2/B6/B12)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from hermes.plugin.gates import check_doc, on_pre_tool_call
from hooks.lib.hook_payload import normalize

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre-brainstorm-ground" / "pre-brainstorm-ground.sh"

GROUNDED = "# B\n\n## Option A\n\nGrounding: wiki/platforms/city-os/blueprints/bp-a\n"
UNGROUNDED = "# B\n\n## Option A\n\nBecause I think so.\n"


def test_normalise_claude_shape():
    out = normalize({"tool_name": "Write", "tool_input": {"file_path": "a.md", "content": "x"}})
    assert out["tool_name"] == "Write"
    assert out["tool_input"] == {"file_path": "a.md", "content": "x"}


def test_normalise_hermes_shape():
    out = normalize({"tool_name": "write_file", "args": {"file_path": "a.md", "content": "x"}})
    assert out["tool_input"] == {"file_path": "a.md", "content": "x"}


def test_normalise_codex_flat_shape():
    out = normalize({"file_path": "a.md", "content": "x"})
    assert out["tool_input"]["file_path"] == "a.md"
    assert out["tool_input"]["content"] == "x"


def test_grounded_doc_is_allowed():
    assert check_doc("docs/brainstorming/x.md", GROUNDED) == []


def test_ungrounded_option_is_reported():
    findings = check_doc("docs/brainstorming/x.md", UNGROUNDED)
    assert findings and "Option A" in findings[0]


def test_doc_without_options_is_reported():
    assert check_doc("docs/brainstorming/x.md", "# just prose\n") != []


def test_non_brainstorm_path_is_ignored():
    assert check_doc("docs/plans/x.md", UNGROUNDED) == []


def test_hook_blocks_a_brainstorm_write(monkeypatch):
    monkeypatch.setenv("TAPWAY_BRAINSTORM_GATE", "1")
    verdict = on_pre_tool_call(
        tool_name="write_file",
        args={"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED},
    )
    assert verdict and verdict["action"] == "block"


def test_hook_allows_a_grounded_write(monkeypatch):
    monkeypatch.setenv("TAPWAY_BRAINSTORM_GATE", "1")
    assert (
        on_pre_tool_call(
            tool_name="write_file",
            args={"file_path": "docs/brainstorming/x.md", "content": GROUNDED},
        )
        is None
    )


def test_hook_is_off_by_default_outside_codemax(monkeypatch, tmp_path):
    monkeypatch.delenv("TAPWAY_BRAINSTORM_GATE", raising=False)
    monkeypatch.delenv("CODEMAX_WORKFLOW", raising=False)
    monkeypatch.chdir(tmp_path)
    assert on_pre_tool_call(tool_name="write_file", args={"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED}) is None


def test_hook_is_on_under_codemax(monkeypatch, tmp_path):
    monkeypatch.delenv("TAPWAY_BRAINSTORM_GATE", raising=False)
    monkeypatch.setenv("CODEMAX_WORKFLOW", "1")
    monkeypatch.chdir(tmp_path)
    verdict = on_pre_tool_call(
        tool_name="write_file", args={"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED}
    )
    assert verdict and verdict["action"] == "block"


def _run_hook(payload: dict, env_gate: str = "1") -> dict:
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "TAPWAY_BRAINSTORM_GATE": env_gate},
    )
    return json.loads(result.stdout or "{}")


def test_e2e_hermes_payload_blocks():
    verdict = _run_hook(
        {"tool_name": "write_file", "args": {"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED}}
    )
    assert verdict.get("decision") == "block" or verdict.get("action") == "block", verdict


def test_e2e_claude_payload_blocks():
    verdict = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED}}
    )
    assert verdict, "Claude-shaped payload was not gated"


def test_e2e_claude_payload_grounded_allows():
    verdict = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "docs/brainstorming/x.md", "content": GROUNDED}}
    )
    assert verdict == {} or verdict.get("decision") not in ("block", "deny") or verdict == {}


def test_e2e_codex_flat_payload_blocks():
    verdict = _run_hook({"file_path": "docs/brainstorming/x.md", "content": UNGROUNDED})
    assert verdict, "Codex-shaped payload was not gated"
