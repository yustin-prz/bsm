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
from ..widgets import StatCard


class MonitorTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._proc = None          # cached psutil.Process
        self._proc_pid = None      # pid the cache was built for
        self._rendered_players = None   # last player list drawn (avoids wiping selection)
        self._build()
        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        top = QHBoxLayout()
        lbl = QLabel("Monitor del servidor")
        lbl.setObjectName("title")
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {RED}; font-size: 18px;")
        self.status_text = QLabel("Detenido")
        self.status_text.setStyleSheet(f"color: {TEXT_DIM}; font-weight: bold;")
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.status_dot)
        top.addWidget(self.status_text)
        layout.addLayout(top)

        sub = QLabel("Uso de recursos del proceso bedrock_server en tiempo real.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        if psutil is None:
            warn = QLabel("⚠  El módulo 'psutil' no está instalado. CPU y RAM no estarán disponibles.\n"
                          "    Instálalo con:  pip install psutil")
            warn.setStyleSheet(f"color: {YELLOW}; padding: 6px;")
            layout.addWidget(warn)

        # Stat cards row
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.cpu_card = StatCard("CPU", with_bar=True)
        self.ram_card = StatCard("MEMORIA (RAM)", with_bar=True)
        self.uptime_card = StatCard("TIEMPO ACTIVO")
        self.players_card = StatCard("JUGADORES")
        cards.addWidget(self.cpu_card)
        cards.addWidget(self.ram_card)
        cards.addWidget(self.uptime_card)
        cards.addWidget(self.players_card)
        layout.addLayout(cards)

        # Connected players list
        players_group = QGroupBox("  Jugadores conectados")
        pg = QVBoxLayout(players_group)
        self.players_list = QListWidget()
        pg.addWidget(self.players_list)
        kick_btn = QPushButton("🚪  Expulsar seleccionado")
        kick_btn.setObjectName("danger")
        kick_btn.clicked.connect(self.kick_selected)
        pg.addWidget(kick_btn)
        layout.addWidget(players_group)

    # ── data helpers ──
    def _get_process(self):
        """Return a live psutil.Process for the server, or None."""
        if psutil is None:
            return None
        thread = self.parent.server_thread
        if not thread or not thread.process or thread.process.poll() is not None:
            self._proc = None
            self._proc_pid = None
            return None
        pid = thread.process.pid
        if self._proc is None or self._proc_pid != pid:
            try:
                self._proc = psutil.Process(pid)
                self._proc_pid = pid
                self._proc.cpu_percent(None)  # prime the first reading
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._proc = None
                self._proc_pid = None
        return self._proc

    @staticmethod
    def _fmt_uptime(seconds):
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h {m:02d}m {s:02d}s"
        if m:
            return f"{m}m {s:02d}s"
        return f"{s}s"

    def kick_selected(self):
        items = self.players_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Nada seleccionado",
                                    "Selecciona un jugador de la lista primero.")
            return
        name = items[0].data(Qt.ItemDataRole.UserRole)
        if not self.parent.send_console_command(f"kick {name}"):
            QMessageBox.warning(self, "Servidor detenido",
                                "El servidor no está en ejecución.")

    def refresh(self):
        running = bool(self.parent.server_thread and
                       self.parent.server_thread.process and
                       self.parent.server_thread.process.poll() is None)

        # Status indicator
        if running:
            self.status_dot.setStyleSheet(f"color: {GREEN}; font-size: 18px;")
            self.status_text.setText("En línea")
            self.status_text.setStyleSheet(f"color: {GREEN}; font-weight: bold;")
        else:
            self.status_dot.setStyleSheet(f"color: {RED}; font-size: 18px;")
            self.status_text.setText("Detenido")
            self.status_text.setStyleSheet(f"color: {TEXT_DIM}; font-weight: bold;")

        # Players (works regardless of psutil)
        players = sorted(self.parent.connected_players) if running else []
        self.players_card.set_value(str(len(players)) if running else "—")
        # Only rebuild the list when the set actually changed, so the user's
        # selection isn't wiped on every refresh tick.
        if players != self._rendered_players:
            previously = {i.data(Qt.ItemDataRole.UserRole)
                          for i in self.players_list.selectedItems()}
            self.players_list.clear()
            for name in players:
                item = QListWidgetItem(f"  👤  {name}")
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.players_list.addItem(item)
                if name in previously:
                    item.setSelected(True)
            self._rendered_players = players

        # Uptime
        if running and self.parent.server_start_time:
            self.uptime_card.set_value(self._fmt_uptime(time.time() - self.parent.server_start_time))
        else:
            self.uptime_card.set_value("—")

        # CPU + RAM
        proc = self._get_process()
        if proc is None:
            for card in (self.cpu_card, self.ram_card):
                card.set_value("—")
                card.set_dim()
                if card.bar is not None:
                    card.bar.setValue(0)
            return

        try:
            cores = psutil.cpu_count() or 1
            cpu_raw = proc.cpu_percent(None)          # may exceed 100 on multicore
            cpu_norm = cpu_raw / cores                # share of whole machine
            self.cpu_card.set_accent()
            self.cpu_card.set_value(
                f"{cpu_norm:.0f}%",
                bar_pct=cpu_norm,
                bar_color=GREEN if cpu_norm < 60 else (YELLOW if cpu_norm < 85 else RED),
            )

            mem = proc.memory_info().rss / (1024 * 1024)   # MB
            mem_pct = proc.memory_percent()
            self.ram_card.set_accent()
            self.ram_card.set_value(
                f"{mem:.0f} MB",
                bar_pct=mem_pct,
                bar_color=GREEN if mem_pct < 60 else (YELLOW if mem_pct < 85 else RED),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._proc = None
            self._proc_pid = None
            for card in (self.cpu_card, self.ram_card):
                card.set_value("—")
                card.set_dim()
