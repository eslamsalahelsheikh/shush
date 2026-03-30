"""About tab — app info, version, links, and credits."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import __app_name__, __version__
from .resources import Palette, _make_bell_pixmap


_GITHUB_URL = "https://github.com/eslamsalahelsheikh/shush"
_LICENSE = "Apache-2.0"


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        layout.addStretch(2)

        icon_label = QLabel()
        icon_label.setPixmap(_make_bell_pixmap(96, Palette.MAUVE))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        name_label = QLabel(f"{__app_name__}")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {Palette.TEXT.name()};"
            " background: transparent;"
        )
        layout.addWidget(name_label)

        version_label = QLabel(f"v{__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(
            f"font-size: 14px; color: {Palette.SUBTEXT.name()};"
            " background: transparent;"
        )
        layout.addWidget(version_label)

        tagline = QLabel("Linux notification filter with a GUI rule editor.")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setWordWrap(True)
        tagline.setStyleSheet(
            f"font-size: 14px; color: {Palette.SUBTEXT.name()};"
            " background: transparent; padding: 0 40px;"
        )
        layout.addWidget(tagline)

        layout.addSpacing(12)

        links = QLabel(
            f'<a href="{_GITHUB_URL}" style="color: {Palette.BLUE.name()};">'
            f"GitHub Repository</a>"
            f'&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'<a href="{_GITHUB_URL}/issues" style="color: {Palette.BLUE.name()};">'
            f"Report a Bug</a>"
            f'&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'<a href="{_GITHUB_URL}/blob/main/LICENSE" style="color: {Palette.BLUE.name()};">'
            f"{_LICENSE} License</a>"
        )
        links.setAlignment(Qt.AlignCenter)
        links.setOpenExternalLinks(True)
        links.setStyleSheet(
            f"font-size: 13px; background: transparent;"
        )
        layout.addWidget(links)

        layout.addSpacing(20)

        credits_label = QLabel(
            f'Made by <span style="color: {Palette.MAUVE.name()};">Eslam Elshiekh</span>'
        )
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet(
            f"font-size: 13px; color: {Palette.SUBTEXT.name()};"
            " background: transparent;"
        )
        layout.addWidget(credits_label)

        tech_label = QLabel("Built with Python · PyQt5 · D-Bus")
        tech_label.setAlignment(Qt.AlignCenter)
        tech_label.setStyleSheet(
            f"font-size: 12px; color: {Palette.OVERLAY.name()};"
            " background: transparent;"
        )
        layout.addWidget(tech_label)

        layout.addStretch(3)

        outer.addWidget(wrapper)
