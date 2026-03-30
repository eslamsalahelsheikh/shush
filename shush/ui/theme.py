"""Shush UI theme — Catppuccin Mocha inspired dark stylesheet with modern polish."""

from __future__ import annotations

from .resources import Palette

_P = Palette

STYLESHEET = f"""
/* ── Global ─────────────────────────────────────────── */
QWidget {{
    background-color: {_P.BG.name()};
    color: {_P.TEXT.name()};
    font-family: "Segoe UI", "Inter", "Cantarell", "Noto Sans", sans-serif;
    font-size: 13px;
}}

/* ── Main window ────────────────────────────────────── */
QMainWindow {{
    background-color: {_P.BG.name()};
}}

/* ── Sidebar nav ────────────────────────────────────── */
QListWidget#nav {{
    background-color: {_P.SURFACE.name()};
    border: none;
    border-right: 1px solid {_P.OVERLAY.name()};
    padding: 8px 0;
    outline: 0;
    font-size: 13px;
    font-weight: 500;
}}
QListWidget#nav::item {{
    color: {_P.SUBTEXT.name()};
    padding: 10px 16px;
    margin: 2px 6px;
    border-radius: 8px;
    border: none;
}}
QListWidget#nav::item:selected {{
    background-color: {_P.OVERLAY.name()};
    color: {_P.MAUVE.name()};
    font-weight: 600;
}}
QListWidget#nav::item:hover:!selected {{
    background-color: rgba(69, 71, 90, 0.5);
    color: {_P.TEXT.name()};
}}

/* ── Stacked widget pages ───────────────────────────── */
QStackedWidget {{
    background-color: {_P.BG.name()};
}}

/* ── Group boxes (cards) ────────────────────────────── */
QGroupBox {{
    background-color: {_P.SURFACE.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 10px;
    margin-top: 8px;
    padding: 12px;
    padding-top: 28px;
    font-weight: 600;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 8px;
    padding: 2px 8px;
    color: {_P.MAUVE.name()};
    background-color: {_P.SURFACE.name()};
    border-radius: 4px;
}}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {{
    background-color: {_P.OVERLAY.name()};
    color: {_P.TEXT.name()};
    border: 1px solid rgba(137, 180, 250, 0.15);
    border-radius: 7px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: rgba(137, 180, 250, 0.18);
    border: 1px solid {_P.BLUE.name()};
    color: {_P.BLUE.name()};
}}
QPushButton:pressed {{
    background-color: rgba(137, 180, 250, 0.28);
}}
QPushButton:disabled {{
    background-color: {_P.SURFACE.name()};
    color: {_P.OVERLAY.name()};
    border: 1px solid transparent;
}}
QPushButton#primary {{
    background-color: {_P.MAUVE.name()};
    color: {_P.BG.name()};
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: #b48cf5;
    color: {_P.BG.name()};
}}
QPushButton#destructive {{
    border: 1px solid rgba(243, 139, 168, 0.3);
}}
QPushButton#destructive:hover {{
    background-color: rgba(243, 139, 168, 0.18);
    border: 1px solid {_P.RED.name()};
    color: {_P.RED.name()};
}}

/* ── Tree widget (rules list) ───────────────────────── */
QTreeWidget {{
    background-color: {_P.SURFACE.name()};
    alternate-background-color: rgba(49, 50, 68, 0.6);
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 10px;
    padding: 4px;
    outline: 0;
    selection-background-color: rgba(203, 166, 247, 0.15);
    selection-color: {_P.TEXT.name()};
}}
QTreeWidget::item {{
    padding: 6px 4px;
    border-radius: 6px;
    margin: 1px 0;
}}
QTreeWidget::item:selected {{
    background-color: rgba(203, 166, 247, 0.15);
}}
QTreeWidget::item:hover:!selected {{
    background-color: rgba(69, 71, 90, 0.4);
}}
QHeaderView::section {{
    background-color: {_P.BG.name()};
    color: {_P.SUBTEXT.name()};
    border: none;
    border-bottom: 2px solid {_P.OVERLAY.name()};
    padding: 6px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}}

/* ── Table widget (activity log) ────────────────────── */
QTableWidget {{
    background-color: {_P.SURFACE.name()};
    alternate-background-color: rgba(49, 50, 68, 0.6);
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 10px;
    padding: 4px;
    gridline-color: rgba(69, 71, 90, 0.5);
    outline: 0;
    selection-background-color: rgba(203, 166, 247, 0.15);
    selection-color: {_P.TEXT.name()};
}}
QTableWidget::item {{
    padding: 4px 8px;
}}

/* ── Line edits & text edits ────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: {_P.SURFACE.name()};
    color: {_P.TEXT.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 7px;
    padding: 6px 10px;
    selection-background-color: {_P.MAUVE.name()};
    selection-color: {_P.BG.name()};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {_P.MAUVE.name()};
}}

/* ── Combo boxes ────────────────────────────────────── */
QComboBox {{
    background-color: {_P.SURFACE.name()};
    color: {_P.TEXT.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 7px;
    padding: 6px 10px;
    min-height: 20px;
}}
QComboBox:hover {{
    border: 1px solid {_P.BLUE.name()};
}}
QComboBox:focus {{
    border: 1px solid {_P.MAUVE.name()};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {_P.SUBTEXT.name()};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {_P.SURFACE.name()};
    color: {_P.TEXT.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: rgba(203, 166, 247, 0.2);
    selection-color: {_P.TEXT.name()};
    outline: 0;
}}

/* ── Check boxes ────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {_P.TEXT.name()};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {_P.OVERLAY.name()};
    border-radius: 5px;
    background-color: transparent;
}}
QCheckBox::indicator:checked {{
    background-color: {_P.MAUVE.name()};
    border: 2px solid {_P.MAUVE.name()};
    image: none;
}}
QCheckBox::indicator:hover {{
    border: 2px solid {_P.BLUE.name()};
}}

/* ── Radio buttons ──────────────────────────────────── */
QRadioButton {{
    spacing: 8px;
    color: {_P.TEXT.name()};
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {_P.OVERLAY.name()};
    border-radius: 10px;
    background-color: transparent;
}}
QRadioButton::indicator:checked {{
    background-color: {_P.MAUVE.name()};
    border: 2px solid {_P.MAUVE.name()};
}}
QRadioButton::indicator:hover {{
    border: 2px solid {_P.BLUE.name()};
}}

/* ── List widgets ───────────────────────────────────── */
QListWidget {{
    background-color: {_P.SURFACE.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 7px;
    padding: 4px;
    outline: 0;
}}
QListWidget::item {{
    padding: 4px 6px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: rgba(203, 166, 247, 0.15);
    color: {_P.TEXT.name()};
}}
QListWidget::item:hover:!selected {{
    background-color: rgba(69, 71, 90, 0.4);
}}

/* ── Scrollbars ─────────────────────────────────────── */
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {_P.OVERLAY.name()};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {_P.SUBTEXT.name()};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: {_P.OVERLAY.name()};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {_P.SUBTEXT.name()};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Status bar ─────────────────────────────────────── */
QStatusBar {{
    background-color: {_P.SURFACE.name()};
    color: {_P.SUBTEXT.name()};
    border-top: 1px solid {_P.OVERLAY.name()};
    font-size: 12px;
    padding: 2px 8px;
}}

/* ── Tab-specific toolbar area ──────────────────────── */
QWidget#toolbar {{
    background-color: {_P.BG.name()};
    border-top: 1px solid {_P.OVERLAY.name()};
    padding: 6px;
}}

/* ── Dialog styling ─────────────────────────────────── */
QDialog {{
    background-color: {_P.BG.name()};
    border-radius: 12px;
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ── Labels ─────────────────────────────────────────── */
QLabel {{
    color: {_P.TEXT.name()};
    background-color: transparent;
}}
QLabel[subtext="true"] {{
    color: {_P.SUBTEXT.name()};
    font-size: 12px;
}}

/* ── Message box ────────────────────────────────────── */
QMessageBox {{
    background-color: {_P.BG.name()};
}}

/* ── Tooltips ───────────────────────────────────────── */
QToolTip {{
    background-color: {_P.SURFACE.name()};
    color: {_P.TEXT.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Menu ───────────────────────────────────────────── */
QMenu {{
    background-color: {_P.SURFACE.name()};
    color: {_P.TEXT.name()};
    border: 1px solid {_P.OVERLAY.name()};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: rgba(203, 166, 247, 0.2);
}}
QMenu::separator {{
    height: 1px;
    background-color: {_P.OVERLAY.name()};
    margin: 4px 8px;
}}

"""
