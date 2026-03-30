"""System tray icon — show/hide window, pause filtering, quit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

from .resources import Palette, _make_shush_pixmap, tray_icon_active, tray_icon_paused

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class TrayIcon(QSystemTrayIcon):
    toggle_window = pyqtSignal()
    show_log = pyqtSignal()
    toggle_pause = pyqtSignal(bool)
    quit_app = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._paused = False
        self._suppressed_count = 0
        self.setIcon(tray_icon_active())
        self.setToolTip("Shush — notification filter active")

        menu = QMenu()

        self._show_action = QAction("Show / Hide", menu)
        self._show_action.triggered.connect(self.toggle_window.emit)
        menu.addAction(self._show_action)

        self._log_action = QAction("Activity Log", menu)
        self._log_action.triggered.connect(self._open_log)
        menu.addAction(self._log_action)

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
            if self._suppressed_count > 0:
                self._open_log()
            else:
                self.toggle_window.emit()

    def _open_log(self):
        self.show_log.emit()
        self.reset_suppressed()

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

    def increment_suppressed(self):
        self._suppressed_count += 1
        self._update_badge()

    def reset_suppressed(self):
        self._suppressed_count = 0
        self._update_badge()

    def _update_badge(self):
        size = 22
        color = Palette.OVERLAY if self._paused else Palette.BLUE
        pm = _make_shush_pixmap(size, color, dimmed=self._paused)

        if self._suppressed_count > 0:
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)

            text = str(self._suppressed_count) if self._suppressed_count < 100 else "99+"
            font = QFont("sans-serif", 7 if len(text) <= 2 else 6, QFont.Bold)
            p.setFont(font)
            fm = p.fontMetrics()

            text_w = fm.horizontalAdvance(text)
            badge_w = max(text_w + 4, fm.height())
            badge_h = fm.height()
            bx = size - badge_w - 0.5
            by = 0.5

            p.setPen(Qt.NoPen)
            p.setBrush(Palette.RED)
            p.drawRoundedRect(QRectF(bx, by, badge_w, badge_h),
                              badge_h / 2, badge_h / 2)

            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(bx, by, badge_w, badge_h),
                       Qt.AlignCenter, text)
            p.end()

        self.setIcon(QIcon(pm))
        tooltip_count = f" ({self._suppressed_count} suppressed)" if self._suppressed_count else ""
        if self._paused:
            self.setToolTip(f"Shush \u2014 filtering PAUSED{tooltip_count}")
        else:
            self.setToolTip(f"Shush \u2014 notification filter active{tooltip_count}")
