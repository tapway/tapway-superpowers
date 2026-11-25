#!/usr/bin/env python3
"""Plan → GitHub issue: renderer, frontmatter write-back, hook and gates.

Runs with the stdlib only (``python3 tests/test_plan_issue.py``), like the rest
of this repo's test scripts — no pytest, no PyYAML, no network.

The renderer checks are the contract for issue readability: every issue this
hook opens must carry Summary, What changes, Acceptance criteria and a collapsed
full plan, whatever shape the source plan has.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes.plugin import plan_issue  # noqa: E402

PLAN = textwrap.dedent(
    """\
    ---
    title: Auto-create the GitHub issue
    date: 2026-11-18
    ---

    # Auto-create the GitHub issue after a plan — Implementation Plan

    **Goal:** Make the plan → issue step happen without anyone remembering it.

    **Problem:** Nothing triggers issue creation today.

    ## Branch 1: feat/plan-issue-autocreate

    ### Task 1.1: A plan → issue renderer that reads well

    **Objective:** One stdlib module that renders a readable body.

    **Files:**
    - Create: `hermes/plugin/plan_issue.py`
    - Test: `tests/test_plan_issue.py`

    ### Task 1.2: Idempotent creation

    **Objective:** Reuse an existing issue, else create one.

    **Files:**
    - Modify: `hermes/plugin/plan_issue.py`

    ## Testing

    - `python3 tests/test_plan_issue.py`
    """
)


ACCEPTED_DESIGN = textwrap.dedent(
    """\
    ---
    status: accepted
    title: Accepted design
    ---

    # Brainstorm: accepted design

    **Problem:** An accepted design must open one issue.

    ## Recommendation

    - Open the issue from the design doc.

    ## Acceptance criteria

    - Exactly one issue is created.
    """
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    )


class PlanFile:
    """A throwaway git checkout with one plan file committed."""

    def __init__(self, text: str = PLAN, branch: str = "feat/plan-issue") -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plan = self.root / "docs" / "plans" / "x.md"
        _git(self.root, "init", "-b", "staging")
        _git(self.root, "remote", "add", "origin", "https://github.com/tapway/fake.git")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "base")
        _git(self.root, "update-ref", "refs/remotes/origin/staging", "HEAD")
        # The plan is written on the feature branch — that is what the PR diff sees.
        _git(self.root, "checkout", "-b", branch)
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text(text, encoding="utf-8")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "plan")

    def cleanup(self) -> None:
        self._tmp.cleanup()


class FakeGh:
    """Records every gh invocation and answers like the real CLI."""

    def __init__(self, *, create_number: int = 77, existing: int | None = None,
                 existing_branch: str = "", issues: list[dict] | None = None,
                 fail: bool = False) -> None:
        self.calls: list[list[str]] = []
        self.create_number = create_number
        self.issues = issues if issues is not None else (
            [{"number": existing, "body": f"- **Branch:** `{existing_branch}`\n"}]
            if existing else []
        )
        self.fail = fail
        self.body_file: str | None = None

    def __call__(self, args: list[str], cwd: Path | None = None):
        self.calls.append(list(args))
        joined = " ".join(args)
        if "issue list" in joined:
            out = json.dumps(self.issues)
        elif "issue create" in joined:
            if self.fail:
                return subprocess.CompletedProcess(args, 1, "", "label not found")
            for i, arg in enumerate(args):
                if arg == "--body-file":
                    self.body_file = Path(args[i + 1]).read_text(encoding="utf-8")
            out = f"https://github.com/tapway/fake/issues/{self.create_number}"
        else:
            out = ""
        return subprocess.CompletedProcess(args, 0, out, "")


class RenderTests(unittest.TestCase):
    def test_title_strips_plan_boilerplate_and_takes_type_from_branch(self):
        title = plan_issue.render_title(PLAN, "feat/plan-issue-autocreate")
        self.assertEqual(title, "feat: Auto-create the GitHub issue after a plan")

    def test_title_falls_back_to_branch_when_plan_has_no_h1(self):
        title = plan_issue.render_title("no headings here\n", "fix/poller-301")
        self.assertEqual(title, "fix: poller 301")

    def test_body_has_the_readable_sections(self):
        body = plan_issue.render_body(PLAN, plan_path="docs/plans/x.md", branch="feat/x",
                                      repo="tapway/fake")
        for heading in ("## Summary", "## Why", "## What changes", "## Acceptance criteria",
                        "## Test plan", "## Files", "## Links"):
            self.assertIn(heading, body)
        self.assertIn("Make the plan → issue step happen", body)
        self.assertIn("Nothing triggers issue creation today", body)

    def test_tasks_become_checkboxes_grouped_by_section(self):
        body = plan_issue.render_body(PLAN, plan_path="docs/plans/x.md", branch="feat/x",
                                      repo="tapway/fake")
        changes = body.split("## What changes", 1)[1].split("## Acceptance criteria", 1)[0]
        self.assertIn("feat/plan-issue-autocreate", changes)
        self.assertIn("- [ ] Task 1.1: A plan → issue renderer that reads well", changes)
        self.assertIn("- [ ] Task 1.2: Idempotent creation", changes)

    def test_files_are_listed_with_their_disposition(self):
        body = plan_issue.render_body(PLAN, plan_path="docs/plans/x.md", branch="feat/x",
                                      repo="tapway/fake")
        files = body.split("## Files", 1)[1].split("## Links", 1)[0]
        self.assertIn("`hermes/plugin/plan_issue.py` — create", files)
        self.assertIn("`tests/test_plan_issue.py` — test", files)

    def test_per_task_acceptance_criteria_are_harvested(self):
        plan = textwrap.dedent(
            """\
            # Tighten the input parser

            **Out of scope:** rewriting the lexer.

            ## Branch 1: feat/parser

            ### Task 1.1: Reject empty keys

            **Acceptance criteria:**
            - AC-1.1.1 An empty key raises ValueError.
            - AC-1.1.2 The error names the offending line.
            """
        )
        body = plan_issue.render_body(plan, plan_path="docs/plans/p.md", branch="feat/parser",
                                      repo="tapway/fake")
        criteria = body.split("## Acceptance criteria", 1)[1].split("## Test plan", 1)[0]
        self.assertIn("- [ ] AC-1.1.1 An empty key raises ValueError.", criteria)
        self.assertIn("- [ ] AC-1.1.2 The error names the offending line.", criteria)
        self.assertIn("## Out of scope", body)
        self.assertIn("rewriting the lexer", body)

    def test_full_plan_is_collapsed_and_body_stays_under_github_limit(self):
        huge = PLAN + "\n" + ("padding line\n" * 20000)
        body = plan_issue.render_body(huge, plan_path="docs/plans/x.md", branch="feat/x",
                                      repo="tapway/fake")
        self.assertLess(len(body), 60000)
        self.assertIn("<details>", body)

    def test_plan_without_recognisable_sections_still_renders(self):
        body = plan_issue.render_body("# Do the thing\n\nJust do it.\n", plan_path="docs/plans/y.md",
                                      branch="feat/y", repo="tapway/fake")
        self.assertIn("## Summary", body)
        self.assertIn("## Acceptance criteria", body)
        self.assertIn("Just do it.", body)


class FrontmatterTests(unittest.TestCase):
    def test_issue_number_reads_frontmatter_only(self):
        self.assertEqual(plan_issue.issue_number("---\nissue: 42\n---\n"), 42)
        self.assertIsNone(plan_issue.issue_number("---\ntitle: x\n---\nissue: 42\n"))

    def test_record_issue_inserts_into_existing_frontmatter(self):
        got = plan_issue.record_issue_text("---\ntitle: x\n---\n\n# H\n", 9)
        self.assertIn("issue: 9", got)
        self.assertIn("title: x", got)
        self.assertTrue(got.rstrip().endswith("# H"))

    def test_record_issue_replaces_an_existing_number(self):
        got = plan_issue.record_issue_text("---\nissue: 1\n---\n\n# H\n", 9)
        self.assertEqual(got.count("issue:"), 1)
        self.assertIn("issue: 9", got)

    def test_record_issue_creates_frontmatter_when_missing(self):
        got = plan_issue.record_issue_text("# H\n\nbody\n", 9)
        self.assertTrue(got.startswith("---\nissue: 9\n---\n"))
        self.assertIn("# H", got)


class EnsureIssueTests(unittest.TestCase):
    def setUp(self):
        self.repo = PlanFile()
        self.addCleanup(self.repo.cleanup)

    def test_plan_with_issue_never_calls_gh(self):
        self.repo.plan.write_text(plan_issue.record_issue_text(self.repo.plan.read_text(), 5),
                                  encoding="utf-8")
        gh = FakeGh()
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=gh)
        self.assertEqual(gh.calls, [])
        self.assertEqual(result.number, 5)
        self.assertFalse(result.created)

    def test_promotion_branches_are_skipped(self):
        for branch in ("master", "staging", "main", "prod"):
            gh = FakeGh()
            result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                             branch=branch, runner=gh)
            self.assertEqual(gh.calls, [], branch)
            self.assertEqual(result.skipped, "protected-branch")

    def test_creates_issue_and_writes_number_back(self):
        gh = FakeGh(create_number=77)
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=gh)
        self.assertTrue(result.created)
        self.assertEqual(result.number, 77)
        create = [c for c in gh.calls if "issue create" in " ".join(c)][0]
        joined = " ".join(create)
        self.assertIn("--label codemax", joined)
        self.assertIn("--repo tapway/fake", joined)
        self.assertIn("feat: Auto-create the GitHub issue after a plan", joined)
        self.assertIn("## Acceptance criteria", gh.body_file or "")
        self.assertEqual(plan_issue.issue_number(self.repo.plan.read_text()), 77)

    def test_reuses_an_existing_issue_instead_of_creating_a_second(self):
        gh = FakeGh(existing=31, existing_branch="feat/plan-issue")
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=gh)
        self.assertFalse(result.created)
        self.assertEqual(result.number, 31)
        self.assertFalse([c for c in gh.calls if "issue create" in " ".join(c)])
        self.assertEqual(plan_issue.issue_number(self.repo.plan.read_text()), 31)

    def test_does_not_adopt_an_issue_from_another_branch(self):
        """Branch names share tokens; adoption must compare the exact branch."""
        other = plan_issue.render_body(
            self.repo.plan.read_text(), plan_path="docs/plans/x.md",
            branch="feat/plan-issue-autocreate", repo="tapway/fake",
        )
        gh = FakeGh(issues=[{"number": 31, "body": other}])
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=gh)
        self.assertTrue(result.created)
        self.assertEqual(result.number, 77)
        self.assertEqual(plan_issue.issue_number(self.repo.plan.read_text()), 77)

    def test_adopts_the_exact_branch_among_overlapping_issues(self):
        other = plan_issue.render_body(
            self.repo.plan.read_text(), plan_path="docs/plans/x.md",
            branch="feat/plan-issue-autocreate", repo="tapway/fake",
        )
        mine = plan_issue.render_body(
            self.repo.plan.read_text(), plan_path="docs/plans/x.md",
            branch="feat/plan-issue", repo="tapway/fake",
        )
        gh = FakeGh(issues=[{"number": 31, "body": other}, {"number": 32, "body": mine}])
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=gh)
        self.assertFalse(result.created)
        self.assertEqual(result.number, 32)
        self.assertFalse([c for c in gh.calls if "issue create" in " ".join(c)])

    def test_failed_create_leaves_the_plan_untouched(self):
        before = self.repo.plan.read_text()
        result = plan_issue.ensure_issue(self.repo.plan, repo="tapway/fake",
                                         branch="feat/plan-issue", runner=FakeGh(fail=True))
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.number)
        self.assertEqual(self.repo.plan.read_text(), before)


class HermesGateTests(unittest.TestCase):
    def setUp(self):
        self.repo = PlanFile()
        self.addCleanup(self.repo.cleanup)
        os.environ["CODEMAX_WORKFLOW"] = "1"
        self.addCleanup(os.environ.pop, "CODEMAX_WORKFLOW", None)

    def test_the_documented_codemax_enabled_switch_turns_the_gate_on(self):
        os.environ.pop("CODEMAX_WORKFLOW", None)
        os.environ["CODEMAX_ENABLED"] = "1"
        self.addCleanup(os.environ.pop, "CODEMAX_ENABLED", None)
        from hermes.plugin import gates

        self.assertTrue(gates.enabled())
        verdict = gates.on_pre_tool_call(
            tool_name="terminal",
            args={"command": "gh pr create --fill", "workdir": str(self.repo.root)},
        )
        self.assertEqual((verdict or {}).get("action"), "block")

    def test_hermes_blocks_gh_pr_create_when_the_plan_has_no_issue(self):
        from hermes.plugin import gates

        verdict = gates.on_pre_tool_call(
            tool_name="terminal",
            args={"command": "gh pr create --base staging --fill", "workdir": str(self.repo.root)},
        )
        self.assertIsNotNone(verdict)
        self.assertEqual(verdict["action"], "block")
        self.assertIn("issue:", verdict["message"])

    def test_hermes_allows_the_same_command_once_the_issue_is_recorded(self):
        self.repo.plan.write_text(plan_issue.record_issue_text(self.repo.plan.read_text(), 12),
                                  encoding="utf-8")
        from hermes.plugin import gates

        self.assertIsNone(
            gates.on_pre_tool_call(
                tool_name="terminal",
                args={"command": "gh pr create --base staging --fill", "workdir": str(self.repo.root)},
            )
        )

    def test_hermes_allows_non_pr_commands_and_unknown_cwd(self):
        from hermes.plugin import gates

        self.assertIsNone(gates.on_pre_tool_call(tool_name="terminal", args={"command": "git status"}))
        self.assertIsNone(
            gates.on_pre_tool_call(
                tool_name="terminal",
                args={"command": "gh pr create --fill", "workdir": "/tmp"},
            )
        )

    def test_hermes_pr_gate_honours_the_documented_escape_hatch(self):
        self.repo.plan.write_text("# no frontmatter\n", encoding="utf-8")
        _git(self.repo.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        _git(self.repo.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "plan")
        os.environ["TAPWAY_PR_GATE"] = "0"
        self.addCleanup(os.environ.pop, "TAPWAY_PR_GATE", None)
        from hermes.plugin import gates

        self.assertIsNone(
            gates.on_pre_tool_call(
                tool_name="terminal",
                args={"command": "gh pr create --fill", "workdir": str(self.repo.root)},
            )
        )


class FlatModuleLoadTests(unittest.TestCase):
    """The gate must work when the plugin files are imported without a package.

    Hermes loads the plugin as a package, but tooling and tests import
    `gates.py` on its own — a relative import there crashed at PR-gate time
    (ImportError: attempted relative import with no known parent package).
    """

    def test_pr_gate_survives_a_flat_module_load(self):
        import importlib.util

        repo = PlanFile()
        self.addCleanup(repo.cleanup)
        os.environ["CODEMAX_ENABLED"] = "1"
        self.addCleanup(os.environ.pop, "CODEMAX_ENABLED", None)
        sys.path.insert(0, str(ROOT / "hermes" / "plugin"))
        self.addCleanup(sys.path.remove, str(ROOT / "hermes" / "plugin"))

        spec = importlib.util.spec_from_file_location("gates_flat", ROOT / "hermes" / "plugin"
                                                      / "gates.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        verdict = mod.on_pre_tool_call(
            tool_name="terminal",
            args={"command": "gh pr create --fill", "workdir": str(repo.root)},
        )
        self.assertEqual((verdict or {}).get("action"), "block")


class HermesPostToolTests(unittest.TestCase):
    """Hermes post_tool_call: same flow, in-process, never raises."""

    def setUp(self):
        self.repo = PlanFile()
        self.addCleanup(self.repo.cleanup)
        os.environ["CODEMAX_WORKFLOW"] = "1"
        self.addCleanup(os.environ.pop, "CODEMAX_WORKFLOW", None)

    def test_plan_write_creates_the_issue_through_the_hook(self):
        gh = FakeGh(create_number=55)
        plan_issue.on_post_tool_call(
            tool_name="write_file",
            args={"file_path": "docs/plans/x.md", "workdir": str(self.repo.root)},
            runner=gh,
        )
        self.assertTrue([c for c in gh.calls if "issue create" in " ".join(c)])
        self.assertEqual(plan_issue.issue_number(self.repo.plan.read_text()), 55)

    def test_non_plan_write_is_ignored(self):
        gh = FakeGh()
        plan_issue.on_post_tool_call(
            tool_name="write_file",
            args={"file_path": "src/app.py", "workdir": str(self.repo.root)},
            runner=gh,
        )
        self.assertEqual(gh.calls, [])

    def test_escape_hatch(self):
        gh = FakeGh()
        os.environ["TAPWAY_ISSUE_AUTOCREATE"] = "0"
        self.addCleanup(os.environ.pop, "TAPWAY_ISSUE_AUTOCREATE", None)
        plan_issue.on_post_tool_call(
            tool_name="write_file",
            args={"file_path": "docs/plans/x.md", "workdir": str(self.repo.root)},
            runner=gh,
        )
        self.assertEqual(gh.calls, [])

    def test_a_broken_runner_never_raises(self):
        def boom(args, cwd=None):
            raise RuntimeError("gh exploded")

        self.assertIsNone(
            plan_issue.on_post_tool_call(
                tool_name="write_file",
                args={"file_path": "docs/plans/x.md", "workdir": str(self.repo.root)},
                runner=boom,
            )
        )
        self.assertIsNone(plan_issue.issue_number(self.repo.plan.read_text()))

    def test_a_non_codemax_repo_is_left_alone(self):
        os.environ.pop("CODEMAX_WORKFLOW", None)
        gh = FakeGh()
        plan_issue.on_post_tool_call(
            tool_name="write_file",
            args={"file_path": "docs/plans/x.md", "workdir": str(self.repo.root)},
            runner=gh,
        )
        self.assertEqual(gh.calls, [])


class HookTests(unittest.TestCase):
    """The Claude/Codex side: a PostToolUse payload in, a real issue out."""

    HOOK = ROOT / "hooks" / "post-plan-issue" / "post-plan-issue.sh"
    CODEX_HOOK = ROOT / "codex" / "hooks" / "post-plan-issue.sh"

    def setUp(self):
        self.repo = PlanFile()
        self.addCleanup(self.repo.cleanup)
        self.bin = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.bin, ignore_errors=True))
        stub = self.bin / "gh"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            "echo \"$@\" >> \"$GH_LOG\"\n"
            "case \"$*\" in\n"
            "  *'issue create'*) echo 'https://github.com/tapway/fake/issues/77' ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        self.log = self.bin / "gh.log"
        self.log.write_text("", encoding="utf-8")

    def _run(self, payload: dict, env: dict | None = None, hook: Path | None = None):
        full_env = {
            "PATH": f"{self.bin}:/usr/local/bin:/usr/bin:/bin",
            "CLAUDE_PLUGIN_ROOT": str(ROOT),
            "GH_LOG": str(self.log),
            "CODEMAX_ENABLED": "1",
        }
        full_env.update(env or {})
        return subprocess.run(
            ["bash", str(hook or self.HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=self.repo.root,
            env=full_env,
        )

    def test_write_outside_docs_plans_is_ignored(self):
        result = self._run({"tool_name": "Write", "tool_input": {"file_path": "src/app.py"}})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.log.read_text().strip(), "")

    def test_accepted_brainstorm_creates_one_issue_on_every_surface(self):
        """An accepted design reaches gh through the shell hooks, not only in-process."""
        rel = "docs/brainstorming/design.md"
        doc = self.repo.root / rel
        doc.parent.mkdir(parents=True, exist_ok=True)
        for surface, hook in (("claude", self.HOOK), ("codex", self.CODEX_HOOK)):
            with self.subTest(surface=surface):
                doc.write_text(ACCEPTED_DESIGN, encoding="utf-8")
                self.log.write_text("", encoding="utf-8")
                result = self._run(
                    {"tool_name": "Write", "tool_input": {"file_path": rel}}, hook=hook
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = [line for line in self.log.read_text().splitlines() if "issue create" in line]
                self.assertEqual(len(calls), 1, f"{surface}: {self.log.read_text()}")
                self.assertEqual(plan_issue.issue_number(doc.read_text()), 77, surface)

    def test_windows_backslash_path_is_routed_on_every_surface(self):
        """Windows sends backslash paths; the shell gate must not drop them."""
        rel = "docs/brainstorming/design.md"
        doc = self.repo.root / rel
        doc.parent.mkdir(parents=True, exist_ok=True)
        # POSIX CI treats a backslash as part of the file name, so put a file
        # under that literal name too. On Windows it is the same file as `doc`.
        windows = rel.replace("/", "\\")
        literal = self.repo.root / windows
        for surface, hook in (("claude", self.HOOK), ("codex", self.CODEX_HOOK)):
            with self.subTest(surface=surface):
                doc.write_text(ACCEPTED_DESIGN, encoding="utf-8")
                literal.write_text(ACCEPTED_DESIGN, encoding="utf-8")
                self.log.write_text("", encoding="utf-8")
                result = self._run(
                    {"tool_name": "Write", "tool_input": {"file_path": windows}}, hook=hook
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = [line for line in self.log.read_text().splitlines() if "issue create" in line]
                self.assertEqual(len(calls), 1, f"{surface}: {self.log.read_text()}")

    def test_proposed_brainstorm_is_ignored_on_every_surface(self):
        rel = "docs/brainstorming/design.md"
        doc = self.repo.root / rel
        doc.parent.mkdir(parents=True, exist_ok=True)
        for surface, hook in (("claude", self.HOOK), ("codex", self.CODEX_HOOK)):
            with self.subTest(surface=surface):
                doc.write_text(ACCEPTED_DESIGN.replace("status: accepted", "status: proposed"),
                               encoding="utf-8")
                self.log.write_text("", encoding="utf-8")
                result = self._run(
                    {"tool_name": "Write", "tool_input": {"file_path": rel}}, hook=hook
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.log.read_text().strip(), "", surface)

    def test_plan_write_creates_one_issue_and_records_it(self):
        result = self._run(
            {"tool_name": "Write", "tool_input": {"file_path": "docs/plans/x.md"}}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [line for line in self.log.read_text().splitlines() if "issue create" in line]
        self.assertEqual(len(calls), 1, self.log.read_text())
        self.assertIn("--label codemax", calls[0])
        self.assertEqual(plan_issue.issue_number(self.repo.plan.read_text()), 77)

    def test_second_write_is_a_no_op(self):
        payload = {"tool_name": "Write", "tool_input": {"file_path": "docs/plans/x.md"}}
        self._run(payload)
        self._run(payload)
        calls = [line for line in self.log.read_text().splitlines() if "issue create" in line]
        self.assertEqual(len(calls), 1)

    def test_escape_hatch(self):
        result = self._run(
            {"tool_name": "Write", "tool_input": {"file_path": "docs/plans/x.md"}},
            {"TAPWAY_ISSUE_AUTOCREATE": "0"},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.log.read_text().strip(), "")


BRAINSTORM = textwrap.dedent(
    """\
    ---
    status: accepted
    title: Native auto-update
    ---

    # Brainstorm: Native auto-update on Claude Code and Hermes

    Intro paragraph for the design.

    ## 1. Problem

    Harness updates are manual today.

    ## 2. Options

    - Option A: generated mirrors
    - Option B: git submodules

    ## 3. Recommendation

    - Publish generated mirrors from the release job
    - Bump the version at release time

    ## 4. Acceptance criteria

    - A fresh install needs no manual update
    """
)

PROPOSED = BRAINSTORM.replace("status: accepted", "status: proposed")


class DocRepo:
    """A throwaway git checkout with arbitrary docs committed on a branch."""

    def __init__(self, files: dict[str, str], branch: str = "feat/brainstorm-issue") -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-b", "staging")
        _git(self.root, "remote", "add", "origin", "https://github.com/tapway/fake.git")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "base")
        _git(self.root, "update-ref", "refs/remotes/origin/staging", "HEAD")
        _git(self.root, "checkout", "-b", branch)
        for rel, content in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "docs")

    def path(self, rel: str) -> Path:
        return self.root / rel

    def cleanup(self) -> None:
        self._tmp.cleanup()


class BrainstormTests(unittest.TestCase):
    """An accepted design doc opens one issue; a draft or a plan does not duplicate it."""

    def setUp(self):
        self.repo = DocRepo({"docs/brainstorming/design.md": BRAINSTORM})
        self.addCleanup(self.repo.cleanup)
        self.doc = self.repo.path("docs/brainstorming/design.md")

    def test_title_strips_the_brainstorm_prefix(self):
        self.assertEqual(
            plan_issue.render_title(BRAINSTORM, "docs/native-auto-update"),
            "docs: Native auto-update on Claude Code and Hermes",
        )

    def test_body_maps_problem_and_recommendation(self):
        body = plan_issue.render_body(
            BRAINSTORM,
            plan_path="docs/brainstorming/design.md",
            branch="docs/native-auto-update",
            repo="tapway/fake",
            kind="brainstorm",
        )
        self.assertIn("## Summary", body)
        self.assertIn("Harness updates are manual today.", body)
        self.assertIn("Publish generated mirrors from the release job", body)
        self.assertIn("## Acceptance criteria", body)
        self.assertIn("<summary>Full design</summary>", body)

    def test_accepted_brainstorm_creates_one_issue_and_records_it(self):
        gh = FakeGh(create_number=91)
        result = plan_issue.ensure_issue(
            self.doc, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh
        )
        self.assertTrue(result.created)
        self.assertEqual(result.number, 91)
        self.assertEqual(plan_issue.issue_number(self.doc.read_text()), 91)
        creates = [c for c in gh.calls if "issue create" in " ".join(c)]
        self.assertEqual(len(creates), 1)
        self.assertIn("feat: Native auto-update on Claude Code and Hermes", " ".join(creates[0]))

    def test_second_pass_is_idempotent(self):
        gh = FakeGh(create_number=91)
        plan_issue.ensure_issue(self.doc, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh)
        again = plan_issue.ensure_issue(
            self.doc, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh
        )
        self.assertEqual(again.number, 91)
        self.assertFalse(again.created)
        self.assertEqual(len([c for c in gh.calls if "issue create" in " ".join(c)]), 1)

    def test_proposed_brainstorm_is_skipped(self):
        self.doc.write_text(PROPOSED, encoding="utf-8")
        gh = FakeGh()
        result = plan_issue.ensure_issue(
            self.doc, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh
        )
        self.assertEqual(gh.calls, [])
        self.assertEqual(result.skipped, "not-accepted")

    def test_brainstorm_without_frontmatter_is_skipped(self):
        self.doc.write_text("# Brainstorm: no status\n\n## 1. Problem\n\nx\n", encoding="utf-8")
        gh = FakeGh()
        result = plan_issue.ensure_issue(
            self.doc, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh
        )
        self.assertEqual(gh.calls, [])
        self.assertEqual(result.skipped, "not-accepted")

    def test_plan_reuses_the_linked_brainstorm_issue(self):
        plan = textwrap.dedent(
            """\
            ---
            title: Build it
            ---

            # Build it — Implementation Plan

            **Decision:** [Option B](../brainstorming/design.md).

            ### Task 1.1: Do the thing

            **Files:**
            - Modify: `a.py`
            """
        )
        plan_path = self.repo.root / "docs" / "plans" / "build.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan, encoding="utf-8")
        self.doc.write_text(plan_issue.record_issue_text(BRAINSTORM, 42), encoding="utf-8")
        gh = FakeGh(create_number=99)
        result = plan_issue.ensure_issue(
            plan_path, repo="tapway/fake", branch="feat/brainstorm-issue", runner=gh
        )
        self.assertEqual(result.number, 42)
        self.assertFalse(result.created)
        self.assertEqual(gh.calls, [])
        self.assertEqual(plan_issue.issue_number(plan_path.read_text()), 42)

    def test_hook_ignores_a_proposed_brainstorm(self):
        os.environ["CODEMAX_WORKFLOW"] = "1"
        self.addCleanup(os.environ.pop, "CODEMAX_WORKFLOW", None)
        self.doc.write_text(PROPOSED, encoding="utf-8")
        gh = FakeGh()
        plan_issue.on_post_tool_call(
            tool_name="write_file",
            args={"file_path": "docs/brainstorming/design.md", "workdir": str(self.repo.root)},
            runner=gh,
        )
        self.assertEqual(gh.calls, [])
        self.assertIsNone(plan_issue.issue_number(self.doc.read_text()))


if __name__ == "__main__":
    unittest.main(verbosity=2)