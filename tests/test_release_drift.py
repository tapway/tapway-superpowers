#!/usr/bin/env python3
"""`scripts/check-release-drift.sh` must actually catch drift.

The silent failure it guards against: the release tags move, the manifests do
not, and every client keeps resolving the old version. A detector nobody has
seen go red is not a detector, so both directions are pinned here.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-release-drift.sh"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True,
        capture_output=True,
        text=True,
    )


class DriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        _git(self.repo, "init", "-b", "master")
        (self.repo / "hermes/plugin").mkdir(parents=True)
        (self.repo / ".claude-plugin").mkdir()
        (self.repo / "hermes/plugin/plugin.yaml").write_text(
            "name: tapway-superpowers\nversion: 1.2.2\n", encoding="utf-8")
        (self.repo / ".claude-plugin/plugin.json").write_text(
            json.dumps({"version": "1.2.2"}), encoding="utf-8")
        (self.repo / ".claude-plugin/marketplace.json").write_text(
            json.dumps({"metadata": {"version": "1.2.2"},
                        "plugins": [{"version": "1.2.2"}]}), encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [1.2.2] — 2026-01-01\n\n- initial\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-m", "chore: init")
        _git(self.repo, "tag", "v1.2.2")

    def run_check(self) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(SCRIPT)], cwd=self.repo,
                              capture_output=True, text=True)

    def test_green_when_every_surface_matches_the_tag(self):
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("GREEN", out.stdout)

    def test_red_when_the_tag_runs_ahead_of_the_manifests(self):
        _git(self.repo, "tag", "v1.2.3")
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("RED", out.stdout)
        self.assertIn("want 1.2.3", out.stdout)

    def test_red_when_one_surface_disagrees(self):
        _git(self.repo, "tag", "v1.2.3")
        for rel, body in (
            ("hermes/plugin/plugin.yaml", "name: tapway-superpowers\nversion: 1.2.3\n"),
            (".claude-plugin/plugin.json", json.dumps({"version": "1.2.3"})),
            ("CHANGELOG.md", "# Changelog\n\n## [1.2.3] — 2026-01-01\n"),
        ):
            (self.repo / rel).write_text(body, encoding="utf-8")
        # marketplace left behind on 1.2.2
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("marketplace.json (metadata) = 1.2.2", out.stdout)

    def test_red_when_the_changelog_has_only_an_unreleased_heading(self):
        _git(self.repo, "tag", "v1.2.3")
        for rel, body in (
            ("hermes/plugin/plugin.yaml", "name: tapway-superpowers\nversion: 1.2.3\n"),
            (".claude-plugin/plugin.json", json.dumps({"version": "1.2.3"})),
            (".claude-plugin/marketplace.json",
             json.dumps({"metadata": {"version": "1.2.3"}, "plugins": [{"version": "1.2.3"}]})),
            ("CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n- pending\n"),
        ):
            (self.repo / rel).write_text(body, encoding="utf-8")
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("CHANGELOG.md (top released heading) = (no released heading)", out.stdout)

    def test_staging_tags_are_not_production(self):
        _git(self.repo, "tag", "v9.9.9-stg")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_prod_tag_is_production(self):
        """From the -prod convention on, the production tag carries the suffix."""
        _git(self.repo, "tag", "v1.2.3-prod")
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("want 1.2.3", out.stdout)

    def test_latest_prod_tag_outranks_an_older_plain_tag(self):
        _git(self.repo, "tag", "v1.2.3-prod")
        _git(self.repo, "tag", "v1.2.4-prod")
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("latest production tag is v1.2.4-prod", out.stdout)


class ReleaseWorkflowTests(unittest.TestCase):
    def test_master_and_manual_production_release_as_prod(self):
        flow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn('master|main|prod) ENV="-prod"', flow)
        self.assertIn('if [ "$INPUT" = "production" ]; then ENV="-prod"', flow)
        self.assertIn("stream == 'prod'", flow,
                      "the manifest sync must still key off the production stream")


class WorkflowSyncTests(unittest.TestCase):
    """The sync step must write every surface the drift check reads."""

    def test_release_workflow_updates_the_hermes_manifest_too(self):
        flow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertRegex(
            flow,
            r"sed -i .*hermes/plugin/plugin\.yaml",
            "the sync step skipped plugin.yaml, so it stayed four releases behind",
        )
        self.assertIn("git add .claude-plugin/marketplace.json", flow)
        self.assertIn("git diff --quiet -- .claude-plugin/ hermes/plugin/plugin.yaml", flow)


if __name__ == "__main__":
    unittest.main(verbosity=2)