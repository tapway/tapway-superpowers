"""Exercise the docs-impact CLI against committed pull request diffs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest


CHECKER = Path(__file__).resolve().parents[1] / "scripts" / "docs_impact.py"
CODE = "scripts/service.py"
WORKFLOWS = "docs/WORKFLOWS.md"
DEPLOYMENT = "docs/DEPLOYMENT.md"
UPDATED = "Docs: updated — docs/WORKFLOWS.md"
NO_IMPACT = "Docs: no impact — Internal test fixture refactor; no public behavior changed."


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, encoding="utf-8",
        errors="replace", timeout=30,
    )
    assert result.returncode == 0, f"git {args!r}:\n{result.stdout}{result.stderr}"
    return result.stdout.strip()


def _commit(repo: Path, changes: Mapping[str, str | None]) -> str:
    for name, content in changes.items():
        path = repo / name
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=Docs Impact Test", "-c", "user.email=test@example.com",
         "commit", "-qm", "Fixture change")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Inherited Git variables/config must not redirect or modify the fixture repo.
    for key in os.environ.copy():
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "unused-gitconfig"))
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "--quiet", "--template=", "-b", "master")
    return path


@pytest.fixture
def base(repo: Path) -> str:
    return _commit(repo, {CODE: "MODE = 'old'\n"})


def _event(repo: Path, base: str, head: str, body: str | None) -> Path:
    event = repo.parent / "event.json"
    event.write_text(json.dumps({
        "action": "synchronize",
        "pull_request": {
            "base": {"sha": base, "ref": "master"},
            "head": {"sha": head, "ref": "feature"},
            "body": body,
        },
    }), encoding="utf-8")
    return event


def _check(repo: Path, event: Path, expected: int, *, advisory: bool = False) -> str:
    args = [sys.executable, str(CHECKER), str(event)]
    if advisory:
        args.append("--advisory")
    result = subprocess.run(
        args, cwd=repo, capture_output=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=30,
    )
    output = result.stdout + "\n" + result.stderr
    # Python exits 2 for a missing script, which is not a checker operational error.
    assert CHECKER.is_file(), output
    assert result.returncode == expected, f"Expected {expected}, got {result.returncode}:{output}"
    return output


@pytest.mark.parametrize(
    ("path", "content"),
    [
        (CODE, "MODE = 'new'\n"),
        (".github/workflows/quality.yml", "name: Quality\non: pull_request\n"),
        ("skills/repo-docs/SKILL.md", "# New docs review instructions\n"),
        ("VERSION", "2.0.0\n"),
    ],
    ids=["code", "workflow-config", "skill-markdown", "extensionless"],
)
def test_requires_declaration_for_non_doc_changes(repo: Path, base: str, path: str, content: str) -> None:
    head = _commit(repo, {path: content})
    _check(repo, _event(repo, base, head, None), 1)


def test_allows_docs_only_pr_without_declaration(repo: Path, base: str) -> None:
    head = _commit(repo, {WORKFLOWS: "# New workflow guide\n"})
    _check(repo, _event(repo, base, head, None), 0)


def test_uses_merge_base_when_base_branch_has_advanced(repo: Path, base: str) -> None:
    _git(repo, "branch", "feature", base)
    advanced_base = _commit(repo, {CODE: "MODE = 'changed on master'\n"})
    _git(repo, "switch", "feature")
    head = _commit(repo, {WORKFLOWS: "# New workflow guide\n"})
    _check(repo, _event(repo, advanced_base, head, None), 0)


@pytest.mark.parametrize("existing", [False, True], ids=["added", "modified"])
def test_updated_accepts_added_or_modified_docs(repo: Path, base: str, existing: bool) -> None:
    if existing:
        base = _commit(repo, {WORKFLOWS: "# Old workflow guide\n"})
    head = _commit(repo, {CODE: "MODE = 'new'\n", WORKFLOWS: "# New workflow guide\n"})
    _check(repo, _event(repo, base, head, UPDATED), 0)


@pytest.mark.parametrize("changed", [True, False], ids=["all-changed", "one-unchanged"])
def test_updated_checks_every_listed_path(repo: Path, base: str, changed: bool) -> None:
    base = _commit(repo, {DEPLOYMENT: "# Old deployment guide\n"})
    changes = {CODE: "MODE = 'new'\n", WORKFLOWS: "# New workflow guide\n"}
    if changed:
        changes[DEPLOYMENT] = "# New deployment guide\n"
    head = _commit(repo, changes)
    _check(repo, _event(repo, base, head, f"{UPDATED}, {DEPLOYMENT}"), 0 if changed else 1)


@pytest.mark.parametrize("status", ["unchanged", "deleted"])
def test_updated_rejects_unchanged_or_deleted_docs(repo: Path, base: str, status: str) -> None:
    base = _commit(repo, {WORKFLOWS: "# Workflow guide\n"})
    changes: dict[str, str | None] = {CODE: "MODE = 'new'\n"}
    if status == "deleted":
        changes[WORKFLOWS] = None
    head = _commit(repo, changes)
    _check(repo, _event(repo, base, head, UPDATED), 1)


@pytest.mark.parametrize("directory", ["plans", "checklists", "brainstorming"])
def test_updated_rejects_planning_artifacts(repo: Path, base: str, directory: str) -> None:
    path = f"docs/{directory}/feature.md"
    head = _commit(repo, {CODE: "MODE = 'new'\n", path: "# Feature notes\n"})
    _check(repo, _event(repo, base, head, f"Docs: updated — {path}"), 1)


def test_no_impact_accepts_specific_reason(repo: Path, base: str) -> None:
    head = _commit(repo, {"tests/test_service.py": "# Refactor the internal fixture\n"})
    _check(repo, _event(repo, base, head, None), 1)
    _check(repo, _event(repo, base, head, NO_IMPACT), 0)


@pytest.mark.parametrize(
    "body",
    [
        "Docs: no impact —",
        f"{NO_IMPACT}\n{NO_IMPACT}",
        NO_IMPACT.replace("—", "-"),
        f"- {NO_IMPACT}",
    ],
    ids=["missing-reason", "duplicate", "wrong-delimiter", "not-a-plain-line"],
)
def test_rejects_invalid_declarations(repo: Path, base: str, body: str) -> None:
    head = _commit(repo, {CODE: "MODE = 'new'\n"})
    _check(repo, _event(repo, base, head, body), 1)


def test_advisory_warns_without_failing_on_policy_violation(repo: Path, base: str) -> None:
    head = _commit(repo, {CODE: "MODE = 'new'\n"})
    output = _check(repo, _event(repo, base, head, None), 0, advisory=True)
    assert any(line.startswith("::warning::") for line in output.splitlines()), output


def test_pr_template_examples_do_not_count_as_a_declaration(repo: Path, base: str) -> None:
    head = _commit(repo, {CODE: "MODE = 'new'\n", WORKFLOWS: "# New workflow guide\n"})
    template = (CHECKER.parents[1] / ".github" / "pull_request_template.md").read_text(
        encoding="utf-8",
    )
    samples = f"{template}\n```text\n{UPDATED}\n```\n"
    _check(repo, _event(repo, base, head, samples), 1)
    _check(repo, _event(repo, base, head, f"{samples}\n{UPDATED}\n"), 0)


def test_uses_event_head_and_rechecks_after_event_update(repo: Path, base: str) -> None:
    old_head = _commit(repo, {CODE: "MODE = 'new'\n", WORKFLOWS: "# Workflow guide\n"})
    event = _event(repo, base, old_head, UPDATED)
    _check(repo, event, 0)

    new_head = _commit(repo, {WORKFLOWS: None})
    _check(repo, event, 0)  # Checkout moved, but the event still describes the old PR diff.
    _check(repo, _event(repo, base, new_head, UPDATED), 1)


@pytest.mark.parametrize("advisory", [False, True], ids=["enforced", "advisory"])
@pytest.mark.parametrize("problem", ["bare-event", "non-sha-ref", "unavailable-commit"])
def test_operational_errors_fail_in_both_modes(repo: Path, base: str, problem: str, advisory: bool) -> None:
    head = _commit(repo, {CODE: "MODE = 'new'\n"})
    if problem == "bare-event":
        event = repo.parent / "event.json"
        event.write_text("{}", encoding="utf-8")
    else:
        invalid_head = "HEAD" if problem == "non-sha-ref" else "f" * len(head)
        event = _event(repo, base, invalid_head, NO_IMPACT)
    _check(repo, event, 2, advisory=advisory)
