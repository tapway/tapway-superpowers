---
name: db-migration-testing
description: >
  Make database migrations safe to ship: test every migration up AND down,
  verify zero-downtime strategies for large tables, and confirm rollback works
  before touching production. Prevents the second most common prod-outage
  class: a migration that corrupts data, locks a table, or can't be rolled
  back. Triggers include "migration", "alembic", "schema change", "migrate",
  "add column", "backfill", "zero-downtime migration", "rollback migration",
  "db migration test".
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [db-migration, alembic, migration, database, rollback, zero-downtime, testing]
    related_skills: [e2e-playwright, verification, quality-gates, repo-docs, tdd, pr]
---

# Skill: Database Migration Testing (Hermes port)

**When to invoke:** Any task that changes the database schema — adding/renaming/
dropping columns, creating tables, backfilling data, changing constraints, or
writing an Alembic/Prisma/Django migration. Also before deploying any migration
to staging or prod.

> **Hermes note:** This skill is coordinator-driven. The agent writes and runs
> the migration test suite (up/down round-trip, data preservation) and wires it
> into the `verification` gate. The zero-downtime guidance is a decision
> checklist the agent applies when the migration touches large tables.

> **Why migration testing?** A bad migration is a prod outage that can't be
> fixed by rolling back code — the data is already changed, sometimes
> destructively. `repo-docs` documents the DB_SCHEMA, but nothing verifies the
> migration itself is safe. This skill is the missing guard.

---

## Core Concept

> Every migration gets tested **up** (does it apply?) and **down** (does it
> roll back?). Large-table changes get a **zero-downtime** strategy. Nothing
> touches prod until all three hold.

| Check | What it catches | Tool |
|---|---|---|
| **Up + down round-trip** | Migration can't apply or can't roll back | pytest + Alembic test fixture |
| **Idempotency** | Migration fails on re-run / partial state | re-run test |
| **Data preservation** | Column rename/drop loses data | data-motion test |
| **Zero-downtime (large tables)** | Locking, long-running ALTER, blocking writes | batch/expand-contract strategy |

---

## Protocol

### Step 0 — Identify the Migration

- [ ] Locate the migration tool (Alembic for SQLAlchemy/FastAPI, Prisma Migrate, Django `migrate`).
- [ ] Identify what the migration changes (add/rename/drop column, new table, backfill, constraint).
- [ ] Estimate table size — **large tables need the zero-downtime path (Step 4).**

### Step 1 — Up Migration Test (always)

Verify the migration applies cleanly to a fresh test database, then that the
schema matches the models.

```python
# backend/tests/integration/test_migrations.py
"""Migration tests using Alembic's testing fixture against a real test DB."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

@pytest.fixture()
def migrated_db(tmp_path):
    """Apply ALL migrations to a fresh SQLite/Postgres test DB."""
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    command.upgrade(cfg, "head")
    return engine

def test_migrations_apply_cleanly(migrated_db):
    """All migrations apply to a fresh DB without error."""
    inspector = inspect(migrated_db)
    tables = inspector.get_table_names()
    assert "users" in tables

def test_schema_matches_models(migrated_db):
    """The migrated schema matches the SQLAlchemy models."""
    # Compare inspector.get_columns('users') against the User model's table
    inspector = inspect(migrated_db)
    user_columns = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "email", "created_at"} <= user_columns
```

### Step 2 — Down Migration Test (always)

Verify the rollback path — `downgrade` to the previous revision — works. This
is the "can we undo this if prod breaks?" guarantee.

```python
def test_migration_round_trip(migrated_db):
    """Up to head then down to base must succeed without error."""
    engine = migrated_db
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    # Upgrade to head (done in fixture) then downgrade all the way
    command.downgrade(cfg, "base")
    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()  # fully rolled back
```

> **Tip:** For a single migration under test (not the whole history), use
> `command.upgrade(cfg, "+1")` then `command.downgrade(cfg, "-1")` around the
> migration in question. Test both the happy rollback and a mid-migration
> failure if it's data-moving.

### Step 3 — Data Preservation Test (renames/drops/backfills)

If the migration moves or transforms data, test that no data is lost or
corrupted:

- [ ] Seed data before the migration (use the pre-migration schema), apply the migration, assert the data is present and correct in the new shape.
- [ ] For a column rename: after migration, values map correctly to the new name.
- [ ] For a backfill: rows get the expected default, and pre-existing non-null values are preserved.

```python
def test_column_rename_preserves_data(migrated_db):
    """Renaming display_name -> full_name keeps existing values.

    Seeds data BEFORE the migration under test, applies it, then asserts
    the data survived. Without the seed step this test is vacuous
    (an empty table makes `all([])` trivially True).
    """
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(migrated_db.url))

    # 1. Seed data at the PRE-migration revision (e.g. before the rename)
    command.downgrade(cfg, "-2")  # or the revision before the rename
    with migrated_db.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO users (id, email, display_name) VALUES (1, 'a@b.c', 'Alice')"
        )

    # 2. Apply the migration under test (the rename)
    command.upgrade(cfg, "-1")

    # 3. Assert values survived into the new column shape
    with migrated_db.connect() as conn:
        values = [r[0] for r in conn.exec_driver_sql("SELECT full_name FROM users")]
    assert values == ["Alice"]  # not empty, not NULL
```

### Step 4 — Zero-Downtime Strategy (large tables / prod)

If the migration touches a large table (millions of rows) or runs long enough
to lock writes, use the **expand-contract** (a.k.a. parallel-change) pattern
instead of a single ALTER:

1. **Expand:** add the new column as nullable / add the new table — old code keeps working.
2. **Backfill:** populate the new column/table in batches (background job, small batches, no lock).
3. **Contract:** once backfill is verified, switch reads/writes to the new shape and drop the old column in a later release.

- [ ] The migration is split into expand → backfill → contract steps
- [ ] Each step is a separate deployable migration
- [ ] Steps are reversible (downgrade tested)
- [ ] For Postgres: use `ADD COLUMN ... DEFAULT NULL` (fast, no rewrite) + batched `UPDATE` (avoid a long table lock)

---

## Verification / Gate

This skill is done when:

- [ ] `alembic upgrade head` applies cleanly to a fresh test DB
- [ ] `alembic downgrade base` rolls back cleanly (round-trip)
- [ ] Data-preservation test passes for renames/drops/backfills
- [ ] Large-table changes use the zero-downtime expand-contract pattern
- [ ] CI runs the migration tests (in the quality gate)

If the migration can't roll back or loses data, it is NOT safe to ship — fix
the migration first.

---

## Hard Rules

- ❌ Never deploy a migration that hasn't been tested up AND down
- ❌ Never rename/drop a column or backfill without a data-preservation test
- ❌ Never run a blocking ALTER on a large table — use expand-contract
- ❌ Never merge a migration without running the migration test suite in CI
- ❌ Never claim "migration is safe" because it worked on your local SQLite — verify on the real DB engine (Postgres) that prod uses
