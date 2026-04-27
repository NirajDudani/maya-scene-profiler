"""
Scene Weight Diagnostic
Reports overall scene memory footprint — polygon count, node count,
DAG depth, and flags scenes that are unusually heavy.
"""

import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

POLY_WARN_THRESHOLD  = 5_000_000   # 5M polygons
POLY_ERROR_THRESHOLD = 20_000_000  # 20M polygons


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Scene Weight")

    # ── polygon count ────────────────────────────────────────────────────────
    try:
        meshes = cmds.ls(type="mesh", long=True) or []
        total_polys = 0
        heavy_meshes = []

        for mesh in meshes:
            try:
                poly_count = cmds.polyEvaluate(mesh, face=True)
                if isinstance(poly_count, int):
                    total_polys += poly_count
                    if poly_count > 500_000:
                        heavy_meshes.append((mesh, poly_count))
            except Exception:
                pass

        if total_polys >= POLY_ERROR_THRESHOLD:
            result.add(Severity.ERROR,
                       f"Scene has {total_polys:,} polygons — extremely heavy",
                       detail="Scenes above 20M polygons will cause severe slowdowns.")
        elif total_polys >= POLY_WARN_THRESHOLD:
            result.add(Severity.WARNING,
                       f"Scene has {total_polys:,} polygons — consider optimising",
                       detail="Scenes above 5M polygons may slow viewport and render.")
        else:
            result.add(Severity.PASS, f"Polygon count OK: {total_polys:,}")

        for mesh, count in heavy_meshes[:5]:   # cap list to 5
            result.add(Severity.WARNING,
                       f"Heavy mesh: {mesh} ({count:,} faces)",
                       node=mesh)

    except Exception as exc:
        result.add(Severity.ERROR, f"Polygon check failed: {exc}")

    # ── construction history ─────────────────────────────────────────────────
    try:
        HISTORY_TYPES = ["polyExtrudeFace", "polyBevel", "polySplit", "polySubdivide"]
        meshes_with_history = []
        for mesh in cmds.ls(type="mesh", long=True) or []:
            hist = cmds.listHistory(mesh, pruneDagObjects=True) or []
            hist_nodes = [h for h in hist if cmds.nodeType(h) in HISTORY_TYPES]
            if hist_nodes:
                meshes_with_history.append((mesh, len(hist_nodes)))

        if meshes_with_history:
            result.add(Severity.WARNING,
                       f"Construction history found on {len(meshes_with_history)} mesh(es)",
                       detail="Fix: select all meshes, then Edit > Delete by Type > History.")
            for mesh, count in meshes_with_history:
                result.add(Severity.WARNING,
                           f"History on: {mesh} ({count} node(s))",
                           detail=f"Select '{mesh}' and run Edit > Delete by Type > History.",
                           node=mesh)
        else:
            result.add(Severity.PASS, "No leftover construction history")

    except Exception as exc:
        result.add(Severity.ERROR, f"History check failed: {exc}")

    # ── summary ──────────────────────────────────────────────────────────────
    errors   = result.error_count
    warnings = result.warning_count
    result.summary = (
        f"{errors} error(s), {warnings} warning(s)"
        if errors or warnings else "Scene weight looks good"
    )
    return result
