"""Live activity log tab — shows allowed/suppressed notifications in real-time."""

from __future__ import annotations

import csv
import io
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import LogEntry
from .resources import Palette, status_dot

_MAX_LOG_ROWS = 2000


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: List[LogEntry] = []
        self._paused = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Status", "App", "Summary", "Rule"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        self.pause_btn = QPushButton("Pause Log")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self._toggle_pause)
        toolbar.addWidget(self.pause_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

    def add_entry(self, entry: LogEntry):
        self._entries.append(entry)
        if self._paused:
            return

        if self.table.rowCount() >= _MAX_LOG_ROWS:
            self.table.removeRow(0)

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(entry.timestamp.strftime("%H:%M:%S")))

        status_item = QTableWidgetItem(entry.status_text)
        dot_color = Palette.RED if entry.suppressed else Palette.GREEN
        status_item.setIcon(QIcon(status_dot(dot_color)))
        status_item.setForeground(dot_color)
        self.table.setItem(row, 1, status_item)

        self.table.setItem(row, 2, QTableWidgetItem(entry.app_name))
        self.table.setItem(row, 3, QTableWidgetItem(entry.summary))
        self.table.setItem(row, 4, QTableWidgetItem(entry.matched_rule or "—"))

        self.table.scrollToBottom()

    def _toggle_pause(self, checked: bool):
        self._paused = checked
        self.pause_btn.setText("Resume Log" if checked else "Pause Log")
        if not checked:
            self._flush_pending()

    def _flush_pending(self):
        self.table.setRowCount(0)
        for entry in self._entries[-_MAX_LOG_ROWS:]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.timestamp.strftime("%H:%M:%S")))
            status_item = QTableWidgetItem(entry.status_text)
            dot_color = Palette.RED if entry.suppressed else Palette.GREEN
            status_item.setIcon(QIcon(status_dot(dot_color)))
            status_item.setForeground(dot_color)
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, QTableWidgetItem(entry.app_name))
            self.table.setItem(row, 3, QTableWidgetItem(entry.summary))
            self.table.setItem(row, 4, QTableWidgetItem(entry.matched_rule or "—"))

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
