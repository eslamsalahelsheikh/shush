"""Tests for the rule evaluation engine."""

import unittest

from shush.models import Action, DefaultAction, GlobalConfig, MatchField, Rule
from shush.rule_engine import RuleEngine


class TestRuleEngine(unittest.TestCase):

    def _engine(self, rules, default=DefaultAction.SUPPRESS_ALL, case_sensitive=False):
        cfg = GlobalConfig(default_action=default, case_sensitive=case_sensitive)
        return RuleEngine(cfg, rules)

    def test_allow_rule_matches_summary(self):
        rule = Rule(name="Boss", keywords=["Ahmed"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY])
        engine = self._engine([rule])
        result = engine.evaluate("Slack", "Message from Ahmed", "")
        self.assertFalse(result.suppress)
        self.assertEqual(result.matched_rule, rule)

    def test_suppress_when_no_match_whitelist(self):
        rule = Rule(name="Boss", keywords=["Ahmed"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY])
        engine = self._engine([rule])
        result = engine.evaluate("Firefox", "Download complete", "")
        self.assertTrue(result.suppress)
        self.assertIsNone(result.matched_rule)

    def test_block_rule_in_blacklist_mode(self):
        rule = Rule(name="Spam", keywords=["lottery"], action=Action.BLOCK,
                    match_fields=[MatchField.BODY])
        engine = self._engine([rule], default=DefaultAction.ALLOW_ALL)
        result = engine.evaluate("Mail", "New email", "You won the lottery!")
        self.assertTrue(result.suppress)

    def test_allow_all_mode_no_match(self):
        rule = Rule(name="Spam", keywords=["lottery"], action=Action.BLOCK,
                    match_fields=[MatchField.BODY])
        engine = self._engine([rule], default=DefaultAction.ALLOW_ALL)
        result = engine.evaluate("Firefox", "Page loaded", "")
        self.assertFalse(result.suppress)

    def test_case_insensitive(self):
        rule = Rule(name="Boss", keywords=["ahmed"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY])
        engine = self._engine([rule], case_sensitive=False)
        result = engine.evaluate("Slack", "AHMED sent a message", "")
        self.assertFalse(result.suppress)

    def test_case_sensitive(self):
        rule = Rule(name="Boss", keywords=["ahmed"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY])
        engine = self._engine([rule], case_sensitive=True)
        result = engine.evaluate("Slack", "AHMED sent a message", "")
        self.assertTrue(result.suppress)

    def test_regex_keyword(self):
        rule = Rule(name="Tickets", keywords=[r"PROJ-\d+"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY], use_regex=True)
        engine = self._engine([rule])
        result = engine.evaluate("Jira", "PROJ-1234 updated", "")
        self.assertFalse(result.suppress)

    def test_app_filter(self):
        rule = Rule(name="Teams only", keywords=["meeting"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY], app_filter="Teams")
        engine = self._engine([rule])
        result_teams = engine.evaluate("Teams", "meeting starting", "")
        self.assertFalse(result_teams.suppress)
        result_slack = engine.evaluate("Slack", "meeting starting", "")
        self.assertTrue(result_slack.suppress)

    def test_disabled_rule_skipped(self):
        rule = Rule(name="Boss", keywords=["Ahmed"], action=Action.ALLOW,
                    match_fields=[MatchField.SUMMARY], enabled=False)
        engine = self._engine([rule])
        result = engine.evaluate("Slack", "Ahmed says hi", "")
        self.assertTrue(result.suppress)

    def test_multiple_keywords_any_matches(self):
        rule = Rule(name="VIPs", keywords=["Ahmed", "Sara", "Omar"],
                    action=Action.ALLOW, match_fields=[MatchField.SUMMARY, MatchField.BODY])
        engine = self._engine([rule])
        self.assertFalse(engine.evaluate("Slack", "hey", "Sara says hi").suppress)
        self.assertTrue(engine.evaluate("Slack", "hey", "nobody here").suppress)

    def test_no_keywords_no_app_is_skipped(self):
        rule = Rule(name="Empty", keywords=[], action=Action.ALLOW, app_filter="")
        engine = self._engine([rule])
        result = engine.evaluate("Firefox", "Anything", "whatever")
        self.assertTrue(result.suppress)
        self.assertIsNone(result.matched_rule)

    def test_no_keywords_with_app_filter_is_catchall(self):
        rule = Rule(name="AllSlack", keywords=[], action=Action.ALLOW, app_filter="Slack")
        engine = self._engine([rule])
        self.assertFalse(engine.evaluate("Slack", "hello", "").suppress)
        self.assertTrue(engine.evaluate("Teams", "hello", "").suppress)

    def test_no_keywords_block_with_app_filter(self):
        rule = Rule(name="BlockSlack", keywords=[], action=Action.BLOCK, app_filter="Slack")
        engine = self._engine([rule], default=DefaultAction.ALLOW_ALL)
        self.assertTrue(engine.evaluate("Slack", "test", "").suppress)
        self.assertFalse(engine.evaluate("Teams", "test", "").suppress)


class TestRuleEngineConfig(unittest.TestCase):

    def test_roundtrip_rule_serialization(self):
        rule = Rule(name="Test", keywords=["x"], action=Action.BLOCK,
                    match_fields=[MatchField.BODY], app_filter="App", use_regex=True)
        d = rule.to_dict()
        restored = Rule.from_dict(d)
        self.assertEqual(rule.name, restored.name)
        self.assertEqual(rule.action, restored.action)
        self.assertEqual(rule.keywords, restored.keywords)
        self.assertEqual(rule.match_fields, restored.match_fields)
        self.assertEqual(rule.app_filter, restored.app_filter)
        self.assertEqual(rule.use_regex, restored.use_regex)


if __name__ == "__main__":
    unittest.main()
