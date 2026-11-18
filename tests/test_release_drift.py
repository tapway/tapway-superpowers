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
        (self.repo / "hermes/plugin/plugin.yaml").write_text(
            "name: tapway-superpowers\nversion: 1.2.3\n", encoding="utf-8")
        (self.repo / ".claude-plugin/plugin.json").write_text(
            json.dumps({"version": "1.2.3"}), encoding="utf-8")
        # marketplace left behind on 1.2.2
        out = self.run_check()
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("marketplace.json (metadata) = 1.2.2", out.stdout)

    def test_suffixed_tags_are_not_production(self):
        _git(self.repo, "tag", "v9.9.9-stg")
        out = self.run_check()
        self.assertEqual(out.returncode, 0, out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)