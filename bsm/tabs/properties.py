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


# ── Properties Tab ─────────────────────────────────────────────────────────────
# Schema from the official Bedrock dedicated server documentation. Each entry:
# key -> (kind, extra, tip). kind: bool | enum | int | float | text.
#   enum  -> extra = list of allowed values
#   int   -> extra = (min, max) or None
#   float -> extra = (min, max) or None
PROP_SCHEMA = {
    "server-name": ("text", None, "Nombre del servidor mostrado en la lista del juego (sin punto y coma)."),
    "gamemode": ("enum", ["survival", "creative", "adventure"], "Modo de juego por defecto."),
    "force-gamemode": ("bool", None, "Si es true, fuerza el modo de juego de server.properties aunque difiera del guardado en el mundo."),
    "difficulty": ("enum", ["peaceful", "easy", "normal", "hard"], "Dificultad del mundo."),
    "allow-cheats": ("bool", None, "Si es true, se pueden usar comandos/trucos."),
    "max-players": ("int", (1, None), "Número máximo de jugadores. Valores altos afectan el rendimiento."),
    "server-port": ("int", (1, 65535), "Puerto IPv4 (por defecto 19132)."),
    "server-portv6": ("int", (1, 65535), "Puerto IPv6 (por defecto 19133)."),
    "enable-lan-visibility": ("bool", None, "Responder a clientes que buscan servidores en la LAN."),
    "level-name": ("text", None, "Nombre del mundo a usar/generar. Cada mundo tiene su carpeta en /worlds."),
    "level-seed": ("text", None, "Semilla del mundo. Vacío = aleatoria. Solo al crear el mundo."),
    "online-mode": ("bool", None, "Si es true, todos deben autenticarse con Xbox Live. Recomendado si el servidor es público."),
    "allow-list": ("bool", None, "Si es true, solo los jugadores de allowlist.json pueden conectarse."),
    "enable-packet-rate-limiter": ("bool", None, "Activa el limitador de paquetes (packetlimitconfig.json)."),
    "view-distance": ("int", (6, None), "Distancia de vista máxima (mayor a 5). Valores altos afectan el rendimiento."),
    "player-idle-timeout": ("int", (0, None), "Minutos de inactividad antes de expulsar. 0 = nunca."),
    "max-threads": ("int", (0, None), "Máximo de hilos del servidor. 0 = los que pueda."),
    "tick-distance": ("int", (4, 12), "Chunks alrededor del jugador que se actualizan. Valores altos afectan el rendimiento."),
    "default-player-permission-level": ("enum", ["visitor", "member", "operator"], "Permiso de los jugadores nuevos al entrar por primera vez."),
    "texturepack-required": ("bool", None, "Fuerza al cliente a usar los texture packs del mundo."),
    "content-log-file-enabled": ("bool", None, "Registra errores de contenido en un archivo."),
    "compression-threshold": ("int", (0, 65535), "Tamaño mínimo de payload para comprimir."),
    "compression-algorithm": ("enum", ["zlib", "snappy"], "Algoritmo de compresión de red."),
    "server-authoritative-movement-strict": ("bool", None, "Movimiento más estricto del lado del servidor (afecta con alta latencia)."),
    "server-authoritative-dismount-strict": ("bool", None, "Posición de desmontaje más estricta del lado del servidor."),
    "server-authoritative-entity-interactions-strict": ("bool", None, "Interacciones entre entidades más estrictas del lado del servidor."),
    "player-position-acceptance-threshold": ("float", None, "Tolerancia de discrepancia de posición cliente/servidor (por defecto 0.5)."),
    "player-movement-action-direction-threshold": ("float", (-1.0, 1.0), "Diferencia permitida entre dirección de ataque y de vista (por defecto 0.85)."),
    "server-authoritative-block-breaking": ("bool", None, "El servidor valida el minado de bloques (no compatible con movimiento client-auth)."),
    "server-authoritative-block-breaking-pick-range-scalar": ("float", None, "Escala del rango de minado (por defecto 1.5)."),
    "chat-restriction": ("enum", ["None", "Dropped", "Disabled"], "Restricción del chat: None (libre), Dropped (se descarta), Disabled (oculto salvo operadores)."),
    "disable-player-interaction": ("bool", None, "Indica a los clientes que ignoren a otros jugadores al interactuar (no es autoritativo)."),
    "client-side-chunk-generation-enabled": ("bool", None, "Permite que el cliente genere chunks visuales fuera del rango de interacción."),
    "block-network-ids-are-hashes": ("bool", None, "Envía IDs de bloque como hashes estables."),
    "disable-persona": ("bool", None, "Uso interno."),
    "disable-custom-skins": ("bool", None, "Desactiva las skins personalizadas (no oficiales) de los jugadores."),
    "server-build-radius-ratio": ("text", None, "«Disabled» o un valor 0.0-1.0. Solo válido si client-side-chunk-generation está activo."),
}


class PropertiesTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.fields = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        top = QHBoxLayout()
        lbl = QLabel("server.properties")
        lbl.setObjectName("title")
        self.load_btn = QPushButton("↻  Descartar cambios")
        self.load_btn.setToolTip("Vuelve a leer server.properties del disco y descarta lo que hayas editado sin guardar.")
        self.save_btn = QPushButton("💾  Guardar cambios")
        self.save_btn.setObjectName("success")
        self.save_btn.setToolTip("Escribe tus cambios en server.properties.")
        self.load_btn.clicked.connect(self.load)
        self.save_btn.clicked.connect(self.save)
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.load_btn)
        top.addWidget(self.save_btn)
        layout.addLayout(top)
        hint = QLabel("Edita los valores y pulsa «Guardar cambios». Reinicia el servidor para que tomen efecto.")
        hint.setObjectName("subtitle")
        layout.addWidget(hint)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QWidget()
        self.form = QFormLayout(container)
        self.form.setSpacing(10)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.load()

    def load(self):
        path = self.parent.props_path()
        if not path or not os.path.exists(path):
            return
        while self.form.rowCount():
            self.form.removeRow(0)
        self.fields.clear()
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                spec = PROP_SCHEMA.get(key)
                tip = spec[2] if spec else ""
                widget = self._make_field(key, val, spec)
                label = QLabel(key)
                if tip:
                    label.setToolTip(tip)
                    widget.setToolTip(tip)
                self.fields[key] = widget
                self.form.addRow(label, widget)

    def _make_field(self, key, val, spec):
        kind = spec[0] if spec else None
        # Booleans (known or detected)
        if kind == "bool" or (kind is None and val in ("true", "false")):
            cb = QCheckBox()
            cb.setChecked(val == "true")
            return cb
        if kind == "enum":
            combo = QComboBox()
            opts = list(spec[1])
            if val not in opts:          # keep an unexpected current value
                opts.append(val)
            combo.addItems(opts)
            i = combo.findText(val)
            if i >= 0:
                combo.setCurrentIndex(i)
            return combo
        if kind in ("int", "float"):
            le = QLineEdit(val)
            rng = spec[1]
            if kind == "int":
                lo = rng[0] if rng and rng[0] is not None else -2_147_483_648
                hi = rng[1] if rng and rng[1] is not None else 2_147_483_647
                le.setValidator(QIntValidator(lo, hi, le))
            else:
                lo = rng[0] if rng and rng[0] is not None else -1e9
                hi = rng[1] if rng and rng[1] is not None else 1e9
                le.setValidator(QDoubleValidator(lo, hi, 4, le))
            return le
        return QLineEdit(val)

    def save(self):
        path = self.parent.props_path()
        if not path:
            QMessageBox.warning(self, "Error", "Primero selecciona la carpeta del servidor.")
            return
        lines = []
        if os.path.exists(path):
            with open(path) as f:
                lines = f.readlines()
        result = []
        for line in lines:
            s = line.strip()
            if s.startswith("#") or not s or "=" not in s:
                result.append(line)
                continue
            key = s.split("=")[0].strip()
            if key in self.fields:
                w = self.fields[key]
                val = ("true" if w.isChecked() else "false") if isinstance(w, QCheckBox) else (w.currentText() if isinstance(w, QComboBox) else w.text())
                result.append(f"{key}={val}\n")
            else:
                result.append(line)
        with open(path, "w") as f:
            f.writelines(result)
        QMessageBox.information(self, "Guardado", "server.properties guardado correctamente.")
