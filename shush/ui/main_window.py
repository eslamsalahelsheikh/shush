"""Main application window — tab bar with Rules, Log, Settings."""

from __future__ import annotations

import logging
from typing import List

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
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
from .rules_tab import RulesTab
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
        self._add_tab("\U0001f4cb  Rules", self.rules_tab)

        self.log_tab = LogTab()
        self._add_tab("\U0001f4ca  Activity Log", self.log_tab)

        self.settings_tab = SettingsTab(self.cfg, self.rules)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)
        self._add_tab("\u2699\ufe0f  Settings", self.settings_tab)

        self.about_tab = AboutTab()
        self._add_tab("\u2139\ufe0f  About", self.about_tab)

        self.nav.setCurrentRow(0)

        self.statusBar().showMessage("Ready")
        self._update_status()

    def _add_tab(self, name: str, widget: QWidget):
        item = QListWidgetItem(name)
        item.setSizeHint(item.sizeHint().__class__(170, 42))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.nav.addItem(item)
        self.stack.addWidget(widget)

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

    def _on_rules_changed(self):
        self.rules_tab.sync_enabled_states()
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
