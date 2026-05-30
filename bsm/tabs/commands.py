import os
import sys
import json
import time
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QTabWidget,
    QFileDialog, QMessageBox, QFormLayout, QScrollArea,
    QGroupBox, QListWidget, QListWidgetItem, QSplitter,
    QStatusBar, QComboBox, QCheckBox, QDialog, QProgressBar,
    QFrame, QCompleter, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QTextCursor, QColor, QIntValidator, QAction, QDoubleValidator

from ..theme import *
from ..commands_data import *
from ..widgets import PickerCombo, PlayerCombo


# ── Commands Tab ─────────────────────────────────────────────────────────────────
class CommandsTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.param_widgets = {}      # key -> (kind, widget)
        self.player_widgets = []     # PlayerCombo instances to refresh live
        self._build()
        self.player_timer = QTimer(self)
        self.player_timer.setInterval(1500)
        self.player_timer.timeout.connect(self._refresh_players)
        self.player_timer.start()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("Constructor de comandos")
        lbl.setObjectName("title")
        layout.addWidget(lbl)
        sub = QLabel("Elige un comando y rellena los campos. Los jugadores se actualizan en vivo.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        # Command searcher: a filter box + a plain (non-editable) combo.
        # Non-editable avoids the editable-combo/completer deletion crash on rebuild.
        cmd_row = QHBoxLayout()
        cmd_lbl = QLabel("Comando:")
        cmd_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar comando (ej. give, kick, tp)...")
        self.search.textChanged.connect(self._filter_commands)
        self.cmd_combo = QComboBox()
        for c in COMMANDS:
            self.cmd_combo.addItem(c.label, c.key)
        self.cmd_combo.currentIndexChanged.connect(self._on_command_changed)
        cmd_row.addWidget(cmd_lbl)
        cmd_row.addWidget(self.search, 1)
        cmd_row.addWidget(self.cmd_combo, 1)
        layout.addLayout(cmd_row)

        self.hint_lbl = QLabel("")
        self.hint_lbl.setObjectName("subtitle")
        layout.addWidget(self.hint_lbl)

        # Dynamic parameter form (swappable container for safe rebuilds)
        self.form_group = QGroupBox("  Parámetros")
        self.form_group_layout = QVBoxLayout(self.form_group)
        self.form_container = None
        layout.addWidget(self.form_group)

        # Preview + send
        prev_group = QGroupBox("  Comando a enviar")
        pv = QVBoxLayout(prev_group)
        self.preview = QLineEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Consolas", 12))
        self.preview.setStyleSheet(f"color: {ACCENT}; background:#060610;")
        pv.addWidget(self.preview)
        btns = QHBoxLayout()
        self.send_btn = QPushButton("▶  Ejecutar")
        self.send_btn.setObjectName("success")
        self.send_btn.clicked.connect(self.send)
        copy_btn = QPushButton("📋  Copiar")
        copy_btn.clicked.connect(self.copy)
        btns.addStretch()
        btns.addWidget(copy_btn)
        btns.addWidget(self.send_btn)
        pv.addLayout(btns)
        layout.addWidget(prev_group)
        layout.addStretch()

        # default selection
        self.cmd_combo.setCurrentIndex(0)
        self._on_command_changed()

    # ── form management ──
    def _filter_commands(self, text):
        text = text.strip().lower()
        if not text:
            return
        for i in range(self.cmd_combo.count()):
            if text in self.cmd_combo.itemText(i).lower():
                self.cmd_combo.setCurrentIndex(i)
                break

    def _current_spec(self):
        return COMMANDS_BY_KEY.get(self.cmd_combo.currentData())

    def _make_widget(self, p):
        if p.kind == "player":
            w = PlayerCombo()
            w.refresh(self.parent.connected_players)
            self.player_widgets.append(w)
            w.currentTextChanged.connect(self._update_preview)
            w.lineEdit().textChanged.connect(self._update_preview)
        elif p.kind in ("item", "effect", "enchant", "entity"):
            opts = {"item": ITEMS, "effect": EFFECTS,
                    "enchant": ENCHANTS, "entity": ENTITIES}[p.kind]
            w = PickerCombo(opts)
            w.currentTextChanged.connect(self._update_preview)
            w.lineEdit().textChanged.connect(self._update_preview)
        elif p.kind == "enum":
            w = QComboBox()
            for value, label in p.options:
                w.addItem(label, value)
            w.currentIndexChanged.connect(self._update_preview)
        elif p.kind == "bool":
            w = QCheckBox()
            if p.default in (True, "true", "1"):
                w.setChecked(True)
            w.stateChanged.connect(self._update_preview)
        elif p.kind == "int":
            w = QLineEdit(str(p.default) if p.default != "" else "")
            w.setValidator(QIntValidator(0, 2_147_483_647, w))
            if p.placeholder:
                w.setPlaceholderText(p.placeholder)
            w.textChanged.connect(self._update_preview)
        else:  # text
            w = QLineEdit(str(p.default) if p.default != "" else "")
            if p.placeholder:
                w.setPlaceholderText(p.placeholder)
            w.textChanged.connect(self._update_preview)
        return w

    def _on_command_changed(self, *args):
        try:
            spec = self._current_spec()
            # Build a brand-new container and swap it in, then defer-delete the
            # old one. Replacing a whole container + deleteLater avoids deleting
            # editable combos/completers mid-paint (which hard-crashes on Windows).
            container = QWidget()
            form = QFormLayout(container)
            form.setSpacing(10)
            form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            self.param_widgets = {}
            self.player_widgets = []
            if spec:
                self.hint_lbl.setText(f"Sintaxis:  {spec.hint}")
                for p in spec.params:
                    label = p.label + ("" if not p.optional else "  (opcional)")
                    w = self._make_widget(p)
                    self.param_widgets[p.key] = (p.kind, w)
                    form.addRow(QLabel(label), w)
            else:
                self.hint_lbl.setText("")

            old = self.form_container
            self.form_container = container
            self.form_group_layout.addWidget(container)
            if old is not None:
                old.setParent(None)
                old.deleteLater()
            self._update_preview()
        except Exception as e:
            self.preview.setText("")
            self.preview.setPlaceholderText(f"Error al armar el formulario: {e}")

    # ── reading values ──
    def _widget_value(self, kind, w):
        if kind in ("player", "item", "effect", "enchant", "entity"):
            return w.value()
        if kind == "enum":
            return w.currentData()
        if kind == "bool":
            return "true" if w.isChecked() else ""
        return w.text().strip()  # int / text

    def val(self, key):
        pair = self.param_widgets.get(key)
        if not pair:
            return ""
        kind, w = pair
        try:
            return self._widget_value(kind, w) or ""
        except RuntimeError:
            return ""  # widget deleted mid-rebuild

    def checked(self, key):
        pair = self.param_widgets.get(key)
        if not pair:
            return False
        _, w = pair
        try:
            return isinstance(w, QCheckBox) and w.isChecked()
        except RuntimeError:
            return False

    def build_command(self):
        spec = self._current_spec()
        if not spec:
            return None, "Selecciona un comando."
        if spec.build:
            return spec.build(self)
        parts = [spec.name]
        for p in spec.params:
            if p.kind == "bool":
                continue  # booleans only used by custom builders
            value = self.val(p.key)
            if value == "":
                if p.optional:
                    break  # stop at first empty optional to keep arguments positional
                return None, f"Falta: {p.label}"
            parts.append(value)
        return " ".join(parts), None

    def _update_preview(self, *args):
        try:
            cmd, err = self.build_command()
        except Exception as e:
            self.preview.setText("")
            self.preview.setPlaceholderText(str(e))
            return
        if err:
            self.preview.setText("")
            self.preview.setPlaceholderText(err)
        else:
            self.preview.setText(cmd)

    def _refresh_players(self):
        for w in list(self.player_widgets):
            try:
                w.refresh(self.parent.connected_players)
            except RuntimeError:
                pass  # widget deleted between rebuilds

    # ── actions ──
    def copy(self):
        cmd, err = self.build_command()
        if err:
            QMessageBox.warning(self, "Comando incompleto", err)
            return
        QApplication.clipboard().setText(cmd)
        self.parent.statusBar().showMessage(f"Copiado: {cmd}", 3000)

    def send(self):
        cmd, err = self.build_command()
        if err:
            QMessageBox.warning(self, "Comando incompleto", err)
            return
        if not self.parent.send_console_command(cmd):
            QMessageBox.warning(self, "Servidor detenido",
                                "El servidor no está en ejecución. Inícialo desde la pestaña Consola.")
