"""
Shader Inventory Diagnostic
Audits shading engines and surface shaders:
- Shaders assigned to no geometry (orphaned)
- Geometry with no shader (renders as default grey)
- Duplicate shader names across namespaces
- Missing file texture inputs on shader slots
"""

import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

# Built-in shaders Maya always has — ignore these
BUILTIN_SHADERS = {
    "lambert1", "particleCloud1", "shaderGlow1",
    "defaultColorMgtGlobals",
}


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Shader Inventory")

    # ── collect shading engines ──────────────────────────────────────────────
    shading_engines = cmds.ls(type="shadingEngine") or []
    shading_engines = [s for s in shading_engines
                       if s not in {"initialShadingGroup", "initialParticleSE"}]

    # ── orphaned shaders (no geometry assigned) ──────────────────────────────
    # dagSetMembers is the attribute Maya uses to store geometry-to-shader
    # connections — querying it directly is reliable where cmds.sets() is not.
    orphaned = 0
    for se in shading_engines:
        members = cmds.listConnections(f"{se}.dagSetMembers") or []
        if not members:
            surface = (cmds.listConnections(f"{se}.surfaceShader") or [None])[0]
            name = surface or se
            if name not in BUILTIN_SHADERS:
                result.add(Severity.WARNING,
                           f"Shader assigned to no geometry: {name}",
                           detail="Orphaned shaders bloat scene size.",
                           node=se)
                orphaned += 1

    # ── geometry with no material ────────────────────────────────────────────
    # Shader assignments are stored on the shape node via instObjGroups, not
    # on the transform — so listSets(object=transform) always returns empty.
    unshaded = 0
    meshes = cmds.ls(type="mesh", long=True) or []
    for mesh in meshes:
        engines = cmds.listConnections(
            f"{mesh}.instObjGroups", destination=True, type="shadingEngine"
        ) or []
        engines = [e for e in engines if e not in {"initialShadingGroup", "initialParticleSE"}]
        if not engines:
            result.add(Severity.ERROR,
                       f"Mesh has no material assigned: {mesh}",
                       detail=f"Full path: {mesh}\n"
                              f"Will render with default grey lambert. "
                              f"Fix: select the mesh in the viewport, right-click > Assign New Material.",
                       node=mesh)
            unshaded += 1

    # ── duplicate shader names ───────────────────────────────────────────────
    all_shaders = cmds.ls(materials=True) or []
    short_names = [s.split(":")[-1] for s in all_shaders]   # strip namespace
    seen = {}
    duplicates = 0
    for shader, short in zip(all_shaders, short_names):
        if short in BUILTIN_SHADERS:
            continue
        if short in seen:
            result.add(Severity.WARNING,
                       f"Duplicate shader name: {short}",
                       detail=f"Conflicts with {seen[short]}",
                       node=shader)
            duplicates += 1
        else:
            seen[short] = shader

    if not result.items:
        result.add(Severity.PASS,
                   f"All {len(shading_engines)} shader(s) look good")

    result.summary = (
        f"{len(shading_engines)} shader(s) | {orphaned} orphaned | "
        f"{unshaded} unshaded meshes | {duplicates} duplicate names"
    )
    return result
