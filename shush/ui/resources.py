"""Programmatic icons and colour palette — zero external asset files."""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap


class Palette:
    BG = QColor("#1e1e2e")
    SURFACE = QColor("#313244")
    OVERLAY = QColor("#45475a")
    TEXT = QColor("#cdd6f4")
    SUBTEXT = QColor("#a6adc8")
    GREEN = QColor("#a6e3a1")
    RED = QColor("#f38ba8")
    YELLOW = QColor("#f9e2af")
    BLUE = QColor("#89b4fa")
    MAUVE = QColor("#cba6f7")
    TEAL = QColor("#94e2d5")


def _make_bell_pixmap(size: int, color: QColor, slash: bool = False) -> QPixmap:
    pm = QPixmap(QSize(size, size))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(color)

    m = size * 0.15
    bell_w = size - 2 * m
    bell_h = bell_w * 0.72

    p.drawEllipse(int(m + bell_w * 0.3), int(m), int(bell_w * 0.4), int(bell_w * 0.22))
    p.drawRoundedRect(int(m), int(m + bell_w * 0.15), int(bell_w), int(bell_h), bell_w * 0.25, bell_w * 0.25)
    p.drawEllipse(int(m + bell_w * 0.3), int(m + bell_w * 0.15 + bell_h - bell_w * 0.1),
                  int(bell_w * 0.4), int(bell_w * 0.22))

    if slash:
        pen = p.pen()
        from PyQt5.QtGui import QPen
        p.setPen(QPen(Palette.RED, size * 0.08, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(int(m), int(size - m), int(size - m), int(m))

    p.end()
    return pm


def app_icon(size: int = 64) -> QIcon:
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128):
        icon.addPixmap(_make_bell_pixmap(s, Palette.MAUVE))
    return icon


def tray_icon_active(size: int = 22) -> QIcon:
    return QIcon(_make_bell_pixmap(size, Palette.MAUVE))


def tray_icon_paused(size: int = 22) -> QIcon:
    return QIcon(_make_bell_pixmap(size, Palette.OVERLAY, slash=True))


def status_dot(color: QColor, size: int = 12) -> QPixmap:
    pm = QPixmap(QSize(size, size))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.end()
    return pm
