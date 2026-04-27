"""
main_window.py
SceneProfiler — dockable Maya tool window.
Uses MayaQWidgetDockableMixin so it can be docked like a native panel.
"""

import os
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from PySide2 import QtWidgets, QtCore, QtGui

from core.runner   import run_all
from core.exporter import export_csv, export_html
from core.result   import DiagnosticResult
from ui.diagnostic_card import DiagnosticCard
from ui.styles import (
    MAIN_STYLE, BG_DARK, BG_MID, BG_PANEL, BG_HEADER,
    BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT
)

TOOL_NAME    = "SceneProfiler"
TOOL_VERSION = "1.0.0"


class SceneProfiler(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """
    Main tool window.
    Launch with: SceneProfiler().show(dockable=True)
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(f"Scene Profiler  v{TOOL_VERSION}")
        self.setObjectName(TOOL_NAME)
        self.setMinimumWidth(420)
        self.setMinimumHeight(300)
        self.setStyleSheet(MAIN_STYLE)

        self._results: list[DiagnosticResult] = []
        self._cards:   list[DiagnosticCard]   = []

        self._build_ui()
        self._refresh_scene_label()

    # ─────────────────────────────────────────────────────────── UI build
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── header bar ────────────────────────────────────────────────────────
        header = QtWidgets.QWidget()
        header.setStyleSheet(f"background:{BG_HEADER}; border-radius:4px;")
        header.setFixedHeight(44)
        hlay = QtWidgets.QHBoxLayout(header)
        hlay.setContentsMargins(10, 0, 10, 0)
        hlay.setSpacing(8)

        icon_label = QtWidgets.QLabel("🎬")
        icon_label.setStyleSheet("font-size:18px; background:transparent;")

        title_label = QtWidgets.QLabel("Scene Profiler")
        title_label.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:14px; font-weight:700; background:transparent;"
        )

        ver_label = QtWidgets.QLabel(f"v{TOOL_VERSION}")
        ver_label.setStyleSheet(f"color:{TEXT_SECONDARY}; font-size:10px; background:transparent;")

        hlay.addWidget(icon_label)
        hlay.addWidget(title_label)
        hlay.addWidget(ver_label)
        hlay.addStretch()
        root.addWidget(header)

        # ── scene path row ────────────────────────────────────────────────────
        scene_row = QtWidgets.QHBoxLayout()
        scene_row.setContentsMargins(2, 0, 2, 0)

        scene_icon = QtWidgets.QLabel("📄")
        scene_icon.setStyleSheet("background:transparent; font-size:11px;")

        self._scene_label = QtWidgets.QLabel("No scene open")
        self._scene_label.setObjectName("sceneLabel")
        self._scene_label.setStyleSheet(
            f"color:{TEXT_SECONDARY}; font-size:11px; background:transparent;"
        )
        self._scene_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )

        scene_row.addWidget(scene_icon)
        scene_row.addWidget(self._scene_label, 1)
        root.addLayout(scene_row)

        # ── action buttons ────────────────────────────────────────────────────
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(6)

        self._run_btn = QtWidgets.QPushButton("▶  Run Diagnostics")
        self._run_btn.setObjectName("runButton")
        self._run_btn.setFixedHeight(32)
        self._run_btn.clicked.connect(self._run_diagnostics)
        self._run_btn.setToolTip("Analyse the current Maya scene")

        self._export_btn = QtWidgets.QPushButton("Export  ▾")
        self._export_btn.setFixedHeight(32)
        self._export_btn.setEnabled(False)
        self._export_btn.setToolTip("Export results as CSV or HTML")

        export_menu = QtWidgets.QMenu(self)
        export_menu.setStyleSheet(f"""
            QMenu {{
                background: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                padding: 4px 0px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background: {ACCENT};
                color: #ffffff;
            }}
        """)
        export_menu.addAction("Export CSV",  self._on_export_csv)
        export_menu.addAction("Export HTML", self._on_export_html)
        self._export_btn.setMenu(export_menu)

        btn_row.addWidget(self._run_btn, 2)
        btn_row.addWidget(self._export_btn, 1)
        root.addLayout(btn_row)

        # ── progress bar ──────────────────────────────────────────────────────
        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(4)
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        self._progress_label = QtWidgets.QLabel("")
        self._progress_label.setStyleSheet(
            f"color:{TEXT_SECONDARY}; font-size:10px; background:transparent;"
        )
        self._progress_label.setAlignment(QtCore.Qt.AlignCenter)
        self._progress_label.setVisible(False)
        root.addWidget(self._progress_label)

        # ── separator ─────────────────────────────────────────────────────────
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet(f"color:{BORDER};")
        root.addWidget(sep)

        # ── summary pills ─────────────────────────────────────────────────────
        self._summary_row = QtWidgets.QHBoxLayout()
        self._summary_row.setContentsMargins(2, 0, 2, 0)
        self._err_pill  = self._make_pill("0 Errors",   "#e85454")
        self._warn_pill = self._make_pill("0 Warnings", "#e8a838")
        self._pass_pill = self._make_pill("0 Passed",   "#4caf76")
        for pill in (self._err_pill, self._warn_pill, self._pass_pill):
            self._summary_row.addWidget(pill)
        self._summary_row.addStretch()
        root.addLayout(self._summary_row)

        # ── scroll area for cards ─────────────────────────────────────────────
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._cards_container = QtWidgets.QWidget()
        self._cards_layout    = QtWidgets.QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 4, 0, 4)
        self._cards_layout.setSpacing(4)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_container)
        root.addWidget(scroll, 1)

        # ── status bar ────────────────────────────────────────────────────────
        self._status = QtWidgets.QLabel("Ready — open a scene and click Run Diagnostics")
        self._status.setStyleSheet(
            f"color:{TEXT_SECONDARY}; font-size:10px; padding:2px 4px; background:transparent;"
        )
        root.addWidget(self._status)

    # ─────────────────────────────────────────────────────────── helpers
    def _make_pill(self, text: str, colour: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet(
            f"background:{colour}22; color:{colour}; border:1px solid {colour}55;"
            f"border-radius:10px; padding:1px 10px; font-size:11px; font-weight:600;"
        )
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        return lbl

    def _refresh_scene_label(self):
        scene = cmds.file(query=True, sceneName=True)
        if scene:
            self._scene_label.setText(os.path.basename(scene))
            self._scene_label.setToolTip(scene)
        else:
            self._scene_label.setText("Unsaved scene")

    def _set_running(self, running: bool):
        self._run_btn.setEnabled(not running)
        self._export_btn.setEnabled(not running and bool(self._results))
        self._progress.setVisible(running)
        self._progress_label.setVisible(running)

    def _update_progress(self, pct: int, label: str):
        self._progress.setValue(pct)
        self._progress_label.setText(f"Running: {label}…")
        QtWidgets.QApplication.processEvents()

    def _update_pills(self):
        from core.result import Severity
        errors   = sum(r.error_count   for r in self._results)
        warnings = sum(r.warning_count for r in self._results)
        passed   = sum(1 for r in self._results if r.severity == Severity.PASS)
        self._err_pill.setText(f"{errors} Error{'s' if errors != 1 else ''}")
        self._warn_pill.setText(f"{warnings} Warning{'s' if warnings != 1 else ''}")
        self._pass_pill.setText(f"{passed} Passed")

    def _clear_cards(self):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

    # ─────────────────────────────────────────────────────────── run
    def _run_diagnostics(self):
        self._refresh_scene_label()
        self._set_running(True)
        self._status.setText("Running diagnostics…")
        self._clear_cards()

        try:
            self._results = run_all(progress_callback=self._update_progress)
        except Exception as exc:
            self._status.setText(f"Error: {exc}")
            self._set_running(False)
            return

        # populate cards
        stretch = self._cards_layout.takeAt(self._cards_layout.count() - 1)
        for result in self._results:
            card = DiagnosticCard(result)
            self._cards.append(card)
            self._cards_layout.addWidget(card)
        self._cards_layout.addStretch()

        self._update_pills()
        total_ms = sum(r.duration_ms for r in self._results)
        self._status.setText(
            f"✓ {len(self._results)} diagnostics completed in {total_ms:.0f} ms"
        )
        self._set_running(False)

    # ─────────────────────────────────────────────────────────── export
    def _on_export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        if path:
            out = export_csv(self._results, path)
            self._status.setText(f"CSV exported → {os.path.basename(out)}")

    def _on_export_html(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export HTML Report", "", "HTML Files (*.html)"
        )
        if path:
            out = export_html(self._results, path)
            self._status.setText(f"HTML report exported → {os.path.basename(out)}")
            # open in browser
            import webbrowser
            webbrowser.open(f"file://{out}")
