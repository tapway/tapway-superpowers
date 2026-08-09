#!/usr/bin/env python3
"""
Phase 2 skills validation suite (TDD): api-contract-testing + db-migration-testing.

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

Verifies both skills exist in the Claude plugin (skills/) and Hermes port
(hermes/skills/), ship templates, are wired into the pipeline, and update
install scripts / READMEs / CHANGELOG. Covers the two most common prod-outage
classes: API contract drift and unsafe DB migrations.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = []
FAIL = []


def check(cond, label):
    if cond:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(label)
        print(f"  FAIL  {label}")


def read(*rel):
    p = os.path.join(ROOT, *rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


print("=" * 68)
print("PHASE 2 — API-CONTRACT + DB-MIGRATION TESTING — VALIDATION SUITE")
print("=" * 68)

# --- 1. api-contract-testing skill --------------------------------------
print("\n[1] api-contract-testing skill present (both copies)")
ac_claude = read("skills", "api-contract-testing", "SKILL.md")
ac_hermes = read("hermes", "skills", "api-contract-testing", "SKILL.md")
check(ac_claude is not None, "skills/api-contract-testing/SKILL.md exists")
check(ac_hermes is not None, "hermes/skills/api-contract-testing/SKILL.md exists")
check(ac_claude is not None and "schemathesis" in ac_claude.lower(),
      "covers schemathesis (property-based API fuzzing)")
check(ac_claude is not None and "openapi" in ac_claude.lower(),
      "references OpenAPI schema")
check(ac_claude is not None and "pact" in ac_claude.lower(),
      "covers Pact (consumer-driven contracts)")
check(ac_claude is not None and "contract" in ac_claude.lower(),
      "mentions contract testing")
check(ac_claude is not None and "drift" in ac_claude.lower(),
      "addresses API contract drift")

# --- 2. db-migration-testing skill --------------------------------------
print("\n[2] db-migration-testing skill present (both copies)")
db_claude = read("skills", "db-migration-testing", "SKILL.md")
db_hermes = read("hermes", "skills", "db-migration-testing", "SKILL.md")
check(db_claude is not None, "skills/db-migration-testing/SKILL.md exists")
check(db_hermes is not None, "hermes/skills/db-migration-testing/SKILL.md exists")
check(db_claude is not None and "alembic" in db_claude.lower() or (db_claude and "migration" in db_claude.lower()),
      "covers Alembic / migration tooling")
check(db_claude is not None and "rollback" in db_claude.lower(),
      "covers migration rollback")
check(db_claude is not None and "downtime" in db_claude.lower(),
      "covers zero-downtime")
check(db_claude is not None and "test" in db_claude.lower(),
      "includes testing strategy")

# --- 3. Templates --------------------------------------------------------
print("\n[3] Templates shipped")
ac_tpl = read("skills", "api-contract-testing", "templates", "schemathesis.toml")
check(ac_tpl is not None, "api-contract-testing schemathesis.toml template exists")
check(ac_tpl is not None and "base-url" in ac_tpl, "schemathesis template uses modern kebab-case keys (base-url)")

db_tpl = read("skills", "db-migration-testing", "templates", "test_migration.py")
check(db_tpl is not None, "db-migration-testing test_migration.py template exists")

# --- 4. Wiring into pipeline ---------------------------------------------
print("\n[4] Wired into pipeline")
ver = read("skills", "verification", "SKILL.md")
check(ver is not None and "api-contract" in ver, "verification references api-contract-testing")
check(ver is not None and "db-migration" in ver, "verification references db-migration-testing")

e2e = read("skills", "e2e-playwright", "SKILL.md")
check(e2e is not None and "api-contract" in e2e, "e2e-playwright references api-contract-testing")
check(e2e is not None and "db-migration" in e2e, "e2e-playwright references db-migration-testing")

# --- 5. Install scripts / bundling ---------------------------------------
print("\n[5] Install scripts + bundling")
install = read("hermes", "install.sh")
check(install is not None and "api-contract-testing" in install, "install.sh includes api-contract-testing")
check(install is not None and "db-migration-testing" in install, "install.sh includes db-migration-testing")

# --- 6. README + CHANGELOG ----------------------------------------------
print("\n[6] README + CHANGELOG updated")
readme = read("README.md")
changelog = read("CHANGELOG.md")
check(readme is not None and "api-contract-testing" in readme, "README references api-contract-testing")
check(readme is not None and "db-migration-testing" in readme, "README references db-migration-testing")
check(changelog is not None and "api-contract-testing" in changelog, "CHANGELOG notes api-contract-testing")
check(changelog is not None and "db-migration-testing" in changelog, "CHANGELOG notes db-migration-testing")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)
