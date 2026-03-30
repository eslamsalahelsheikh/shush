"""Application bootstrap — wires D-Bus, rule engine, and Qt together."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys

from gi.repository import GLib
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from . import __app_name__, __version__
from .config import load, save
from .dbus_filter import DBusFilter
from .desktop_apps import scan_installed_apps
from .rule_engine import RuleEngine
from .ui.main_window import MainWindow
from .ui.resources import app_icon
from .ui.tray import TrayIcon

log = logging.getLogger("shush")


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="shush",
        description="Shush — Linux notification filter with a GUI rule editor.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--dry-run", action="store_true",
                   help="Log what would be suppressed without closing notifications.")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Enable debug-level logging.")
    p.add_argument("--minimized", action="store_true",
                   help="Start minimized to system tray.")
    p.add_argument("--no-fork", action="store_true",
                   help="Stay in the foreground (do not daemonize).")
    return p.parse_args(argv)


def _daemonize() -> None:
    """Fork into the background so the launching terminal is released."""
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)


def run(argv=None) -> int:
    args = parse_args(argv)

    if not args.no_fork and not args.verbose and not args.dry_run:
        _daemonize()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg, rules = load()
    engine = RuleEngine(cfg, rules)

    installed_apps = scan_installed_apps()
    log.debug("Scanned %d installed apps from .desktop files", len(installed_apps))

    qt_app = QApplication(sys.argv[:1])
    qt_app.setApplicationName(__app_name__)
    qt_app.setApplicationVersion(__version__)
    qt_app.setWindowIcon(app_icon())
    qt_app.setQuitOnLastWindowClosed(False)

    dbus_filter = DBusFilter(engine, dry_run=args.dry_run)

    window = MainWindow(cfg, rules, installed_apps=installed_apps)

    def on_rules_or_settings_changed():
        engine.update(cfg, rules)

    window.rules_tab.rules_changed.connect(on_rules_or_settings_changed)
    window.settings_tab.settings_changed.connect(on_rules_or_settings_changed)

    def on_new_app(app_name: str):
        if cfg.record_app(app_name):
            save(cfg, rules)
            log.debug("New app recorded: %s", app_name)

    dbus_filter.connect_log(window.add_log_entry)
    dbus_filter.connect_new_app(on_new_app)

    tray = TrayIcon()
    tray.toggle_window.connect(lambda: window.hide() if window.isVisible() else window.show())
    tray.toggle_pause.connect(_make_pause_handler(dbus_filter))
    tray.quit_app.connect(qt_app.quit)
    tray.show()

    if not args.minimized:
        window.show()

    glib_ctx = GLib.MainContext.default()
    dbus_timer = QTimer()
    dbus_timer.timeout.connect(lambda: _pump_glib(glib_ctx))
    dbus_timer.start(50)

    signal.signal(signal.SIGHUP, lambda *_: _reload(cfg, rules, engine, window))
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    log.info("Shush %s started  (dry_run=%s)", __version__, args.dry_run)
    return qt_app.exec_()


def _pump_glib(ctx):
    while ctx.iteration(False):
        pass


def _make_pause_handler(dbus_filter: DBusFilter):
    def handler(paused: bool):
        dbus_filter.paused = paused
        state = "PAUSED" if paused else "ACTIVE"
        log.info("Filtering %s", state)
    return handler


def _reload(cfg, rules, engine, window):
    from .config import load as reload_config
    new_cfg, new_rules = reload_config()
    cfg.__dict__.update(new_cfg.__dict__)
    rules.clear()
    rules.extend(new_rules)
    engine.update(cfg, rules)
    window.rules_tab._populate()
    window.settings_tab._load()
    log.info("Configuration reloaded via SIGHUP")
