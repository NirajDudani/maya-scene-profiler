# Maya Scene Profiler

A dockable Maya 2024 tool that audits a lighting scene and reports problems instantly — missing textures, broken references, shader issues, render settings, AOVs, and more. Built with PySide2 and the Maya Python API.

![Maya](https://img.shields.io/badge/Maya-2022--2025-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Qt](https://img.shields.io/badge/PySide2%20%7C%20PySide6-supported-green)

---

## Demo

[![Maya Scene Profiler Demo](https://img.youtube.com/vi/pKyocGW9Ha0/0.jpg)](https://youtu.be/pKyocGW9Ha0?si=1Zjd2pMuhUvC8Z7T)

---

## Why I built this

During my time in school I was working on a lighting assignment and kept running into render failures that I couldn't figure out. I'd spend more time debugging the scene than actually lighting it. Every time something broke I'd go through the same process — checking if textures were loading, checking if my lights were set up correctly, checking render settings — all manually, clicking through different editors one by one.

At some point I realised I was doing the exact same checks every single time. It was never anything new, it was always one of the same five or six problems. That repetition is what made me think — this should just be a script. If I'm checking the same things in the same order every time a scene breaks, a tool can do that in seconds.

That's what led me to build the Scene Profiler. I wanted something that could look at a lighting scene and immediately tell me what was wrong instead of me having to hunt for it manually. It saved me a lot of time finishing that assignment and I realised it would be even more valuable in a real production where you're dealing with dozens of shots and dozens of artists all hitting the same kinds of problems.

---

## Features

- Docks into Maya's UI like a native panel — no floating windows
- Runs seven independent diagnostics in one click
- Collapsible result cards with subcategory dropdowns — expand only what you need to investigate
- Summary pills showing total Errors, Warnings, and Passed checks at a glance
- Per-finding detail tooltips with plain-English explanations and fix instructions
- **Convert to TX** — detects existing `.tx` files automatically, scans a folder for missing ones, converts any remainder with `maketx`, and retargets all file nodes in one flow
- Export results as a **CSV spreadsheet** or **HTML report**
- Auto-launches on Maya startup via `userSetup.py` — no shelf button or Script Editor needed
- Compatible with Maya 2022–2025 (PySide2 and PySide6 detected automatically)

---

## Diagnostics

Each diagnostic runs independently. Results are shown as collapsible cards with a severity badge (PASS / WARNING / ERROR), a one-line summary, and an expandable table of individual findings. Every finding includes the Maya node name and a plain-English explanation of how to fix it.

---

### Scene Weight

Checks the overall heaviness of the scene.

| Check | Threshold | Severity |
|---|---|---|
| Total polygon count | > 5 million | WARNING |
| Total polygon count | > 20 million | ERROR |
| Individual heavy mesh | > 500,000 faces — reports full DAG path | WARNING |
| Construction history | Any `polyExtrudeFace`, `polyBevel`, `polySplit`, or `polySubdivide` nodes remaining — lists each affected mesh by full path | WARNING |

---

### Texture Audit

Checks every `file` texture node in the scene. Findings are grouped into collapsible subcategories inside the card.

| Check | Condition | Severity |
|---|---|---|
| No textures in scene | Zero file nodes found | INFO |
| Empty texture path | Node has no path set — reports which shader owns it | WARNING |
| Missing file on disk | Path is set but the file does not exist | ERROR |
| Non-TX format | Texture does not end in `.tx` (Arnold expects `.tx`) — includes a **Convert to TX** button | WARNING |
| Oversized texture | PNG width or height exceeds 4096px | WARNING |
| Unconnected node | File node has no outgoing connections — not used by any shader | WARNING |
| Shared textures | Same texture file used by 2 or more distinct materials — hover to see which materials | INFO |

#### Convert to TX

Clicking **Convert to TX** in the Non-TX Format subcategory runs the following flow:

1. Checks whether a `.tx` sibling already exists next to each texture on disk
2. If all `.tx` files are present — offers to retarget the file nodes immediately, no conversion needed
3. If some are missing — asks whether you have a folder containing the `.tx` files, scans it recursively, and matches by filename
4. Any textures still missing after the folder scan are converted with Arnold's `maketx` tool
5. All file nodes in the scene are updated to point to the `.tx` versions

Requires Arnold for Maya to be installed. `maketx` is located automatically from the loaded plugin.

---

### Reference Graph

Checks every file reference in the scene.

| Check | Condition | Severity |
|---|---|---|
| No references | Zero reference nodes found | INFO |
| No file path on reference | Reference node exists but has no path | ERROR |
| Broken reference | File path set but file does not exist on disk | ERROR |
| Unloaded reference | Reference exists but is currently unloaded | WARNING |
| Duplicate reference path | Same file referenced more than once | WARNING |
| Deep nesting | Reference is nested more than 3 levels deep | WARNING |

---

### Light Inventory

Checks all lights. Supports native Maya lights and Arnold, VRay, and Redshift light types.

| Check | Condition | Severity |
|---|---|---|
| No lights | Zero lights found in scene | WARNING |
| Default name | Transform name matches Maya's auto-assigned defaults (e.g. `directionalLight1`) | WARNING |
| Naming convention | Transform name does not follow `prefix_type_NNN` pattern (e.g. `key_area_001`) | WARNING |
| High intensity | Light intensity exceeds 10,000 | WARNING |
| Extreme intensity | Light intensity exceeds 100,000 | ERROR |
| Invisible light | Parent transform has visibility turned off — light will not contribute to render | WARNING |

---

### Shader Inventory

Checks shading engines and materials.

| Check | Condition | Severity |
|---|---|---|
| Orphaned shader | Shading engine has no geometry connected via `dagSetMembers` | WARNING |
| Unshaded mesh | Mesh has no shading engine connected via `instObjGroups` — will render as default grey | ERROR |
| Duplicate shader name | Two materials share the same name across namespaces | WARNING |

---

### Render Layer Audit

Checks render layers and global render settings. Detects whether the scene uses legacy render layers or Maya's Render Setup automatically.

| Check | Condition | Severity |
|---|---|---|
| No Render Setup layers | Render Setup is active but no layers are defined | INFO |
| Render Setup layer disabled | Layer's `enabled` attribute is off — will not render on the farm | WARNING |
| Legacy layer not renderable | Layer's `renderable` attribute is off | WARNING |
| Empty render layer | Layer has no members assigned — reports how many meshes are available to assign | WARNING |
| Default frame range | Start and end frame are both 1 (never changed from default) | WARNING |
| No image file prefix | `imageFilePrefix` is empty in Render Settings — output files may overwrite each other | WARNING |

---

### AOV Report

Arnold-only. Skipped gracefully with an INFO message if Arnold is not loaded.

| Check | Condition | Severity |
|---|---|---|
| Arnold not loaded | Arnold not available in the renderer list | INFO |
| No AOVs defined | Zero `aiAOV` nodes in scene | WARNING |
| AOV disabled | AOV exists but `enabled` attribute is off — will not be written during render | WARNING |
| Duplicate AOV name | Two AOVs share the same name | ERROR |
| Invalid AOV name | Name contains characters outside `A–Z a–z 0–9 _` | WARNING |
| Missing expected AOVs | Any of `beauty`, `diffuse`, `specular`, `shadow`, `Z`, `N` not defined — each includes a plain-English description of what the pass is used for in compositing | WARNING |

---

## Requirements

- Autodesk Maya 2022, 2023, 2024, or 2025
- Python 3.10+ (bundled with Maya 2022+)
- PySide2 (Maya 2022–2024) or PySide6 (Maya 2025+) — detected automatically
- Arnold for Maya *(AOV Report and Convert to TX only — skipped gracefully if not loaded)*

No pip installs required. All dependencies ship with Maya.

---

## Installation

**1. Clone or copy the folder into your Maya scripts directory:**

```
C:/Users/<you>/Documents/maya/2024/scripts/mayaSceneProfiler/
```

**2. Create `userSetup.py` in your Maya scripts directory** (one level above the tool folder):

```python
"""
userSetup.py
Maya executes this file automatically on every startup.
Launches Scene Profiler docked to the right panel.
"""

import sys
import os
import maya.utils
import maya.cmds as cmds


def _launch_scene_profiler():
    # cmds.internalVar gives us the exact scripts dir Maya is using
    scripts_dir = cmds.internalVar(userScriptDir=True).rstrip("/\\")
    tool_path = os.path.join(scripts_dir, "mayaSceneProfiler")

    if not os.path.isdir(tool_path):
        print(f"[SceneProfiler] Tool folder not found at: {tool_path}")
        return

    if tool_path not in sys.path:
        sys.path.insert(0, tool_path)

    try:
        import scene_profiler
        scene_profiler.launch()
        print("[SceneProfiler] Launched successfully.")
    except Exception as e:
        import traceback
        print(f"[SceneProfiler] Launch failed: {e}")
        traceback.print_exc()


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
│   ├── diagnostic_card.py     # Collapsible per-diagnostic result card with subcategory dropdowns
│   ├── qt_shim.py             # PySide2 / PySide6 compatibility shim
│   └── styles.py              # Maya dark theme stylesheet and colour constants
└── diagnostics/
    ├── scene_weight.py        # Polygon count, heavy meshes, construction history
    ├── texture_audit.py       # File nodes, missing textures, TX format, shared textures
    ├── maketx_converter.py    # Locates maketx, converts textures, scans folders for .tx files
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

## Contributing

Bug reports and suggestions are welcome. If you run into a false positive, a missing check, or a Maya version compatibility issue, open an issue with the scene setup that triggered it and the full error message from the Script Editor output.

---

## License

MIT License — free to use, modify, and distribute for personal and commercial projects. See [LICENSE](LICENSE) for the full text.
