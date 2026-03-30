"""Rules management tab — list, add, edit, remove, duplicate, reorder."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import Action, GlobalConfig, Rule
from .resources import Palette
from .rule_dialog import RuleDialog

if TYPE_CHECKING:
    pass


class _RuleTree(QTreeWidget):
    """QTreeWidget subclass that syncs the rules list after drag-and-drop."""

    reordered = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self._flatten()
        self.reordered.emit()

    def _flatten(self):
        """Move any accidentally nested children back to top level."""
        i = 0
        while i < self.topLevelItemCount():
            parent = self.topLevelItem(i)
            while parent.childCount():
                child = parent.takeChild(0)
                self.insertTopLevelItem(i + 1, child)
            i += 1


class RulesTab(QWidget):
    rules_changed = pyqtSignal()

    def __init__(self, rules: List[Rule], cfg: GlobalConfig = None,
                 installed_apps: List[str] = None, parent=None):
        super().__init__(parent)
        self.rules = rules
        self.cfg = cfg
        self.installed_apps = installed_apps or []
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        self.tree = _RuleTree()
        self.tree.setHeaderLabels(["", "Name", "Action", "Keywords", "App Filter"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.itemDoubleClicked.connect(self._on_edit)
        self.tree.reordered.connect(self._on_rows_moved)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.tree)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(6)
        _btn_defs = [
            ("+  Add", self._on_add, "primary"),
            ("\u270e  Edit", self._on_edit, None),
            ("\u2750  Duplicate", self._on_duplicate, None),
            ("\u2212  Remove", self._on_remove, "destructive"),
            ("\u25b2  Up", self._on_move_up, None),
            ("\u25bc  Down", self._on_move_down, None),
        ]
        for label, slot, obj_name in _btn_defs:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            if obj_name:
                btn.setObjectName(obj_name)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

    def _populate(self):
        self.tree.clear()
        for rule in self.rules:
            self._add_item(rule)

    def _add_item(self, rule: Rule) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setFlags(
            (item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
            & ~Qt.ItemIsDropEnabled
        )
        item.setCheckState(0, Qt.Checked if rule.enabled else Qt.Unchecked)
        is_catchall = not rule.keywords
        name_display = rule.name
        if is_catchall:
            name_display = f"\u26a0 {rule.name}  (catch-all)"
            item.setToolTip(1, "This rule has no keywords — it matches ALL notifications"
                            + (f" from {rule.app_filter}" if rule.app_filter else ""))
        item.setText(1, name_display)
        action_text = "Allow" if rule.action == Action.ALLOW else "Block"
        item.setText(2, action_text)
        item.setForeground(2, Palette.GREEN if rule.action == Action.ALLOW else Palette.RED)
        if is_catchall:
            item.setText(3, "(all)")
            item.setForeground(3, Palette.YELLOW)
        else:
            item.setText(3, ", ".join(rule.keywords[:4]) + ("..." if len(rule.keywords) > 4 else ""))
        item.setText(4, rule.app_filter or "—")
        item.setData(0, Qt.UserRole, rule.id)
        self.tree.addTopLevelItem(item)
        return item

    def _selected_index(self) -> int:
        items = self.tree.selectedItems()
        if not items:
            return -1
        return self.tree.indexOfTopLevelItem(items[0])

    def _rule_for_index(self, idx: int) -> Rule | None:
        if 0 <= idx < len(self.rules):
            return self.rules[idx]
        return None

    def _make_dialog(self, rule=None) -> RuleDialog:
        seen = self.cfg.seen_apps if self.cfg else []
        schedules = self.cfg.schedules if self.cfg else []
        return RuleDialog(
            rule=rule, seen_apps=seen,
            installed_apps=self.installed_apps,
            schedules=schedules, parent=self,
        )

    def _on_add(self):
        dlg = self._make_dialog()
        if dlg.exec_():
            rule = dlg.get_rule()
            self.rules.append(rule)
            self._add_item(rule)
            self.rules_changed.emit()

    def _on_edit(self, item=None):
        idx = self._selected_index()
        rule = self._rule_for_index(idx)
        if rule is None:
            return
        dlg = self._make_dialog(rule=rule)
        if dlg.exec_():
            updated = dlg.get_rule()
            updated.id = rule.id
            self.rules[idx] = updated
            self._populate()
            self.rules_changed.emit()

    def _on_duplicate(self):
        idx = self._selected_index()
        rule = self._rule_for_index(idx)
        if rule is None:
            return
        import copy, uuid
        dup = copy.deepcopy(rule)
        dup.id = uuid.uuid4().hex[:12]
        dup.name = f"{rule.name} (copy)"
        self.rules.insert(idx + 1, dup)
        self._populate()
        self.rules_changed.emit()

    def _on_remove(self):
        idx = self._selected_index()
        if 0 <= idx < len(self.rules):
            self.rules.pop(idx)
            self._populate()
            self.rules_changed.emit()

    def _on_move_up(self):
        idx = self._selected_index()
        if idx > 0:
            self.rules[idx - 1], self.rules[idx] = self.rules[idx], self.rules[idx - 1]
            self._populate()
            self.tree.setCurrentItem(self.tree.topLevelItem(idx - 1))
            self.rules_changed.emit()

    def _on_move_down(self):
        idx = self._selected_index()
        if 0 <= idx < len(self.rules) - 1:
            self.rules[idx], self.rules[idx + 1] = self.rules[idx + 1], self.rules[idx]
            self._populate()
            self.tree.setCurrentItem(self.tree.topLevelItem(idx + 1))
            self.rules_changed.emit()

    def _on_rows_moved(self):
        new_order = []
        for i in range(self.tree.topLevelItemCount()):
            rid = self.tree.topLevelItem(i).data(0, Qt.UserRole)
            for r in self.rules:
                if r.id == rid:
                    new_order.append(r)
                    break
        self.rules.clear()
        self.rules.extend(new_order)
        self.rules_changed.emit()

    def sync_enabled_states(self):
        """Push checkbox states back into rule objects."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if i < len(self.rules):
                self.rules[i].enabled = item.checkState(0) == Qt.Checked
