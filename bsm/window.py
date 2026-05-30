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

from .theme import *
from .server import ServerThread
from .tabs.console import ConsoleTab
from .tabs.monitor import MonitorTab
from .tabs.commands import CommandsTab
from .tabs.properties import PropertiesTab
from .tabs.allowlist import AllowlistTab
from .tabs.packs import PacksTab
from .tabs.rawjson import RawJsonTab
from .tabs.leveldat import LevelDatTab


# ── Main Window ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.server_dir = ""
        self.server_start_time = None
        self.connected_players = set()
        self.setWindowTitle("Bedrock Server Manager")
        self.setMinimumSize(1050, 700)
        self._build()
        self.setStyleSheet(STYLE)
        self._load_cfg()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("⛏  Bedrock Server Manager")
        title.setObjectName("title")
        self.path_lbl = QLabel("Sin servidor seleccionado")
        self.path_lbl.setObjectName("subtitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.path_lbl)
        main_layout.addLayout(header)

        self.tabs = QTabWidget()
        self.console_tab    = ConsoleTab(self)
        self.props_tab      = PropertiesTab(self)
        self.allowlist_tab  = AllowlistTab(self)
        self.packs_tab      = PacksTab(self)
        self.raw_json_tab   = RawJsonTab(self)
        self.leveldat_tab   = LevelDatTab(self)
        self.monitor_tab    = MonitorTab(self)
        self.commands_tab   = CommandsTab(self)
        self.tabs.addTab(self.console_tab,   "  🖥  Consola  ")
        self.tabs.addTab(self.monitor_tab,   "  📊  Monitor  ")
        self.tabs.addTab(self.commands_tab,  "  🎮  Comandos  ")
        self.tabs.addTab(self.props_tab,     "  ⚙  Propiedades  ")
        self.tabs.addTab(self.allowlist_tab, "  👥  Allowlist  ")
        self.tabs.addTab(self.packs_tab,     "  📦  Packs  ")
        self.tabs.addTab(self.raw_json_tab,  "  📝  JSON  ")
        self.tabs.addTab(self.leveldat_tab,  "  🧬  level.dat  ")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Listo")

    def _on_tab_changed(self, index):
        # Keep the data-driven tabs fresh when the user opens them.
        w = self.tabs.widget(index)
        if w is self.raw_json_tab:
            self.raw_json_tab.refresh_all()
        elif w is self.packs_tab:
            self.packs_tab.reload_lists()
        elif w is self.leveldat_tab:
            self.leveldat_tab.load()

    def _cfg_path(self):
        return os.path.join(os.path.expanduser("~"), ".bedrock_manager.json")

    def _load_cfg(self):
        cfg = self._cfg_path()
        if not os.path.exists(cfg): return
        try:
            with open(cfg) as f:
                data = json.load(f)
            self.server_dir = data.get("server_dir", "")
            if self.server_dir:
                self.path_lbl.setText(self.server_dir)
                self.statusBar().showMessage(f"Servidor: {self.server_dir}")
                self.props_tab.load()
                self.allowlist_tab.load()
                self.packs_tab.reload_lists()
                self.raw_json_tab.refresh_all()
        except Exception:
            pass

    def _save_cfg(self):
        with open(self._cfg_path(), "w") as f:
            json.dump({"server_dir": self.server_dir}, f)

    def props_path(self):
        return os.path.join(self.server_dir, "server.properties") if self.server_dir else None

    def allowlist_path(self):
        return os.path.join(self.server_dir, "allowlist.json") if self.server_dir else None

    def world_path(self):
        if not self.server_dir: return None
        props = self.props_path()
        level = "Bedrock level"
        if props and os.path.exists(props):
            with open(props) as f:
                for line in f:
                    if line.startswith("level-name="):
                        level = line.split("=", 1)[1].strip()
                        break
        return os.path.join(self.server_dir, "worlds", level)

    def select_server(self):
        path = QFileDialog.getOpenFileName(
            self, "Seleccionar bedrock_server.exe", "",
            "Ejecutable del servidor (bedrock_server.exe);;Todos los archivos (*)"
        )[0]
        if path:
            self.server_dir = os.path.dirname(path)
            self.path_lbl.setText(self.server_dir)
            self.statusBar().showMessage(f"Servidor: {self.server_dir}")
            self._save_cfg()
            self.props_tab.load()
            self.allowlist_tab.load()
            self.packs_tab.reload_lists()
            self.raw_json_tab.refresh_all()

    def start_server(self):
        if not self.server_dir:
            QMessageBox.warning(self, "Error", "Primero selecciona el archivo bedrock_server.exe.")
            return
        exe = os.path.join(self.server_dir, "bedrock_server.exe")
        if not os.path.exists(exe):
            QMessageBox.critical(self, "Error", f"No se encontró bedrock_server.exe en:\n{self.server_dir}")
            return
        self.console_tab.set_starting()           # instant feedback
        QApplication.processEvents()
        self.server_thread = ServerThread(exe)
        self.server_thread.output_received.connect(self.console_tab.append_line)
        self.server_thread.output_received.connect(self._track_players)
        self.server_thread.server_stopped.connect(self.on_server_stopped)
        self.server_start_time = time.time()
        self.connected_players = set()
        self.server_thread.start()
        self.console_tab.set_running(True)
        self.console_tab.append_line("▶ Iniciando servidor...", color=GREEN)
        self.statusBar().showMessage("Servidor en línea")

    def stop_server(self):
        if self.server_thread:
            self.console_tab.append_line("■ Deteniendo servidor...", color=YELLOW)
            self.server_thread.stop()

    def _track_players(self, line):
        """Parse server output to maintain the set of connected players."""
        if "Player connected:" in line:
            try:
                seg = line.split("Player connected:", 1)[1].strip()
                name = seg.split(",")[0].strip()
                if name:
                    self.connected_players.add(name)
            except Exception:
                pass
        elif "Player disconnected:" in line:
            try:
                seg = line.split("Player disconnected:", 1)[1].strip()
                name = seg.split(",")[0].strip()
                self.connected_players.discard(name)
            except Exception:
                pass

    def send_console_command(self, cmd):
        """Send a command to the running server and echo it. Returns True if sent."""
        cmd = (cmd or "").strip()
        if not cmd:
            return False
        if not (self.server_thread and self.server_thread.process
                and self.server_thread.process.poll() is None):
            return False
        self.server_thread.send_command(cmd)
        self.console_tab.append_line(f"> {cmd}", color=ACCENT)
        return True

    def on_server_stopped(self):
        self.console_tab.set_running(False)
        self.console_tab.append_line("■ Servidor detenido.", color=RED)
        self.statusBar().showMessage("Servidor detenido")
        self.server_thread = None
        self.server_start_time = None
        self.connected_players = set()

    def closeEvent(self, event):
        if self.server_thread:
            reply = QMessageBox.question(
                self, "Servidor activo",
                "El servidor está corriendo. ¿Detenerlo y salir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_server()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
