import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import models  # noqa: F401  (registers tables)
from backend.database.session import Base

SCHEMA = Path(__file__).resolve().parents[1] / "backend" / "database" / "sqlite_schema.sql"


class SchemaDriftTests(unittest.TestCase):
    def test_model_tables_and_columns_match_sql(self):
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        for table in Base.metadata.sorted_tables:
            rows = conn.execute(f"PRAGMA table_info({table.name})").fetchall()
            self.assertTrue(rows, f"{table.name} missing from sqlite_schema.sql")
            self.assertEqual({r[1] for r in rows}, {c.name for c in table.columns}, table.name)


if __name__ == "__main__":
    unittest.main()