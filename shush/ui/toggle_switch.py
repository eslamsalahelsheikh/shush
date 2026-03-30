"""Animated iOS-style toggle switch widget."""

from __future__ import annotations

from PyQt5.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QAbstractButton

from .resources import Palette


class ToggleSwitch(QAbstractButton):
    """A smooth sliding toggle switch, API-compatible with QCheckBox."""

    toggled_signal = pyqtSignal(bool)

    _TRACK_W = 44
    _TRACK_H = 24
    _HANDLE_MARGIN = 3
    _HANDLE_SIZE = _TRACK_H - 2 * _HANDLE_MARGIN

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._label = text
        self._handle_x = float(self._HANDLE_MARGIN)

        self._anim = QPropertyAnimation(self, b"handleX", self)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.setDuration(200)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self.toggled_signal.emit(self.isChecked())

    def sizeHint(self) -> QSize:
        w = self._TRACK_W
        if self._label:
            fm = self.fontMetrics()
            w += 10 + fm.horizontalAdvance(self._label)
        return QSize(w, max(self._TRACK_H, self.fontMetrics().height()))

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        end = self._on_x() if checked else float(self._HANDLE_MARGIN)
        self._handle_x = end
        self.update()

    def _on_x(self) -> float:
        return float(self._TRACK_W - self._HANDLE_MARGIN - self._HANDLE_SIZE)

    @pyqtProperty(float)
    def handleX(self) -> float:
        return self._handle_x

    @handleX.setter
    def handleX(self, val: float):
        self._handle_x = val
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        checked = self.isChecked()
        progress = (self._handle_x - self._HANDLE_MARGIN) / (
            self._on_x() - self._HANDLE_MARGIN
        ) if self._on_x() != self._HANDLE_MARGIN else 0.0
        progress = max(0.0, min(1.0, progress))

        track_color = self._blend(Palette.OVERLAY, Palette.BLUE, progress)
        p.setPen(Qt.NoPen)
        p.setBrush(track_color)
        y_offset = (self.height() - self._TRACK_H) // 2
        p.drawRoundedRect(
            0, y_offset, self._TRACK_W, self._TRACK_H,
            self._TRACK_H / 2, self._TRACK_H / 2,
        )

        handle_color = QColor("#ffffff") if checked else Palette.SUBTEXT
        handle_color_blended = self._blend(Palette.SUBTEXT, QColor("#ffffff"), progress)
        p.setBrush(handle_color_blended)
        p.drawEllipse(
            int(self._handle_x),
            y_offset + self._HANDLE_MARGIN,
            self._HANDLE_SIZE,
            self._HANDLE_SIZE,
        )

        if self._label:
            p.setPen(Palette.TEXT)
            text_x = self._TRACK_W + 10
            text_rect = QRect(text_x, 0, self.width() - text_x, self.height())
            p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self._label)

        p.end()

    def nextCheckState(self):
        super().nextCheckState()
        self._animate()

    def _animate(self):
        self._anim.stop()
        self._anim.setStartValue(self._handle_x)
        end = self._on_x() if self.isChecked() else float(self._HANDLE_MARGIN)
        self._anim.setEndValue(end)
        self._anim.start()

    @staticmethod
    def _blend(c1: QColor, c2: QColor, t: float) -> QColor:
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue() + (c2.blue() - c1.blue()) * t),
            int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
        )
