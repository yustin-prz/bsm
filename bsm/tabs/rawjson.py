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
from ..packs import PackInstaller


# ── Raw JSON Tab ───────────────────────────────────────────────────────────────
class RawJsonTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        lbl = QLabel("Editor JSON directo")
        lbl.setObjectName("title")
        layout.addWidget(lbl)
        sub = QLabel("Se actualiza solo al instalar o quitar packs. La referencia muestra a qué pack pertenece cada UUID.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.ref_labels = {}
        for kind, attr in [("behavior", "bp_editor"), ("resource", "rp_editor")]:
            fname = "world_behavior_packs.json" if kind == "behavior" else "world_resource_packs.json"
            group = QGroupBox(f"  {fname}")
            gl = QVBoxLayout(group)
            editor = QTextEdit()
            editor.setFont(QFont("Consolas", 11))
            setattr(self, attr, editor)
            load_btn = QPushButton("↻ Recargar")
            load_btn.setToolTip("Vuelve a leer el archivo del disco y descarta cambios sin guardar.")
            save_btn = QPushButton("💾 Guardar")
            save_btn.setToolTip("Escribe el contenido del editor en el archivo.")
            load_btn.clicked.connect(lambda _, k=kind: self.load_pack(k))
            save_btn.clicked.connect(lambda _, k=kind: self.save_pack(k))
            btns = QHBoxLayout()
            btns.addWidget(load_btn)
            btns.addWidget(save_btn)
            gl.addLayout(btns)
            gl.addWidget(editor)
            ref = QLabel("")
            ref.setWordWrap(True)
            ref.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding: 4px;")
            self.ref_labels[kind] = ref
            ref_group = QGroupBox("  Referencia (UUID → nombre)")
            rl = QVBoxLayout(ref_group)
            rl.addWidget(ref)
            gl.addWidget(ref_group)
            splitter.addWidget(group)
        layout.addWidget(splitter)
        self.refresh_all()

    def refresh_all(self):
        """Reload both editors and rebuild the UUID→name reference."""
        self.load_pack("behavior")
        self.load_pack("resource")
        self._update_references()

    def _update_references(self):
        if not self.parent.server_dir:
            return
        world = self.parent.world_path()
        installer = PackInstaller(self.parent.server_dir, world or "")
        scan = installer.scan_installed()
        for kind in ("behavior", "resource"):
            path = self._pack_path(kind)
            lines = []
            if path and os.path.exists(path):
                try:
                    with open(path) as f:
                        for e in json.load(f):
                            u = e.get("pack_id", "")
                            info = scan.get(u)
                            name = info["name"] if info else "(no encontrado en disco)"
                            lines.append(f"• {name}\n   {u}")
                except Exception:
                    pass
            self.ref_labels[kind].setText("\n".join(lines) if lines else "(vacío)")

    def _pack_path(self, kind):
        world = self.parent.world_path()
        if not world: return None
        fname = "world_behavior_packs.json" if kind == "behavior" else "world_resource_packs.json"
        return os.path.join(world, fname)

    def load_pack(self, kind):
        path = self._pack_path(kind)
        editor = self.bp_editor if kind == "behavior" else self.rp_editor
        if not path or not os.path.exists(path):
            editor.clear()
            editor.setPlaceholderText("Aún no existe este archivo (se crea al instalar un pack).")
            return
        with open(path) as f:
            editor.setText(f.read())

    def save_pack(self, kind):
        path = self._pack_path(kind)
        if not path:
            QMessageBox.warning(self, "Error", "Primero selecciona la carpeta del servidor.")
            return
        editor = self.bp_editor if kind == "behavior" else self.rp_editor
        try:
            data = json.loads(editor.toPlainText())
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Guardado", f"Archivo guardado correctamente.")
            self._update_references()
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON inválido", str(e))
