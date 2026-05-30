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
from ..packs import PackInstaller, read_pack_config


class PackConfigDialog(QDialog):
    """Shows a pack's subpacks (which CAN be forced server-side by baking them in)
    and its settings (which are chosen per-player on the client, shown for info)."""
    def __init__(self, packs_tab, pack_name, target, pack_dir):
        super().__init__(packs_tab)
        self.tab = packs_tab
        self.target = target          # {uuid, kind, folder}
        self.pack_dir = pack_dir
        self.setWindowTitle(f"Subpacks / Ajustes — {pack_name}")
        self.setMinimumSize(560, 520)
        self.setStyleSheet(STYLE)
        self._build(pack_name)

    def _build(self, pack_name):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        title = QLabel(f"⚙  {pack_name}")
        title.setObjectName("title")
        layout.addWidget(title)

        cfg = read_pack_config(self.pack_dir) or {"subpacks": [], "settings": []}
        installer = PackInstaller(self.tab.parent.server_dir, self.tab.parent.world_path() or "")
        has_bak = installer.has_backup(self.target["kind"], self.target["folder"])
        options, active = installer.subpack_state(self.target["kind"], self.target["folder"])

        # ── Subpacks (forceable) ──
        sp_group = QGroupBox("  Subpacks (variantes del pack)")
        spl = QVBoxLayout(sp_group)
        if options:
            hint = QLabel("Elige una variante y fíjala para TODOS los jugadores del servidor.\n"
                          "Nota: Bedrock no guarda el subpack en el .json; se aplica directamente "
                          "a los archivos del pack y se sube su versión. Se hace copia (.bak) para revertir.")
            hint.setObjectName("subtitle")
            hint.setWordWrap(True)
            spl.addWidget(hint)
            if active:
                act_name = next((o["name"] for o in options if o["folder"] == active), active)
                cur = QLabel(f"✅  Subpack activo ahora: {act_name}")
                cur.setStyleSheet(f"color: {GREEN}; font-weight: bold;")
                cur.setWordWrap(True)
                spl.addWidget(cur)
            self.sp_buttons = []
            for sp in options:
                rb = QCheckBox(sp["name"])        # checkboxes acting as exclusive radios
                if sp["folder"] == active:
                    rb.setChecked(True)
                rb.clicked.connect(lambda _ck, b=rb: self._exclusive(b))
                self.sp_buttons.append((rb, sp))
                spl.addWidget(rb)
            force_btn = QPushButton("✅  Aplicar el subpack seleccionado para todos")
            force_btn.setObjectName("success")
            force_btn.clicked.connect(self._force)
            spl.addWidget(force_btn)
        else:
            self.sp_buttons = []
            spl.addWidget(QLabel("Este pack no define subpacks."))
        if has_bak:
            restore_btn = QPushButton("↩  Restaurar pack original (.bak)")
            restore_btn.clicked.connect(self._restore)
            spl.addWidget(restore_btn)
        layout.addWidget(sp_group)

        # ── Settings (client-side, informational) ──
        st_group = QGroupBox("  Ajustes del pack")
        stl = QVBoxLayout(st_group)
        note = QLabel("ℹ Estos ajustes los elige cada jugador en su propio cliente "
                      "(el ícono de engranaje en «Recursos globales»). El servidor no puede "
                      "fijarlos; se muestran aquí como referencia.")
        note.setStyleSheet(f"color: {YELLOW};")
        note.setWordWrap(True)
        stl.addWidget(note)
        if cfg["settings"]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            inner = QWidget()
            il = QVBoxLayout(inner)
            il.setAlignment(Qt.AlignmentFlag.AlignTop)
            for s in cfg["settings"]:
                if s["type"] == "toggle":
                    txt = f"🔘  {s['label']}  —  por defecto: {'ON' if s['default'] else 'OFF'}"
                elif s["type"] == "dropdown":
                    opts = ", ".join(s["options"])
                    txt = f"▼  {s['label']}  —  por defecto: {s['default']}\n        Opciones: {opts}"
                else:
                    txt = f"—  {s['label']}  (por defecto: {s['default']})"
                lab = QLabel(txt)
                lab.setWordWrap(True)
                lab.setStyleSheet("padding: 4px 2px;")
                il.addWidget(lab)
            scroll.setWidget(inner)
            stl.addWidget(scroll)
        else:
            stl.addWidget(QLabel("Este pack no define ajustes."))
        layout.addWidget(st_group, 1)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)

    def _exclusive(self, chosen):
        for rb, _sp in self.sp_buttons:
            if rb is not chosen:
                rb.setChecked(False)
        chosen.setChecked(True)

    def _selected_subpack(self):
        for rb, sp in self.sp_buttons:
            if rb.isChecked():
                return sp
        return None

    def _force(self):
        sp = self._selected_subpack()
        if not sp:
            QMessageBox.information(self, "Nada seleccionado", "Elige un subpack primero.")
            return
        reply = QMessageBox.question(
            self, "Aplicar subpack",
            f"Se aplicará «{sp['name']}» para todos los jugadores.\n\n"
            "Importante: Bedrock no permite indicar el subpack en world_resource_packs.json, "
            "así que se aplica copiando sus archivos sobre el pack y subiendo su versión "
            "(se guarda copia .bak para revertir). En el .json solo cambiará la versión.\n\n"
            "Hazlo con el servidor apagado.\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        installer = PackInstaller(self.tab.parent.server_dir, self.tab.parent.world_path() or "")
        try:
            name = installer.force_subpack(self.target["kind"], self.target["folder"],
                                           sp["folder"], self.target.get("uuid"))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self.tab.reload_lists()
        self.tab.parent.raw_json_tab.refresh_all()
        QMessageBox.information(
            self, "Listo",
            f"«{name}» aplicado para todos.\n\n"
            "Reinicia el servidor; los jugadores verán una pequeña descarga por el cambio de versión.\n"
            "Puedes volver a abrir esta ventana para cambiar a otro subpack cuando quieras.")
        self.accept()

    def _restore(self):
        installer = PackInstaller(self.tab.parent.server_dir, self.tab.parent.world_path() or "")
        if installer.restore_pack(self.target["kind"], self.target["folder"]):
            QMessageBox.information(self, "Restaurado",
                                   "Se restauró el pack original (sin subpack fijado).")
            self.tab.reload_lists()
            self.accept()
        else:
            QMessageBox.warning(self, "Sin copia", "No hay copia de seguridad para restaurar.")


# ── Packs Manager Tab ──────────────────────────────────────────────────────────
class PacksTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        top = QHBoxLayout()
        lbl = QLabel("Gestión de Packs")
        lbl.setObjectName("title")
        install_btn = QPushButton("📦  Instalar addon / pack")
        install_btn.setObjectName("success")
        install_btn.clicked.connect(self.install_pack)
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(install_btn)
        layout.addLayout(top)

        sub = QLabel("Arrastra o selecciona archivos .mcaddon, .mcpack o .zip para instalarlos automáticamente.")
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        drop = QLabel("⬇  Arrastra un .mcaddon / .mcpack / .zip aquí")
        drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {ACCENT};
                border-radius: 8px;
                color: {TEXT_DIM};
                padding: 18px;
                font-size: 13px;
            }}
        """)
        drop.setAcceptDrops(True)
        drop.dragEnterEvent = self._drag_enter
        drop.dropEvent = self._drop
        layout.addWidget(drop)

        group = QGroupBox("  Contenido instalado")
        gl = QVBoxLayout(group)
        order_hint = QLabel("El orden define la prioridad: lo de arriba se aplica por encima de lo de abajo "
                            "(útil si dos resource packs chocan texturas). Usa ▲ ▼ para reordenar.")
        order_hint.setObjectName("subtitle")
        order_hint.setWordWrap(True)
        gl.addWidget(order_hint)
        self.list = QListWidget()
        self.list.setStyleSheet("QListWidget::item { padding: 8px 8px; }")
        gl.addWidget(self.list)
        btn_row = QHBoxLayout()
        up_btn = QPushButton("▲ Subir")
        up_btn.setToolTip("Sube el pack seleccionado (mayor prioridad).")
        up_btn.clicked.connect(lambda: self.move_selected(-1))
        down_btn = QPushButton("▼ Bajar")
        down_btn.setToolTip("Baja el pack seleccionado (menor prioridad).")
        down_btn.clicked.connect(lambda: self.move_selected(1))
        cfg_btn = QPushButton("⚙  Subpacks / Ajustes")
        cfg_btn.setToolTip("Ver subpacks y ajustes del pack, y forzar un subpack para todos.")
        cfg_btn.clicked.connect(self.open_config)
        remove_btn = QPushButton("🗑  Quitar (borra archivos)")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self.remove_selected)
        reload_btn = QPushButton("🔄  Recargar")
        reload_btn.clicked.connect(self.reload_lists)
        btn_row.addWidget(up_btn)
        btn_row.addWidget(down_btn)
        btn_row.addWidget(cfg_btn)
        btn_row.addStretch()
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(reload_btn)
        gl.addLayout(btn_row)
        layout.addWidget(group)

        self.reload_lists()

    def _drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".mcaddon", ".mcpack", ".zip")):
                self._do_install(path)

    def install_pack(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar addon o pack", "",
            "Packs de Minecraft (*.mcaddon *.mcpack *.zip);;Todos los archivos (*)"
        )
        for path in paths:
            self._do_install(path)

    def _do_install(self, path):
        if not self.parent.server_dir:
            QMessageBox.warning(self, "Error", "Primero selecciona la carpeta del servidor.")
            return
        world = self.parent.world_path()
        if not world:
            QMessageBox.warning(self, "Error", "No se pudo determinar la carpeta del mundo.\nVerifica que server.properties tenga level-name configurado.")
            return
        os.makedirs(world, exist_ok=True)
        installer = PackInstaller(self.parent.server_dir, world)
        try:
            results = installer.install(path)
            msg_lines = []
            for r in results:
                kind_label = "BP" if r["kind"] == "behavior" else "RP"
                status = "⚠ Ya estaba en el JSON" if r["already_present"] else "✅ Agregado"
                msg_lines.append(f"[{kind_label}] {r['name']}\n    {status}")
            QMessageBox.information(
                self, "Instalación completada",
                f"Archivo: {os.path.basename(path)}\n\n" + "\n\n".join(msg_lines)
            )
            self.reload_lists()
            self.parent.raw_json_tab.refresh_all()   # keep JSON tab in sync
        except Exception as e:
            QMessageBox.critical(self, "Error al instalar", str(e))

    def reload_lists(self):
        self.list.clear()
        world = self.parent.world_path()
        if not world:
            return
        installer = PackInstaller(self.parent.server_dir, world)

        # active packs per kind, preserving the order from the world JSONs
        order = {"behavior": [], "resource": []}
        for kind in ("behavior", "resource"):
            path = installer._world_json_path(kind)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        for e in json.load(f):
                            u = e.get("pack_id")
                            if u:
                                order[kind].append(u)
                except Exception:
                    pass
        active = {k: set(v) for k, v in order.items()}
        pos = {k: {u: i for i, u in enumerate(order[k])} for k in order}

        scan = installer.scan_installed()
        meta = installer._load_meta()
        covered = set()
        built = []   # (data, text)

        for g in meta.get("groups", []):
            active_packs = [p for p in g.get("packs", [])
                            if p.get("uuid") in active.get(p.get("kind"), set())]
            if not active_packs:
                continue
            kinds = {p["kind"] for p in active_packs}
            comp = " + ".join([t for t, k in (("BP", "behavior"), ("RP", "resource")) if k in kinds])
            is_addon = len(active_packs) >= 2 or len(kinds) >= 2
            name = g.get("name") or "(sin nombre)"
            if is_addon:
                text = f"  📦  {name}\n        Addon · {comp}"
            elif "behavior" in kinds:
                text = f"  🧩  {name}\n        Behavior pack (BP)"
            else:
                text = f"  🎨  {name}\n        Resource pack (RP)"
            data = {"name": name, "source": g.get("source"),
                    "packs": [{"uuid": p["uuid"], "kind": p["kind"], "folder": p.get("folder", "")}
                              for p in active_packs]}
            built.append((data, text))
            for p in active_packs:
                covered.add((p["kind"], p["uuid"]))

        for kind in ("behavior", "resource"):
            for u in order[kind]:
                if (kind, u) in covered:
                    continue
                info = scan.get(u)
                name = info["name"] if info else u
                folder = info["folder"] if info else ""
                text = (f"  🧩  {name}\n        Behavior pack (BP)" if kind == "behavior"
                        else f"  🎨  {name}\n        Resource pack (RP)")
                data = {"name": name, "source": None,
                        "packs": [{"uuid": u, "kind": kind, "folder": folder}]}
                built.append((data, text))

        # order entries by load order: resource position first, then behavior
        def order_key(data):
            rps = [pos["resource"].get(p["uuid"], 9999) for p in data["packs"] if p["kind"] == "resource"]
            bps = [pos["behavior"].get(p["uuid"], 9999) for p in data["packs"] if p["kind"] == "behavior"]
            if rps:
                return (0, min(rps))
            if bps:
                return (1, min(bps))
            return (2, 0)
        built.sort(key=lambda dt: order_key(dt[0]))

        for data, text in built:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.list.addItem(item)

        if self.list.count() == 0:
            self.list.addItem(QListWidgetItem("  (No hay packs activos en este mundo)"))

    def _persist_order(self):
        """Rewrite both world JSONs to match the current top-to-bottom list order."""
        world = self.parent.world_path()
        if not world:
            return
        installer = PackInstaller(self.parent.server_dir, world)
        versions = {}
        for kind in ("behavior", "resource"):
            path = installer._world_json_path(kind)
            if os.path.exists(path):
                try:
                    for e in json.load(open(path)):
                        versions[(kind, e.get("pack_id"))] = e.get("version", [0, 0, 0])
                except Exception:
                    pass
        new = {"behavior": [], "resource": []}
        for i in range(self.list.count()):
            data = self.list.item(i).data(Qt.ItemDataRole.UserRole)
            if not data:
                continue
            for p in data.get("packs", []):
                new[p["kind"]].append({"pack_id": p["uuid"],
                                       "version": versions.get((p["kind"], p["uuid"]), [0, 0, 0])})
        installer._save_world_json("behavior", new["behavior"])
        installer._save_world_json("resource", new["resource"])

    def move_selected(self, delta):
        row = self.list.currentRow()
        if row < 0:
            QMessageBox.information(self, "Nada seleccionado", "Selecciona un pack primero.")
            return
        new = row + delta
        if new < 0 or new >= self.list.count():
            return
        item = self.list.takeItem(row)
        self.list.insertItem(new, item)
        self.list.setCurrentRow(new)
        self._persist_order()
        self.parent.raw_json_tab.refresh_all()

    def open_config(self):
        items = self.list.selectedItems()
        if not items:
            QMessageBox.information(self, "Nada seleccionado", "Selecciona un pack primero.")
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if not data or not data.get("packs"):
            return
        # prefer the resource pack of the group (subpacks/settings usually live there)
        packs = data["packs"]
        target = next((p for p in packs if p["kind"] == "resource"), packs[0])
        root = "resource_packs" if target["kind"] == "resource" else "behavior_packs"
        pack_dir = os.path.join(self.parent.server_dir, root, target["folder"])
        if not os.path.isdir(pack_dir):
            QMessageBox.warning(self, "No encontrado",
                                "No se encontró la carpeta del pack en el servidor.")
            return
        dlg = PackConfigDialog(self, data.get("name", ""), target, pack_dir)
        dlg.exec()

    def remove_selected(self):
        items = self.list.selectedItems()
        if not items:
            QMessageBox.information(self, "Nada seleccionado", "Selecciona un pack de la lista primero.")
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        name = data.get("name", "")
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"Se quitará «{name}» de los JSON del mundo y se BORRARÁN sus archivos "
            f"de behavior_packs/ y resource_packs/.\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        world = self.parent.world_path()
        installer = PackInstaller(self.parent.server_dir, world)
        for p in data.get("packs", []):
            installer.remove(p["kind"], p["uuid"])
            installer.delete_pack_files(p["kind"], p.get("folder", ""))
        if data.get("source"):
            installer.remove_group_meta(data["source"])
        self.reload_lists()
        self.parent.raw_json_tab.refresh_all()   # keep JSON tab in sync
        QMessageBox.information(self, "Listo",
                               f"«{name}» eliminado de los JSON y del disco.")
