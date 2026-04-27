"""
qt_shim.py
Abstracts the PySide2 / PySide6 difference so the rest of the tool
does not need to know which version of Qt Maya is running.

  Maya 2022 – 2024  →  PySide2
  Maya 2025+        →  PySide6
"""

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
