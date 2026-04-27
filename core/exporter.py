"""
Exporter
Converts a list of DiagnosticResult objects into CSV or HTML reports.
"""

import csv
import datetime
import os
from typing import List

from core.result import DiagnosticResult, Severity


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ─────────────────────────────────────────────────────────────── CSV
def export_csv(results: List[DiagnosticResult], path: str = None) -> str:
    """Write results to CSV. Returns the file path written."""
    if path is None:
        path = os.path.join(os.path.expanduser("~"), f"scene_profiler_{_timestamp()}.csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Diagnostic", "Severity", "Message", "Detail", "Node", "Duration (ms)"])
        for result in results:
            if not result.items:
                writer.writerow([result.name, "PASS", result.summary, "", "", f"{result.duration_ms:.1f}"])
            for item in result.items:
                writer.writerow([
                    result.name,
                    item.severity.value.upper(),
                    item.message,
                    item.detail or "",
                    item.node or "",
                    f"{result.duration_ms:.1f}",
                ])
    return path


# ─────────────────────────────────────────────────────────────── HTML
_SEVERITY_COLOR = {
    Severity.PASS:    "#4caf76",
    Severity.WARNING: "#e8a838",
    Severity.ERROR:   "#e85454",
    Severity.INFO:    "#5b9bd5",
}

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Scene Profiler Report</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background:#1e1e1e; color:#ccc; margin:0; padding:24px; }}
  h1   {{ color:#fff; font-size:20px; margin-bottom:4px; }}
  .meta{{ color:#888; font-size:12px; margin-bottom:24px; }}
  .card{{ background:#2a2a2a; border-radius:6px; margin-bottom:16px; overflow:hidden; }}
  .card-header {{ display:flex; align-items:center; padding:12px 16px; gap:12px; }}
  .badge {{ border-radius:4px; padding:2px 10px; font-size:11px; font-weight:700;
             text-transform:uppercase; color:#fff; }}
  .card-title  {{ font-size:14px; font-weight:600; color:#fff; flex:1; }}
  .duration    {{ font-size:11px; color:#666; }}
  table  {{ width:100%; border-collapse:collapse; font-size:12px; }}
  th     {{ background:#333; color:#aaa; padding:8px 16px; text-align:left; font-weight:600; }}
  td     {{ padding:8px 16px; border-top:1px solid #333; vertical-align:top; }}
  .sev-pass    {{ color:#4caf76; }} .sev-warning {{ color:#e8a838; }}
  .sev-error   {{ color:#e85454; }} .sev-info    {{ color:#5b9bd5; }}
</style>
</head>
<body>
<h1>🎬 Maya Scene Profiler Report</h1>
<div class="meta">Generated: {timestamp}</div>
{cards}
</body>
</html>"""

_CARD_TEMPLATE = """
<div class="card">
  <div class="card-header">
    <span class="badge" style="background:{color}">{severity}</span>
    <span class="card-title">{name}</span>
    <span class="duration">{duration:.0f} ms</span>
  </div>
  {table}
</div>"""

_ROW_TEMPLATE = """<tr>
  <td class="sev-{sev_lower}">{severity}</td>
  <td>{message}</td>
  <td>{node}</td>
  <td style="color:#666;font-size:11px">{detail}</td>
</tr>"""


def export_html(results: List[DiagnosticResult], path: str = None) -> str:
    """Write results to HTML. Returns the file path written."""
    if path is None:
        path = os.path.join(os.path.expanduser("~"), f"scene_profiler_{_timestamp()}.html")

    cards_html = ""
    for result in results:
        sev   = result.severity
        color = _SEVERITY_COLOR[sev]

        if result.items:
            rows = "".join(
                _ROW_TEMPLATE.format(
                    sev_lower = item.severity.value,
                    severity  = item.severity.value.upper(),
                    message   = item.message,
                    node      = item.node or "",
                    detail    = (item.detail or "").replace("\n", "<br>"),
                )
                for item in result.items
            )
            table = (
                "<table><tr>"
                "<th>Severity</th><th>Message</th><th>Node</th><th>Detail</th>"
                f"</tr>{rows}</table>"
            )
        else:
            table = f'<p style="padding:8px 16px;color:#4caf76;margin:0">✓ {result.summary or "No issues found"}</p>'

        cards_html += _CARD_TEMPLATE.format(
            color    = color,
            severity = sev.value.upper(),
            name     = result.name,
            duration = result.duration_ms,
            table    = table,
        )

    html = _HTML_TEMPLATE.format(
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        cards     = cards_html,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path
