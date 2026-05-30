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


# ── Console Tab ────────────────────────────────────────────────────────────────
class ConsoleTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        status_row = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {RED}; font-size: 18px;")
        self.status_label = QLabel("Servidor detenido")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM}; font-weight: bold;")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: #060610;
                color: #c8ffc8;
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.console)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("▶  Iniciar servidor")
        self.start_btn.setObjectName("success")
        self.start_btn.clicked.connect(self.parent.start_server)
        self.stop_btn = QPushButton("■  Detener servidor")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.parent.stop_server)
        self.clear_btn = QPushButton("🗑  Limpiar")
        self.clear_btn.clicked.connect(self.console.clear)
        self.path_btn = QPushButton("📁  Seleccionar servidor")
        self.path_btn.clicked.connect(self.parent.select_server)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.clear_btn)
        controls.addStretch()
        controls.addWidget(self.path_btn)
        layout.addLayout(controls)

        cmd_row = QHBoxLayout()
        lbl = QLabel("Comando:")
        lbl.setStyleSheet(f"color: {ACCENT};")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Escribe un comando y presiona Enter...")
        self.cmd_input.returnPressed.connect(self.send_command)
        self.cmd_input.setEnabled(False)
        self.send_btn = QPushButton("Enviar")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_command)
        cmd_row.addWidget(lbl)
        cmd_row.addWidget(self.cmd_input)
        cmd_row.addWidget(self.send_btn)
        layout.addLayout(cmd_row)

    def send_command(self):
        cmd = self.cmd_input.text().strip()
        if cmd and self.parent.server_thread:
            self.parent.server_thread.send_command(cmd)
            self.append_line(f"> {cmd}", color=ACCENT)
            self.cmd_input.clear()

    def append_line(self, text, color=None):
        if color:
            c = color
        elif "ERROR" in text or "error" in text:
            c = "#ff6b6b"
        elif "WARN" in text or "warn" in text:
            c = YELLOW
        elif "Player connected" in text or "Player Spawned" in text:
            c = "#7efff5"
        elif text.startswith(">"):
            c = ACCENT
        else:
            c = "#c8ffc8"
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.console.append(f'<span style="color:{c};">{safe}</span>')
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def set_running(self, running):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.cmd_input.setEnabled(running)
        self.send_btn.setEnabled(running)
        if running:
            self.start_btn.setText("🟢  Servidor en ejecución")
            self.status_dot.setStyleSheet(f"color: {GREEN}; font-size: 18px;")
            self.status_label.setText("Servidor en línea")
            self.status_label.setStyleSheet(f"color: {GREEN}; font-weight: bold;")
        else:
            self.start_btn.setText("▶  Iniciar servidor")
            self.status_dot.setStyleSheet(f"color: {RED}; font-size: 18px;")
            self.status_label.setText("Servidor detenido")
            self.status_label.setStyleSheet(f"color: {TEXT_DIM}; font-weight: bold;")

    def set_starting(self):
        """Immediate visual feedback the moment the user clicks start."""
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳  Iniciando...")
