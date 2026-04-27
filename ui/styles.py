"""
styles.py
Maya-native colour palette applied via Qt stylesheet.
Colours are sampled from Maya 2024's dark theme so the tool
feels indistinguishable from a built-in panel.
"""

# ── Maya 2024 palette ────────────────────────────────────────────────────────
BG_DARK      = "#1e1e1e"
BG_MID       = "#2b2b2b"
BG_PANEL     = "#333333"
BG_HEADER    = "#3a3a3a"
BG_HOVER     = "#404040"
BG_SELECTED  = "#4a4a4a"

BORDER       = "#555555"
BORDER_LIGHT = "#666666"

TEXT_PRIMARY  = "#cccccc"
TEXT_SECONDARY= "#999999"
TEXT_DISABLED = "#666666"

ACCENT       = "#5285a6"     # Maya's blue accent

SEV_PASS     = "#4caf76"
SEV_WARNING  = "#e8a838"
SEV_ERROR    = "#e85454"
SEV_INFO     = "#5b9bd5"

BUTTON_BG    = "#4a4a4a"
BUTTON_HOVER = "#5a5a5a"
BUTTON_PRESS = "#3a3a3a"

# ── main stylesheet ──────────────────────────────────────────────────────────
MAIN_STYLE = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 12px;
}}

/* ── scroll area ── */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {BG_MID}; width: 8px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BG_PANEL}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── buttons ── */
QPushButton {{
    background-color: {BUTTON_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 14px;
    font-size: 12px;
}}
QPushButton:hover  {{ background-color: {BUTTON_HOVER}; border-color: {BORDER_LIGHT}; }}
QPushButton:pressed {{ background-color: {BUTTON_PRESS}; }}
QPushButton:disabled {{ color: {TEXT_DISABLED}; background-color: {BG_MID}; }}

/* run button — accent colour */
QPushButton#runButton {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: #ffffff;
    font-weight: 600;
    padding: 6px 20px;
}}
QPushButton#runButton:hover  {{ background-color: #5f96bb; }}
QPushButton#runButton:pressed {{ background-color: #3a6e8f; }}

/* ── labels ── */
QLabel {{ background: transparent; }}
QLabel#sceneLabel {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    padding: 2px 0;
}}

/* ── progress bar ── */
QProgressBar {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}

/* ── separator ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ── tool tip ── */
QToolTip {{
    background: {BG_HEADER};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    padding: 4px 8px;
    border-radius: 3px;
}}

/* ── combo box ── */
QComboBox {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 3px 8px;
    color: {TEXT_PRIMARY};
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background: {BG_PANEL};
    border: 1px solid {BORDER_LIGHT};
    selection-background-color: {BG_SELECTED};
}}
"""

# ── severity badge colours ────────────────────────────────────────────────────
SEVERITY_BADGE = {
    "pass":    f"background:{SEV_PASS};   color:#fff; border-radius:3px; padding:1px 8px; font-weight:700;",
    "warning": f"background:{SEV_WARNING};color:#fff; border-radius:3px; padding:1px 8px; font-weight:700;",
    "error":   f"background:{SEV_ERROR};  color:#fff; border-radius:3px; padding:1px 8px; font-weight:700;",
    "info":    f"background:{SEV_INFO};   color:#fff; border-radius:3px; padding:1px 8px; font-weight:700;",
}

SEVERITY_BORDER = {
    "pass":    SEV_PASS,
    "warning": SEV_WARNING,
    "error":   SEV_ERROR,
    "info":    SEV_INFO,
}
