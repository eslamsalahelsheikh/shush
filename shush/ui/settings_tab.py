"""Settings tab — global options and focus-mode presets."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
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
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import config
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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)

        # --- Default action ---
        action_group = QGroupBox("Default Action")
        ag_layout = QVBoxLayout(action_group)
        self.suppress_radio = QRadioButton("Suppress all (whitelist mode)")
        self.allow_radio = QRadioButton("Allow all (blacklist mode)")
        self.action_btn_group = QButtonGroup(self)
        self.action_btn_group.addButton(self.suppress_radio, 0)
        self.action_btn_group.addButton(self.allow_radio, 1)
        ag_layout.addWidget(self.suppress_radio)
        ag_layout.addWidget(self.allow_radio)
        hint = QLabel(
            'Whitelist: everything is silenced except rules marked "Allow". '
            'Blacklist: everything shows except rules marked "Block".'
        )
        hint.setWordWrap(True)
        hint.setProperty("subtext", True)
        ag_layout.addWidget(hint)
        layout.addWidget(action_group)

        # --- Sound control ---
        sound_group = QGroupBox("Sound Control")
        sg_layout = QVBoxLayout(sound_group)
        self.sound_cb = QCheckBox("Suppress sounds for blocked notifications")
        sg_layout.addWidget(self.sound_cb)
        hint2 = QLabel(
            "When enabled, Shush mutes GNOME notification sounds and only "
            "plays them for allowed notifications. Original settings are "
            "restored on exit."
        )
        hint2.setWordWrap(True)
        hint2.setProperty("subtext", True)
        sg_layout.addWidget(hint2)
        layout.addWidget(sound_group)

        # --- Autostart ---
        auto_group = QGroupBox("Startup")
        auto_layout = QVBoxLayout(auto_group)
        self.autostart_cb = ToggleSwitch("Launch Shush automatically on login")
        auto_layout.addWidget(self.autostart_cb)
        hint_auto = QLabel(
            "Installs a .desktop file in ~/.config/autostart/ so Shush "
            "starts minimized to the system tray when you log in."
        )
        hint_auto.setWordWrap(True)
        hint_auto.setProperty("subtext", True)
        auto_layout.addWidget(hint_auto)
        layout.addWidget(auto_group)

        # --- Matching ---
        match_group = QGroupBox("Matching")
        mg_layout = QVBoxLayout(match_group)
        self.case_cb = QCheckBox("Case-sensitive keyword matching")
        mg_layout.addWidget(self.case_cb)
        layout.addWidget(match_group)

        # --- Logging ---
        log_group = QGroupBox("Activity Log File")
        lg_layout = QVBoxLayout(log_group)
        self.log_file_cb = QCheckBox("Write suppressed notifications to file")
        lg_layout.addWidget(self.log_file_cb)
        path_row = QHBoxLayout()
        path_label = QLabel("Path:")
        path_row.addWidget(path_label)
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setPlaceholderText("~/.config/shush/activity.log")
        path_row.addWidget(self.log_path_edit)
        lg_layout.addLayout(path_row)
        layout.addWidget(log_group)

        # --- Focus presets ---
        preset_group = QGroupBox("Focus-Mode Presets")
        pg_layout = QVBoxLayout(preset_group)
        hint3 = QLabel(
            'Presets let you activate only a subset of rules with one click '
            '(e.g., "Meeting" enables Boss + Calendar only).'
        )
        hint3.setWordWrap(True)
        hint3.setProperty("subtext", True)
        pg_layout.addWidget(hint3)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(none \u2014 all enabled rules active)")
        pg_layout.addWidget(self.preset_combo)

        preset_btns = QHBoxLayout()
        self.new_preset_btn = QPushButton("New")
        self.new_preset_btn.clicked.connect(self._new_preset)
        preset_btns.addWidget(self.new_preset_btn)
        self.edit_preset_btn = QPushButton("Edit")
        self.edit_preset_btn.clicked.connect(self._edit_preset)
        preset_btns.addWidget(self.edit_preset_btn)
        self.del_preset_btn = QPushButton("Delete")
        self.del_preset_btn.setObjectName("destructive")
        self.del_preset_btn.clicked.connect(self._del_preset)
        preset_btns.addWidget(self.del_preset_btn)
        preset_btns.addStretch()
        pg_layout.addLayout(preset_btns)
        layout.addWidget(preset_group)

        layout.addStretch()

        apply_btn = QPushButton("\u2714  Apply Settings")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _load(self):
        if self.cfg.default_action == DefaultAction.SUPPRESS_ALL:
            self.suppress_radio.setChecked(True)
        else:
            self.allow_radio.setChecked(True)
        self.sound_cb.setChecked(self.cfg.sound_control)
        self.autostart_cb.setChecked(config.is_autostart_installed())
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
        self.cfg.sound_control = self.sound_cb.isChecked()
        want_autostart = self.autostart_cb.isChecked()
        if want_autostart != config.is_autostart_installed():
            if want_autostart:
                config.install_autostart()
            else:
                config.remove_autostart()
        self.cfg.autostart = want_autostart
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
