"""Data models for shush rules and configuration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Action(Enum):
    ALLOW = "allow"
    BLOCK = "block"


class DefaultAction(Enum):
    SUPPRESS_ALL = "suppress_all"
    ALLOW_ALL = "allow_all"


class MatchField(Enum):
    APP_NAME = "app_name"
    SUMMARY = "summary"
    BODY = "body"


ALL_MATCH_FIELDS = [MatchField.APP_NAME, MatchField.SUMMARY, MatchField.BODY]


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class Schedule:
    """A recurring weekly time window for filtering.

    When ``inverted`` is False (the default, "Active" mode), filtering is
    ON during the specified window.  When ``inverted`` is True ("Disable"
    mode), filtering is OFF during the window.
    """
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    enabled: bool = True
    days: List[int] = field(default_factory=list)  # 0=Mon … 6=Sun
    start_time: str = "09:00"  # HH:MM
    end_time: str = "17:00"    # HH:MM
    inverted: bool = False

    def _in_window(self) -> bool:
        """Return True if the current time is inside the time/day window."""
        if not self.days:
            return False
        now = datetime.now()
        if now.weekday() not in self.days:
            return False
        from datetime import time as _time
        parts_s = self.start_time.split(":")
        parts_e = self.end_time.split(":")
        start = _time(int(parts_s[0]), int(parts_s[1]))
        end = _time(int(parts_e[0]), int(parts_e[1]))
        cur = now.time().replace(second=0, microsecond=0)
        if start <= end:
            return start <= cur < end
        return cur >= start or cur < end

    def is_active_now(self) -> bool:
        """Return True if filtering should be active according to this schedule."""
        if not self.enabled:
            return False
        in_window = self._in_window()
        return (not in_window) if self.inverted else in_window

    def days_display(self) -> str:
        if sorted(self.days) == list(range(7)):
            return "Every day"
        if sorted(self.days) == list(range(5)):
            return "Weekdays"
        if sorted(self.days) == [5, 6]:
            return "Weekends"
        return ", ".join(DAY_NAMES[d] for d in sorted(self.days))

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "days": self.days,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
        if self.inverted:
            d["inverted"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Schedule:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:12]),
            name=d.get("name", ""),
            enabled=d.get("enabled", True),
            days=d.get("days", []),
            start_time=d.get("start_time", "09:00"),
            end_time=d.get("end_time", "17:00"),
            inverted=d.get("inverted", False),
        )


@dataclass
class Rule:
    name: str
    keywords: List[str] = field(default_factory=list)
    action: Action = Action.ALLOW
    match_fields: List[MatchField] = field(default_factory=lambda: list(ALL_MATCH_FIELDS))
    app_filter: str = ""
    use_regex: bool = False
    enabled: bool = True
    notes: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    schedule_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "action": self.action.value,
            "keywords": self.keywords,
            "match_fields": [f.value for f in self.match_fields],
            "app_filter": self.app_filter,
            "use_regex": self.use_regex,
            "notes": self.notes,
        }
        if self.schedule_id:
            d["schedule_id"] = self.schedule_id
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Rule:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:12]),
            name=d.get("name", "Untitled"),
            enabled=d.get("enabled", True),
            action=Action(d.get("action", "allow")),
            keywords=d.get("keywords", []),
            match_fields=[MatchField(f) for f in d.get("match_fields", ["summary", "body"])],
            app_filter=d.get("app_filter", ""),
            use_regex=d.get("use_regex", False),
            notes=d.get("notes", ""),
            schedule_id=d.get("schedule_id"),
        )


@dataclass
class FocusPreset:
    name: str
    rule_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "rule_ids": self.rule_ids}

    @classmethod
    def from_dict(cls, d: dict) -> FocusPreset:
        return cls(id=d.get("id", uuid.uuid4().hex[:12]),
                   name=d.get("name", ""), rule_ids=d.get("rule_ids", []))


@dataclass
class GlobalConfig:
    default_action: DefaultAction = DefaultAction.SUPPRESS_ALL
    case_sensitive: bool = False
    log_to_file: bool = False
    log_file: str = ""
    autostart: bool = False
    focus_presets: List[FocusPreset] = field(default_factory=list)
    active_preset_id: Optional[str] = None
    seen_apps: List[str] = field(default_factory=list)
    sound_control: bool = False
    schedules: List[Schedule] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "default_action": self.default_action.value,
            "case_sensitive": self.case_sensitive,
            "log_to_file": self.log_to_file,
            "log_file": self.log_file,
            "autostart": self.autostart,
            "focus_presets": [p.to_dict() for p in self.focus_presets],
            "active_preset_id": self.active_preset_id,
            "seen_apps": sorted(set(self.seen_apps)),
            "sound_control": self.sound_control,
            "schedules": [s.to_dict() for s in self.schedules],
        }

    @classmethod
    def from_dict(cls, d: dict) -> GlobalConfig:
        return cls(
            default_action=DefaultAction(d.get("default_action", "suppress_all")),
            case_sensitive=d.get("case_sensitive", False),
            log_to_file=d.get("log_to_file", False),
            log_file=d.get("log_file", ""),
            autostart=d.get("autostart", False),
            focus_presets=[FocusPreset.from_dict(p) for p in d.get("focus_presets", [])],
            active_preset_id=d.get("active_preset_id"),
            seen_apps=d.get("seen_apps", []),
            sound_control=d.get("sound_control", False),
            schedules=[Schedule.from_dict(s) for s in d.get("schedules", [])],
        )

    def record_app(self, app_name: str) -> bool:
        """Add an app name to the seen list. Returns True if it was new."""
        if not app_name or app_name in self.seen_apps:
            return False
        self.seen_apps.append(app_name)
        self.seen_apps.sort()
        return True


@dataclass
class LogEntry:
    timestamp: datetime
    app_name: str
    summary: str
    body: str
    suppressed: bool
    matched_rule: Optional[str] = None

    @property
    def status_text(self) -> str:
        return "Suppressed" if self.suppressed else "Allowed"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "app_name": self.app_name,
            "summary": self.summary,
            "body": self.body,
            "suppressed": self.suppressed,
            "matched_rule": self.matched_rule,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LogEntry":
        return cls(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            app_name=d.get("app_name", ""),
            summary=d.get("summary", ""),
            body=d.get("body", ""),
            suppressed=d.get("suppressed", False),
            matched_rule=d.get("matched_rule"),
        )
