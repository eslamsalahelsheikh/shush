"""Tests for config load/save."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shush.config import load, save
from shush.models import DefaultAction, GlobalConfig, Rule


class TestConfigPersistence(unittest.TestCase):

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules_file = Path(tmp) / "rules.json"
            with mock.patch("shush.config.RULES_FILE", rules_file), \
                 mock.patch("shush.config.CONFIG_DIR", Path(tmp)):
                cfg = GlobalConfig(default_action=DefaultAction.ALLOW_ALL, case_sensitive=True)
                rules = [Rule(name="Test", keywords=["hello"])]
                save(cfg, rules)

                self.assertTrue(rules_file.exists())

                loaded_cfg, loaded_rules = load()
                self.assertEqual(loaded_cfg.default_action, DefaultAction.ALLOW_ALL)
                self.assertTrue(loaded_cfg.case_sensitive)
                self.assertEqual(len(loaded_rules), 1)
                self.assertEqual(loaded_rules[0].name, "Test")

    def test_load_creates_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules_file = Path(tmp) / "rules.json"
            with mock.patch("shush.config.RULES_FILE", rules_file), \
                 mock.patch("shush.config.CONFIG_DIR", Path(tmp)):
                cfg, rules = load()
                self.assertTrue(rules_file.exists())
                self.assertGreater(len(rules), 0)

    def test_load_handles_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules_file = Path(tmp) / "rules.json"
            rules_file.write_text("{invalid json")
            with mock.patch("shush.config.RULES_FILE", rules_file), \
                 mock.patch("shush.config.CONFIG_DIR", Path(tmp)):
                cfg, rules = load()
                self.assertIsInstance(cfg, GlobalConfig)


if __name__ == "__main__":
    unittest.main()
