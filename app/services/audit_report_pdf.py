from __future__ import annotations

import re
from io import BytesIO
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.audit import AuditEngagement, AuditEngagementItem


COMPLETED_STATUSES = {"Complied", "Not Applicable"}


def _value(details: dict[str, str], key: str, fallback: str = "____________") -> str:
    return escape(details.get(key) or fallback)


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def _findings(items: list[AuditEngagementItem]) -> list[AuditEngagementItem]:
    return [item for item in items if item.status == "Not Complied"]


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {document.page}")
    canvas.restoreState()


def _findings_table(items: list[AuditEngagementItem], styles) -> Table:
    rows = [[
        Paragraph("<b>Sr.</b>", styles["body"]),
        Paragraph("<b>Requirement / provision</b>", styles["body"]),
        Paragraph("<b>Deviation / observation</b>", styles["body"]),
    ]]
    if not items:
        rows.append([
            _paragraph("-", styles["body"]),
            _paragraph("No audit items are marked as Not Complied.", styles["body"]),
            _paragraph("-", styles["body"]),
        ])
    else:
        for index, item in enumerate(items, start=1):
            requirement = " - ".join(
                value for value in [item.law_name, item.provision_name, item.statutory_reference] if value
            )
            observation = item.observation_notes or item.auditor_remarks or "Not recorded"
            rows.append([
                _paragraph(str(index), styles["body"]),
                _paragraph(requirement, styles["body"]),
                _paragraph(observation, styles["body"]),
            ])
    table = Table(rows, colWidths=[12 * mm, 78 * mm, 82 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2F8")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C7D9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def build_audit_report_pdf(
    *,
    engagement: AuditEngagement,
    items: list[AuditEngagementItem],
    laws: list[dict[str, object]],
    report_type: str,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="MR-3 Report" if report_type == "mr3" else "Compliance Audit Report",
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("report-title", parent=base["Title"], alignment=TA_CENTER, fontSize=14, leading=18, spaceAfter=6),
        "subtitle": ParagraphStyle("report-subtitle", parent=base["Normal"], alignment=TA_CENTER, fontSize=10, leading=14, spaceAfter=12),
        "heading": ParagraphStyle("report-heading", parent=base["Heading2"], fontSize=11, leading=15, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("report-body", parent=base["Normal"], fontSize=9.5, leading=14, spaceAfter=7),
    }
    details = engagement.report_details or {}
    period = engagement.audit_period_label
    findings = _findings(items)
    story = []

    if report_type == "mr3":
        story.extend([
            Paragraph("Form No. MR-3", styles["subtitle"]),
            Paragraph("SECRETARIAL AUDIT REPORT", styles["title"]),
            Paragraph(f"FOR THE FINANCIAL YEAR ENDED {period}", styles["subtitle"]),
            _paragraph(f"To,\nThe Members,\n{engagement.client_name}", styles["body"]),
            _paragraph(
                f"I/We have conducted the secretarial audit of {engagement.client_name} for the financial year ended {engagement.audit_period_label}. "
                "The audit has been conducted on the basis of the books, papers, minute books, forms, returns, records and explanations made available for review.",
                styles["body"],
            ),
            Paragraph("Statutes and regulations examined", styles["heading"]),
        ])
        for index, law in enumerate(laws, start=1):
            story.append(_paragraph(f"{index}. {str(law.get('law_name') or 'Law')}", styles["body"]))
        story.extend([
            Paragraph("Observations, qualifications and adverse remarks", styles["heading"]),
            _findings_table(findings, styles),
            Paragraph("Board processes and compliance mechanism", styles["heading"]),
            _paragraph(details.get("board_process_statement") or "PCS review statement to be completed before final issue.", styles["body"]),
            Paragraph("Material events during the audit period", styles["heading"]),
            _paragraph(details.get("material_events") or "PCS input required before final issue.", styles["body"]),
        ])
    else:
        sebi_law_ids = {
            str(law.get("law_id"))
            for law in laws
            if law.get("applicability_scope") == "SEBI_LISTED"
        }
        sebi_laws = [law for law in laws if law.get("applicability_scope") == "SEBI_LISTED"]
        sebi_findings = [item for item in findings if item.law_id in sebi_law_ids]
        story.extend([
            Paragraph("ANNUAL SECRETARIAL COMPLIANCE REPORT", styles["title"]),
            _paragraph(f"{engagement.client_name} - REVIEW PERIOD: {period}", styles["subtitle"]),
            _paragraph(
                f"I/We have examined the records made available by {engagement.client_name} for the review period, including applicable filings, submissions, website disclosures and SEBI regulatory records.",
                styles["body"],
            ),
            Paragraph("Regulations examined", styles["heading"]),
        ])
        for index, law in enumerate(sebi_laws, start=1):
            story.append(_paragraph(f"{index}. {str(law.get('law_name') or 'SEBI regulation')}", styles["body"]))
        story.extend([
            Paragraph("Exceptions and deviations", styles["heading"]),
            _findings_table(sebi_findings, styles),
            Paragraph("Observations in previous reports", styles["heading"]),
            _paragraph(details.get("prior_observations") or "No prior-report observations have been recorded for this engagement.", styles["body"]),
        ])

    story.extend([
        Spacer(1, 14 * mm),
        _paragraph(
            f"Place: {_value(details, 'place')}\nDate: {_value(details, 'report_date')}\n\n"
            f"Signature: {_value(details, 'signer_name')}\n"
            f"Name of Practicing Company Secretary / Firm: {_value(details, 'signer_firm_name')}\n"
            f"ACS/FCS No.: {_value(details, 'membership_number')}\nCP No.: {_value(details, 'certificate_number')}",
            styles["body"],
        ),
    ])
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def report_filename(client_name: str, period: str, report_type: str) -> str:
    report_name = "MR-3" if report_type == "mr3" else "Compliance-Audit-Report"
    clean_client = re.sub(r"[^A-Za-z0-9]+", "-", client_name).strip("-") or "Client"
    clean_period = re.sub(r"[^A-Za-z0-9]+", "-", period).strip("-") or "Period"
    return f"{clean_client}-{clean_period}-{report_name}.pdf"
