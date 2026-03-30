"""Live activity log tab — shows allowed/suppressed notifications in real-time."""

from __future__ import annotations

import csv
import io
import logging
from typing import List

import dbus
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..models import Action, LogEntry, MatchField, Rule
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
    rule_requested = pyqtSignal(object)  # emits a pre-filled Rule

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
        for entry in reversed(self._entries[-_MAX_LOG_ROWS:]):
            self._append_row(entry)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by app, summary, or rule\u2026")
        self.search_edit.setClearButtonEnabled(True)
        filter_row.addWidget(self.search_edit)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All", "all")
        self.status_filter.addItem("Suppressed only", "suppressed")
        self.status_filter.addItem("Allowed only", "allowed")
        self.status_filter.setFixedWidth(150)
        filter_row.addWidget(self.status_filter)
        layout.addLayout(filter_row)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._apply_filters)
        self.search_edit.textChanged.connect(lambda: self._search_timer.start())
        self.status_filter.currentIndexChanged.connect(lambda: self._apply_filters())

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Status", "App", "Summary", "Rule"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)

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
        self._write_row(0, entry)

    def _append_row(self, entry: LogEntry):
        """Add a row at the bottom (used for bulk loading)."""
        self._write_row(self.table.rowCount(), entry)

    def _write_row(self, row: int, entry: LogEntry):
        if self.table.rowCount() >= _MAX_LOG_ROWS:
            self.table.removeRow(self.table.rowCount() - 1)

        self.table.insertRow(row)

        idx = self._find_entry_index(entry)
        time_item = QTableWidgetItem(entry.timestamp.strftime("%H:%M:%S"))
        time_item.setData(Qt.UserRole, idx)
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
        return len(self._entries) - 1

    def _apply_filters(self):
        """Hide rows that don't match the current search text + status filter."""
        text = self.search_edit.text().strip().lower()
        status = self.status_filter.currentData()
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 1)
            app_item = self.table.item(row, 2)
            summary_item = self.table.item(row, 3)
            rule_item = self.table.item(row, 4)
            if status_item is None:
                continue
            if status == "suppressed" and status_item.text() != "Suppressed":
                self.table.setRowHidden(row, True)
                continue
            if status == "allowed" and status_item.text() != "Allowed":
                self.table.setRowHidden(row, True)
                continue
            if text:
                haystack = " ".join(
                    (it.text() if it else "") for it in (app_item, summary_item, rule_item)
                ).lower()
                if text not in haystack:
                    self.table.setRowHidden(row, True)
                    continue
            self.table.setRowHidden(row, False)

    def focus_search(self):
        """Give keyboard focus to the search bar."""
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _entry_for_row(self, row: int) -> LogEntry | None:
        item = self.table.item(row, 0)
        if item is None:
            return None
        idx = item.data(Qt.UserRole)
        if idx is None or idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]

    def _context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        entry = self._entry_for_row(row) if row >= 0 else None
        if entry is None:
            return
        menu = QMenu(self)
        detail_action = menu.addAction("View Details\u2026")
        rule_action = menu.addAction("Create Rule from This\u2026")
        chosen = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if chosen == detail_action:
            dlg = _NotificationDetailDialog(entry, self)
            dlg.exec_()
        elif chosen == rule_action:
            self._request_rule(entry)

    def _request_rule(self, entry: LogEntry):
        import uuid
        rule = Rule(
            id=uuid.uuid4().hex[:12],
            name=entry.app_name or "New Rule",
            action=Action.ALLOW,
            keywords=[entry.summary] if entry.summary else [],
            match_fields=[MatchField.SUMMARY, MatchField.BODY],
            app_filter=entry.app_name or "",
        )
        self.rule_requested.emit(rule)

    def _on_double_click(self, row: int, _col: int):
        entry = self._entry_for_row(row)
        if entry is None:
            return
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
        for entry in reversed(self._entries[-_MAX_LOG_ROWS:]):
            self._append_row(entry)

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
