#!/usr/bin/env python3
"""Contract test for automated 'The nine accounts' README table generation (issue #101).

Asserts that scripts/sync_readme.py generates the specimen summary table directly from
fixture.toml sidecars, sorted alphabetically by id, and enforces synchronization in README.md.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.sync_readme import (
    ACCOUNTS_END,
    ACCOUNTS_START,
    count_fixtures,
    generate_accounts_table,
    sync,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"


class ReadmeFixtureTableTest(unittest.TestCase):
    def test_generate_accounts_table_markers(self) -> None:
        table = generate_accounts_table()
        self.assertTrue(table.startswith(ACCOUNTS_START))
        self.assertTrue(table.endswith(ACCOUNTS_END))
        self.assertIn("| Fixture | Why it is here |", table)

    def test_generate_accounts_table_contains_all_fixtures(self) -> None:
        table = generate_accounts_table()
        count = count_fixtures()
        # Number of fixture rows = lines - markers (2) - header (1) - separator (1)
        lines = [line for line in table.splitlines() if line.startswith("| `")]
        self.assertEqual(len(lines), count)

    def test_generate_accounts_table_sorted_by_id(self) -> None:
        table = generate_accounts_table()
        fixture_ids = [
            line.split("|")[1].strip().strip("`")
            for line in table.splitlines()
            if line.startswith("| `")
        ]
        self.assertEqual(fixture_ids, sorted(fixture_ids))

    def test_readme_contains_markers_and_is_synced(self) -> None:
        self.assertTrue(README_PATH.is_file())
        readme_content = README_PATH.read_text(encoding="utf-8")
        self.assertIn(ACCOUNTS_START, readme_content)
        self.assertIn(ACCOUNTS_END, readme_content)
        self.assertTrue(sync(check=True), "README.md accounts table must match sidecars")

    def test_zero_em_dashes(self) -> None:
        content = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn("\u2014", content)


if __name__ == "__main__":
    unittest.main()
