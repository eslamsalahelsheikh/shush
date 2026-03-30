"""Notification sound control via GNOME gsettings.

When enabled, Shush disables GNOME's built-in notification sounds and plays
them itself only for allowed notifications.  Original settings are restored
on exit (including abnormal termination via SIGTERM).
"""

from __future__ import annotations

import atexit
import logging
import shutil
import signal
import subprocess
from typing import Dict, Optional

log = logging.getLogger(__name__)

_SCHEMA = "org.gnome.desktop.notifications.application"
_SCHEMA_PATH_FMT = "/org/gnome/desktop/notifications/application/{}/"
_KEY = "enable-sound-alerts"
_PARENT_SCHEMA = "org.gnome.desktop.notifications"
_PARENT_KEY = "application-children"

_original_values: Dict[str, bool] = {}
_active = False


def _gsettings(*args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["gsettings"] + list(args),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        log.debug("gsettings %s failed: %s", " ".join(args), result.stderr.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.debug("gsettings unavailable: %s", exc)
    return None


def _list_app_ids() -> list[str]:
    raw = _gsettings("get", _PARENT_SCHEMA, _PARENT_KEY)
    if not raw:
        return []
    raw = raw.strip("[] \n")
    return [tok.strip().strip("'\"") for tok in raw.split(",") if tok.strip()]


def activate() -> bool:
    """Mute notification sounds for all registered apps. Returns True on success."""
    global _active
    if _active:
        return True

    if not shutil.which("gsettings"):
        log.warning("gsettings not found — sound control unavailable")
        return False

    app_ids = _list_app_ids()
    if not app_ids:
        log.info("No GNOME notification apps found — sound control skipped")
        return False

    for app_id in app_ids:
        path = _SCHEMA_PATH_FMT.format(app_id)
        val = _gsettings("get", _SCHEMA + ":" + path, _KEY)
        if val is not None:
            _original_values[app_id] = val.strip().lower() == "true"
            _gsettings("set", _SCHEMA + ":" + path, _KEY, "false")

    _active = True
    atexit.register(restore)

    prev_sigterm = signal.getsignal(signal.SIGTERM)

    def _sigterm_handler(signum, frame):
        restore()
        if callable(prev_sigterm) and prev_sigterm not in (signal.SIG_DFL, signal.SIG_IGN):
            prev_sigterm(signum, frame)
        else:
            raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, _sigterm_handler)

    log.info("Sound control active — muted %d app(s), will play for allowed", len(_original_values))
    return True


def restore():
    """Restore original notification sound settings."""
    global _active
    if not _active:
        return
    for app_id, was_enabled in _original_values.items():
        if was_enabled:
            path = _SCHEMA_PATH_FMT.format(app_id)
            _gsettings("set", _SCHEMA + ":" + path, _KEY, "true")
    _original_values.clear()
    _active = False
    log.info("Sound control deactivated — restored notification sounds")


def play_notification_sound():
    """Play the standard notification sound for an allowed notification."""
    try:
        subprocess.Popen(
            ["canberra-gtk-play", "-i", "message-new-instant", "-d",
             "Shush notification sound"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log.debug("canberra-gtk-play not found — cannot play notification sound")


def is_active() -> bool:
    return _active
