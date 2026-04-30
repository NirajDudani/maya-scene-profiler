"""
Shared result types used across all diagnostics.
Every diagnostic returns a DiagnosticResult containing a list of DiagnosticItems.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    PASS    = "pass"
    WARNING = "warning"
    ERROR   = "error"
    INFO    = "info"


@dataclass
class DiagnosticItem:
    """A single finding within a diagnostic check."""
    severity: Severity
    message: str
    detail: Optional[str] = None      # extra context shown when card is expanded
    node: Optional[str] = None        # Maya node name, if applicable
    category: Optional[str] = None    # optional grouping label for subcategory display


@dataclass
class DiagnosticResult:
    """Full result returned by one diagnostic module."""
    name: str                                      # display name, e.g. "Texture Audit"
    items: List[DiagnosticItem] = field(default_factory=list)
    summary: str = ""                              # one-line summary shown on collapsed card
    duration_ms: float = 0.0                       # how long the check took

    # ------------------------------------------------------------------ helpers
    @property
    def severity(self) -> Severity:
        """Worst severity across all items — drives card colour."""
        if any(i.severity == Severity.ERROR   for i in self.items):
            return Severity.ERROR
        if any(i.severity == Severity.WARNING for i in self.items):
            return Severity.WARNING
        return Severity.PASS

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.WARNING)

    def add(self, severity: Severity, message: str,
            detail: str = None, node: str = None,
            category: str = None) -> None:
        self.items.append(DiagnosticItem(severity, message, detail, node, category))
