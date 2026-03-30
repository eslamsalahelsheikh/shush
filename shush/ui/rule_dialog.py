"""Rule editor dialog — add or edit a single rule."""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QColor, QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import Action, MatchField, Rule

_SEPARATOR = "─"
_SEEN_HEADER = f"{_SEPARATOR * 3}  Seen (exact D-Bus names)  {_SEPARATOR * 3}"
_GUESS_HEADER = f"{_SEPARATOR * 3}  Installed Apps (guesses)  {_SEPARATOR * 3}"


class RuleDialog(QDialog):
    def __init__(
        self,
        rule: Optional[Rule] = None,
        seen_apps: Optional[List[str]] = None,
        installed_apps: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit Rule" if rule else "New Rule")
        self.setMinimumWidth(480)
        self._rule = rule
        self._seen_apps = seen_apps or []
        self._installed_apps = installed_apps or []
        self._build_ui()
        if rule:
            self._load(rule)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Boss — John Smith")
        form.addRow("Name:", self.name_edit)

        self.enabled_cb = QCheckBox("Enabled")
        self.enabled_cb.setChecked(True)
        form.addRow("", self.enabled_cb)

        self.action_combo = QComboBox()
        self.action_combo.addItem("Allow", Action.ALLOW)
        self.action_combo.addItem("Block", Action.BLOCK)
        form.addRow("Action:", self.action_combo)

        kw_container = QWidget()
        kw_layout = QVBoxLayout(kw_container)
        kw_layout.setContentsMargins(0, 0, 0, 0)
        self.kw_list = QListWidget()
        self.kw_list.setMaximumHeight(120)
        kw_layout.addWidget(self.kw_list)

        kw_btn_row = QHBoxLayout()
        self.kw_input = QLineEdit()
        self.kw_input.setPlaceholderText("Type keyword and press Add")
        self.kw_input.returnPressed.connect(self._add_keyword)
        kw_btn_row.addWidget(self.kw_input)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_keyword)
        kw_btn_row.addWidget(add_btn)
        rm_btn = QPushButton("Remove")
        rm_btn.clicked.connect(self._remove_keyword)
        kw_btn_row.addWidget(rm_btn)
        kw_layout.addLayout(kw_btn_row)
        form.addRow("Keywords:", kw_container)

        mf_container = QWidget()
        mf_layout = QHBoxLayout(mf_container)
        mf_layout.setContentsMargins(0, 0, 0, 0)
        self.mf_app = QCheckBox("App Name")
        self.mf_summary = QCheckBox("Summary")
        self.mf_summary.setChecked(True)
        self.mf_body = QCheckBox("Body")
        self.mf_body.setChecked(True)
        mf_layout.addWidget(self.mf_app)
        mf_layout.addWidget(self.mf_summary)
        mf_layout.addWidget(self.mf_body)
        mf_layout.addStretch()
        form.addRow("Match in:", mf_container)

        app_container = QWidget()
        app_layout = QVBoxLayout(app_container)
        app_layout.setContentsMargins(0, 0, 0, 0)

        self.app_filter_combo = QComboBox()
        self.app_filter_combo.setEditable(True)
        self.app_filter_combo.setInsertPolicy(QComboBox.NoInsert)
        self.app_filter_combo.lineEdit().setPlaceholderText(
            "Leave empty to match all apps, or pick / type a name"
        )
        self._populate_app_combo()

        completer = QCompleter(self._all_app_names(), self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.app_filter_combo.setCompleter(completer)

        app_layout.addWidget(self.app_filter_combo)
        hint = QLabel(
            '<small><i>"Seen" names come from real notifications and will match exactly. '
            '"Installed" names are guesses from .desktop files — they may need tweaking.</i></small>'
        )
        hint.setWordWrap(True)
        app_layout.addWidget(hint)
        form.addRow("App filter:", app_container)

        self.regex_cb = QCheckBox("Treat keywords as regular expressions")
        form.addRow("", self.regex_cb)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Optional notes about this rule")
        form.addRow("Notes:", self.notes_edit)

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

    def _all_app_names(self) -> List[str]:
        return list(dict.fromkeys(self._seen_apps + self._installed_apps))

    def _populate_app_combo(self):
        self.app_filter_combo.clear()
        self.app_filter_combo.addItem("")

        if self._seen_apps:
            self.app_filter_combo.addItem(_SEEN_HEADER)
            idx = self.app_filter_combo.count() - 1
            self.app_filter_combo.model().item(idx).setEnabled(False)
            font = self.app_filter_combo.model().item(idx).font()
            font.setBold(True)
            self.app_filter_combo.model().item(idx).setFont(font)
            for name in self._seen_apps:
                self.app_filter_combo.addItem(f"  {name}", name)

        guesses = [n for n in self._installed_apps if n not in self._seen_apps]
        if guesses:
            self.app_filter_combo.addItem(_GUESS_HEADER)
            idx = self.app_filter_combo.count() - 1
            self.app_filter_combo.model().item(idx).setEnabled(False)
            font = self.app_filter_combo.model().item(idx).font()
            font.setBold(True)
            self.app_filter_combo.model().item(idx).setFont(font)
            italic = QFont()
            italic.setItalic(True)
            for name in guesses:
                self.app_filter_combo.addItem(f"  {name}", name)
                item_idx = self.app_filter_combo.count() - 1
                self.app_filter_combo.model().item(item_idx).setFont(italic)
                self.app_filter_combo.model().item(item_idx).setForeground(
                    QColor(140, 140, 140)
                )

    def _load(self, rule: Rule):
        self.name_edit.setText(rule.name)
        self.enabled_cb.setChecked(rule.enabled)
        idx = self.action_combo.findData(rule.action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)
        for kw in rule.keywords:
            self.kw_list.addItem(kw)
        self.mf_app.setChecked(MatchField.APP_NAME in rule.match_fields)
        self.mf_summary.setChecked(MatchField.SUMMARY in rule.match_fields)
        self.mf_body.setChecked(MatchField.BODY in rule.match_fields)
        if rule.app_filter:
            self.app_filter_combo.setCurrentText(rule.app_filter)
        self.regex_cb.setChecked(rule.use_regex)
        self.notes_edit.setPlainText(rule.notes)

    def _validate_and_accept(self):
        has_keywords = self.kw_list.count() > 0
        app_text = self.app_filter_combo.currentData()
        if app_text is None:
            app_text = self.app_filter_combo.currentText().strip()
        has_app = bool(app_text)

        if not has_keywords and not has_app:
            self._error_label.setText(
                "A rule needs at least one keyword or an app filter. "
                "Without either, it would match every notification."
            )
            self._error_label.show()
            return

        self._error_label.hide()
        self.accept()

    def _add_keyword(self):
        text = self.kw_input.text().strip()
        if text:
            self.kw_list.addItem(text)
            self.kw_input.clear()

    def _remove_keyword(self):
        for item in self.kw_list.selectedItems():
            self.kw_list.takeItem(self.kw_list.row(item))

    def get_rule(self) -> Rule:
        mf = []
        if self.mf_app.isChecked():
            mf.append(MatchField.APP_NAME)
        if self.mf_summary.isChecked():
            mf.append(MatchField.SUMMARY)
        if self.mf_body.isChecked():
            mf.append(MatchField.BODY)

        keywords = [self.kw_list.item(i).text() for i in range(self.kw_list.count())]

        app_text = self.app_filter_combo.currentData()
        if app_text is None:
            app_text = self.app_filter_combo.currentText().strip()

        import uuid
        return Rule(
            id=self._rule.id if self._rule else uuid.uuid4().hex[:12],
            name=self.name_edit.text().strip() or "Untitled",
            enabled=self.enabled_cb.isChecked(),
            action=self.action_combo.currentData(),
            keywords=keywords,
            match_fields=mf or [MatchField.SUMMARY, MatchField.BODY],
            app_filter=app_text,
            use_regex=self.regex_cb.isChecked(),
            notes=self.notes_edit.toPlainText().strip(),
        )
