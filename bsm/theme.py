# ── Theme ──────────────────────────────────────────────────────────────────────
BG       = "#1a1a2e"
PANEL    = "#16213e"
ACCENT   = "#00d4aa"
ACCENT2  = "#0f3460"
TEXT     = "#e0e0e0"
TEXT_DIM = "#888888"
RED      = "#e74c3c"
GREEN    = "#2ecc71"
YELLOW   = "#f39c12"
BORDER   = "#0f3460"

STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {PANEL};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {BG};
    color: {TEXT_DIM};
    padding: 8px 20px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {PANEL};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QPushButton {{
    background-color: {ACCENT2};
    color: {TEXT};
    border: 1px solid {ACCENT};
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {ACCENT}; color: #000; }}
QPushButton:disabled {{ background-color: #2a2a3e; color: {TEXT_DIM}; border-color: #333; }}
QPushButton#danger {{ border-color: {RED}; color: {RED}; }}
QPushButton#danger:hover {{ background-color: {RED}; color: #fff; }}
QPushButton#success {{ border-color: {GREEN}; color: {GREEN}; }}
QPushButton#success:hover {{ background-color: {GREEN}; color: #000; }}
QPushButton#warn {{ border-color: {YELLOW}; color: {YELLOW}; }}
QPushButton#warn:hover {{ background-color: {YELLOW}; color: #000; }}
QTextEdit, QLineEdit {{
    background-color: #0d0d1a;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {ACCENT};
    selection-color: #000;
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: {ACCENT}; }}
QLabel {{ color: {TEXT}; }}
QLabel#title {{ color: {ACCENT}; font-size: 18px; font-weight: bold; }}
QLabel#subtitle {{ color: {TEXT_DIM}; font-size: 11px; }}
QLabel#section {{ color: {ACCENT}; font-weight: bold; font-size: 13px; padding: 4px 0; }}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    color: {ACCENT};
    font-weight: bold;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
QListWidget {{
    background-color: #0d0d1a;
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT};
}}
QListWidget::item {{ padding: 6px 8px; border-bottom: 1px solid #1a1a2e; }}
QListWidget::item:selected {{ background-color: {ACCENT2}; color: {ACCENT}; }}
QScrollBar:vertical {{
    background: {BG}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT2}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QComboBox {{
    background-color: #0d0d1a; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 4px; padding: 5px 10px;
}}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: #0d0d1a; color: {TEXT};
    selection-background-color: {ACCENT2};
}}
QCheckBox {{ color: {TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER}; border-radius: 3px; background: #0d0d1a;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QStatusBar {{ background: {PANEL}; color: {TEXT_DIM}; border-top: 1px solid {BORDER}; }}
QSplitter::handle {{ background: {BORDER}; }}
QProgressBar {{
    background: #0d0d1a; border: 1px solid {BORDER};
    border-radius: 4px; text-align: center; color: {TEXT};
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}
"""
