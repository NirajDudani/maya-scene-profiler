"""
maketx_converter.py
Locates Arnold's maketx tool and converts image files to .tx format.
"""

import os
import subprocess
import maya.cmds as cmds


def find_maketx() -> str | None:
    """Return the path to maketx.exe, or None if not found."""
    # Most reliable: derive from the loaded mtoa plugin
    try:
        plugin_path = cmds.pluginInfo("mtoa", query=True, path=True)
        if plugin_path:
            candidate = os.path.join(
                os.path.dirname(os.path.dirname(plugin_path)), "bin", "maketx.exe"
            )
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    # Environment variable fallbacks
    for env_var in ("ARNOLD_PATH", "MTOA_PATH"):
        root = os.environ.get(env_var)
        if root:
            candidate = os.path.join(root, "bin", "maketx.exe")
            if os.path.isfile(candidate):
                return candidate

    # Common installation paths
    common = [
        r"C:\ProgramData\Autodesk\ApplicationPlugins\mtoa\bin\maketx.exe",
        r"C:\Program Files\Autodesk\Arnold\maya2024\bin\maketx.exe",
        r"C:\Program Files\Autodesk\Arnold\maya2025\bin\maketx.exe",
        r"C:\Program Files\Autodesk\Arnold\maya2023\bin\maketx.exe",
        r"C:\Program Files\Autodesk\Arnold\maya2022\bin\maketx.exe",
    ]
    for path in common:
        if os.path.isfile(path):
            return path

    return None


def convert_to_tx(paths: list) -> tuple:
    """
    Convert a list of image paths to .tx using maketx.
    Returns (maketx_path_or_None, results) where results is a list of
    (input_path, success: bool, message: str).
    """
    maketx = find_maketx()
    if not maketx:
        return None, []

    results = []
    for path in paths:
        tx_path = os.path.splitext(path)[0] + ".tx"
        try:
            proc = subprocess.run(
                [maketx, path, "-o", tx_path,
                 "--colorconvert", "sRGB", "linear"],
                capture_output=True, text=True, timeout=180
            )
            if proc.returncode == 0:
                results.append((path, True, tx_path))
            else:
                err = proc.stderr.strip() or proc.stdout.strip() or "Unknown error"
                results.append((path, False, err))
        except subprocess.TimeoutExpired:
            results.append((path, False, "Timed out after 180 s"))
        except Exception as exc:
            results.append((path, False, str(exc)))

    return maketx, results


def find_tx_siblings(paths: list) -> tuple:
    """Check whether a .tx sibling exists next to each source path.
    Returns (already_have, missing) — two lists of original paths.
    """
    already_have = []
    missing = []
    for path in paths:
        tx_path = os.path.splitext(path)[0] + ".tx"
        if os.path.isfile(tx_path):
            already_have.append(path)
        else:
            missing.append(path)
    return already_have, missing
