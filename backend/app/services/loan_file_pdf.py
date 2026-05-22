from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime


'''helper function'''''
def color_to_hex(c):
    return f"#{c.hexval()[2:].upper()}"  # '0x15803d' -> '15803D' -> '#15803D'

# ─── Color Palette ───────────────────────────────────────────────
DARK       = colors.HexColor("#0f172a")
BLUE       = colors.HexColor("#1e40af")
GREEN      = colors.HexColor("#15803d")
AMBER      = colors.HexColor("#b45309")
RED        = colors.HexColor("#b91c1c")
LIGHT_GRAY = colors.HexColor("#f8fafc")
BORDER     = colors.HexColor("#e2e8f0")
TEXT_GRAY  = colors.HexColor("#64748b")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold",
            fontSize=22, textColor=DARK,
            spaceAfter=4
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica",
            fontSize=11, textColor=TEXT_GRAY,
            spaceAfter=2
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold",
            fontSize=12, textColor=BLUE,
            spaceBefore=14, spaceAfter=6
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica",
            fontSize=8, textColor=TEXT_GRAY,
            spaceAfter=1
        ),
        "value": ParagraphStyle(
            "value", fontName="Helvetica-Bold",
            fontSize=10, textColor=DARK,
            spaceAfter=4
        ),
        "normal": ParagraphStyle(
            "normal", fontName="Helvetica",
            fontSize=9, textColor=DARK,
            spaceAfter=2
        ),
        "small": ParagraphStyle(
            "small", fontName="Helvetica",
            fontSize=7, textColor=TEXT_GRAY
        ),
        "approve": ParagraphStyle(
            "approve", fontName="Helvetica-Bold",
            fontSize=14, textColor=GREEN,
            alignment=TA_CENTER
        ),
        "right": ParagraphStyle(
            "right", fontName="Helvetica",
            fontSize=8, textColor=TEXT_GRAY,
            alignment=TA_RIGHT
        ),
    }


def _metric_table(data: list, col_widths=None) -> Table:
    """Create a clean metrics table."""
    if not col_widths:
        col_widths = [45*mm] * (170 // 45)

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("GRID",       (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return t


def generate_loan_package_pdf(loan_package: dict) -> bytes:
    """
    Generate professional loan file PDF from loan package data.
    Returns PDF as bytes — save to file or send as response.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
        title="CreditBridge Loan Package"
    )

    S = _styles()
    story = []
    W = 174*mm  # usable width

    pkg = loan_package.get("loan_package", loan_package)
    biz = pkg.get("business_profile", {})
    credit = pkg.get("credit_assessment", {})
    fin = pkg.get("financial_summary", {})
    cf = pkg.get("cash_flow_summary", {})
    wc = pkg.get("working_capital", {})
    rec = pkg.get("lender_recommendation", {})
    pl = pkg.get("pl_statement", {})
    cf_detail = pkg.get("cash_flow_statement", {})

    # ── PAGE 1: COVER ─────────────────────────────────────────────

    story.append(Spacer(1, 8*mm))

    # Header bar
    header_data = [[
        Paragraph("<b>CREDITBRIDGE</b>", ParagraphStyle(
            "hdr", fontName="Helvetica-Bold",
            fontSize=10, textColor=colors.white
        )),
        Paragraph("LOAN READINESS PACKAGE", ParagraphStyle(
            "hdr2", fontName="Helvetica",
            fontSize=8, textColor=colors.HexColor("#93c5fd"),
            alignment=TA_RIGHT
        ))
    ]]
    ht = Table(header_data, colWidths=[W*0.5, W*0.5])
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(ht)
    story.append(Spacer(1, 8*mm))

    # Business name + details
    story.append(Paragraph(biz.get("name", "Business Name"), S["title"]))
    story.append(Paragraph(
        f"{biz.get('business_type', '').title()} | {biz.get('city', '')} | "
        f"Owner: {biz.get('owner', '')}",
        S["subtitle"]
    ))
    story.append(HRFlowable(width=W, thickness=1, color=BORDER, spaceAfter=8))

    # Score highlight box
    score = credit.get("score", 0)
    grade = credit.get("grade", "")
    score_color = GREEN if score >= 750 else AMBER if score >= 650 else RED

    score_data = [[
        Paragraph(
            f'<font color="{color_to_hex(score_color)}"><b>{score}</b></font>',
            ParagraphStyle("sc", fontName="Helvetica-Bold",
                           fontSize=36, textColor=score_color, alignment=TA_CENTER)
        ),
        [
            Paragraph(f"Grade: <b>{grade}</b>", ParagraphStyle(
                "gr", fontName="Helvetica-Bold",
                fontSize=16, textColor=score_color
            )),
            Spacer(1, 4),
            Paragraph(
                f"Recommended Limit: <b>Rs. {credit.get('recommended_limit', 0)/100000:.0f}L</b>",
                ParagraphStyle("rl", fontName="Helvetica-Bold", fontSize=12, textColor=DARK)
            ),
            Spacer(1, 4),
            Paragraph(
                f"Confidence: {credit.get('confidence', 0)*100:.0f}% | "
                f"Data: {fin.get('data_months', 12)} months",
                ParagraphStyle("conf", fontName="Helvetica", fontSize=9, textColor=TEXT_GRAY)
            ),
        ],
        Paragraph(
            f"<b>{rec.get('decision', 'REVIEW')}</b>",
            ParagraphStyle("dec", fontName="Helvetica-Bold",
                           fontSize=18,
                           textColor=GREEN if rec.get("decision") == "APPROVE" else AMBER,
                           alignment=TA_CENTER)
        )
    ]]

    st = Table(score_data, colWidths=[35*mm, W-85*mm, 50*mm])
    st.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (0, 0),  "CENTER"),
        ("ALIGN",         (2, 0), (2, 0),  "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(st)
    story.append(Spacer(1, 6*mm))

    # Key metrics row
    story.append(Paragraph("KEY FINANCIAL METRICS", S["section"]))
    metrics = [
        ["Avg Monthly Revenue", "Gross Margin", "Net Margin", "Positive Months"],
        [
            f"Rs. {fin.get('avg_monthly_revenue', 0)/100000:.1f}L",
            f"{fin.get('gross_margin_pct', 0):.1f}%",
            f"{fin.get('net_margin_pct', 0):.1f}%",
            f"{fin.get('profitable_months', 0)}/12"
        ],
        ["Avg Monthly Inflow", "Avg Net Cash Flow", "Collection Days", "Health"],
        [
            f"Rs. {cf.get('avg_monthly_inflow', 0)/100000:.1f}L",
            f"Rs. {cf.get('avg_net_cash_flow', 0)/100000:.1f}L",
            f"{wc.get('avg_collection_days', 0):.0f} days",
            wc.get("health", "N/A").replace("_", " ").title()
        ]
    ]
    mt = Table(metrics, colWidths=[W/4]*4)
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("BACKGROUND",    (0, 2), (-1, 2), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR",     (0, 2), (-1, 2), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME",      (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("FONTSIZE",      (0, 1), (-1, 1), 11),
        ("FONTSIZE",      (0, 3), (-1, 3), 11),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [colors.white]),
        ("ROWBACKGROUNDS", (0, 3), (-1, 3), [LIGHT_GRAY]),
    ]))
    story.append(mt)
    story.append(Spacer(1, 6*mm))

    # Business profile + Risk flags side by side
    story.append(Paragraph("BUSINESS PROFILE", S["section"]))
    profile_data = [
        ["Field", "Details"],
        ["Business Name", biz.get("name", "")],
        ["Owner", biz.get("owner", "")],
        ["GSTIN", biz.get("gstin", "")],
        ["PAN", biz.get("pan", "")],
        ["City", biz.get("city", "")],
        ["Sector", biz.get("business_type", "").title()],
        ["Phone", biz.get("phone", "")],
    ]
    pt = Table(profile_data, colWidths=[50*mm, W/2 - 50*mm])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))

    flags = credit.get("flags", [])
    positives = credit.get("positive_factors", [])

    risk_items = [["Risk Signals"]]
    for f in flags:
        risk_items.append([f"  WARNING  {f.replace('_', ' ').title()}"])
    if not flags:
        risk_items.append(["  No risk flags detected"])

    risk_items.append(["Positive Factors"])
    for p in positives:
        risk_items.append([f"  OK  {p}"])

    rt = Table(risk_items, colWidths=[W/2 - 6*mm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("BACKGROUND",  (0, len(flags)+1), (-1, len(flags)+1), colors.HexColor("#14532d")),
        ("TEXTCOLOR",   (0, len(flags)+1), (-1, len(flags)+1), colors.white),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, len(flags)), [colors.HexColor("#fef2f2"), LIGHT_GRAY]),
        ("ROWBACKGROUNDS", (0, len(flags)+2), (-1, -1), [colors.HexColor("#f0fdf4"), LIGHT_GRAY]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))

    side_data = [[pt, rt]]
    side_t = Table(side_data, colWidths=[W/2, W/2])
    side_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 4),
        ("LEFTPADDING", (1, 0), (1, 0), 4),
    ]))
    story.append(side_t)

    # Footer page 1
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}  |  "
        f"CreditBridge Intelligence Platform  |  Confidential",
        S["small"]
    ))

    # ── PAGE 2: P&L + CASH FLOW ───────────────────────────────────
    story.append(PageBreak())

    story.append(Paragraph("PROFIT & LOSS STATEMENT", S["section"]))
    story.append(Paragraph(
        f"Period: {pl.get('period', 'N/A')}  |  Auto-generated from bank transaction data",
        S["small"]
    ))
    story.append(Spacer(1, 3*mm))

    pl_header = ["Month", "Revenue", "COGS", "Gross Profit", "GM%", "Expenses", "Net Profit", "NM%"]
    pl_rows = [pl_header]
    for row in pl.get("monthly_breakdown", []):
        expenses = row.get("salary", 0) + row.get("other_expense", 0)
        pl_rows.append([
            row["month"],
            f"Rs.{row['revenue']/100000:.1f}L",
            f"Rs.{row['cogs']/100000:.1f}L",
            f"Rs.{row['gross_profit']/100000:.1f}L",
            f"{row['gross_margin_pct']:.0f}%",
            f"Rs.{expenses/100000:.1f}L",
            f"Rs.{row['net_profit']/100000:.1f}L",
            f"{row['net_margin_pct']:.0f}%"
        ])

    # Summary row
    s = pl.get("summary", {})
    pl_rows.append([
        "TOTAL",
        f"Rs.{s.get('total_revenue', 0)/100000:.1f}L",
        "",
        f"Rs.{s.get('total_gross_profit', 0)/100000:.1f}L",
        f"{s.get('gross_margin_pct', 0):.0f}%",
        "",
        f"Rs.{s.get('total_net_profit', 0)/100000:.1f}L",
        f"{s.get('net_margin_pct', 0):.0f}%"
    ])

    cw = [20*mm, 22*mm, 18*mm, 24*mm, 14*mm, 20*mm, 24*mm, 14*mm]
    pl_t = Table(pl_rows, colWidths=cw)
    pl_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), BLUE),
        ("TEXTCOLOR",     (0, -1), (-1, -1), colors.white),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.3, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT_GRAY]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(pl_t)
    story.append(Spacer(1, 6*mm))

    # Cash Flow Table
    story.append(Paragraph("CASH FLOW STATEMENT", S["section"]))
    story.append(Paragraph(
        f"Period: {cf_detail.get('period', 'N/A')}  |  "
        f"Positive months: {cf_detail.get('summary', {}).get('positive_months', 0)}/12",
        S["small"]
    ))
    story.append(Spacer(1, 3*mm))

    cf_header = ["Month", "Total Inflow", "Total Outflow", "Net Cash Flow", "Closing Balance", "Status"]
    cf_rows = [cf_header]
    for row in cf_detail.get("monthly_breakdown", []):
        status = "POSITIVE" if row["is_positive"] else "NEGATIVE"
        cf_rows.append([
            row["month"],
            f"Rs.{row['inflow']/100000:.1f}L",
            f"Rs.{row['outflow']/100000:.1f}L",
            f"Rs.{row['net_cash_flow']/100000:.1f}L",
            f"Rs.{row['closing_balance']/100000:.1f}L",
            status
        ])

    cw2 = [22*mm, 30*mm, 30*mm, 30*mm, 32*mm, 30*mm]
    cf_t = Table(cf_rows, colWidths=cw2)
    cf_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN",         (5, 0), (5, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.3, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))

    # Color positive/negative
    for i, row in enumerate(cf_detail.get("monthly_breakdown", []), 1):
        color = colors.HexColor("#f0fdf4") if row["is_positive"] else colors.HexColor("#fef2f2")
        cf_t.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), color)]))
        text_c = GREEN if row["is_positive"] else RED
        cf_t.setStyle(TableStyle([("TEXTCOLOR", (5, i), (5, i), text_c)]))

    story.append(cf_t)
    story.append(Spacer(1, 4*mm))

    # Lender recommendation box
    story.append(HRFlowable(width=W, thickness=1, color=BLUE, spaceAfter=4))
    rec_color = GREEN if rec.get("decision") == "APPROVE" else AMBER
    rec_data = [[
        Paragraph(
            f"LENDER RECOMMENDATION: <b>{rec.get('decision', '')}</b>",
            ParagraphStyle("rec", fontName="Helvetica-Bold",
                           fontSize=12, textColor=rec_color)
        ),
        Paragraph(
            f"Amount: <b>Rs. {rec.get('suggested_amount', 0)/100000:.0f}L</b>  |  "
            f"Tenure: <b>{rec.get('tenure_months', 12)} months</b>  |  "
            f"Basis: {rec.get('basis', '')}",
            ParagraphStyle("rec2", fontName="Helvetica",
                           fontSize=9, textColor=DARK, alignment=TA_RIGHT)
        )
    ]]
    rt2 = Table(rec_data, colWidths=[W*0.45, W*0.55])
    rt2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 1, rec_color),
    ]))
    story.append(rt2)
    story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "DISCLAIMER: This report is auto-generated by CreditBridge using bank transaction data "
        "and AI-based analysis. It is indicative and does not constitute a formal credit guarantee. "
        "Lenders should perform their own due diligence.",
        S["small"]
    ))

    doc.build(story)
    return buffer.getvalue()