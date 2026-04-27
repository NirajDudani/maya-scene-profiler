"""
Reference Graph Diagnostic
Checks all file references in the scene:
- Broken / unresolved references
- Nested reference depth (> 3 levels is a warning)
- Duplicate reference paths
- References that failed to load
"""

import os
import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

MAX_DEPTH = 3


def _reference_depth(ref_node: str) -> int:
    """Walk up parent references to calculate nesting depth."""
    depth = 0
    current = ref_node
    while True:
        try:
            parent = cmds.referenceQuery(current, referenceNode=True, parent=True)
            if parent:
                depth += 1
                current = parent
            else:
                break
        except Exception:
            break
    return depth


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Reference Graph")

    try:
        ref_nodes = cmds.ls(type="reference") or []
        # Filter out the internal _UNKNOWN_REF_NODE_ Maya always creates
        ref_nodes = [r for r in ref_nodes if "sharedReferenceNode" not in r]
    except Exception as exc:
        result.add(Severity.ERROR, f"Could not list references: {exc}")
        result.summary = "Reference query failed"
        return result

    if not ref_nodes:
        result.add(Severity.INFO, "Scene has no file references")
        result.summary = "No references in scene"
        return result

    seen_paths = {}
    broken     = 0
    deep       = 0
    total      = len(ref_nodes)

    for ref in ref_nodes:
        try:
            # ── resolve path ─────────────────────────────────────────────────
            try:
                path = cmds.referenceQuery(ref, filename=True, withoutCopyNumber=True)
            except Exception:
                path = None

            if not path:
                result.add(Severity.ERROR,
                           f"Reference has no file path",
                           node=ref)
                broken += 1
                continue

            # ── file exists? ─────────────────────────────────────────────────
            if not os.path.isfile(path):
                result.add(Severity.ERROR,
                           f"Broken reference: {os.path.basename(path)}",
                           detail=f"File not found: {path}", node=ref)
                broken += 1
                continue

            # ── loaded? ──────────────────────────────────────────────────────
            try:
                loaded = cmds.referenceQuery(ref, isLoaded=True)
            except Exception:
                loaded = True

            if not loaded:
                result.add(Severity.WARNING,
                           f"Reference is unloaded: {os.path.basename(path)}",
                           detail=path, node=ref)

            # ── duplicate path ───────────────────────────────────────────────
            norm = os.path.normcase(path)
            if norm in seen_paths:
                result.add(Severity.WARNING,
                           f"Duplicate reference: {os.path.basename(path)}",
                           detail=f"Also referenced by {seen_paths[norm]}", node=ref)
            else:
                seen_paths[norm] = ref

            # ── nesting depth ────────────────────────────────────────────────
            depth = _reference_depth(ref)
            if depth > MAX_DEPTH:
                result.add(Severity.WARNING,
                           f"Deep reference nesting ({depth} levels): {os.path.basename(path)}",
                           detail="Deep nesting slows scene load and can cause resolve errors.",
                           node=ref)
                deep += 1

        except Exception as exc:
            result.add(Severity.ERROR, f"Could not inspect reference {ref}: {exc}", node=ref)

    result.summary = (
        f"{total} reference(s) | {broken} broken | {deep} deeply nested"
    )
    return result
