"""Dialog for creating / editing a single schedule."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import DAY_NAMES, Schedule


class ScheduleDialog(QDialog):
    def __init__(self, schedule: Optional[Schedule] = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Schedule" if schedule else "New Schedule")
        self.setMinimumWidth(420)
        self._schedule = schedule
        self._build_ui()
        if schedule:
            self._load(schedule)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Work Hours, Night Quiet Time")
        form.addRow("Name:", self.name_edit)

        self.enabled_cb = QCheckBox("Enabled")
        self.enabled_cb.setChecked(True)
        form.addRow("", self.enabled_cb)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Active \u2014 filtering ON during this window", False)
        self.mode_combo.addItem("Disable \u2014 filtering OFF during this window", True)
        self.mode_combo.currentIndexChanged.connect(self._update_hint)
        form.addRow("Mode:", self.mode_combo)

        days_container = QWidget()
        days_layout = QVBoxLayout(days_container)
        days_layout.setContentsMargins(0, 0, 0, 0)
        days_layout.setSpacing(6)

        self._day_cbs: list[QCheckBox] = []
        day_row = QHBoxLayout()
        day_row.setSpacing(8)
        for i, name in enumerate(DAY_NAMES):
            cb = QCheckBox(name)
            self._day_cbs.append(cb)
            day_row.addWidget(cb)
        day_row.addStretch()
        days_layout.addLayout(day_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        weekdays_btn = QPushButton("Weekdays")
        weekdays_btn.clicked.connect(lambda: self._quick_days(list(range(5))))
        quick_row.addWidget(weekdays_btn)
        weekends_btn = QPushButton("Weekends")
        weekends_btn.clicked.connect(lambda: self._quick_days([5, 6]))
        quick_row.addWidget(weekends_btn)
        every_btn = QPushButton("Every Day")
        every_btn.clicked.connect(lambda: self._quick_days(list(range(7))))
        quick_row.addWidget(every_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._quick_days([]))
        quick_row.addWidget(clear_btn)
        quick_row.addStretch()
        days_layout.addLayout(quick_row)
        form.addRow("Days:", days_container)

        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(QTime(9, 0))
        time_layout.addWidget(QLabel("From:"))
        time_layout.addWidget(self.start_time)

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setTime(QTime(17, 0))
        time_layout.addWidget(QLabel("To:"))
        time_layout.addWidget(self.end_time)
        time_layout.addStretch()
        form.addRow("Time:", time_container)

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setProperty("subtext", True)
        form.addRow("", self._hint)
        self._update_hint()

        layout.addLayout(form)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _quick_days(self, days: list[int]):
        for i, cb in enumerate(self._day_cbs):
            cb.setChecked(i in days)

    def _update_hint(self):
        inverted = self.mode_combo.currentData()
        if inverted:
            self._hint.setText(
                "Disable mode: filtering is turned OFF during this window and "
                "ON outside it. Use this to set break / downtime periods."
            )
        else:
            self._hint.setText(
                "Active mode: filtering is ON during this window. "
                "If the end time is before the start, it wraps across midnight "
                "(e.g. 22:00\u201307:00)."
            )

    def _load(self, s: Schedule):
        self.name_edit.setText(s.name)
        self.enabled_cb.setChecked(s.enabled)
        idx = self.mode_combo.findData(s.inverted)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        for i, cb in enumerate(self._day_cbs):
            cb.setChecked(i in s.days)
        parts_s = s.start_time.split(":")
        self.start_time.setTime(QTime(int(parts_s[0]), int(parts_s[1])))
        parts_e = s.end_time.split(":")
        self.end_time.setTime(QTime(int(parts_e[0]), int(parts_e[1])))

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            self._error_label.setText("Schedule name is required.")
            self._error_label.show()
            return
        days = [i for i, cb in enumerate(self._day_cbs) if cb.isChecked()]
        if not days:
            self._error_label.setText("Select at least one day.")
            self._error_label.show()
            return
        self._error_label.hide()
        self.accept()

    def get_schedule(self) -> Schedule:
        import uuid
        return Schedule(
            id=self._schedule.id if self._schedule else uuid.uuid4().hex[:12],
            name=self.name_edit.text().strip() or "Untitled",
            enabled=self.enabled_cb.isChecked(),
            days=[i for i, cb in enumerate(self._day_cbs) if cb.isChecked()],
            start_time=self.start_time.time().toString("HH:mm"),
            end_time=self.end_time.time().toString("HH:mm"),
            inverted=bool(self.mode_combo.currentData()),
        )
