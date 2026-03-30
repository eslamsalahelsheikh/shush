"""Live activity log tab — shows allowed/suppressed notifications in real-time."""

from __future__ import annotations

import csv
import io
import logging
from typing import List

import dbus
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..models import LogEntry
from .resources import Palette, status_dot

_MAX_LOG_ROWS = 2000
_log = logging.getLogger(__name__)


class _NotificationDetailDialog(QDialog):
    """Shows full notification details with a Re-send button."""

    def __init__(self, entry: LogEntry, parent=None):
        super().__init__(parent)
        self._entry = entry
        self.setWindowTitle("Notification Detail")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        status_text = self._entry.status_text
        status_color = Palette.RED.name() if self._entry.suppressed else Palette.GREEN.name()
        status_label = QLabel(f'<span style="color:{status_color};">{status_text}</span>')
        form.addRow("Status:", status_label)

        form.addRow("Time:", QLabel(self._entry.timestamp.strftime("%Y-%m-%d  %H:%M:%S")))
        form.addRow("App:", QLabel(self._entry.app_name or "(unknown)"))
        form.addRow("Summary:", QLabel(self._entry.summary or "(empty)"))
        form.addRow("Rule:", QLabel(self._entry.matched_rule or "— (default action)"))

        layout.addLayout(form)

        body_label = QLabel("Body:")
        layout.addWidget(body_label)

        body_edit = QTextEdit()
        body_edit.setPlainText(self._entry.body or "(empty)")
        body_edit.setReadOnly(True)
        body_edit.setMaximumHeight(120)
        layout.addWidget(body_edit)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        resend_btn = QPushButton("Re-send Notification")
        resend_btn.setObjectName("primary")
        resend_btn.clicked.connect(self._resend)
        btn_row.addWidget(resend_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _resend(self):
        try:
            bus = dbus.SessionBus()
            proxy = bus.get_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
            )
            iface = dbus.Interface(proxy, "org.freedesktop.Notifications")
            iface.Notify(
                self._entry.app_name or "Shush",
                dbus.UInt32(0),
                "",
                self._entry.summary or "",
                self._entry.body or "",
                dbus.Array([], signature="s"),
                dbus.Dictionary({}, signature="sv"),
                dbus.Int32(-1),
            )
            self.accept()
        except dbus.DBusException as exc:
            _log.warning("Re-send failed: %s", exc)


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: List[LogEntry] = config.load_log()
        self._paused = False
        self._dirty = False
        self._build_ui()
        self._load_saved_entries()

        self._save_timer = QTimer(self)
        self._save_timer.setInterval(30_000)
        self._save_timer.timeout.connect(self._persist)
        self._save_timer.start()

    def _load_saved_entries(self):
        for entry in self._entries:
            self._render_row(entry)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Status", "App", "Summary", "Rule"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_double_click)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 4, 0, 0)
        toolbar.setSpacing(6)

        self.pause_btn = QPushButton("\u23f8  Pause Log")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self._toggle_pause)
        toolbar.addWidget(self.pause_btn)

        export_btn = QPushButton("\u2913  Export CSV")
        export_btn.clicked.connect(self._export)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("\u2715  Clear")
        clear_btn.setObjectName("destructive")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

    def add_entry(self, entry: LogEntry):
        self._entries.append(entry)
        self._dirty = True
        if self._paused:
            return
        self._render_row(entry)
        self.table.scrollToBottom()

    def _render_row(self, entry: LogEntry):
        if self.table.rowCount() >= _MAX_LOG_ROWS:
            self.table.removeRow(0)

        row = self.table.rowCount()
        self.table.insertRow(row)

        time_item = QTableWidgetItem(entry.timestamp.strftime("%H:%M:%S"))
        time_item.setData(Qt.UserRole, len(self._entries) - 1 if entry is self._entries[-1] else self._find_entry_index(entry))
        self.table.setItem(row, 0, time_item)

        status_item = QTableWidgetItem(entry.status_text)
        dot_color = Palette.RED if entry.suppressed else Palette.GREEN
        status_item.setIcon(QIcon(status_dot(dot_color)))
        status_item.setForeground(dot_color)
        self.table.setItem(row, 1, status_item)

        self.table.setItem(row, 2, QTableWidgetItem(entry.app_name))
        self.table.setItem(row, 3, QTableWidgetItem(entry.summary))
        self.table.setItem(row, 4, QTableWidgetItem(entry.matched_rule or "—"))

    def _find_entry_index(self, entry: LogEntry) -> int:
        for i, e in enumerate(self._entries):
            if e is entry:
                return i
        return -1

    def _on_double_click(self, row: int, _col: int):
        item = self.table.item(row, 0)
        if item is None:
            return
        idx = item.data(Qt.UserRole)
        if idx is None or idx < 0 or idx >= len(self._entries):
            return
        entry = self._entries[idx]
        dlg = _NotificationDetailDialog(entry, self)
        dlg.exec_()

    def _persist(self):
        if self._dirty:
            config.save_log(self._entries)
            self._dirty = False

    def _toggle_pause(self, checked: bool):
        self._paused = checked
        self.pause_btn.setText("\u25b6  Resume Log" if checked else "\u23f8  Pause Log")
        if not checked:
            self._flush_pending()

    def _flush_pending(self):
        self.table.setRowCount(0)
        for entry in self._entries[-_MAX_LOG_ROWS:]:
            self._render_row(entry)

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log", "shush_log.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Status", "App", "Summary", "Rule"])
            for e in self._entries:
                writer.writerow([
                    e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    e.status_text,
                    e.app_name,
                    e.summary,
                    e.matched_rule or "",
                ])

    def _clear(self):
        self._entries.clear()
        self.table.setRowCount(0)
        self._dirty = True
        self._persist()
