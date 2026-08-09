"""Migration test template — Alembic up/down round-trip + data preservation.

Copy to: backend/tests/integration/test_migrations.py
Adjust: engine URL, expected table/column names, migration revisions.
Run with: pytest backend/tests/integration/test_migrations.py -v
"""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture()
def migrated_db(tmp_path):
    """Apply ALL migrations to a fresh SQLite test DB (or swap for test Postgres)."""
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
    """The migrated schema matches the SQLAlchemy models' expected columns."""
    inspector = inspect(migrated_db)
    user_columns = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "email", "created_at"} <= user_columns


def test_migration_round_trip(migrated_db):
    """Up to head then down to base must succeed without error (rollback path)."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(migrated_db.url))
    command.downgrade(cfg, "base")
    inspector = inspect(migrated_db)
    assert "users" not in inspector.get_table_names()


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
        rows = conn.exec_driver_sql("SELECT full_name FROM users")
        values = [r[0] for r in rows]
    assert values == ["Alice"]  # not empty, not NULL
