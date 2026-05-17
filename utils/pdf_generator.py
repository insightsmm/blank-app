from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
from datetime import datetime
import streamlit as st

# Brand colors
_GREEN = colors.HexColor("#10B981")
_DARK = colors.HexColor("#1F2937")
_GRAY = colors.HexColor("#6B7280")
_LIGHT_GRAY = colors.HexColor("#F9FAFB")
_BORDER = colors.HexColor("#E5E7EB")
_ALT_ROW = colors.HexColor("#F0FDF4")
_WHITE = colors.white


def _styles():
    """Build and return a dict of ParagraphStyles."""
    base = getSampleStyleSheet()

    return {
        "company_name": ParagraphStyle(
            "company_name",
            parent=base["Normal"],
            fontSize=22,
            fontName="Helvetica-Bold",
            textColor=_GREEN,
            spaceAfter=2,
        ),
        "company_detail": ParagraphStyle(
            "company_detail",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=_GRAY,
            spaceAfter=2,
        ),
        "proposal_label": ParagraphStyle(
            "proposal_label",
            parent=base["Normal"],
            fontSize=28,
            fontName="Helvetica-Bold",
            textColor=_GREEN,
            alignment=TA_RIGHT,
        ),
        "proposal_meta": ParagraphStyle(
            "proposal_meta",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=_GRAY,
            alignment=TA_RIGHT,
            spaceAfter=2,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            parent=base["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=_DARK,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=_DARK,
            spaceAfter=3,
            leading=14,
        ),
        "client_name": ParagraphStyle(
            "client_name",
            parent=base["Normal"],
            fontSize=12,
            fontName="Helvetica-Bold",
            textColor=_DARK,
            spaceAfter=3,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=_WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=_DARK,
        ),
        "table_cell_right": ParagraphStyle(
            "table_cell_right",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=_DARK,
            alignment=TA_RIGHT,
        ),
        "total_label": ParagraphStyle(
            "total_label",
            parent=base["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=_DARK,
            alignment=TA_RIGHT,
        ),
        "total_value": ParagraphStyle(
            "total_value",
            parent=base["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=_GREEN,
            alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=_GRAY,
            alignment=TA_CENTER,
        ),
        "terms_title": ParagraphStyle(
            "terms_title",
            parent=base["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=_DARK,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "terms_body": ParagraphStyle(
            "terms_body",
            parent=base["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=_GRAY,
            spaceAfter=2,
            leading=12,
        ),
    }


def generate_proposal_pdf(
    estimate: dict,
    client: dict,
    company: dict,
    line_items: list,
    proposal_notes: str = "",
) -> bytes:
    """
    Generate a professional proposal PDF and return as bytes.

    estimate: estimate record dict
    client: client record dict
    company: company record dict
    line_items: list of {description, qty, unit_price, total}
    proposal_notes: optional additional scope notes
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = _styles()
    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    company_name = company.get("name", "ServicePro")
    company_email = company.get("email", "")
    company_phone = company.get("phone", "")
    company_address = company.get("address", "")
    company_website = company.get("website", "")

    proposal_number = f"P-{datetime.now().strftime('%Y%m%d%H%M')}"
    proposal_date = datetime.now().strftime("%B %d, %Y")
    valid_until = estimate.get("valid_until", "")
    if valid_until:
        try:
            valid_until = datetime.strptime(str(valid_until)[:10], "%Y-%m-%d").strftime("%B %d, %Y")
        except Exception:
            valid_until = str(valid_until)

    # Two-column header: company info left, PROPOSAL right
    company_left = []
    company_left.append(Paragraph(company_name, styles["company_name"]))
    if company_email:
        company_left.append(Paragraph(f"📧 {company_email}", styles["company_detail"]))
    if company_phone:
        company_left.append(Paragraph(f"📞 {company_phone}", styles["company_detail"]))
    if company_address:
        company_left.append(Paragraph(f"📍 {company_address}", styles["company_detail"]))
    if company_website:
        company_left.append(Paragraph(f"🌐 {company_website}", styles["company_detail"]))

    proposal_right = []
    proposal_right.append(Paragraph("PROPOSAL", styles["proposal_label"]))
    proposal_right.append(Paragraph(f"# {proposal_number}", styles["proposal_meta"]))
    proposal_right.append(Paragraph(f"Date: {proposal_date}", styles["proposal_meta"]))
    if valid_until:
        proposal_right.append(Paragraph(f"Valid Until: {valid_until}", styles["proposal_meta"]))

    header_table = Table(
        [[company_left, proposal_right]],
        colWidths=[4 * inch, 3 * inch],
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 12))

    # Green divider
    story.append(HRFlowable(width="100%", thickness=2, color=_GREEN, spaceAfter=12))

    # ── CLIENT INFO BOX ───────────────────────────────────────────────────────
    client_name = client.get("name", "Client")
    client_email_val = client.get("email", "")
    client_phone = client.get("phone", "")
    client_addr_parts = [
        client.get("address", ""),
        client.get("city", ""),
        client.get("state", ""),
        client.get("zip", ""),
    ]
    client_address = ", ".join(p for p in client_addr_parts if p)

    client_info_rows = [
        [Paragraph("<b>PREPARED FOR</b>", styles["company_detail"]), ""],
        [Paragraph(client_name, styles["client_name"]), ""],
    ]
    if client_email_val:
        client_info_rows.append([Paragraph(f"📧 {client_email_val}", styles["body"]), ""])
    if client_phone:
        client_info_rows.append([Paragraph(f"📞 {client_phone}", styles["body"]), ""])
    if client_address:
        client_info_rows.append([Paragraph(f"📍 {client_address}", styles["body"]), ""])

    client_table = Table(client_info_rows, colWidths=[5 * inch, 2 * inch])
    client_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 1, _BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    story.append(client_table)
    story.append(Spacer(1, 16))

    # ── SCOPE OF WORK ─────────────────────────────────────────────────────────
    story.append(Paragraph("Scope of Work", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER, spaceAfter=6))

    trade_type = (estimate.get("trade_type") or "Service").title()
    story.append(Paragraph(f"<b>Service Type:</b> {trade_type}", styles["body"]))

    start_date = estimate.get("inputs", {}).get("start_date", "") if isinstance(estimate.get("inputs"), dict) else ""
    if start_date:
        story.append(Paragraph(f"<b>Proposed Start Date:</b> {start_date}", styles["body"]))

    if proposal_notes:
        story.append(Spacer(1, 6))
        for line in proposal_notes.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["body"]))

    if estimate.get("notes"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Additional Notes:</b> {estimate['notes']}", styles["body"]))

    story.append(Spacer(1, 16))

    # ── LINE ITEMS TABLE ──────────────────────────────────────────────────────
    story.append(Paragraph("Estimate Breakdown", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER, spaceAfter=6))

    # Table header row
    table_data = [
        [
            Paragraph("Service / Item", styles["table_header"]),
            Paragraph("Qty", styles["table_header"]),
            Paragraph("Unit Price", styles["table_header"]),
            Paragraph("Total", styles["table_header"]),
        ]
    ]

    # Line item rows
    for i, item in enumerate(line_items or []):
        description = str(item.get("description", "Service"))
        qty = item.get("qty", item.get("quantity", 1))
        unit_price = float(item.get("unit_price", 0) or 0)
        total = float(item.get("total", 0) or 0)

        row_bg = _ALT_ROW if i % 2 == 0 else _WHITE
        table_data.append(
            [
                Paragraph(description, styles["table_cell"]),
                Paragraph(str(qty), styles["table_cell_right"]),
                Paragraph(f"${unit_price:,.2f}", styles["table_cell_right"]),
                Paragraph(f"${total:,.2f}", styles["table_cell_right"]),
            ]
        )

    # Summary rows
    subtotal = float(estimate.get("subtotal", 0) or 0)
    tax = float(estimate.get("tax", 0) or 0)
    discount = float(estimate.get("discount", 0) or 0)
    grand_total = float(estimate.get("total", 0) or 0)

    # Blank separator row
    table_data.append(["", "", "", ""])

    table_data.append(
        ["", "", Paragraph("Subtotal:", styles["table_cell_right"]), Paragraph(f"${subtotal:,.2f}", styles["table_cell_right"])]
    )
    if tax > 0:
        table_data.append(
            ["", "", Paragraph("Tax:", styles["table_cell_right"]), Paragraph(f"${tax:,.2f}", styles["table_cell_right"])]
        )
    if discount > 0:
        table_data.append(
            ["", "", Paragraph("Discount:", styles["table_cell_right"]), Paragraph(f"-${discount:,.2f}", styles["table_cell_right"])]
        )
    table_data.append(
        ["", "", Paragraph("<b>TOTAL DUE:</b>", styles["total_label"]), Paragraph(f"<b>${grand_total:,.2f}</b>", styles["total_value"])]
    )

    num_items = len(line_items or [])
    item_row_indices = list(range(1, num_items + 1))

    items_table = Table(
        table_data,
        colWidths=[3.5 * inch, 0.7 * inch, 1.2 * inch, 1.1 * inch],
    )

    table_style = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUND", (0, 0), (-1, 0), _GREEN),
        # All cells padding
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Alternating row colors for data rows
        ("GRID", (0, 0), (-1, num_items), 0.5, _BORDER),
        # Bottom border for summary section
        ("LINEABOVE", (2, num_items + 1), (3, num_items + 1), 1, _BORDER),
        # Bold total row
        ("FONTNAME", (2, -1), (3, -1), "Helvetica-Bold"),
        ("FONTSIZE", (2, -1), (3, -1), 11),
        ("LINEABOVE", (2, -1), (3, -1), 1.5, _GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]

    # Alternating row backgrounds
    for i in range(num_items):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), _ALT_ROW))

    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 20))

    # ── TERMS & CONDITIONS ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER, spaceAfter=8))
    story.append(Paragraph("Terms & Conditions", styles["terms_title"]))

    terms = [
        "<b>Acceptance:</b> This proposal is valid for 30 days from the date issued. "
        "Acceptance of this proposal constitutes a binding agreement between the client and service provider.",
        "<b>Payment Terms:</b> A deposit of 50% is required to schedule the work. "
        "The remaining balance is due upon completion of services. We accept cash, check, and major credit cards.",
        "<b>Changes & Additions:</b> Any changes to the scope of work must be agreed upon in writing. "
        "Additional work requested beyond this proposal will be billed at our standard rates.",
        "<b>Warranty:</b> All workmanship is guaranteed for 1 year from the date of completion. "
        "Material warranties are subject to manufacturer terms.",
        "<b>Liability:</b> The service provider carries full general liability insurance and workers' compensation. "
        "We are not responsible for pre-existing conditions discovered during the course of work.",
        "<b>Cancellation:</b> Cancellations must be made at least 48 hours prior to the scheduled start date. "
        "Deposits may be forfeited for late cancellations.",
    ]

    for term in terms:
        story.append(Paragraph(term, styles["terms_body"]))

    story.append(Spacer(1, 12))

    # ── DIGITAL ACCEPTANCE ────────────────────────────────────────────────────
    acceptance_data = [
        [
            Paragraph("<b>Digital Acceptance</b>", styles["body"]),
            "",
        ],
        [
            Paragraph(
                "By proceeding with this service, client accepts the above terms and authorizes "
                "the work described in this proposal.",
                styles["terms_body"],
            ),
            "",
        ],
        [
            Paragraph("Client Signature: _________________________________", styles["body"]),
            Paragraph(f"Date: _______________", styles["body"]),
        ],
        [
            Paragraph(f"Printed Name: _________________________________", styles["body"]),
            "",
        ],
    ]

    acceptance_table = Table(acceptance_data, colWidths=[4.5 * inch, 2.5 * inch])
    acceptance_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 1, _BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("SPAN", (0, 0), (1, 0)),
            ("SPAN", (0, 1), (1, 1)),
        ])
    )
    story.append(acceptance_table)
    story.append(Spacer(1, 16))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER, spaceAfter=6))
    story.append(
        Paragraph(
            f"<b>{company_name}</b> | Professional Field Services | Thank you for your business!",
            styles["footer"],
        )
    )
    if company_email or company_phone:
        contact = " | ".join(filter(None, [company_email, company_phone]))
        story.append(Paragraph(contact, styles["footer"]))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
