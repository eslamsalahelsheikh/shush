"""D-Bus notification monitor — eavesdrops on Notify() and closes suppressed ones."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Set

import dbus
from dbus.mainloop.glib import DBusGMainLoop

from .models import LogEntry

if TYPE_CHECKING:
    from .rule_engine import RuleEngine

log = logging.getLogger(__name__)

MSG_TYPE_METHOD_CALL = 1
MSG_TYPE_METHOD_RETURN = 2


class DBusFilter:
    """Monitors the session bus for desktop notifications and suppresses non-matching ones.

    Lifecycle:
        1. __init__ sets up dbus-python with the GLib main loop.
        2. The owner pumps GLib.MainContext via a QTimer so events flow
           without a dedicated GLib thread.
    """

    def __init__(self, engine: RuleEngine, dry_run: bool = False):
        self.engine = engine
        self.dry_run = dry_run
        self.paused = False
        self._pending: Dict[int, dict] = {}
        self._recently_allowed: Set[str] = set()
        self._recently_closed: Set[int] = set()
        self._on_entry_callbacks: list = []
        self._on_new_app_callbacks: list = []

        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()

        proxy = self.bus.get_object(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
        )
        self._iface = dbus.Interface(proxy, "org.freedesktop.Notifications")

        self.bus.add_match_string(
            "eavesdrop='true',"
            "type='method_call',"
            "interface='org.freedesktop.Notifications',"
            "member='Notify'"
        )
        self.bus.add_match_string(
            "eavesdrop='true',"
            "type='method_return'"
        )
        self.bus.add_message_filter(self._filter)
        log.info("D-Bus notification filter attached (dry_run=%s)", dry_run)

    def connect_log(self, callback) -> None:
        """Register a callback(LogEntry) for every processed notification."""
        self._on_entry_callbacks.append(callback)

    def connect_new_app(self, callback) -> None:
        """Register a callback(str) fired when a previously-unseen app_name appears."""
        self._on_new_app_callbacks.append(callback)

    def _emit_log(self, entry: LogEntry) -> None:
        for cb in self._on_entry_callbacks:
            try:
                cb(entry)
            except Exception:
                log.exception("Log callback error")

    def _filter(self, bus, message):
        msg_type = message.get_type()

        if msg_type == MSG_TYPE_METHOD_CALL:
            self._handle_notify_call(message)
        elif msg_type == MSG_TYPE_METHOD_RETURN:
            self._handle_return(message)

    def _handle_notify_call(self, message):
        iface = message.get_interface()
        member = message.get_member()
        if iface != "org.freedesktop.Notifications" or member != "Notify":
            return

        args = message.get_args_list()
        if len(args) < 5:
            return

        app_name = str(args[0])
        summary = str(args[3])
        body = str(args[4])

        if app_name:
            for cb in self._on_new_app_callbacks:
                try:
                    cb(app_name)
                except Exception:
                    log.exception("New-app callback error")

        dedup_key = f"{app_name}\0{summary}\0{body}"
        if dedup_key in self._recently_allowed:
            return
        self._recently_allowed.add(dedup_key)
        if len(self._recently_allowed) > 200:
            self._recently_allowed.clear()

        if self.paused:
            self._emit_log(LogEntry(
                timestamp=datetime.now(), app_name=app_name,
                summary=summary, body=body, suppressed=False,
                matched_rule="(paused)",
            ))
            return

        result = self.engine.evaluate(app_name, summary, body)
        rule_name = result.matched_rule.name if result.matched_rule else None

        if result.suppress:
            serial = message.get_serial()
            self._pending[serial] = {
                "app_name": app_name,
                "summary": summary,
                "body": body,
                "rule_name": rule_name,
            }
        else:
            log.debug("ALLOW app=%r summary=%r rule=%s", app_name, summary, rule_name)
            self._emit_log(LogEntry(
                timestamp=datetime.now(), app_name=app_name,
                summary=summary, body=body, suppressed=False,
                matched_rule=rule_name,
            ))

    def _handle_return(self, message):
        reply_serial = message.get_reply_serial()
        if reply_serial not in self._pending:
            return

        info = self._pending.pop(reply_serial)
        args = message.get_args_list()
        if not args:
            return

        notif_id = int(args[0])
        self._close(notif_id, info)

    def _close(self, notif_id: int, info: dict) -> None:
        if notif_id in self._recently_closed:
            return
        self._recently_closed.add(notif_id)
        if len(self._recently_closed) > 200:
            self._recently_closed.clear()

        log.info("SUPPRESS id=%d app=%r summary=%r", notif_id, info["app_name"], info["summary"])
        self._emit_log(LogEntry(
            timestamp=datetime.now(),
            app_name=info["app_name"],
            summary=info["summary"],
            body=info["body"],
            suppressed=True,
            matched_rule=info.get("rule_name"),
        ))
        if self.dry_run:
            return
        try:
            self._iface.CloseNotification(dbus.UInt32(notif_id))
        except dbus.DBusException as exc:
            log.warning("CloseNotification(%d) failed: %s", notif_id, exc)
