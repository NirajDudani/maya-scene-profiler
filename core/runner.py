"""
DiagnosticRunner
Executes every registered diagnostic against the current Maya scene
and returns an ordered list of DiagnosticResult objects.
"""

import time
import traceback
from typing import List, Callable

from core.result import DiagnosticResult, DiagnosticItem, Severity

# ── import every diagnostic module ──────────────────────────────────────────
from diagnostics.texture_audit    import run as run_texture_audit
from diagnostics.reference_graph  import run as run_reference_graph
from diagnostics.light_inventory  import run as run_light_inventory
from diagnostics.shader_inventory import run as run_shader_inventory
from diagnostics.render_layer_audit import run as run_render_layer_audit
from diagnostics.aov_report       import run as run_aov_report
from diagnostics.scene_weight     import run as run_scene_weight


# Registry — (display_name, callable)
_DIAGNOSTICS: List[tuple] = [
    ("Scene Weight",        run_scene_weight),
    ("Texture Audit",       run_texture_audit),
    ("Reference Graph",     run_reference_graph),
    ("Light Inventory",     run_light_inventory),
    ("Shader Inventory",    run_shader_inventory),
    ("Render Layer Audit",  run_render_layer_audit),
    ("AOV Report",          run_aov_report),
]


def run_all(progress_callback: Callable[[int, str], None] = None) -> List[DiagnosticResult]:
    """
    Run every diagnostic.

    progress_callback(percent: int, label: str) is called before each check
    so the UI can update a progress bar.

    Returns a list of DiagnosticResult in registry order.
    """
    results: List[DiagnosticResult] = []
    total = len(_DIAGNOSTICS)

    for idx, (name, fn) in enumerate(_DIAGNOSTICS):
        if progress_callback:
            progress_callback(int((idx / total) * 100), name)

        result = DiagnosticResult(name=name)
        t0 = time.perf_counter()

        try:
            result = fn()                          # each diagnostic returns its own result
        except Exception as exc:
            result.add(
                Severity.ERROR,
                f"Diagnostic crashed: {exc}",
                detail=traceback.format_exc(),
            )
            result.summary = "Diagnostic failed — see details"

        result.duration_ms = (time.perf_counter() - t0) * 1000
        results.append(result)

    if progress_callback:
        progress_callback(100, "Complete")

    return results
