"""Schedule tab — manage recurring time windows for filtering."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import GlobalConfig, Schedule
from .resources import Palette
from .schedule_dialog import ScheduleDialog

if TYPE_CHECKING:
    from ..scheduler import Scheduler

log = logging.getLogger(__name__)


class ScheduleTab(QWidget):
    schedules_changed = pyqtSignal()

    def __init__(self, cfg: GlobalConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self._scheduler: Scheduler | None = None
        self._build_ui()
        self._populate()

        self._status_timer = QTimer(self)
        self._status_timer.setInterval(60_000)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start()

    def set_scheduler(self, scheduler: Scheduler) -> None:
        self._scheduler = scheduler
        scheduler.state_changed.connect(lambda _: self._update_status())
        self._update_status()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        font = self._status_label.font()
        font.setPointSize(font.pointSize() + 1)
        self._status_label.setFont(font)
        layout.addWidget(self._status_label)

        hint = QLabel(
            "Schedules define when Shush actively filters notifications. "
            "If no schedules are defined, filtering is always on. "
            "Active mode = filtering ON during the window. "
            "Disable mode = filtering OFF during the window (e.g. lunch break)."
        )
        hint.setWordWrap(True)
        hint.setProperty("subtext", True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Mode", "Days", "Time", "Enabled"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_selected)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 4, 0, 0)
        toolbar.setSpacing(6)

        add_btn = QPushButton("+  Add Schedule")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add)
        toolbar.addWidget(add_btn)

        edit_btn = QPushButton("\u270E  Edit")
        edit_btn.clicked.connect(self._edit_selected)
        toolbar.addWidget(edit_btn)

        del_btn = QPushButton("\u2212  Delete")
        del_btn.setObjectName("destructive")
        del_btn.clicked.connect(self._delete)
        toolbar.addWidget(del_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._update_status()

    def _update_status(self):
        if self._scheduler is None:
            if not self.cfg.schedules:
                text = "Always active (no schedules defined)"
            else:
                text = "Checking..."
        else:
            text = self._scheduler.next_change_text()

        active = self._scheduler.is_globally_active() if self._scheduler else True
        color = Palette.GREEN.name() if active else Palette.YELLOW.name()
        dot = "\u25cf"
        self._status_label.setText(
            f'<span style="color:{color}; font-size:14px;">{dot}</span>  {text}'
        )

    def _populate(self):
        self.table.setRowCount(0)
        for sched in self.cfg.schedules:
            self._add_row(sched)

    def _add_row(self, sched: Schedule):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(sched.name)
        name_item.setData(Qt.UserRole, sched.id)
        self.table.setItem(row, 0, name_item)

        if sched.inverted:
            mode_item = QTableWidgetItem("Disable")
            mode_item.setForeground(Palette.RED)
        else:
            mode_item = QTableWidgetItem("Active")
            mode_item.setForeground(Palette.GREEN)
        self.table.setItem(row, 1, mode_item)

        self.table.setItem(row, 2, QTableWidgetItem(sched.days_display()))
        self.table.setItem(row, 3, QTableWidgetItem(
            f"{sched.start_time} \u2013 {sched.end_time}"
        ))

        enabled_text = "\u2713 Yes" if sched.enabled else "\u2717 No"
        enabled_item = QTableWidgetItem(enabled_text)
        enabled_item.setForeground(Palette.GREEN if sched.enabled else Palette.SUBTEXT)
        self.table.setItem(row, 4, enabled_item)

    def _add(self):
        dlg = ScheduleDialog(parent=self)
        if dlg.exec_() != ScheduleDialog.Accepted:
            return
        sched = dlg.get_schedule()
        self.cfg.schedules.append(sched)
        self._populate()
        self._emit_changed()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        sched_id = self.table.item(row, 0).data(Qt.UserRole)
        sched = next((s for s in self.cfg.schedules if s.id == sched_id), None)
        if sched is None:
            return
        dlg = ScheduleDialog(schedule=sched, parent=self)
        if dlg.exec_() != ScheduleDialog.Accepted:
            return
        updated = dlg.get_schedule()
        idx = self.cfg.schedules.index(sched)
        self.cfg.schedules[idx] = updated
        self._populate()
        self._emit_changed()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        sched_id = self.table.item(row, 0).data(Qt.UserRole)
        self.cfg.schedules = [s for s in self.cfg.schedules if s.id != sched_id]
        self._populate()
        self._emit_changed()

    def _emit_changed(self):
        self._update_status()
        self.schedules_changed.emit()
