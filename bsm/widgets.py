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


# ── Monitor Tab ────────────────────────────────────────────────────────────────
class StatCard(QFrame):
    """A small card showing a label, a big value, and an optional progress bar."""
    def __init__(self, title, with_bar=False):
        super().__init__()
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: #0d0d1a;
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: bold; border: none;")
        self.value_lbl = QLabel("—")
        self.value_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 22px; font-weight: bold; border: none;")
        lay.addWidget(self.title_lbl)
        lay.addWidget(self.value_lbl)
        self.bar = None
        if with_bar:
            self.bar = QProgressBar()
            self.bar.setRange(0, 100)
            self.bar.setValue(0)
            self.bar.setTextVisible(False)
            self.bar.setFixedHeight(8)
            lay.addWidget(self.bar)

    def set_value(self, text, bar_pct=None, bar_color=None):
        self.value_lbl.setText(text)
        if self.bar is not None and bar_pct is not None:
            self.bar.setValue(int(max(0, min(100, bar_pct))))
            if bar_color:
                self.bar.setStyleSheet(
                    f"QProgressBar {{ background:#060610; border:1px solid {BORDER}; border-radius:4px; }}"
                    f"QProgressBar::chunk {{ background:{bar_color}; border-radius:3px; }}"
                )

    def set_dim(self):
        self.value_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 22px; font-weight: bold; border: none;")

    def set_accent(self):
        self.value_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 22px; font-weight: bold; border: none;")


class PickerCombo(QComboBox):
    """Editable combo with an indexed 'contains' search. value() returns the id,
    resolving loosely from a fragment of the friendly name OR the english id."""
    def __init__(self, options, placeholder="Buscar..."):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMaxVisibleItems(15)
        # Alphabetical order makes scanning the list much easier
        opts = sorted(options, key=lambda o: o[1].lower())
        self._index = []  # (label_lower, id_lower, id_short_lower, id)
        for value, label in opts:
            self.addItem(f"{label}  ·  {value}", value)
            vid = str(value).lower()
            short = vid.split(":", 1)[1] if ":" in vid else vid
            self._index.append((label.lower(), vid, short, value))
        self.setCurrentIndex(-1)
        self.lineEdit().setPlaceholderText(placeholder)
        comp = QCompleter([self.itemText(i) for i in range(self.count())], self)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(comp)

    def value(self):
        text = self.currentText().strip()
        idx = self.findText(text)          # exact "label · id" match
        if idx >= 0:
            return self.itemData(idx)
        low = text.lower()
        if not low:
            return ""
        for lab, vid, short, val in self._index:       # exact id / name
            if low in (vid, short, lab):
                return val
        for lab, vid, short, val in self._index:       # starts with
            if short.startswith(low) or lab.startswith(low):
                return val
        for lab, vid, short, val in self._index:       # contains
            if low in lab or low in vid:
                return val
        return text


class PlayerCombo(QComboBox):
    """Editable combo populated live with connected players + target selectors."""
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lineEdit().setPlaceholderText("Jugador o selector (@a, @p...)")
        self.refresh([])

    def refresh(self, players):
        current = self.currentText()
        self.blockSignals(True)
        self.clear()
        self.addItems(TARGET_SELECTORS)
        if players:
            self.insertSeparator(self.count())
            self.addItems(sorted(players))
        self.setEditText(current)
        self.blockSignals(False)

    def value(self):
        return self.currentText().strip()
