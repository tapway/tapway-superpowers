#!/usr/bin/env python3
"""scripts/release_notes.py: descriptive notes built from merged PR descriptions.

Run: python tests/test_release_notes.py
No network: GitHub is replaced by a fake fetcher.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_notes as rn  # noqa: E402

URL = "https://github.com/o/r/pull/"
COMPARE = "**Full Changelog**: https://github.com/o/r/compare/v1.0.0-prod...v1.1.0-prod"


def generated(*prs):
    """A body shaped like GitHub's generated release notes."""
    lines = ["## What's Changed"]
    lines += [f"* {title} by @{who} in {URL}{n}" for n, title, who in prs]
    lines += ["", "## New Contributors", f"* @new made their first contribution in {URL}999"]
    return "\n".join(lines + ["", "", COMPARE])


def build(prs, bodies):
    return rn.build_notes(generated(*prs), lambda n: bodies[n])


class Describe(unittest.TestCase):
    def test_release_note_section_wins_and_keeps_all_paragraphs(self):
        body = "## Summary\nInternal detail.\n\n## Release note\nFirst.\n\nSecond.\n\n## Test plan\n- x"
        self.assertEqual(rn.describe(body), ["First.", "Second."])

    def test_untouched_template_comment_falls_back_to_summary(self):
        body = "## Summary\nAdds login.\r\n\r\n## Release note\n<!-- one to three\nsentences -->\n"
        self.assertEqual(rn.describe(body), ["Adds login."])

    def test_release_note_none_means_no_description(self):
        self.assertEqual(rn.describe("## Summary\nRefactor.\n\n## Release note\nNone\n"), [])

    def test_bulleted_summary_is_kept_as_bullets(self):
        body = "## Summary\n- Adds login\n- Adds logout\n\n## Test Plan\n- [ ] run"
        self.assertEqual(rn.describe(body), ["- Adds login", "- Adds logout"])

    def test_body_without_headings_uses_first_paragraph_without_footer(self):
        body = "Follow-up to #78.\nIgnored paths.\n\n\U0001F916 Generated with Claude Code"
        self.assertEqual(rn.describe(body), ["Follow-up to #78. Ignored paths."])

    def test_empty_body_and_docs_lines_give_nothing(self):
        self.assertEqual(rn.describe(None), [])
        self.assertEqual(rn.describe("## Summary\n\nDocs: no impact — x\n"), [])

    def test_long_fallback_text_is_truncated(self):
        (line,) = rn.describe("word " * 500)
        self.assertLessEqual(len(line), rn.MAX_FALLBACK_CHARS + 1)
        self.assertTrue(line.endswith("…"))


class BuildNotes(unittest.TestCase):
    def test_groups_by_type_and_describes_each_change(self):
        notes = build(
            [(1, "fix(auth): stop logout loop", "a"), (2, "feat: add export", "b"),
             (3, "refactor!: drop v1 API", "c"), (4, "docs: tidy", "d")],
            {1: "Loop fixed.", 2: "CSV export.", 3: "v1 is gone.", 4: ""},
        )
        headings = [line for line in notes.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["## Breaking changes", "## Features", "## Fixes", "## Other changes"])
        self.assertIn("- **auth:** stop logout loop (#1, by `@a`)\n  Loop fixed.", notes)
        self.assertIn("- add export (#2, by `@b`)\n  CSV export.", notes)
        self.assertTrue(notes.rstrip().endswith(COMPARE))
        self.assertNotIn("#999", notes)

    def test_release_and_sync_prs_are_left_out(self):
        notes = build(
            [(1, "chore(release): promote staging to master", "a"),
             (2, "chore(staging): sync staging with master [skip ci]", "a")],
            {},
        )
        self.assertNotIn("#1", notes)
        self.assertIn("No user-facing changes", notes)
        self.assertIn(COMPARE, notes)

    def test_mentions_in_descriptions_do_not_notify_anyone(self):
        notes = build([(1, "fix: bump @types/node", "a")], {1: "Thanks @octocat, mail a@b.com"})
        self.assertIn("`@types/node`", notes)
        self.assertIn("Thanks `@octocat`, mail a@b.com", notes)

    def test_unreadable_pr_keeps_its_title(self):
        def boom(number):
            raise RuntimeError("403")

        notes = rn.build_notes(generated((1, "fix: a thing", "a")), boom)
        self.assertIn("- a thing (#1, by `@a`)", notes)


class Wiring(unittest.TestCase):
    def read(self, *parts):
        return ROOT.joinpath(*parts).read_text(encoding="utf-8")

    def test_both_release_workflows_use_the_script_with_a_fallback(self):
        for name in ("release.yml", "reusable-release.yml"):
            text = self.read(".github", "workflows", name)
            self.assertIn("release_notes.py", text, name)
            self.assertIn("--notes-file", text, name)
            self.assertIn('--generate-notes ${PREVIOUS:+--notes-start-tag "$PREVIOUS"}', text, name)

    def test_reusable_workflow_inherits_the_callers_permissions(self):
        text = self.read(".github", "workflows", "reusable-release.yml")
        code = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
        self.assertFalse([line for line in code if line.strip() == "permissions:"])

    def test_every_setup_project_copy_calls_the_reusable_workflow(self):
        for tree in ("skills", "codex/skills", "hermes/skills", "hermes/plugin/skills"):
            text = self.read(*tree.split("/"), "setup-project", "SKILL.md")
            self.assertIn("workflows/reusable-release.yml@master", text, tree)
            self.assertIn("pull-requests: read", text, tree)
            self.assertNotIn("gh release create", text, tree)

    def test_template_and_pr_skill_ask_for_a_release_note(self):
        self.assertIn("## Release note", self.read(".github", "pull_request_template.md"))
        for tree in ("skills", "codex/skills", "hermes/skills", "hermes/plugin/skills"):
            self.assertIn("## Release note", self.read(*tree.split("/"), "pr", "SKILL.md"), tree)


if __name__ == "__main__":
    unittest.main(verbosity=1)
