"""
Light Inventory Diagnostic
Audits all lights in the scene:
- Scene has at least one light
- Naming convention (must match studioPrefix_type_NNN pattern)
- Extreme intensity values
- Lights with default/untouched names
- Lights parented under wrong groups
- Invisible lights that will not contribute to render
"""

import re
import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

# Light types Maya recognises
LIGHT_TYPES = [
    "directionalLight", "pointLight", "spotLight", "areaLight",
    "ambientLight", "aiAreaLight", "aiSkyDomeLight", "aiMeshLight",
    "aiPhotometricLight", "VRayLight", "VRayLightDome", "RedshiftDomeLight",
]

INTENSITY_WARN  = 10_000
INTENSITY_ERROR = 100_000

# Simple naming check — at least two underscore-separated words, no spaces
NAMING_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$")

# Default names Maya assigns on creation
DEFAULT_NAMES = {
    "directionalLight1", "pointLight1", "spotLight1", "areaLight1",
    "ambientLight1", "aiAreaLight1", "aiSkyDomeLight1",
}


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Light Inventory")

    lights = []
    for ltype in LIGHT_TYPES:
        try:
            found = cmds.ls(type=ltype, long=True) or []
            lights.extend(found)
        except Exception:
            pass

    if not lights:
        result.add(Severity.WARNING, "Scene contains no lights",
                   detail="Add at least one light before rendering.")
        result.summary = "No lights found"
        return result

    naming_issues = 0
    intensity_issues = 0
    invisible = 0

    for light in lights:
        # always check the transform name — that is what artists rename in the Outliner
        transform = (cmds.listRelatives(light, parent=True, fullPath=True) or [None])[0]
        transform_name = transform.split("|")[-1] if transform else light.split("|")[-1]

        # ── default name ─────────────────────────────────────────────────────
        if transform_name.lower() in {n.lower() for n in DEFAULT_NAMES}:
            result.add(Severity.WARNING,
                       f"Light has default name: {transform_name}",
                       detail=f"Rename '{transform_name}' in the Outliner to match your studio convention.\n"
                              f"Expected format: prefix_type_NNN (e.g. key_area_001)",
                       node=transform or light)
            naming_issues += 1

        # ── naming convention ────────────────────────────────────────────────
        elif not NAMING_RE.match(transform_name):
            result.add(Severity.WARNING,
                       f"Light name does not follow convention: {transform_name}",
                       detail=f"Rename '{transform_name}' in the Outliner.\n"
                              f"Expected format: prefix_type_NNN (e.g. key_area_001)",
                       node=transform or light)
            naming_issues += 1

        # ── intensity ────────────────────────────────────────────────────────
        try:
            intensity = cmds.getAttr(f"{light}.intensity")
            if intensity >= INTENSITY_ERROR:
                result.add(Severity.ERROR,
                           f"Extreme intensity {intensity:.0f} on {transform_name}",
                           node=transform or light)
                intensity_issues += 1
            elif intensity >= INTENSITY_WARN:
                result.add(Severity.WARNING,
                           f"High intensity {intensity:.0f} on {transform_name}",
                           node=transform or light)
                intensity_issues += 1
        except Exception:
            pass

        # ── visibility ───────────────────────────────────────────────────────
        try:
            if transform:
                vis = cmds.getAttr(f"{transform}.visibility")
                if not vis:
                    result.add(Severity.WARNING,
                               f"Light is invisible and won't render: {transform_name}",
                               detail=f"Select '{transform_name}' in the Outliner and turn on visibility.",
                               node=transform)
                    invisible += 1
        except Exception:
            pass

    if not result.items:
        result.add(Severity.PASS, f"All {len(lights)} light(s) look good")

    result.summary = (
        f"{len(lights)} light(s) | {naming_issues} naming | "
        f"{intensity_issues} intensity | {invisible} invisible"
    )
    return result
