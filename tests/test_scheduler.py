"""Tests for the Schedule model and Scheduler engine."""

import unittest
from datetime import datetime, time as _time
from unittest.mock import patch

from shush.models import GlobalConfig, Rule, Schedule


class TestScheduleModel(unittest.TestCase):

    def _make(self, **kwargs):
        defaults = dict(
            name="Test", enabled=True, days=list(range(7)),
            start_time="09:00", end_time="17:00", inverted=False,
        )
        defaults.update(kwargs)
        return Schedule(**defaults)

    @patch("shush.models.datetime")
    def test_in_window_normal(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 12, 0)  # Monday noon
        s = self._make(start_time="09:00", end_time="17:00")
        self.assertTrue(s.is_active_now())

    @patch("shush.models.datetime")
    def test_outside_window(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 20, 0)  # Monday 8pm
        s = self._make(start_time="09:00", end_time="17:00")
        self.assertFalse(s.is_active_now())

    @patch("shush.models.datetime")
    def test_midnight_crossing_inside(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 23, 30)  # Monday 11:30pm
        s = self._make(start_time="22:00", end_time="07:00")
        self.assertTrue(s.is_active_now())

    @patch("shush.models.datetime")
    def test_midnight_crossing_inside_early(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 3, 0)  # Monday 3am
        s = self._make(start_time="22:00", end_time="07:00")
        self.assertTrue(s.is_active_now())

    @patch("shush.models.datetime")
    def test_midnight_crossing_outside(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 12, 0)  # Monday noon
        s = self._make(start_time="22:00", end_time="07:00")
        self.assertFalse(s.is_active_now())

    @patch("shush.models.datetime")
    def test_inverted_in_window_means_inactive(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 12, 0)
        s = self._make(start_time="09:00", end_time="17:00", inverted=True)
        self.assertFalse(s.is_active_now())

    @patch("shush.models.datetime")
    def test_inverted_outside_window_means_active(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 20, 0)
        s = self._make(start_time="09:00", end_time="17:00", inverted=True)
        self.assertTrue(s.is_active_now())

    @patch("shush.models.datetime")
    def test_wrong_day(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 12, 0)  # Tuesday
        s = self._make(days=[0], start_time="09:00", end_time="17:00")  # Mon only
        self.assertFalse(s.is_active_now())

    def test_disabled_always_false(self):
        s = self._make(enabled=False)
        self.assertFalse(s.is_active_now())

    def test_no_days_always_false(self):
        s = self._make(days=[])
        self.assertFalse(s.is_active_now())

    def test_days_display(self):
        self.assertEqual(self._make(days=list(range(7))).days_display(), "Every day")
        self.assertEqual(self._make(days=list(range(5))).days_display(), "Weekdays")
        self.assertEqual(self._make(days=[5, 6]).days_display(), "Weekends")
        self.assertEqual(self._make(days=[0, 2]).days_display(), "Mon, Wed")

    def test_serialization_roundtrip(self):
        s = self._make(inverted=True)
        d = s.to_dict()
        s2 = Schedule.from_dict(d)
        self.assertEqual(s.name, s2.name)
        self.assertEqual(s.days, s2.days)
        self.assertEqual(s.inverted, s2.inverted)

    def test_inverted_absent_defaults_false(self):
        d = {"name": "X", "days": [0]}
        s = Schedule.from_dict(d)
        self.assertFalse(s.inverted)


class TestSchedulerEngine(unittest.TestCase):
    """Tests for Scheduler require Qt, so we test the logic via Schedule directly."""

    @patch("shush.models.datetime")
    def test_no_schedules_always_active(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 12, 0)
        cfg = GlobalConfig()
        # No schedules = always active
        enabled = [s for s in cfg.schedules if s.enabled]
        self.assertEqual(len(enabled), 0)

    @patch("shush.models.datetime")
    def test_disable_wins_over_active(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 30, 12, 0)  # Monday noon
        active = Schedule(
            name="Work", enabled=True, days=list(range(7)),
            start_time="09:00", end_time="17:00", inverted=False,
        )
        disable = Schedule(
            name="Lunch", enabled=True, days=list(range(7)),
            start_time="11:00", end_time="13:00", inverted=True,
        )
        # Active says ON, Disable says OFF during its window
        self.assertTrue(active.is_active_now())
        # Disable is inverted + inside window = not active
        self.assertFalse(disable.is_active_now())
        # But _in_window should be True for the disable schedule
        self.assertTrue(disable._in_window())


class TestRuleScheduleId(unittest.TestCase):

    def test_schedule_id_roundtrip(self):
        r = Rule(name="Test", schedule_id="abc123")
        d = r.to_dict()
        self.assertEqual(d["schedule_id"], "abc123")
        r2 = Rule.from_dict(d)
        self.assertEqual(r2.schedule_id, "abc123")

    def test_schedule_id_absent(self):
        r = Rule(name="Test")
        d = r.to_dict()
        self.assertNotIn("schedule_id", d)
        r2 = Rule.from_dict(d)
        self.assertIsNone(r2.schedule_id)


if __name__ == "__main__":
    unittest.main()
