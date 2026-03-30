"""Settings tab — global options and focus-mode presets."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ..models import DefaultAction, FocusPreset, GlobalConfig, Rule


class SettingsTab(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, cfg: GlobalConfig, rules: List[Rule], parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.rules = rules
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Default action ---
        action_group = QGroupBox("Default Action (when no rule matches)")
        ag_layout = QVBoxLayout(action_group)
        self.suppress_radio = QRadioButton("Suppress all notifications (whitelist mode)")
        self.allow_radio = QRadioButton("Allow all notifications (blacklist mode)")
        self.action_btn_group = QButtonGroup(self)
        self.action_btn_group.addButton(self.suppress_radio, 0)
        self.action_btn_group.addButton(self.allow_radio, 1)
        ag_layout.addWidget(self.suppress_radio)
        ag_layout.addWidget(self.allow_radio)
        ag_layout.addWidget(QLabel(
            '<small><i>Whitelist: everything is silenced except rules marked "Allow".<br>'
            'Blacklist: everything shows except rules marked "Block".</i></small>'
        ))
        layout.addWidget(action_group)

        # --- Matching ---
        match_group = QGroupBox("Matching")
        mg_layout = QFormLayout(match_group)
        self.case_cb = QCheckBox("Case-sensitive keyword matching")
        mg_layout.addRow(self.case_cb)
        layout.addWidget(match_group)

        # --- Logging ---
        log_group = QGroupBox("Activity Log File")
        lg_layout = QFormLayout(log_group)
        self.log_file_cb = QCheckBox("Write suppressed notifications to file")
        lg_layout.addRow(self.log_file_cb)
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setPlaceholderText("~/.config/shush/activity.log")
        lg_layout.addRow("Path:", self.log_path_edit)
        layout.addWidget(log_group)

        # --- Focus presets ---
        preset_group = QGroupBox("Focus-Mode Presets")
        pg_layout = QVBoxLayout(preset_group)
        pg_layout.addWidget(QLabel(
            '<small>Presets let you activate only a subset of rules with one click '
            '(e.g., "Meeting" enables Boss + Calendar only).</small>'
        ))

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(none — all enabled rules active)")
        pg_layout.addWidget(self.preset_combo)

        preset_btns = QHBoxLayout()
        self.new_preset_btn = QPushButton("New Preset")
        self.new_preset_btn.clicked.connect(self._new_preset)
        preset_btns.addWidget(self.new_preset_btn)
        self.edit_preset_btn = QPushButton("Edit Preset")
        self.edit_preset_btn.clicked.connect(self._edit_preset)
        preset_btns.addWidget(self.edit_preset_btn)
        self.del_preset_btn = QPushButton("Delete Preset")
        self.del_preset_btn.clicked.connect(self._del_preset)
        preset_btns.addWidget(self.del_preset_btn)
        preset_btns.addStretch()
        pg_layout.addLayout(preset_btns)
        layout.addWidget(preset_group)

        layout.addStretch()

        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn)

    def _load(self):
        if self.cfg.default_action == DefaultAction.SUPPRESS_ALL:
            self.suppress_radio.setChecked(True)
        else:
            self.allow_radio.setChecked(True)
        self.case_cb.setChecked(self.cfg.case_sensitive)
        self.log_file_cb.setChecked(self.cfg.log_to_file)
        self.log_path_edit.setText(self.cfg.log_file)
        self._refresh_presets()

    def _refresh_presets(self):
        self.preset_combo.clear()
        self.preset_combo.addItem("(none — all enabled rules active)", None)
        for p in self.cfg.focus_presets:
            self.preset_combo.addItem(p.name, p.id)
        if self.cfg.active_preset_id:
            idx = self.preset_combo.findData(self.cfg.active_preset_id)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def _apply(self):
        self.cfg.default_action = (
            DefaultAction.SUPPRESS_ALL if self.suppress_radio.isChecked()
            else DefaultAction.ALLOW_ALL
        )
        self.cfg.case_sensitive = self.case_cb.isChecked()
        self.cfg.log_to_file = self.log_file_cb.isChecked()
        self.cfg.log_file = self.log_path_edit.text().strip()
        self.cfg.active_preset_id = self.preset_combo.currentData()
        self.settings_changed.emit()

    def _new_preset(self):
        name, ok = QInputDialog.getText(self, "New Focus Preset", "Preset name:")
        if not ok or not name.strip():
            return
        rule_ids = self._pick_rules(f"Select rules for '{name.strip()}'")
        if rule_ids is None:
            return
        preset = FocusPreset(name=name.strip(), rule_ids=rule_ids)
        self.cfg.focus_presets.append(preset)
        self._refresh_presets()
        self.settings_changed.emit()

    def _edit_preset(self):
        pid = self.preset_combo.currentData()
        if pid is None:
            return
        preset = next((p for p in self.cfg.focus_presets if p.id == pid), None)
        if preset is None:
            return
        rule_ids = self._pick_rules(f"Select rules for '{preset.name}'", preset.rule_ids)
        if rule_ids is None:
            return
        preset.rule_ids = rule_ids
        self.settings_changed.emit()

    def _del_preset(self):
        pid = self.preset_combo.currentData()
        if pid is None:
            return
        self.cfg.focus_presets = [p for p in self.cfg.focus_presets if p.id != pid]
        if self.cfg.active_preset_id == pid:
            self.cfg.active_preset_id = None
        self._refresh_presets()
        self.settings_changed.emit()

    def _pick_rules(self, title: str, selected_ids: list | None = None) -> list | None:
        """Show a checklist dialog to pick rules for a preset."""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(350)
        vl = QVBoxLayout(dlg)
        lw = QListWidget()
        from PyQt5.QtCore import Qt
        for r in self.rules:
            from PyQt5.QtWidgets import QListWidgetItem
            item = QListWidgetItem(r.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            checked = selected_ids and r.id in selected_ids
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            item.setData(Qt.UserRole, r.id)
            lw.addItem(item)
        vl.addWidget(lw)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        vl.addWidget(bb)
        if not dlg.exec_():
            return None
        ids = []
        for i in range(lw.count()):
            item = lw.item(i)
            if item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids
