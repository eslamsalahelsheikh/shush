"""Schedule engine — evaluates time-based filtering windows."""

from __future__ import annotations

import logging
from datetime import datetime, time as _time, timedelta
from typing import List, Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .models import GlobalConfig, Rule, Schedule

log = logging.getLogger(__name__)

_CHECK_INTERVAL_MS = 60_000  # re-evaluate every 60 seconds


class Scheduler(QObject):
    """Periodically checks schedules and emits when global active state changes."""

    state_changed = pyqtSignal(bool)  # True = filtering active

    def __init__(self, cfg: GlobalConfig, parent: QObject | None = None):
        super().__init__(parent)
        self._cfg = cfg
        self._was_active: bool | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(_CHECK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._tick()

    def update(self, cfg: GlobalConfig) -> None:
        self._cfg = cfg
        self._tick()

    def is_globally_active(self) -> bool:
        """True if filtering should be running right now.

        Resolution order:
        1. No schedules at all → always active.
        2. Disable-mode schedules checked first: if any inverted schedule
           is currently inside its window, filtering is OFF (disable wins).
        3. Active-mode schedules: if any non-inverted schedule says active,
           filtering is ON.
        4. If only Disable schedules exist and none are in their window,
           filtering is ON.
        5. Otherwise filtering is OFF.
        """
        schedules = self._cfg.schedules
        if not schedules:
            return True
        enabled = [s for s in schedules if s.enabled]
        if not enabled:
            return True

        disable_schedules = [s for s in enabled if s.inverted]
        active_schedules = [s for s in enabled if not s.inverted]

        for s in disable_schedules:
            if s._in_window():
                return False

        if active_schedules:
            return any(s.is_active_now() for s in active_schedules)

        return True

    def is_rule_active(self, rule: Rule) -> bool:
        """Check if a specific rule is within its schedule window.

        If the rule has a schedule_id, only that schedule is checked.
        Otherwise falls back to is_globally_active().
        """
        if not rule.schedule_id:
            return self.is_globally_active()
        sched = self._find_schedule(rule.schedule_id)
        if sched is None:
            return self.is_globally_active()
        return sched.is_active_now()

    def next_change_text(self) -> str:
        """Human-readable description of the next state transition."""
        schedules = self._cfg.schedules
        enabled = [s for s in schedules if s.enabled and s.days]
        if not enabled:
            return "Always active (no schedules)"

        active = self.is_globally_active()
        now = datetime.now()
        best: datetime | None = None

        for sched in enabled:
            dt = self._next_boundary(sched, now)
            if dt is not None and (best is None or dt < best):
                best = dt

        if best is None:
            return "Active" if active else "Inactive"

        delta = best - now
        mins = int(delta.total_seconds() // 60)
        if mins < 1:
            when = "in less than a minute"
        elif mins < 60:
            when = f"in {mins} min"
        else:
            hours = mins // 60
            rem = mins % 60
            when = f"in {hours}h {rem}m" if rem else f"in {hours}h"

        if active:
            return f"Active — turns off {when}"
        return f"Inactive — turns on {when}"

    def _find_schedule(self, schedule_id: str) -> Schedule | None:
        for s in self._cfg.schedules:
            if s.id == schedule_id:
                return s
        return None

    def _next_boundary(self, sched: Schedule, now: datetime) -> datetime | None:
        """Find the next time this schedule flips between active/inactive."""
        parts_s = sched.start_time.split(":")
        parts_e = sched.end_time.split(":")
        start = _time(int(parts_s[0]), int(parts_s[1]))
        end = _time(int(parts_e[0]), int(parts_e[1]))

        for day_offset in range(8):
            check = now + timedelta(days=day_offset)
            if check.weekday() not in sched.days:
                continue

            base = check.replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = base.replace(hour=start.hour, minute=start.minute)
            end_dt = base.replace(hour=end.hour, minute=end.minute)
            if start > end:
                end_dt += timedelta(days=1)

            if start_dt > now:
                return start_dt
            if end_dt > now:
                return end_dt

        return None

    def _tick(self) -> None:
        active = self.is_globally_active()
        if self._was_active is not None and active != self._was_active:
            state = "ACTIVE" if active else "INACTIVE"
            log.info("Schedule state changed → %s", state)
            self.state_changed.emit(active)
        self._was_active = active
