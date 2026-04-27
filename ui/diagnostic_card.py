"""
DiagnosticCard
A collapsible card widget that displays one DiagnosticResult.
Matches Maya's panel aesthetic using the shared stylesheet.
"""

from PySide2 import QtWidgets, QtCore, QtGui
from core.result import DiagnosticResult, Severity
from ui.styles import SEVERITY_BADGE, SEVERITY_BORDER, BG_MID, BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY


class DiagnosticCard(QtWidgets.QWidget):
    def __init__(self, result: DiagnosticResult, parent=None):
        super().__init__(parent)
        self._result   = result
        self._expanded = False
        self._build_ui()
        self._apply_severity()

    # ─────────────────────────────────────────────────────── build
    def _build_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 2)
        root.setSpacing(0)

        # ── card frame ────────────────────────────────────────────────────────
        self._frame = QtWidgets.QFrame()
        self._frame.setObjectName("diagCard")
        frame_layout = QtWidgets.QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # ── header row ────────────────────────────────────────────────────────
        self._header = QtWidgets.QWidget()
        self._header.setCursor(QtCore.Qt.PointingHandCursor)
        self._header.setFixedHeight(36)
        header_layout = QtWidgets.QHBoxLayout(self._header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(8)

        # chevron
        self._chevron = QtWidgets.QLabel("▶")
        self._chevron.setFixedWidth(14)
        self._chevron.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")

        # severity badge
        self._badge = QtWidgets.QLabel()
        self._badge.setFixedWidth(80)
        self._badge.setAlignment(QtCore.Qt.AlignCenter)

        # title
        self._title = QtWidgets.QLabel(self._result.name)
        self._title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")

        # summary
        self._summary = QtWidgets.QLabel(self._result.summary)
        self._summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self._summary.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # duration
        self._duration = QtWidgets.QLabel(f"{self._result.duration_ms:.0f} ms")
        self._duration.setFixedWidth(50)
        self._duration.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        self._duration.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        header_layout.addWidget(self._chevron)
        header_layout.addWidget(self._badge)
        header_layout.addWidget(self._title)
        header_layout.addWidget(self._summary, 1)
        header_layout.addWidget(self._duration)

        # ── detail table (hidden by default) ─────────────────────────────────
        self._detail_widget = QtWidgets.QWidget()
        self._detail_widget.setVisible(False)
        detail_layout = QtWidgets.QVBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(10, 0, 10, 8)
        detail_layout.setSpacing(0)

        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Severity", "Message", "Node"])
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_MID};
                border: none;
                font-size: 11px;
                gridline-color: transparent;
            }}
            QTableWidget::item {{ padding: 4px 8px; border: none; }}
            QTableWidget::item:alternate {{ background: {BG_PANEL}; }}
            QHeaderView::section {{
                background: {BG_PANEL};
                color: {TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 4px 8px;
                font-weight: 600;
            }}
        """)

        self._populate_table()
        detail_layout.addWidget(self._table)

        frame_layout.addWidget(self._header)
        frame_layout.addWidget(self._detail_widget)
        root.addWidget(self._frame)

        # ── click to expand ───────────────────────────────────────────────────
        self._header.mousePressEvent = self._toggle

    # ─────────────────────────────────────────────────────── populate
    def _populate_table(self):
        SEV_COLOURS = {
            Severity.PASS:    "#4caf76",
            Severity.WARNING: "#e8a838",
            Severity.ERROR:   "#e85454",
            Severity.INFO:    "#5b9bd5",
        }
        items = self._result.items
        self._table.setRowCount(len(items))

        for row, item in enumerate(items):
            colour = SEV_COLOURS.get(item.severity, TEXT_SECONDARY)

            sev_cell = QtWidgets.QTableWidgetItem(item.severity.value.upper())
            sev_cell.setForeground(QtGui.QColor(colour))

            msg_cell = QtWidgets.QTableWidgetItem(item.message)
            if item.detail:
                msg_cell.setToolTip(item.detail)

            node_cell = QtWidgets.QTableWidgetItem(item.node or "")
            node_cell.setForeground(QtGui.QColor(TEXT_SECONDARY))

            self._table.setItem(row, 0, sev_cell)
            self._table.setItem(row, 1, msg_cell)
            self._table.setItem(row, 2, node_cell)

        # size table to show all rows without internal scrolling
        row_h = 28
        header_h = 34
        visible_rows = len(items) if items else 1
        self._table.setFixedHeight(header_h + visible_rows * row_h)

    # ─────────────────────────────────────────────────────── severity
    def _apply_severity(self):
        sev  = self._result.severity.value
        self._badge.setStyleSheet(SEVERITY_BADGE[sev])
        self._badge.setText(sev.upper())

        border_col = SEVERITY_BORDER[sev]
        self._frame.setStyleSheet(f"""
            QFrame#diagCard {{
                background: {BG_MID};
                border: 1px solid {BORDER};
                border-left: 3px solid {border_col};
                border-radius: 4px;
            }}
        """)

    # ─────────────────────────────────────────────────────── toggle
    def _toggle(self, _event):
        self._expanded = not self._expanded
        self._detail_widget.setVisible(self._expanded)
        self._chevron.setText("▼" if self._expanded else "▶")

    def refresh(self, result: DiagnosticResult):
        """Update card with fresh result data."""
        self._result = result
        self._title.setText(result.name)
        self._summary.setText(result.summary)
        self._duration.setText(f"{result.duration_ms:.0f} ms")
        self._populate_table()
        self._apply_severity()
        if self._expanded:
            self._detail_widget.setVisible(True)
