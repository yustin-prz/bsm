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
from ..nbt import (
    TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE,
    TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY,
    TAG_NAMES, _INT_TYPES, _FLOAT_TYPES, _CONTAINER_TYPES, _ARRAY_TYPES,
    NbtTag, load_level_dat, save_level_dat, comp_get, comp_set_byte,
)


# ── level.dat Editor Tab ─────────────────────────────────────────────────────────
# Common Bedrock experiment toggles. Availability depends on the game version;
# any extra byte toggles already present in the world are also shown automatically.
KNOWN_EXPERIMENTS = [
    ("gametest", "Beta APIs (GameTest / scripting)"),
    ("data_driven_items", "Holiday Creator Features"),
    ("data_driven_biomes", "Biomas personalizados (data-driven)"),
    ("upcoming_creator_features", "Próximas funciones de creador"),
    ("experimental_molang_features", "Funciones Molang experimentales"),
    ("cameras", "Cámaras experimentales"),
    ("villager_trades_rebalance", "Reequilibrio de comercio de aldeanos"),
    ("jigsaw_structures", "Estructuras Jigsaw"),
]
_EXP_BOOKKEEPING = ("experiments_ever_used", "saved_with_toggled_experiments")


class LevelDatTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.version = None
        self.root_name = ""
        self.root = None
        self.exp_checks = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        top = QHBoxLayout()
        lbl = QLabel("Editor de level.dat (NBT)")
        lbl.setObjectName("title")
        self.load_btn = QPushButton("↻  Cargar")
        self.load_btn.setToolTip("Lee level.dat del mundo actual y descarta cambios sin guardar.")
        self.load_btn.clicked.connect(self.load)
        self.save_btn = QPushButton("💾  Guardar (crea copia .bak)")
        self.save_btn.setObjectName("success")
        self.save_btn.setToolTip("Guarda los cambios. Antes hace una copia de seguridad level.dat.bak.")
        self.save_btn.clicked.connect(self.save)
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.load_btn)
        top.addWidget(self.save_btn)
        layout.addLayout(top)

        warn = QLabel("⚠ Detén el servidor antes de editar: si está encendido, sobrescribirá tus cambios al cerrarse.")
        warn.setStyleSheet(f"color: {YELLOW};")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Experiments panel
        exp_group = QGroupBox("  Experimentos (activar/desactivar)")
        exp_outer = QVBoxLayout(exp_group)
        exp_hint = QLabel("Marca para activar. Las opciones disponibles dependen de tu versión de Minecraft.")
        exp_hint.setObjectName("subtitle")
        exp_hint.setWordWrap(True)
        exp_outer.addWidget(exp_hint)
        exp_scroll = QScrollArea()
        exp_scroll.setWidgetResizable(True)
        exp_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.exp_container = QWidget()
        self.exp_layout = QVBoxLayout(self.exp_container)
        self.exp_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        exp_scroll.setWidget(self.exp_container)
        exp_outer.addWidget(exp_scroll)
        splitter.addWidget(exp_group)

        # Full NBT tree
        tree_group = QGroupBox("  Árbol NBT completo")
        tl = QVBoxLayout(tree_group)
        tl.addWidget(QLabel("Doble clic en un valor para editarlo · clic derecho para más opciones."))
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Etiqueta", "Valor"])
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_menu)
        tl.addWidget(self.tree)
        splitter.addWidget(tree_group)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)

        self._set_enabled(False)

    def _set_enabled(self, on):
        self.save_btn.setEnabled(on)
        self.tree.setEnabled(on)
        self.exp_container.setEnabled(on)

    def _dat_path(self):
        world = self.parent.world_path()
        if not world:
            return None
        return os.path.join(world, "level.dat")

    def load(self):
        path = self._dat_path()
        self.tree.clear()
        self._clear_experiments()
        if not path or not os.path.exists(path):
            self._set_enabled(False)
            self.tree.addTopLevelItem(QTreeWidgetItem(
                ["(no se encontró level.dat)", "Selecciona el servidor y un mundo válido"]))
            return
        try:
            self.version, self.root_name, self.root = load_level_dat(path)
        except Exception as e:
            self._set_enabled(False)
            QMessageBox.critical(self, "Error al leer level.dat", str(e))
            return
        self._set_enabled(True)
        self._populate_experiments()
        self._populate_tree()

    # ── experiments ──
    def _clear_experiments(self):
        self.exp_checks = {}
        while self.exp_layout.count():
            item = self.exp_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _populate_experiments(self):
        self._clear_experiments()
        exp = comp_get(self.root, "experiments") if self.root else None
        present = {}
        if exp and exp.type == TAG_COMPOUND:
            for n, tag in exp.value:
                if tag.type == TAG_BYTE and n not in _EXP_BOOKKEEPING:
                    present[n] = tag.value
        # known toggles first, then any extra ones already in the world
        keys = [k for k, _ in KNOWN_EXPERIMENTS]
        labels = dict(KNOWN_EXPERIMENTS)
        for k in present:
            if k not in keys:
                keys.append(k)
                labels[k] = k
        for k in keys:
            cb = QCheckBox(labels.get(k, k))
            cb.setChecked(bool(present.get(k, 0)))
            self.exp_layout.addWidget(cb)
            self.exp_checks[k] = cb

    def _apply_experiments(self):
        exp = comp_get(self.root, "experiments")
        if exp is None or exp.type != TAG_COMPOUND:
            exp = NbtTag(TAG_COMPOUND, [])
            self.root.value.append(["experiments", exp])
        any_on = False
        for k, cb in self.exp_checks.items():
            on = cb.isChecked()
            any_on = any_on or on
            comp_set_byte(exp, k, on)
        # Minecraft sets these bookkeeping flags when experiments are toggled
        comp_set_byte(exp, "experiments_ever_used", any_on)
        comp_set_byte(exp, "saved_with_toggled_experiments", any_on)

    # ── tree ──
    def _value_summary(self, tag):
        if tag.type == TAG_COMPOUND:
            return f"({len(tag.value)} etiquetas)"
        if tag.type == TAG_LIST:
            return f"({len(tag.value[1])} elementos)"
        if tag.type in _ARRAY_TYPES:
            return f"[{len(tag.value)} valores]"
        return str(tag.value)

    def _add_tree_node(self, parent_item, name, tag, parent_comp):
        label = f"{name}  ·  {TAG_NAMES.get(tag.type, '?')}"
        item = QTreeWidgetItem([label, self._value_summary(tag)])
        # store (parent_compound_or_None, name, tag) for editing
        item.setData(0, Qt.ItemDataRole.UserRole, (parent_comp, name, tag))
        if parent_item is None:
            self.tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        if tag.type == TAG_COMPOUND:
            for cn, ctag in tag.value:
                self._add_tree_node(item, cn, ctag, tag)
        elif tag.type == TAG_LIST:
            et, items = tag.value
            for idx, it in enumerate(items):
                self._add_tree_node(item, f"[{idx}]", it, None)  # list items: not individually deletable
        return item

    def _populate_tree(self):
        self.tree.clear()
        root_item = self._add_tree_node(None, self.root_name or "level.dat", self.root, None)
        root_item.setExpanded(True)

    def _coerce(self, t, text):
        text = text.strip()
        if t in _INT_TYPES:
            return int(text)
        if t in _FLOAT_TYPES:
            return float(text)
        if t == TAG_STRING:
            return text
        raise ValueError("Este tipo no se puede editar directamente.")

    def _on_double_click(self, item, _col):
        self._edit_item(item)

    def _edit_item(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        _parent, name, tag = data
        if tag.type in _CONTAINER_TYPES or tag.type in _ARRAY_TYPES:
            QMessageBox.information(self, "No editable",
                                    "Solo se editan valores simples (números y texto).\n"
                                    "Expande este nodo para ver/editar sus elementos.")
            return
        text, ok = QInputDialog.getText(
            self, f"Editar «{name}»",
            f"Nuevo valor ({TAG_NAMES.get(tag.type)}):", text=str(tag.value))
        if not ok:
            return
        try:
            tag.value = self._coerce(tag.type, text)
        except Exception:
            QMessageBox.warning(self, "Valor inválido",
                                f"«{text}» no es válido para el tipo {TAG_NAMES.get(tag.type)}.")
            return
        item.setText(1, self._value_summary(tag))

    def _show_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        parent_comp, name, tag = data
        menu = QMenu(self)
        if tag.type not in _CONTAINER_TYPES and tag.type not in _ARRAY_TYPES:
            act_edit = menu.addAction("✏  Editar valor")
            act_edit.triggered.connect(lambda: self._edit_item(item))
        if tag.type == TAG_COMPOUND:
            act_add = menu.addAction("➕  Añadir etiqueta…")
            act_add.triggered.connect(lambda: self._add_tag(tag))
        if parent_comp is not None:
            act_del = menu.addAction("🗑  Eliminar etiqueta")
            act_del.triggered.connect(lambda: self._delete_tag(parent_comp, name))
        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _add_tag(self, comp):
        type_labels = ["Byte", "Short", "Int", "Long", "Float", "Double", "String", "Compound"]
        type_map = {"Byte": TAG_BYTE, "Short": TAG_SHORT, "Int": TAG_INT, "Long": TAG_LONG,
                    "Float": TAG_FLOAT, "Double": TAG_DOUBLE, "String": TAG_STRING,
                    "Compound": TAG_COMPOUND}
        tname, ok = QInputDialog.getItem(self, "Añadir etiqueta", "Tipo:", type_labels, 0, False)
        if not ok:
            return
        key, ok = QInputDialog.getText(self, "Añadir etiqueta", "Nombre de la etiqueta:")
        if not ok or not key.strip():
            return
        key = key.strip()
        t = type_map[tname]
        if t == TAG_COMPOUND:
            comp.value.append([key, NbtTag(TAG_COMPOUND, [])])
        else:
            val, ok = QInputDialog.getText(self, "Añadir etiqueta", f"Valor ({tname}):")
            if not ok:
                return
            try:
                value = self._coerce(t, val) if t != TAG_STRING else val
            except Exception:
                QMessageBox.warning(self, "Valor inválido", "El valor no es válido para ese tipo.")
                return
            comp.value.append([key, NbtTag(t, value)])
        self._populate_tree()

    def _delete_tag(self, comp, name):
        comp.value = [e for e in comp.value if e[0] != name]
        self._populate_tree()

    # ── save ──
    def save(self):
        path = self._dat_path()
        if not path or self.root is None:
            QMessageBox.warning(self, "Error", "No hay un level.dat cargado.")
            return
        running = bool(self.parent.server_thread and
                       self.parent.server_thread.process and
                       self.parent.server_thread.process.poll() is None)
        if running:
            reply = QMessageBox.question(
                self, "Servidor encendido",
                "El servidor está corriendo y sobrescribirá level.dat al cerrarse, "
                "perdiendo estos cambios.\n\n¿Guardar de todas formas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._apply_experiments()
        try:
            if os.path.exists(path):
                shutil.copy2(path, path + ".bak")
            save_level_dat(path, self.version, self.root_name, self.root)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))
            return
        self._populate_tree()
        QMessageBox.information(
            self, "Guardado",
            "level.dat guardado.\nSe creó una copia de seguridad: level.dat.bak\n\n"
            "Recuerda reiniciar el servidor para aplicar los cambios.")
