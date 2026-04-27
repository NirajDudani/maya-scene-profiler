"""
scene_profiler.py
Entry point — paste into Maya's Script Editor (Python tab) to launch.

Usage:
    import sys, os
    tool_path = r"C:/path/to/maya-scene-profiler"
    if tool_path not in sys.path:
        sys.path.insert(0, tool_path)

    import scene_profiler
    scene_profiler.launch()
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_WINDOW = None
TOOL_NAME = "SceneProfilerWorkspaceControl"


def launch():
    global _WINDOW

    try:
        import maya.cmds as cmds
        if cmds.workspaceControl(TOOL_NAME, exists=True):
            cmds.deleteUI(TOOL_NAME)
    except Exception:
        pass

    from ui.main_window import SceneProfiler
    _WINDOW = SceneProfiler()
    _WINDOW.show(dockable=True,
                 area="right",
                 allowedArea=["right", "left"],
                 retain=False)
    return _WINDOW


if __name__ == "__main__":
    launch()
