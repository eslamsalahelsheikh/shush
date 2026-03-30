"""Configuration persistence — load/save rules and settings to JSON."""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import List, Tuple

from .models import GlobalConfig, Rule

log = logging.getLogger(__name__)

_XDG_CONFIG = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
CONFIG_DIR = Path(_XDG_CONFIG) / "shush"
RULES_FILE = CONFIG_DIR / "rules.json"

DEFAULT_RULES: List[dict] = [
    {
        "id": "example-boss",
        "name": "Boss — example",
        "enabled": True,
        "action": "allow",
        "keywords": ["Boss Name"],
        "match_fields": ["summary", "body"],
        "app_filter": "",
        "use_regex": False,
        "notes": "Allow anything mentioning your boss's name",
    },
    {
        "id": "example-teams",
        "name": "Microsoft Teams",
        "enabled": True,
        "action": "allow",
        "keywords": ["Teams"],
        "match_fields": ["app_name"],
        "app_filter": "",
        "use_regex": False,
        "notes": "Allow all Teams notifications",
    },
    {
        "id": "example-urgent",
        "name": "Urgent messages",
        "enabled": True,
        "action": "allow",
        "keywords": ["urgent", "critical", "emergency", "ASAP"],
        "match_fields": ["summary", "body"],
        "app_filter": "",
        "use_regex": False,
        "notes": "Always let through urgent messages",
    },
]


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> Tuple[GlobalConfig, List[Rule]]:
    """Load global config and rules from disk, creating defaults if absent."""
    ensure_config_dir()
    if not RULES_FILE.exists():
        log.info("No config found — writing defaults to %s", RULES_FILE)
        cfg = GlobalConfig()
        rules = [Rule.from_dict(r) for r in DEFAULT_RULES]
        save(cfg, rules)
        return cfg, rules

    try:
        with open(RULES_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        log.error("Failed to read %s: %s — using defaults", RULES_FILE, exc)
        return GlobalConfig(), [Rule.from_dict(r) for r in DEFAULT_RULES]

    cfg = GlobalConfig.from_dict(data.get("global", {}))
    rules = [Rule.from_dict(r) for r in data.get("rules", [])]

    repaired = False
    seen_ids: set[str] = set()
    for rule in rules:
        if not rule.id or rule.id in seen_ids:
            rule.id = uuid.uuid4().hex[:12]
            repaired = True
        seen_ids.add(rule.id)
    if repaired:
        log.info("Assigned unique IDs to rules with missing/duplicate IDs")
        save(cfg, rules)

    return cfg, rules


def save(cfg: GlobalConfig, rules: List[Rule]) -> None:
    """Persist global config and rules to disk."""
    ensure_config_dir()
    data = {
        "global": cfg.to_dict(),
        "rules": [r.to_dict() for r in rules],
    }
    tmp = RULES_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(RULES_FILE)
    log.debug("Config saved to %s", RULES_FILE)
