"""PDF report generator (uses reportlab)."""
from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils.helpers import get_logger

logger = get_logger(__name__)


def generate(year: int, month: int, all_metrics: dict[str, dict], output_dir: str = "reports") -> str:
    """Generate a PDF report and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"social_report_{year}_{month:02d}.pdf")

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = f"Social Media Report – {date(year, month, 1).strftime('%B %Y')}"
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Table data
    table_data = [["Platform", "Metric", "Value"]]
    for platform, metrics in all_metrics.items():
        if not metrics:
            continue
        for metric, value in metrics.items():
            table_data.append([
                platform.capitalize(),
                metric.replace("_", " ").title(),
                str(value),
            ])

    if len(table_data) > 1:
        tbl = Table(table_data, colWidths=[4 * cm, 7 * cm, 4 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EBF0FA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(tbl)
    else:
        elements.append(Paragraph("No metrics data available.", styles["Normal"]))

    doc.build(elements)
    logger.info("PDF report saved: %s", filepath)
    return filepath
