"""Contract gate tests (B4/B5/B10/B12)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.workflow_gate import check_file

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre-pr-contract" / "pre-pr-contract.sh"


def test_plan_without_issue_is_a_finding():
    findings = check_file("docs/plans/x.md", "---\ntitle: x\n---\n\n# X\n")
    assert findings and "issue:" in findings[0]


def test_plan_with_issue_passes():
    assert check_file("docs/plans/x.md", "---\nissue: 42\n---\n\n# X\n") == []


def test_brainstorm_without_grounding_is_a_finding():
    assert check_file("docs/brainstorming/x.md", "# B\n\n## Option A\n\nno citation\n")


def test_unrelated_doc_is_ignored():
    assert check_file("README.md", "# hello\n") == []


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def test_pre_pr_hook_blocks_a_plan_without_issue(tmp_path: Path):
    _git(tmp_path, "init", "-b", "staging")
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "plans" / "x.md").write_text("# base\n")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "base")

    _git(tmp_path, "checkout", "-b", "feat")
    (tmp_path / "docs" / "plans" / "x.md").write_text("---\ntitle: no issue\n---\n\n# X\n")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "plan")

    result = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh pr create --fill"}}),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "CLAUDE_PLUGIN_ROOT": str(ROOT),
            "TAPWAY_PR_BASE": "staging",
        },
    )
    verdict = json.loads(result.stdout or "{}")
    assert verdict.get("decision") == "block", verdict


def test_pre_pr_hook_ignores_other_commands(tmp_path: Path):
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "CLAUDE_PLUGIN_ROOT": str(ROOT)},
    )
    assert json.loads(result.stdout or "{}") == {}
