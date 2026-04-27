"""
AOV Report Diagnostic
Checks Arnold AOV (Arbitrary Output Variable) configuration:
- AOVs defined but not enabled
- Duplicate AOV names
- AOV output paths not set
- Missing expected AOVs (beauty, diffuse, specular)
- Non-standard AOV naming
Works with Arnold (aiAOV nodes). Gracefully skips if Arnold not loaded.
"""

import re
import maya.cmds as cmds
from core.result import DiagnosticResult, Severity

# AOVs a lighting pipeline typically expects
EXPECTED_AOVS = {"beauty", "diffuse", "specular", "shadow", "Z", "N"}
NAMING_RE     = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

AOV_DESCRIPTIONS = {
    "beauty":   "The final combined render — the base layer every composite starts from.",
    "diffuse":  "Diffuse lighting contribution — lets compositors adjust surface colour and lighting independently.",
    "specular": "Specular highlights — allows reflections to be tweaked or removed in comp without a re-render.",
    "shadow":   "Shadow pass — used to soften, tint, or remove shadows at the compositing stage.",
    "Z":        "Depth pass (distance from camera in world units) — required for depth-of-field and atmospheric fog in comp.",
    "N":        "World-space surface normals — used for relighting, normal-based colour grading, and contact shadow effects in comp.",
}


def _arnold_loaded() -> bool:
    try:
        return "Arnold" in (cmds.renderer(query=True, namesOfAvailableRenderers=True) or [])
    except Exception:
        return False


def run() -> DiagnosticResult:
    result = DiagnosticResult(name="AOV Report")

    if not _arnold_loaded():
        result.add(Severity.INFO,
                   "Arnold renderer not loaded — AOV check skipped",
                   detail="Load Arnold via Plug-in Manager to enable this check.")
        result.summary = "Arnold not loaded"
        return result

    aov_nodes = cmds.ls(type="aiAOV") or []

    if not aov_nodes:
        result.add(Severity.WARNING,
                   "No AOVs defined",
                   detail="Add AOVs in Render Settings > AOVs for multi-pass compositing.")
        result.summary = "No AOVs configured"
        return result

    defined_names = set()
    enabled_names = set()
    duplicates    = 0
    disabled      = 0
    bad_names     = 0

    for aov in aov_nodes:
        try:
            name = cmds.getAttr(f"{aov}.name") or ""
        except Exception:
            name = aov

        # ── duplicate ────────────────────────────────────────────────────────
        if name in defined_names:
            result.add(Severity.ERROR,
                       f"Duplicate AOV name: {name}",
                       node=aov)
            duplicates += 1
        defined_names.add(name)

        # ── enabled? ─────────────────────────────────────────────────────────
        try:
            enabled = cmds.getAttr(f"{aov}.enabled")
        except Exception:
            enabled = True

        if not enabled:
            result.add(Severity.WARNING,
                       f"AOV is disabled: {name}",
                       detail="Disabled AOVs will not be written during render.",
                       node=aov)
            disabled += 1
        else:
            enabled_names.add(name)

        # ── naming convention ────────────────────────────────────────────────
        if name and not NAMING_RE.match(name):
            result.add(Severity.WARNING,
                       f"AOV name contains invalid characters: {name}",
                       detail="Use only letters, digits, and underscores.",
                       node=aov)
            bad_names += 1

    # ── missing expected AOVs ────────────────────────────────────────────────
    missing = EXPECTED_AOVS - defined_names
    for m in sorted(missing):
        result.add(Severity.WARNING,
                   f"Expected AOV not defined: '{m}'",
                   detail=AOV_DESCRIPTIONS.get(m, "Compositors typically expect this AOV to be present.")
                          + "\nFix: open Render Settings > AOVs tab and add this AOV.")

    if not result.items:
        result.add(Severity.PASS, f"All {len(aov_nodes)} AOV(s) look good")

    result.summary = (
        f"{len(aov_nodes)} AOV(s) | {disabled} disabled | "
        f"{duplicates} duplicate | {len(missing)} missing expected"
    )
    return result
