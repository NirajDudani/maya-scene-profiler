"""
shelf_button.py
Called automatically by userSetup.py on every Maya startup.
Can also be run manually once from Maya's Script Editor.
"""

import os
import maya.cmds as cmds
import maya.mel as mel

TOOL_PATH = os.path.dirname(os.path.abspath(__file__))

LAUNCH_CMD = """
import sys, os
tool_path = r"{path}"
if tool_path not in sys.path:
    sys.path.insert(0, tool_path)
import importlib, scene_profiler
importlib.reload(scene_profiler)
scene_profiler.launch()
""".format(path=TOOL_PATH)

BUTTON_NAME = "SceneProfilerBtn"


def add_shelf_button():
    shelf_top = mel.eval("$tmpVar = $gShelfTopLevel")
    current_shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)

    # avoid adding a duplicate button on every startup
    existing = cmds.shelfLayout(current_shelf, query=True, childArray=True) or []
    for child in existing:
        try:
            if cmds.shelfButton(child, query=True, label=True) == "SceneProfiler":
                return
        except Exception:
            pass

    cmds.shelfButton(
        parent            = current_shelf,
        label             = "SceneProfiler",
        annotation        = "Maya Scene Profiler — run scene diagnostics",
        command           = LAUNCH_CMD,
        sourceType        = "python",
        imageOverlayLabel = "PROF",
        overlayLabelColor = (1, 1, 1),
        overlayLabelBackColor = (0.2, 0.4, 0.6, 0.8),
        image1            = "menuIconFile.png",
    )
    cmds.inViewMessage(
        amg="<hl>Scene Profiler</hl> button added to shelf.",
        pos="midCenter", fade=True
    )
