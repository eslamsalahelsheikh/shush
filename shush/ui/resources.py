"""Programmatic icons and colour palette — zero external asset files."""

from PyQt5.QtCore import QPointF, QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


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


def _make_shush_pixmap(size: int, color: QColor, dimmed: bool = False) -> QPixmap:
    """Draw a 'shush' face: circle head, eyes, open mouth, finger over lips."""
    pm = QPixmap(QSize(size, size))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    s = float(size)
    cx, cy = s * 0.5, s * 0.48
    r = s * 0.38
    stroke = max(1.5, s * 0.045)

    draw_color = QColor(color)
    if dimmed:
        draw_color.setAlpha(120)

    p.setPen(QPen(draw_color, stroke, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), r, r)

    p.setPen(Qt.NoPen)
    p.setBrush(draw_color)
    eye_r = s * 0.04
    p.drawEllipse(QPointF(cx - r * 0.35, cy - r * 0.22), eye_r, eye_r)
    p.drawEllipse(QPointF(cx + r * 0.35, cy - r * 0.22), eye_r, eye_r)

    # Mouth — small "o" shape
    mouth_cy = cy + r * 0.38
    mouth_rx = s * 0.065
    mouth_ry = mouth_rx * 1.1
    p.setPen(QPen(draw_color, stroke * 0.9, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, mouth_cy), mouth_rx, mouth_ry)

    # Finger — vertical, placed directly over the mouth
    finger_w = s * 0.07
    finger_h = s * 0.32
    finger_x = cx - finger_w / 2
    finger_center_y = mouth_cy
    finger_top = finger_center_y - finger_h * 0.55
    finger_path = QPainterPath()
    finger_path.addRoundedRect(finger_x, finger_top, finger_w, finger_h,
                               finger_w / 2, finger_w / 2)
    p.setCompositionMode(QPainter.CompositionMode_Source)
    p.setPen(Qt.NoPen)
    p.setBrush(Qt.transparent)
    # Clear a slightly wider area behind the finger for clean separation
    clear_w = finger_w + s * 0.03
    clear_path = QPainterPath()
    clear_path.addRoundedRect(cx - clear_w / 2, finger_top - s * 0.01,
                              clear_w, finger_h + s * 0.02,
                              clear_w / 2, clear_w / 2)
    p.drawPath(clear_path)
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
    p.setBrush(draw_color)
    p.drawPath(finger_path)

    p.end()
    return pm


def app_icon(size: int = 64) -> QIcon:
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128):
        icon.addPixmap(_make_shush_pixmap(s, Palette.BLUE))
    return icon


def tray_icon_active(size: int = 22) -> QIcon:
    return QIcon(_make_shush_pixmap(size, Palette.BLUE))


def tray_icon_paused(size: int = 22) -> QIcon:
    return QIcon(_make_shush_pixmap(size, Palette.OVERLAY, dimmed=True))


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
