"""System tray icon — show/hide window, pause filtering, quit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

from .resources import tray_icon_active, tray_icon_paused

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class TrayIcon(QSystemTrayIcon):
    toggle_window = pyqtSignal()
    toggle_pause = pyqtSignal(bool)
    quit_app = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._paused = False
        self.setIcon(tray_icon_active())
        self.setToolTip("Shush — notification filter active")

        menu = QMenu()

        self._show_action = QAction("Show / Hide", menu)
        self._show_action.triggered.connect(self.toggle_window.emit)
        menu.addAction(self._show_action)

        self._pause_action = QAction("Pause Filtering", menu)
        self._pause_action.setCheckable(True)
        self._pause_action.toggled.connect(self._on_pause)
        menu.addAction(self._pause_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window.emit()

    def _on_pause(self, checked: bool):
        self._paused = checked
        if checked:
            self.setIcon(tray_icon_paused())
            self.setToolTip("Shush \u2014 filtering PAUSED")
        else:
            self.setIcon(tray_icon_active())
            self.setToolTip("Shush \u2014 notification filter active")
        self.toggle_pause.emit(checked)

    def set_paused(self, paused: bool):
        self._pause_action.setChecked(paused)
