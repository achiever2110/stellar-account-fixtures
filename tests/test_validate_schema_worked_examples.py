#!/usr/bin/env python3
"""Contract test for SCHEMA.md worked sidecar examples (issue #39).

Parses the captured and synthetic fixture.toml examples documented in SCHEMA.md Section 3,
verifying that both adhere to the schema specification and pass validate.py rules.
"""

from __future__ import annotations

import re
import tempfile
import tomllib
import unittest
from pathlib import Path

import validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "SCHEMA.md"
DEFAULT_PLAIN_ACCOUNT = REPO_ROOT / "fixtures" / "default-plain" / "account.json"


class SchemaWorkedExamplesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file(), f"{SCHEMA_PATH} does not exist")
        self.schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

    def _extract_toml_blocks(self) -> list[str]:
        section_start = self.schema_text.find("### Worked examples")
        self.assertNotEqual(section_start, -1)
        section_end = self.schema_text.find("## 4. What", section_start)
        section_text = (
            self.schema_text[section_start:section_end]
            if section_end != -1
            else self.schema_text[section_start:]
        )
        matches = re.findall(r"```toml\n(.*?)\n```", section_text, re.DOTALL)
        return matches

    def test_schema_has_two_worked_examples(self) -> None:
        blocks = self._extract_toml_blocks()
        self.assertEqual(len(blocks), 2, "SCHEMA.md must carry exactly two worked TOML examples")

    def test_captured_example_validates(self) -> None:
        blocks = self._extract_toml_blocks()
        captured_toml = blocks[0]
        data = tomllib.loads(captured_toml)

        self.assertEqual(data.get("kind"), "captured")
        for key in ["source_url", "captured_at", "ledger", "horizon_version", "sha256"]:
            self.assertIn(key, data, f"captured example missing mandatory provenance key {key}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / data["id"]
            tmp_path.mkdir()
            (tmp_path / "fixture.toml").write_text(captured_toml.strip() + "\n", encoding="utf-8")
            (tmp_path / "account.json").write_bytes(DEFAULT_PLAIN_ACCOUNT.read_bytes())

            corpus = validate.Corpus(tmp_path.parent)
            validate.validate_fixture(corpus, tmp_path, {})
            self.assertEqual(
                corpus.problems, [], f"captured example failed validation: {corpus.problems}"
            )

    def test_synthetic_example_validates(self) -> None:
        blocks = self._extract_toml_blocks()
        synthetic_toml = blocks[1]
        data = tomllib.loads(synthetic_toml)

        self.assertEqual(data.get("kind"), "synthetic")
        self.assertTrue(
            str(data.get("scenario", "")).startswith("synthetic:"),
            "synthetic scenario must begin with 'synthetic:'",
        )
        for key in ["source_url", "captured_at", "ledger", "horizon_version", "sha256"]:
            self.assertNotIn(key, data, f"synthetic example carries forbidden provenance key {key}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / data["id"]
            tmp_path.mkdir()
            (tmp_path / "fixture.toml").write_text(synthetic_toml.strip() + "\n", encoding="utf-8")
            # Minimal synthetic account JSON with single signer (weight 1) and thresholds zero
            account_json = (
                b'{"account_id":"'
                + data["account_id"].encode("utf-8")
                + b'","signers":[{"key":"'
                + data["account_id"].encode("utf-8")
                + b'","weight":1}],'
                + b'"thresholds":{"low_threshold":0,"med_threshold":0,"high_threshold":0}}\n'
            )
            (tmp_path / "account.json").write_bytes(account_json)

            corpus = validate.Corpus(tmp_path.parent)
            validate.validate_fixture(corpus, tmp_path, {})
            self.assertEqual(
                corpus.problems, [], f"synthetic example failed validation: {corpus.problems}"
            )

    def test_worked_examples_section_contains_zero_em_dashes(self) -> None:
        section_start = self.schema_text.find("### Worked examples")
        self.assertNotEqual(section_start, -1)
        section_end = self.schema_text.find("## 4. What", section_start)
        section_text = (
            self.schema_text[section_start:section_end]
            if section_end != -1
            else self.schema_text[section_start:]
        )
        self.assertNotIn("\u2014", section_text)


if __name__ == "__main__":
    unittest.main()
