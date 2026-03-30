"""Main application window — tab bar with Rules, Log, Settings."""

from __future__ import annotations

import logging
from typing import List

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QShortcut,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..config import save
from ..models import GlobalConfig, LogEntry, Rule
from .about_tab import AboutTab
from .log_tab import LogTab
from .resources import app_icon
from .rule_dialog import RuleDialog
from .rules_tab import RulesTab
from .schedule_tab import ScheduleTab
from .settings_tab import SettingsTab

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, cfg: GlobalConfig, rules: List[Rule],
                 installed_apps: list[str] | None = None):
        super().__init__()
        self.cfg = cfg
        self.rules = rules
        self._installed_apps = installed_apps or []

        self.setWindowTitle(f"{__app_name__} \u2014 Notification Filter")
        self.setWindowIcon(app_icon())
        self.resize(880, 580)
        self.setMinimumSize(660, 420)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(170)
        self.nav.setSpacing(4)
        self.nav.currentRowChanged.connect(self._switch_tab)
        root.addWidget(self.nav)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.rules_tab = RulesTab(self.rules, cfg=self.cfg,
                                  installed_apps=self._installed_apps)
        self.rules_tab.rules_changed.connect(self._on_rules_changed)
        self._add_tab("\u2295  Rules", self.rules_tab)

        self.log_tab = LogTab()
        self.log_tab.rule_requested.connect(self._on_rule_from_log)
        self._add_tab("\u2263  Activity Log", self.log_tab)

        self.schedule_tab = ScheduleTab(self.cfg)
        self.schedule_tab.schedules_changed.connect(self._on_schedules_changed)
        self._add_tab("\u25F7  Schedule", self.schedule_tab)

        self.settings_tab = SettingsTab(self.cfg, self.rules)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)
        self._add_tab("\u2699  Settings", self.settings_tab)

        self.about_tab = AboutTab()
        self._add_tab("\u24d8  About", self.about_tab)

        self.nav.setCurrentRow(0)

        self.statusBar().showMessage("Ready")
        self._update_status()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        for i in range(min(self.stack.count(), 9)):
            sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            sc.activated.connect(lambda idx=i: self.nav.setCurrentRow(idx))

        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(
            lambda: (self.nav.setCurrentRow(0), self.rules_tab._on_add())
        )
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: (self.nav.setCurrentRow(1), self.log_tab.focus_search())
        )
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(
            QApplication.instance().quit
        )

    def _add_tab(self, name: str, widget: QWidget):
        item = QListWidgetItem(name)
        item.setSizeHint(item.sizeHint().__class__(170, 42))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.nav.addItem(item)
        self.stack.addWidget(widget)

    def show_log_tab(self):
        """Switch to the Activity Log tab and show the window."""
        self.nav.setCurrentRow(1)
        self.show()
        self.raise_()
        self.activateWindow()

    def _switch_tab(self, index: int):
        widget = self.stack.widget(index)
        if widget is None:
            return
        self.stack.setCurrentIndex(index)

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_rule_from_log(self, rule):
        """Open the rule editor pre-filled so the user can review before adding."""
        seen = self.cfg.seen_apps if self.cfg else []
        dlg = RuleDialog(
            rule=rule,
            seen_apps=seen,
            installed_apps=self.rules_tab.installed_apps,
            schedules=self.cfg.schedules,
            parent=self,
        )
        if dlg.exec_() == RuleDialog.Accepted:
            confirmed = dlg.get_rule()
            self.rules.append(confirmed)
            self.rules_tab._populate()
            self.rules_tab.rules_changed.emit()
            self.nav.setCurrentRow(0)

    def _on_rules_changed(self):
        self.rules_tab.sync_enabled_states()
        self._save()
        self._update_status()

    def _on_schedules_changed(self):
        self._save()
        self._update_status()

    def _on_settings_changed(self):
        self._save()
        self._update_status()

    def _save(self):
        save(self.cfg, self.rules)
        log.debug("Configuration saved")

    def _update_status(self):
        n_enabled = sum(1 for r in self.rules if r.enabled)
        mode = "whitelist" if self.cfg.default_action.value == "suppress_all" else "blacklist"
        self.statusBar().showMessage(
            f"{n_enabled}/{len(self.rules)} rules enabled  |  Mode: {mode}"
        )

    def add_log_entry(self, entry: LogEntry):
        self.log_tab.add_entry(entry)

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange and self.isMinimized():
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._minimize_to_tray)
        super().changeEvent(event)

    def _minimize_to_tray(self):
        self.setWindowState(Qt.WindowNoState)
        self.hide()
        tray = getattr(self, "tray", None)
        if tray is not None:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(300, self._show_tray_message)

    def _show_tray_message(self):
        tray = getattr(self, "tray", None)
        if tray is None:
            return
        try:
            import dbus
            bus = dbus.SessionBus()
            proxy = bus.get_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
            )
            iface = dbus.Interface(proxy, "org.freedesktop.Notifications")
            iface.Notify(
                "Shush",
                dbus.UInt32(0),
                "",
                "Shush",
                "Minimized to tray. Filtering continues in the background.",
                dbus.Array([], signature="s"),
                dbus.Dictionary({}, signature="sv"),
                dbus.Int32(3000),
            )
        except Exception:
            from PyQt5.QtWidgets import QSystemTrayIcon
            tray.showMessage(
                "Shush",
                "Minimized to tray. Filtering continues in the background.",
                QSystemTrayIcon.Information,
                3000,
            )

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("Close Shush")
        msg.setText("Shush is still filtering in the background.")
        msg.setInformativeText("Keep running or stop completely?")
        minimize_btn = msg.addButton("  Hide to Tray  ", QMessageBox.AcceptRole)
        quit_btn = msg.addButton("  Quit  ", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("  Cancel  ", QMessageBox.RejectRole)
        msg.setDefaultButton(minimize_btn)

        msg.exec_()
        clicked = msg.clickedButton()

        if clicked == minimize_btn:
            self.hide()
            event.ignore()
        elif clicked == quit_btn:
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()

    def get_engine_params(self):
        """Return (cfg, rules) to update the RuleEngine after changes."""
        return self.cfg, self.rules
