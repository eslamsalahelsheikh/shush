"""Scan installed .desktop files for application names (best-guess seed list)."""

from __future__ import annotations

import configparser
import glob
import logging
import os
from typing import List

log = logging.getLogger(__name__)

_DESKTOP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
    "/var/lib/flatpak/exports/share/applications",
    os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    "/snap/current/share/applications",
]


def scan_installed_apps() -> List[str]:
    """Return sorted unique app names from .desktop files on the system.

    These are best-guess names — the actual D-Bus notification app_name
    may differ.  The list is used as a fallback when no real notifications
    have been seen yet.
    """
    names: set[str] = set()
    for d in _DESKTOP_DIRS:
        for path in glob.glob(os.path.join(d, "*.desktop")):
            name = _parse_desktop_name(path)
            if name:
                names.add(name)
    return sorted(names)


def _parse_desktop_name(path: str) -> str | None:
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(path, encoding="utf-8")
    except Exception:
        return None
    if not cp.has_section("Desktop Entry"):
        return None
    entry_type = cp.get("Desktop Entry", "Type", fallback="")
    if entry_type != "Application":
        return None
    if cp.get("Desktop Entry", "NoDisplay", fallback="false").lower() == "true":
        return None
    return cp.get("Desktop Entry", "Name", fallback="") or None
