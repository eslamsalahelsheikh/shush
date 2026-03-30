"""Rule evaluation engine — match notification fields against rules."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from .models import Action, DefaultAction, GlobalConfig, MatchField, Rule

log = logging.getLogger(__name__)


@dataclass
class MatchResult:
    suppress: bool
    matched_rule: Optional[Rule] = None


class RuleEngine:
    """Evaluates incoming notifications against configured rules."""

    def __init__(self, cfg: GlobalConfig, rules: List[Rule]):
        self.update(cfg, rules)

    def update(self, cfg: GlobalConfig, rules: List[Rule]) -> None:
        self.cfg = cfg
        self.rules = rules
        self._compiled: dict[str, list] = {}
        self._compile_all()

    def _compile_all(self) -> None:
        flags = 0 if self.cfg.case_sensitive else re.IGNORECASE
        self._compiled.clear()
        for rule in self.rules:
            if not rule.enabled:
                continue
            patterns = []
            for kw in rule.keywords:
                try:
                    pat = re.compile(kw, flags) if rule.use_regex else re.compile(re.escape(kw), flags)
                    patterns.append(pat)
                except re.error as exc:
                    log.warning("Bad regex in rule %r keyword %r: %s", rule.name, kw, exc)
            self._compiled[rule.id] = patterns

    def evaluate(self, app_name: str, summary: str, body: str) -> MatchResult:
        """Return whether this notification should be suppressed."""
        fields = {
            MatchField.APP_NAME: app_name or "",
            MatchField.SUMMARY: summary or "",
            MatchField.BODY: body or "",
        }

        preset_ids = None
        if self.cfg.active_preset_id:
            for p in self.cfg.focus_presets:
                if p.id == self.cfg.active_preset_id:
                    preset_ids = set(p.rule_ids)
                    break

        for rule in self.rules:
            if not rule.enabled:
                continue
            if preset_ids is not None and rule.id not in preset_ids:
                continue
            if rule.app_filter and rule.app_filter.lower() != app_name.lower():
                continue

            patterns = self._compiled.get(rule.id, [])
            if not patterns:
                if not rule.app_filter:
                    # No keywords AND no app filter = misconfigured, skip.
                    continue
                # No keywords but has app_filter = catch-all for that app
                # (app_filter was already checked above).
                if rule.action == Action.ALLOW:
                    return MatchResult(suppress=False, matched_rule=rule)
                else:
                    return MatchResult(suppress=True, matched_rule=rule)

            for pat in patterns:
                for mf in rule.match_fields:
                    if pat.search(fields[mf]):
                        if rule.action == Action.ALLOW:
                            return MatchResult(suppress=False, matched_rule=rule)
                        else:
                            return MatchResult(suppress=True, matched_rule=rule)

        if self.cfg.default_action == DefaultAction.SUPPRESS_ALL:
            return MatchResult(suppress=True)
        return MatchResult(suppress=False)
