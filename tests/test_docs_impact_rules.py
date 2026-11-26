#!/usr/bin/env python3
"""Per-document rules of scripts/docs_impact.py.

Run: python tests/test_docs_impact_rules.py
Drives the script against throwaway git repos; no network, no pytest.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[1] / "scripts" / "docs_impact.py"
GENERAL = "Docs: no impact — internal change, existing docs stay accurate."


class Rules(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        self.event = Path(tmp.name) / "event.json"
        self.git("init", "-q", "-b", "staging")
        self.base = self.commit({"app/service.py": "x = 1\n", "docs/DB_SCHEMA.md": "old\n"})

    def git(self, *args):
        out = subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            check=True, capture_output=True, encoding="utf-8",
        )
        return out.stdout.strip()

    def commit(self, files):
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "change")
        return self.git("rev-parse", "HEAD")

    def check(self, files, body=GENERAL, head_ref="feat/x", base_ref="staging", advisory=False):
        head = self.commit(files)
        self.event.write_text(json.dumps({
            "repository": {"full_name": "tapway/app"},
            "pull_request": {
                "body": body,
                "user": {"login": "dev"},
                "base": {"sha": self.base, "ref": base_ref},
                "head": {"sha": head, "ref": head_ref, "repo": {"full_name": "tapway/app"}},
            },
        }), encoding="utf-8")
        args = [sys.executable, str(CHECKER), str(self.event)] + (["--advisory"] if advisory else [])
        result = subprocess.run(
            args, cwd=self.repo, capture_output=True, encoding="utf-8", errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        return result.returncode, result.stdout + result.stderr

    def assertBlocked(self, needle, files, **kwargs):
        code, out = self.check(files, **kwargs)
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def assertPasses(self, files, **kwargs):
        code, out = self.check(files, **kwargs)
        self.assertEqual(code, 0, out)
        return out

    # --- blocking rules ----------------------------------------------------
    def test_schema_changes_need_the_schema_doc(self):
        for path in ("backend/alembic/versions/1_add.py", "db/migrations/2.sql",
                     "backend/src/models/user.py", "prisma/schema.prisma"):
            with self.subTest(path):
                self.git("reset", "-q", "--hard", self.base)
                self.assertBlocked("docs/DB_SCHEMA.md", {path: "x\n"})

    def test_updating_the_schema_doc_satisfies_it(self):
        self.assertPasses(
            {"db/migrations/2.sql": "x\n", "docs/DB_SCHEMA.md": "new\n"},
            body="Docs: updated — docs/DB_SCHEMA.md",
        )

    def test_a_scoped_reason_satisfies_only_its_own_rule(self):
        files = {"db/2.sql": "x\n", "Dockerfile": "FROM x\n"}
        self.assertBlocked("docs/DEPLOYMENT.md", files,
                           body="Docs: no impact (schema) — index rename only")
        self.git("reset", "-q", "--hard", self.base)
        self.assertPasses(files, body="Docs: no impact (schema) — index rename only\n"
                                      "Docs: no impact (deployment) — comment only")

    def test_a_general_reason_does_not_satisfy_a_rule(self):
        self.assertBlocked("Docs: no impact (deployment)", {"docker-compose.yml": "a: 1\n"})

    def test_deployment_files(self):
        for path in ("api/Dockerfile.api", "compose.prod.yaml", "deploy/run.sh",
                     "backend/.env.example", "k8s/app.yaml"):
            with self.subTest(path):
                self.git("reset", "-q", "--hard", self.base)
                self.assertBlocked("docs/DEPLOYMENT.md", {path: "x\n"})

    # --- things that must not trigger --------------------------------------
    def test_model_weights_and_tests_are_not_schema(self):
        out = self.assertPasses({"deepstream/models/peoplenet/labels.txt": "x\n",
                                 "tests/models/test_user.py": "x\n",
                                 "tests/fixtures/seed.sql": "x\n"})
        self.assertNotIn("DB_SCHEMA", out)

    def test_a_plain_code_change_triggers_nothing(self):
        out = self.assertPasses({"app/service.py": "x = 2\n"})
        self.assertNotIn("::warning::", out)

    # --- warning rules ------------------------------------------------------
    def test_architecture_and_workflows_only_warn(self):
        out = self.assertPasses({"requirements.txt": "kafka\n", "app/workers/sync.py": "x\n"})
        self.assertIn("::warning::", out)
        self.assertIn("docs/ARCHITECTURE.md", out)
        self.assertIn("docs/WORKFLOWS.md", out)

    # --- configuration ------------------------------------------------------
    def test_config_on_the_target_branch_turns_schema_off(self):
        self.base = self.commit({".docs-impact.json": '{"database": false}'})
        self.assertPasses({"app/models/net.py": "x\n"})

    def test_a_pr_cannot_switch_off_its_own_rule(self):
        self.assertBlocked("docs/DB_SCHEMA.md", {
            ".docs-impact.json": '{"database": false}', "db/2.sql": "x\n",
        })

    def test_config_can_rename_a_document(self):
        self.base = self.commit(
            {".docs-impact.json": '{"rules": {"deployment": {"doc": "docs/DEPLOY_FLOW.md"}}}'})
        self.assertPasses({"Dockerfile": "x\n", "docs/DEPLOY_FLOW.md": "new\n"},
                          body="Docs: updated — docs/DEPLOY_FLOW.md")

    def test_a_broken_config_is_an_operational_error(self):
        self.base = self.commit({".docs-impact.json": "{not json"})
        code, out = self.check({"app/service.py": "x = 2\n"})
        self.assertEqual(code, 2, out)

    # --- declarations -------------------------------------------------------
    def test_still_needs_some_declaration(self):
        self.assertBlocked("Docs:", {"app/service.py": "x = 2\n"}, body="")

    def test_unknown_or_repeated_scopes_are_rejected(self):
        self.assertBlocked("schema", {"app/service.py": "x = 2\n"},
                           body="Docs: no impact (database) — x")
        self.git("reset", "-q", "--hard", self.base)
        line = "Docs: no impact (schema) — x"
        self.assertBlocked("once", {"db/2.sql": "x\n"}, body=f"{line}\n{line}")

    # --- exemptions ---------------------------------------------------------
    def test_promotions_and_syncs_are_exempt(self):
        self.assertPasses({"db/2.sql": "x\n"}, body="", head_ref="staging", base_ref="master")
        self.git("reset", "-q", "--hard", self.base)
        self.assertPasses({"db/2.sql": "x\n"}, body="", head_ref="master")

    def test_advisory_reports_missing_documents_without_failing(self):
        out = self.assertPasses({"db/2.sql": "x\n"}, advisory=True)
        self.assertIn("::warning::", out)
        self.assertIn("docs/DB_SCHEMA.md", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
