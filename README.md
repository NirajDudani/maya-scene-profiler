# Maya Scene Profiler

A dockable Maya 2024 tool that audits a lighting scene and reports problems instantly — missing textures, broken references, shader issues, render settings, AOVs, and more. Built with PySide2 and the Maya Python API.

![Maya](https://img.shields.io/badge/Maya-2022--2025-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Qt](https://img.shields.io/badge/PySide2%20%7C%20PySide6-supported-green)

---

## Why I built this

During my time in school I was working on a lighting assignment and kept running into render failures that I couldn't figure out. I'd spend more time debugging the scene than actually lighting it. Every time something broke I'd go through the same process — checking if textures were loading, checking if my lights were set up correctly, checking render settings — all manually, clicking through different editors one by one.

At some point I realised I was doing the exact same checks every single time. It was never anything new, it was always one of the same five or six problems. That repetition is what made me think — this should just be a script. If I'm checking the same things in the same order every time a scene breaks, a tool can do that in seconds.

That's what led me to build the Scene Profiler. I wanted something that could look at a lighting scene and immediately tell me what was wrong instead of me having to hunt for it manually. It saved me a lot of time finishing that assignment and I realised it would be even more valuable in a real production where you're dealing with dozens of shots and dozens of artists all hitting the same kinds of problems.

---

## Features

- Docks into Maya's UI like a native panel — no floating windows
- Runs seven independent diagnostics in one click
- Collapsible result cards — expand only what you need to investigate
- Summary pills showing total Errors, Warnings, and Passed checks at a glance
- Per-finding detail tooltips with plain-English explanations and fix instructions
- Export results as a **CSV spreadsheet** or **HTML report**
- Auto-launches on Maya startup via `userSetup.py` — no shelf button or Script Editor needed

---

## Diagnostics

| Diagnostic | What it checks |
|---|---|
| **Scene Weight** | Polygon count thresholds, individual heavy meshes, leftover construction history nodes and which objects have them |
| **Texture Audit** | Missing files on disk, non-TX formats, oversized textures (>4096px), duplicate paths, unconnected file nodes |
| **Reference Graph** | Broken or unresolved references, unloaded references, duplicate reference paths, nesting depth >3 levels |
| **Light Inventory** | No lights in scene, default or non-convention names, extreme intensity values, invisible lights that won't render |
| **Shader Inventory** | Orphaned shaders assigned to no geometry, meshes with no material, duplicate shader names across namespaces |
| **Render Layer Audit** | Disabled or empty render layers, default frame range, missing image file prefix in Render Settings |
| **AOV Report** | Arnold only — disabled AOVs, duplicate names, invalid characters, missing expected passes (beauty, diffuse, specular, shadow, Z, N) |

---

## Requirements

- Autodesk Maya 2022, 2023, 2024, or 2025
- Python 3.10+ (bundled with Maya 2022+)
- PySide2 (Maya 2022–2024) or PySide6 (Maya 2025+) — detected automatically
- Arnold for Maya *(AOV Report only — skipped gracefully if not loaded)*

No pip installs required. All dependencies ship with Maya.

---

## Installation

**1. Clone or copy the folder into your Maya scripts directory:**

```
C:/Users/<you>/Documents/maya/2024/scripts/mayaSceneProfiler/
```

**2. Create `userSetup.py` in your Maya scripts directory** (one level above the tool folder):

```python
import sys, os, maya.utils, maya.cmds as cmds

def _launch_scene_profiler():
    scripts_dir = cmds.internalVar(userScriptDir=True).rstrip("/\\")
    tool_path = os.path.join(scripts_dir, "mayaSceneProfiler")
    if tool_path not in sys.path:
        sys.path.insert(0, tool_path)
    try:
        import scene_profiler
        scene_profiler.launch()
    except Exception as e:
        print(f"[SceneProfiler] Launch failed: {e}")

maya.utils.executeDeferred(_launch_scene_profiler)
```

**3. Restart Maya.** The tool opens automatically, docked to the right panel.

---

## Running manually

If you prefer to launch from the Script Editor instead of auto-starting:

```python
import sys, os
tool_path = r"C:/Users/<you>/Documents/maya/2024/scripts/mayaSceneProfiler"
if tool_path not in sys.path:
    sys.path.insert(0, tool_path)
import scene_profiler
scene_profiler.launch()
```

---

## Project structure

```
mayaSceneProfiler/
├── scene_profiler.py          # Entry point — call scene_profiler.launch()
├── shelf_button.py            # Shelf button installer (optional)
├── README.md
├── .gitignore
├── core/
│   ├── result.py              # DiagnosticResult and DiagnosticItem data model
│   ├── runner.py              # Runs all diagnostics and collects results
│   └── exporter.py            # CSV and HTML export logic
├── ui/
│   ├── main_window.py         # Main dockable window (MayaQWidgetDockableMixin)
│   ├── diagnostic_card.py     # Collapsible per-diagnostic result card
│   └── styles.py              # Maya 2024 dark theme stylesheet and colour constants
└── diagnostics/
    ├── scene_weight.py        # Polygon count, heavy meshes, construction history
    ├── texture_audit.py       # File nodes, missing textures, TX format, duplicates
    ├── reference_graph.py     # File references, broken paths, nesting depth
    ├── light_inventory.py     # Light names, intensity, visibility
    ├── shader_inventory.py    # Orphaned shaders, unshaded meshes, duplicate names
    ├── render_layer_audit.py  # Layer state, frame range, image prefix
    └── aov_report.py          # Arnold AOV completeness and validity
```

---

## Exporting results

After running diagnostics, click **Export ▾** to choose a format.

### HTML
A formatted, self-contained report suitable for sharing with a supervisor or pipeline TD. Includes:
- Timestamp and scene name in the header
- One card per diagnostic with severity badge and run time
- Full findings table with Severity, Message, Node, and Detail columns
- Color-coded rows matching the in-tool display
- Opens automatically in your default browser after export

### CSV
A flat data file for use in pipeline scripts or spreadsheets. Columns: `Diagnostic`, `Severity`, `Message`, `Detail`, `Node`, `Duration (ms)`. Every finding is one row, making it easy to filter and sort across multiple scene exports.

---

## Adding a new diagnostic

1. Create `diagnostics/my_check.py` with a `run()` function that returns a `DiagnosticResult`.
2. Use `result.add(Severity.WARNING, "message", detail="...", node="...")` to record findings.
3. Register it in `core/runner.py` by adding `("My Check", run_my_check)` to `_DIAGNOSTICS`.

```python
# diagnostics/my_check.py
from core.result import DiagnosticResult, Severity
import maya.cmds as cmds

def run() -> DiagnosticResult:
    result = DiagnosticResult(name="My Check")
    # ... your logic ...
    result.summary = "Summary shown on collapsed card"
    return result
```

```python
# core/runner.py — add to _DIAGNOSTICS list
from diagnostics.my_check import run as run_my_check

_DIAGNOSTICS = [
    ...
    ("My Check", run_my_check),
]
```

The runner handles timing, exception catching, and progress reporting automatically — your `run()` function only needs to return a result.
