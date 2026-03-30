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

    def to_dict(self) -> dict:
        return {
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
