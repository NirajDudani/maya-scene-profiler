"""
Texture Audit Diagnostic
Scans all file texture nodes for:
- Missing files on disk
- Non-TX textures (studios expect .tx for Arnold)
- Oversized textures (> 4K)
- Textures not connected to any shader
- Textures shared across 2 or more materials
"""

import os
import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

OVERSIZE_THRESHOLD = 4096   # flag textures with width or height above this


def _get_materials_for_node(node: str) -> list:
    """Return material nodes downstream of a file texture node."""
    future = cmds.listHistory(node, future=True, allFuture=True) or []
    all_mats = set(cmds.ls(materials=True) or [])
    return [n for n in future if n in all_mats]


def _get_image_dimensions(path: str):
    """Try to read image dimensions without importing heavy libs."""
    try:
        import struct
        if path.lower().endswith(".png"):
            with open(path, "rb") as f:
                f.read(8)                        # signature
                f.read(4)                        # chunk length
                f.read(4)                        # IHDR
                w = struct.unpack(">I", f.read(4))[0]
                h = struct.unpack(">I", f.read(4))[0]
                return w, h
    except Exception:
        pass
    return None, None


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Texture Audit")

    file_nodes = cmds.ls(type="file") or []

    if not file_nodes:
        result.add(Severity.INFO, "No file texture nodes found in scene")
        result.summary = "No textures in scene"
        return result

    # normalized path -> set of material names that use it
    path_to_mats = {}

    total       = len(file_nodes)
    missing     = 0
    non_tx      = 0
    oversized   = 0
    unconnected = 0

    for node in file_nodes:
        try:
            raw_path = cmds.getAttr(f"{node}.fileTextureName") or ""
            path     = raw_path.strip()

            # ── missing file ─────────────────────────────────────────────────
            if not path:
                connected = cmds.listConnections(node, destination=True) or []
                owner = f"connected to: {connected[0]}" if connected else "no shader connection found"
                result.add(Severity.WARNING,
                           f"Empty texture path on node ({owner})",
                           detail=f"Open Hypershade, select '{node}' and set a valid file path.",
                           node=node, category="Missing")
                missing += 1
                continue

            if not os.path.isfile(path):
                result.add(Severity.ERROR,
                           f"Missing texture: {os.path.basename(path)}",
                           detail=f"Full path: {path}", node=node,
                           category="Missing")
                missing += 1
                continue

            # ── accumulate materials per unique file path ─────────────────────
            norm = os.path.normcase(path)
            path_to_mats.setdefault(norm, set())
            for mat in _get_materials_for_node(node):
                path_to_mats[norm].add(mat)

            # ── non-TX ───────────────────────────────────────────────────────
            if not path.lower().endswith(".tx"):
                result.add(Severity.WARNING,
                           f"Non-TX texture: {os.path.basename(path)}",
                           detail="Arnold expects .tx textures for best performance.",
                           node=node, category="Non-TX Format")
                non_tx += 1

            # ── oversized ────────────────────────────────────────────────────
            w, h = _get_image_dimensions(path)
            if w and h and (w > OVERSIZE_THRESHOLD or h > OVERSIZE_THRESHOLD):
                result.add(Severity.WARNING,
                           f"Oversized texture {w}x{h}: {os.path.basename(path)}",
                           node=node, category="Oversized")
                oversized += 1

            # ── unconnected node ─────────────────────────────────────────────
            connections = cmds.listConnections(node, destination=True) or []
            if not connections:
                result.add(Severity.WARNING,
                           f"Texture node '{node}' is not connected to any shader",
                           detail=f"File: {path}\n"
                                  f"This texture is loaded in the scene but not used by any material. "
                                  f"Either connect it in Hypershade or delete it to reduce scene size.",
                           node=node, category="Unconnected")
                unconnected += 1

        except Exception as exc:
            result.add(Severity.ERROR, f"Could not inspect node: {exc}", node=node,
                       category="Errors")

    # ── shared textures — one INFO per file used by 2+ distinct materials ────
    shared = 0
    for norm_path, mats in path_to_mats.items():
        if len(mats) < 2:
            continue
        basename = os.path.basename(norm_path)
        mat_list = "\n".join(f"  • {m}" for m in sorted(mats))
        result.add(Severity.INFO,
                   f"Shared texture ({len(mats)} materials): {basename}",
                   detail=f"Used by {len(mats)} materials:\n{mat_list}",
                   category="Shared Textures")
        shared += 1

    result.summary = (
        f"{total} textures | {missing} missing | {non_tx} non-TX | "
        f"{oversized} oversized | {unconnected} unconnected | {shared} shared"
    )
    return result
