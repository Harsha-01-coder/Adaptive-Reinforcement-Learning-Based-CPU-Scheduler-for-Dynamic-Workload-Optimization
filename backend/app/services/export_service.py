"""
Export Service — CSV and PDF report generation.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from typing import Any, Dict, List


def export_csv(simulation_result: Dict[str, Any]) -> bytes:
    """Generate a CSV export of simulation process results."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "pid", "arrival_time", "burst_time", "priority", "process_type",
        "start_time", "completion_time", "waiting_time",
        "turnaround_time", "response_time", "context_switches"
    ])

    for p in simulation_result.get("processes", []):
        writer.writerow([
            p.get("pid"), p.get("arrival_time"), p.get("burst_time"),
            p.get("priority"), p.get("process_type"), p.get("start_time"),
            p.get("completion_time"), p.get("waiting_time"),
            p.get("turnaround_time"), p.get("response_time"),
            p.get("context_switches"),
        ])

    return output.getvalue().encode("utf-8")


def export_pdf(simulation_result: Dict[str, Any]) -> bytes:
    """Generate a PDF report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        # Fallback: return a simple text-based "PDF"
        content = _text_report(simulation_result)
        return content.encode("utf-8")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=18, textColor=colors.HexColor("#6366f1"),
        spaceAfter=12,
    )
    story.append(Paragraph("CPU Scheduler Simulation Report", title_style))
    story.append(Paragraph(
        f"Algorithm: <b>{simulation_result.get('algorithm', 'N/A')}</b> | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── Metrics ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Performance Metrics", styles["Heading2"]))
    metrics = simulation_result.get("metrics", {})
    metric_data = [
        ["Metric", "Value"],
        ["Avg Waiting Time", f"{metrics.get('avg_waiting_time', 0):.4f}"],
        ["Avg Turnaround Time", f"{metrics.get('avg_turnaround_time', 0):.4f}"],
        ["Avg Response Time", f"{metrics.get('avg_response_time', 0):.4f}"],
        ["CPU Utilization", f"{metrics.get('cpu_utilization', 0):.2f}%"],
        ["Throughput", f"{metrics.get('throughput', 0):.4f} proc/unit"],
        ["Context Switches", str(metrics.get('total_context_switches', 0))],
        ["Fairness Score (Jain's)", f"{metrics.get('fairness_score', 0):.4f}"],
        ["Makespan", f"{metrics.get('makespan', 0):.4f}"],
    ]
    metric_table = Table(metric_data, colWidths=[8*cm, 8*cm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f8ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Process Table ─────────────────────────────────────────────────────────
    story.append(Paragraph("Process Details", styles["Heading2"]))
    proc_data = [["PID", "Arrival", "Burst", "Priority", "Start", "Completion", "Wait", "TAT", "RT"]]
    for p in simulation_result.get("processes", []):
        proc_data.append([
            str(p.get("pid")),
            f"{p.get('arrival_time', 0):.1f}",
            f"{p.get('burst_time', 0):.1f}",
            str(p.get("priority")),
            f"{p.get('start_time', 0):.1f}",
            f"{p.get('completion_time', 0):.1f}",
            f"{p.get('waiting_time', 0):.2f}",
            f"{p.get('turnaround_time', 0):.2f}",
            f"{p.get('response_time', 0):.2f}",
        ])

    proc_table = Table(proc_data)
    proc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0ff")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(proc_table)

    doc.build(story)
    return buffer.getvalue()


def _text_report(result: Dict[str, Any]) -> str:
    """Fallback plain-text report when ReportLab is unavailable."""
    lines = [
        f"CPU Scheduler Simulation Report",
        f"Algorithm: {result.get('algorithm', 'N/A')}",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "=== Metrics ===",
    ]
    for k, v in result.get("metrics", {}).items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("=== Processes ===")
    lines.append("PID  Arrival  Burst  Priority  Start  Completion  Wait  TAT  RT")
    for p in result.get("processes", []):
        lines.append(
            f"{p['pid']:4d}  {p['arrival_time']:7.1f}  {p['burst_time']:5.1f}  "
            f"{p['priority']:8d}  {p['start_time']:5.1f}  "
            f"{p['completion_time']:10.1f}  {p['waiting_time']:4.2f}  "
            f"{p['turnaround_time']:5.2f}  {p['response_time']:.2f}"
        )
    return "\n".join(lines)
