"""
DiagnosticCard
A collapsible card widget that displays one DiagnosticResult.
If items have categories set, renders collapsible sub-sections per category
instead of a single flat table.
"""

from collections import OrderedDict
from ui.qt_shim import QtWidgets, QtCore, QtGui
from core.result import DiagnosticResult, Severity
from ui.styles import SEVERITY_BADGE, SEVERITY_BORDER, BG_MID, BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY

SEV_COLOURS = {
    Severity.PASS:    "#4caf76",
    Severity.WARNING: "#e8a838",
    Severity.ERROR:   "#e85454",
    Severity.INFO:    "#5b9bd5",
}

TABLE_STYLE = f"""
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
"""


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

        self._chevron = QtWidgets.QLabel("▶")
        self._chevron.setFixedWidth(14)
        self._chevron.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")

        self._badge = QtWidgets.QLabel()
        self._badge.setFixedWidth(80)
        self._badge.setAlignment(QtCore.Qt.AlignCenter)

        self._title = QtWidgets.QLabel(self._result.name)
        self._title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")

        self._summary = QtWidgets.QLabel(self._result.summary)
        self._summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self._summary.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self._duration = QtWidgets.QLabel(f"{self._result.duration_ms:.0f} ms")
        self._duration.setFixedWidth(50)
        self._duration.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        self._duration.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        header_layout.addWidget(self._chevron)
        header_layout.addWidget(self._badge)
        header_layout.addWidget(self._title)
        header_layout.addWidget(self._summary, 1)
        header_layout.addWidget(self._duration)

        # ── detail area (hidden by default) ──────────────────────────────────
        self._detail_widget = QtWidgets.QWidget()
        self._detail_widget.setVisible(False)
        self._detail_layout = QtWidgets.QVBoxLayout(self._detail_widget)
        self._detail_layout.setContentsMargins(10, 0, 10, 8)
        self._detail_layout.setSpacing(4)

        self._populate_detail()

        frame_layout.addWidget(self._header)
        frame_layout.addWidget(self._detail_widget)
        root.addWidget(self._frame)

        self._header.mousePressEvent = self._toggle

    # ─────────────────────────────────────────────────────── populate
    def _populate_detail(self):
        """Build either a grouped or flat view depending on whether items have categories."""
        # clear any existing content (for refresh)
        while self._detail_layout.count():
            child = self._detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = self._result.items
        has_categories = any(item.category for item in items)

        if has_categories:
            self._populate_grouped(items)
        else:
            self._detail_layout.addWidget(self._make_table(items))

    def _populate_grouped(self, items):
        """Group items by category and build a collapsible sub-section for each."""
        groups = OrderedDict()
        for item in items:
            key = item.category or "Other"
            groups.setdefault(key, []).append(item)

        for category, cat_items in groups.items():
            self._detail_layout.addWidget(self._make_sub_section(category, cat_items))

    def _make_sub_section(self, category: str, items: list) -> QtWidgets.QWidget:
        """A collapsible header + table for one category group."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # worst severity in this group
        worst = Severity.PASS
        for item in items:
            if item.severity == Severity.ERROR:
                worst = Severity.ERROR
                break
            if item.severity == Severity.WARNING:
                worst = Severity.WARNING

        # sub-header
        sub_header = QtWidgets.QWidget()
        sub_header.setFixedHeight(28)
        sub_header.setCursor(QtCore.Qt.PointingHandCursor)
        sub_header.setStyleSheet(
            f"background: {BG_PANEL}; border-radius: 3px;"
        )
        sh_layout = QtWidgets.QHBoxLayout(sub_header)
        sh_layout.setContentsMargins(8, 0, 8, 0)
        sh_layout.setSpacing(6)

        chevron = QtWidgets.QLabel("▶")
        chevron.setFixedWidth(12)
        chevron.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9px; background: transparent;")

        name_lbl = QtWidgets.QLabel(category)
        name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 600; background: transparent;")

        count_lbl = QtWidgets.QLabel(f"{len(items)} item{'s' if len(items) != 1 else ''}")
        count_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; background: transparent;")

        sev_badge = QtWidgets.QLabel(worst.value.upper())
        sev_badge.setFixedWidth(80)
        sev_badge.setAlignment(QtCore.Qt.AlignCenter)
        sev_badge.setStyleSheet(SEVERITY_BADGE[worst.value])

        sh_layout.addWidget(chevron)
        sh_layout.addWidget(name_lbl)
        sh_layout.addWidget(count_lbl)
        sh_layout.addStretch()
        sh_layout.addWidget(sev_badge)

        # table (collapsed by default)
        table = self._make_table(items)
        table.setVisible(False)

        layout.addWidget(sub_header)
        layout.addWidget(table)

        def _toggle(event, t=table, c=chevron):
            visible = not t.isVisible()
            t.setVisible(visible)
            c.setText("▼" if visible else "▶")

        sub_header.mousePressEvent = _toggle
        return container

    def _make_table(self, items: list) -> QtWidgets.QTableWidget:
        """Create a fully configured QTableWidget for the given items."""
        table = QtWidgets.QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Severity", "Message", "Node"])
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        table.setStyleSheet(TABLE_STYLE)
        table.setRowCount(len(items))

        for row, item in enumerate(items):
            colour = SEV_COLOURS.get(item.severity, TEXT_SECONDARY)

            sev_cell = QtWidgets.QTableWidgetItem(item.severity.value.upper())
            sev_cell.setForeground(QtGui.QColor(colour))

            msg_cell = QtWidgets.QTableWidgetItem(item.message)
            if item.detail:
                msg_cell.setToolTip(item.detail)

            node_cell = QtWidgets.QTableWidgetItem(item.node or "")
            node_cell.setForeground(QtGui.QColor(TEXT_SECONDARY))

            table.setItem(row, 0, sev_cell)
            table.setItem(row, 1, msg_cell)
            table.setItem(row, 2, node_cell)

        row_h = 28
        header_h = 34
        visible_rows = len(items) if items else 1
        table.setFixedHeight(header_h + visible_rows * row_h)
        return table

    # ─────────────────────────────────────────────────────── severity
    def _apply_severity(self):
        sev = self._result.severity.value
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
        self._populate_detail()
        self._apply_severity()
        if self._expanded:
            self._detail_widget.setVisible(True)
