#!/usr/bin/env python3
"""Version derivation for the Auto Release workflow (release-drift bug).

The workflow computes the next version from git tags. Two defects made the
tag and the plugin manifests disagree:

1. on master (no suffix) the tag glob ``v*`` also matched ``-stg`` tags, so a
   staging release polluted the production version stream;
2. the manifests were written by a step that could not push to the protected
   branch, and the failure was swallowed.

This file pins (1). The script under test is ``scripts/next_version.sh``; it is
called by ``.github/workflows/release.yml`` so the logic is testable at all.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "next_version.sh"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True,
        capture_output=True,
        text=True,
    )


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)
        _git(self.path, "init", "-b", "master")
        (self.path / "README.md").write_text("x\n", encoding="utf-8")
        _git(self.path, "add", "-A")
        _git(self.path, "commit", "-m", "chore: init")

    def commit(self, message: str) -> None:
        (self.path / "f.txt").write_text(message, encoding="utf-8")
        _git(self.path, "add", "-A")
        _git(self.path, "commit", "-m", message)

    def tag(self, name: str) -> None:
        _git(self.path, "tag", name)

    def next_version(self, *args: str) -> str:
        out = subprocess.run(
            ["bash", str(SCRIPT), *args], cwd=self.path, capture_output=True, text=True
        )
        if out.returncode != 0:
            raise AssertionError(f"next_version.sh failed: {out.stderr.strip()}")
        return out.stdout.strip()

    def cleanup(self) -> None:
        self._tmp.cleanup()


class NextVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_first_release_from_a_feat_is_0_1_0(self):
        """SemVer from 0.0.0: a feat is a minor bump, not an instant 1.0.0."""
        self.repo.commit("feat: first feature")
        self.assertEqual(self.repo.next_version(""), "v0.1.0")

    def test_feat_is_a_minor_bump(self):
        self.repo.tag("v1.2.3")
        self.repo.commit("feat(skills): a thing")
        self.assertEqual(self.repo.next_version(""), "v1.3.0")

    def test_fix_is_a_patch_bump(self):
        self.repo.tag("v1.2.3")
        self.repo.commit("fix(gates): a thing")
        self.assertEqual(self.repo.next_version(""), "v1.2.4")

    def test_breaking_change_is_a_major_bump(self):
        self.repo.tag("v1.2.3")
        self.repo.commit("feat!: drop the old gate")
        self.assertEqual(self.repo.next_version(""), "v2.0.0")

    def test_master_stream_ignores_staging_tags(self):
        """The drift bug: `v*` matched `-stg` tags, so staging bumped master."""
        self.repo.tag("v1.0.0")
        self.repo.commit("chore: shared")
        self.repo.tag("v2.0.0-stg")
        self.repo.commit("fix: a fix")
        self.assertEqual(self.repo.next_version(""), "v1.0.1")

    def test_staging_stream_only_counts_its_own_tags(self):
        self.repo.tag("v1.0.0")
        self.repo.commit("chore: shared")
        self.repo.tag("v1.0.0-stg")
        self.repo.commit("feat: staging work")
        self.assertEqual(self.repo.next_version("-stg"), "v1.1.0-stg")

    def test_staging_stream_starts_from_its_own_line(self):
        self.repo.commit("feat: staging only")
        self.assertEqual(self.repo.next_version("-stg"), "v0.1.0-stg")

    def test_production_stream_seeds_from_the_latest_plain_tag(self):
        """The first -prod release must continue the existing production line.

        Before this convention the production stream was untagged (`v2.11.3`).
        Starting -prod from 0.0.0 would publish v0.0.1-prod over a 2.x product.
        """
        self.repo.tag("v2.11.3")
        self.repo.commit("fix: a fix")
        self.assertEqual(self.repo.next_version("-prod"), "v2.11.4-prod")

    def test_staging_stream_prefers_a_newer_plain_baseline(self):
        """An old v1.x -stg tag must not outrank the live 2.x production line."""
        self.repo.tag("v1.2.0-stg")
        self.repo.commit("chore: shared")
        self.repo.tag("v2.11.3")
        self.repo.commit("fix: a fix")
        self.assertEqual(self.repo.next_version("-stg"), "v2.11.4-stg")

    def test_stream_tag_wins_when_it_is_ahead_of_plain(self):
        self.repo.tag("v2.11.3")
        self.repo.commit("chore: shared")
        self.repo.tag("v2.12.0-prod")
        self.repo.commit("feat: next")
        self.assertEqual(self.repo.next_version("-prod"), "v2.13.0-prod")

    def test_non_ancestor_baseline_bumps_patch(self):
        """A rewritten history makes commit classification meaningless.

        staging was squashed forward from master, so the baseline tag is not an
        ancestor of HEAD. Walking `tag..HEAD` then sees the whole old branch and
        a stray `feat!` there promoted the first staging release to v3.0.0-stg.
        """
        self.repo.tag("v2.0.0")
        _git(self.repo.path, "checkout", "--orphan", "rewritten")
        (self.repo.path / "f.txt").write_text("rewritten", encoding="utf-8")
        _git(self.repo.path, "add", "-A")
        _git(self.repo.path, "commit", "-m", "feat!: unrelated old history")
        self.assertEqual(self.repo.next_version("-stg"), "v2.0.1-stg")

    def test_only_commits_since_the_matching_tag_count(self):
        self.repo.tag("v1.0.0")
        self.repo.commit("feat: counted")
        self.repo.tag("v1.1.0")
        self.repo.commit("chore: docs only")
        self.assertEqual(self.repo.next_version(""), "v1.1.1")


if __name__ == "__main__":
    unittest.main(verbosity=2)