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


# ── Allowlist Tab ──────────────────────────────────────────────────────────────
class AllowlistTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        top = QHBoxLayout()
        lbl = QLabel("Lista de jugadores permitidos")
        lbl.setObjectName("title")
        reload_btn = QPushButton("🔄  Recargar")
        reload_btn.clicked.connect(self.load)
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(reload_btn)
        layout.addLayout(top)
        sub = QLabel("Solo los jugadores en esta lista pueden conectarse (si allow-list=true)")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)
        sub2 = QLabel("Tras guardar, aplica los cambios con el comando «allowlist reload» en la consola, o reinicia el servidor.")
        sub2.setObjectName("subtitle")
        layout.addWidget(sub2)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del jugador (Gamertag)...")
        self.name_input.returnPressed.connect(self.add_player)
        add_btn = QPushButton("➕  Agregar")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self.add_player)
        rem_btn = QPushButton("➖  Eliminar")
        rem_btn.setObjectName("danger")
        rem_btn.clicked.connect(self.remove_player)
        save_btn = QPushButton("💾  Guardar")
        save_btn.clicked.connect(self.save)
        row.addWidget(self.name_input)
        row.addWidget(add_btn)
        row.addWidget(rem_btn)
        row.addWidget(save_btn)
        layout.addLayout(row)
        self.load()

    def load(self):
        self.list_widget.clear()
        path = self.parent.allowlist_path()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for entry in data:
                item = QListWidgetItem(f"  👤  {entry.get('name','')}")
                item.setData(Qt.ItemDataRole.UserRole, entry)
                self.list_widget.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def add_player(self):
        name = self.name_input.text().strip()
        if not name: return
        item = QListWidgetItem(f"  👤  {name}")
        item.setData(Qt.ItemDataRole.UserRole, {"name": name, "xuid": "", "ignoresPlayerLimit": False})
        self.list_widget.addItem(item)
        self.name_input.clear()

    def remove_player(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def save(self):
        path = self.parent.allowlist_path()
        if not path:
            QMessageBox.warning(self, "Error", "Primero selecciona la carpeta del servidor.")
            return
        data = [self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.list_widget.count())]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        QMessageBox.information(self, "Guardado", "allowlist.json guardado.")
