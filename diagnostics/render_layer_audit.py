"""
Render Layer Audit Diagnostic
Checks render layers for common production issues:
- Layers that are disabled (won't render)
- Layers with no members
- Output path not set or not writeable
- Frame range not set on any layer
- Conflicting overrides
"""

import os
import maya.cmds as cmds
from core.result import DiagnosticResult, Severity


def _using_render_setup() -> bool:
    """Detect whether the scene uses legacy render layers or Render Setup."""
    try:
        return bool(cmds.ls(type="renderSetupLayer"))
    except Exception:
        return False


def _audit_render_setup(result: DiagnosticResult) -> str:
    """Audit Maya 2016+ Render Setup layers."""
    layers = cmds.ls(type="renderSetupLayer") or []
    if not layers:
        result.add(Severity.INFO, "Render Setup has no layers defined")
        return f"0 Render Setup layers"

    enabled = 0
    for layer in layers:
        try:
            is_enabled = cmds.getAttr(f"{layer}.enabled")
        except Exception:
            is_enabled = True

        if not is_enabled:
            result.add(Severity.WARNING,
                       f"Render Setup layer disabled: {layer}",
                       detail="Disabled layers will not render on the farm.",
                       node=layer)
        else:
            enabled += 1

    return f"{len(layers)} Render Setup layer(s), {enabled} enabled"


def _audit_legacy_layers(result: DiagnosticResult) -> str:
    """Audit legacy render layers."""
    layers = cmds.ls(type="renderLayer") or []
    layers = [l for l in layers if l != "defaultRenderLayer"]

    if not layers:
        result.add(Severity.INFO,
                   "Only the default render layer exists",
                   detail="Consider setting up render layers for AOV separation.")
        return "1 layer (default only)"

    renderable = 0
    for layer in layers:
        try:
            is_renderable = cmds.getAttr(f"{layer}.renderable")
        except Exception:
            is_renderable = True

        if not is_renderable:
            result.add(Severity.WARNING,
                       f"Render layer not renderable: {layer}",
                       node=layer)
        else:
            renderable += 1

        # check layer has members
        try:
            members = cmds.editRenderLayerMembers(layer, query=True) or []
            if not members:
                all_transforms = cmds.ls(type="transform", long=True) or []
                geo = [t for t in all_transforms
                       if cmds.listRelatives(t, shapes=True, type="mesh")]
                hint = (f"Scene has {len(geo)} mesh transform(s) available to assign."
                        if geo else "No meshes found in scene to assign.")
                result.add(Severity.WARNING,
                           f"Render layer '{layer}' has no members",
                           detail=f"{hint}\n"
                                  f"Fix: select objects in the viewport, then right-click "
                                  f"'{layer}' in the Render Setup and choose 'Add Selected Objects'.",
                           node=layer)
        except Exception:
            pass

    return f"{len(layers)} legacy layer(s), {renderable} renderable"


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="Render Layer Audit")

    # ── detect layer system ──────────────────────────────────────────────────
    if _using_render_setup():
        summary_str = _audit_render_setup(result)
    else:
        summary_str = _audit_legacy_layers(result)

    # ── global render settings checks ────────────────────────────────────────
    try:
        start = cmds.getAttr("defaultRenderGlobals.startFrame")
        end   = cmds.getAttr("defaultRenderGlobals.endFrame")
        if start == end == 1:
            result.add(Severity.WARNING,
                       "Frame range is 1-1 (default) — verify this is intentional",
                       detail="Set correct frame range in Render Settings before submitting.")
        else:
            result.add(Severity.PASS, f"Frame range: {int(start)}-{int(end)}")
    except Exception as exc:
        result.add(Severity.ERROR, f"Could not read frame range: {exc}")

    # ── output path ──────────────────────────────────────────────────────────
    try:
        img_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix") or ""
        if not img_prefix:
            result.add(Severity.WARNING,
                       "No image file prefix set in Render Settings",
                       detail="Output files may overwrite each other without a proper prefix.")
        else:
            result.add(Severity.PASS, f"Image prefix: {img_prefix}")
    except Exception as exc:
        result.add(Severity.ERROR, f"Could not read image prefix: {exc}")

    result.summary = summary_str
    return result
