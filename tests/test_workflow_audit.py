#!/usr/bin/env python3
"""scripts/workflow_audit.py: every PR needs a plan, unless it is routine.

Run: python tests/test_workflow_audit.py
Drives the script against throwaway git repos; no network.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workflow_audit.py"
PLAN = "docs/plans/feature.md"


class Audit(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        self.event_path = Path(tmp.name) / "event.json"
        self.git("init", "-q", "-b", "staging")
        self.commit("chore: init", {"README.md": "x\n", "docs/plans/merged.md": "plan\n"})
        self.git("update-ref", "refs/remotes/origin/staging", "HEAD")
        self.git("checkout", "-q", "-b", "work")

    def git(self, *args):
        subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            check=True, capture_output=True,
        )

    def commit(self, message, files):
        for name, content in files.items():
            path = self.repo / name
            if content is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def audit(self, body="", head="feat/x", base="staging", user="dev", fork=False):
        if base != "staging":
            self.git("update-ref", f"refs/remotes/origin/{base}", "refs/remotes/origin/staging")
        event = {
            "repository": {"full_name": "tapway/app"},
            "pull_request": {
                "body": body,
                "user": {"login": user},
                "base": {"ref": base},
                "head": {"ref": head, "repo": {"full_name": "other/app" if fork else "tapway/app"}},
            },
        }
        self.event_path.write_text(json.dumps(event), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=self.repo, capture_output=True, encoding="utf-8",
            env={**os.environ, "GITHUB_EVENT_PATH": str(self.event_path), "PYTHONIOENCODING": "utf-8"},
        )
        return result.returncode, result.stdout + result.stderr

    def assertPasses(self, **kwargs):
        code, out = self.audit(**kwargs)
        self.assertEqual(code, 0, out)

    def assertBlocked(self, reason, **kwargs):
        code, out = self.audit(**kwargs)
        self.assertEqual(code, 1, out)
        self.assertIn(reason, out)

    # --- the plan rule ------------------------------------------------------
    def test_a_fix_without_a_plan_is_blocked(self):
        self.commit("fix: a thing", {"app.py": "x = 1\n"})
        self.assertBlocked("no plan")

    def test_a_plan_added_in_the_pr_passes(self):
        self.commit("docs: plan", {PLAN: "plan\n"})
        self.commit("feat: a thing", {"app.py": "x = 1\n"})
        self.assertPasses()

    def test_deleting_a_plan_does_not_count(self):
        self.commit("chore: drop plan", {"docs/plans/merged.md": None})
        self.assertBlocked("no plan")

    def test_a_link_to_a_merged_plan_passes(self):
        self.commit("feat: backend package", {"app.py": "x = 1\n"})
        for body in (
            "## Summary\nx\n\nPlan: docs/plans/merged.md\n",
            "Plan: `docs/plans/merged.md`",
            "**Plan:** [merged](docs/plans/merged.md)",
        ):
            self.assertPasses(body=body)

    def test_a_link_to_a_missing_plan_is_blocked(self):
        self.commit("feat: a thing", {"app.py": "x = 1\n"})
        self.assertBlocked("not on staging", body="Plan: docs/plans/nope.md")

    def test_a_commented_out_link_does_not_count(self):
        self.commit("feat: a thing", {"app.py": "x = 1\n"})
        self.assertBlocked("no plan", body="<!--\nPlan: docs/plans/merged.md\n-->")

    # --- routine PRs --------------------------------------------------------
    def test_routine_prs_need_no_plan(self):
        self.commit("Merge staging", {"app.py": "x = 1\n"})
        self.assertPasses(head="staging", base="master")
        self.assertPasses(head="master", base="staging")
        self.assertPasses(head="chore/manifest-sync-1.2.3", base="master", user="github-actions[bot]")
        self.assertPasses(head="dependabot/pip/x", user="dependabot[bot]")

    def test_a_fork_or_a_person_cannot_claim_an_exemption(self):
        self.commit("fix: a thing", {"app.py": "x = 1\n"})
        self.assertBlocked("no plan", head="staging", base="master", fork=True)
        self.assertBlocked("no plan", head="chore/manifest-sync-1.2.3")

    # --- the other blocking checks ------------------------------------------
    def test_unconventional_commits_are_blocked(self):
        self.commit("did stuff", {PLAN: "plan\n"})
        self.assertBlocked("non-conventional")

    def test_scoped_commits_with_slashes_are_conventional(self):
        self.commit("fix(api/v2.1): a thing", {PLAN: "plan\n"})
        self.assertPasses()

    def test_an_added_secret_is_blocked_even_on_a_routine_pr(self):
        self.commit("chore: oops", {"app.py": "k = 'AKIA" + "A" * 16 + "'\n"})
        self.assertBlocked("secret", head="staging", base="master")

    def test_the_diff_is_taken_against_the_pr_base(self):
        """A secret already on the base branch is not this PR's doing."""
        self.git("checkout", "-q", "staging")
        self.commit("chore: old", {"old.py": "k = 'AKIA" + "B" * 16 + "'\n"})
        self.git("update-ref", "refs/remotes/origin/staging", "HEAD")
        self.git("checkout", "-q", "-b", "later")
        self.commit("fix: a thing", {PLAN: "plan\n"})
        self.assertPasses()


class Wiring(unittest.TestCase):
    def read(self, *parts):
        return ROOT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_workflow_is_callable_and_runs_the_script(self):
        text = self.read(".github", "workflows", "workflow-audit.yml")
        for needle in ("workflow_call:", "scripts/workflow_audit.py", ".tapway-superpowers", "edited"):
            self.assertIn(needle, text)
        self.assertNotIn("pull-requests: write", text)

    def test_writing_plans_says_how_a_shared_plan_gets_merged(self):
        for tree in ("skills", "codex/skills", "hermes/skills", "hermes/plugin/skills"):
            text = self.read(*tree.split("/"), "writing-plans", "SKILL.md")
            self.assertIn("Plan: docs/plans/[feature-name].md", text, tree)
            self.assertIn("merge it before", text, tree)
            self.assertNotIn("origin/main", text, tree)

    def test_pr_skill_and_template_mention_the_plan_line(self):
        self.assertIn("Plan: docs/plans/", self.read(".github", "pull_request_template.md"))
        for tree in ("skills", "codex/skills", "hermes/skills", "hermes/plugin/skills"):
            self.assertIn("Plan: docs/plans/", self.read(*tree.split("/"), "pr", "SKILL.md"), tree)


if __name__ == "__main__":
    unittest.main(verbosity=1)
