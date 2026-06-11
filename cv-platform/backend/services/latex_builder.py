"""Builds CV documents from structured CV data.

build_latex_cv() renders a moderncv "banking" style LaTeX source that the
user can compile locally with lualatex/xelatex. render_cv_pdf() renders an
actual downloadable PDF using reportlab (pure Python, no system LaTeX
required) so the platform works without a LaTeX toolchain installed.
"""

import io
import json
import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib import colors

_FONTS_PATH = Path(__file__).parent.parent / "data" / "cv_fonts.json"
_FONTS: dict[str, dict] = {f["id"]: f for f in json.loads(_FONTS_PATH.read_text())}
_DEFAULT_FONT_ID = "classic"


def _font(font_id: str | None) -> dict:
    return _FONTS.get(font_id or _DEFAULT_FONT_ID, _FONTS[_DEFAULT_FONT_ID])


_LATEX_SPECIAL = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}
_LATEX_RE = re.compile("|".join(re.escape(k) for k in _LATEX_SPECIAL))


def _escape_latex(text: str) -> str:
    if not text:
        return ""
    return _LATEX_RE.sub(lambda m: _LATEX_SPECIAL[m.group()], str(text))


_MODERNCV_TEMPLATE = r"""\documentclass[11pt,a4paper,sans]{{moderncv}}
\moderncvstyle{{banking}}
\moderncvcolor{{blue}}
{font_preamble}
\usepackage[scale=0.85]{{geometry}}

\name{{{first_name}}}{{{last_name}}}
\title{{{headline}}}
{contact_lines}

\begin{{document}}
\makecvtitle

{summary_section}
{experience_section}
{education_section}
{skills_section}
{certifications_section}
\end{{document}}
"""


def _contact_lines(data: dict) -> str:
    lines = []
    if data.get("email"):
        lines.append(rf"\email{{{_escape_latex(data['email'])}}}")
    if data.get("phone"):
        lines.append(rf"\phone{{{_escape_latex(data['phone'])}}}")
    return "\n".join(lines)


def _summary_section(data: dict) -> str:
    if not data.get("summary"):
        return ""
    return (
        "\\section{Summary}\n"
        f"\\cvline{{}}{{{_escape_latex(data['summary'])}}}\n"
    )


def _experience_section(data: dict) -> str:
    experience = data.get("experience") or []
    if not experience:
        return ""
    parts = ["\\section{Experience}"]
    for exp in experience:
        bullets = exp.get("bullets") or []
        bullet_tex = ""
        if bullets:
            items = "\n".join(f"\\item {_escape_latex(b)}" for b in bullets)
            bullet_tex = f"\\begin{{itemize}}\n{items}\n\\end{{itemize}}"
        parts.append(
            "\\cventry{{{start}--{end}}}{{{title}}}{{{company}}}{{}}{{}}{{{desc}}}".format(
                start=_escape_latex(exp.get("start_date", "")),
                end=_escape_latex(exp.get("end_date", "") or "Present"),
                title=_escape_latex(exp.get("title", "")),
                company=_escape_latex(exp.get("company", "")),
                desc=bullet_tex,
            )
        )
    return "\n".join(parts) + "\n"


def _education_section(data: dict) -> str:
    education = data.get("education") or []
    if not education:
        return ""
    parts = ["\\section{Education}"]
    for edu in education:
        degree_field = ", ".join(filter(None, [edu.get("degree"), edu.get("field")]))
        parts.append(
            "\\cventry{{{year}}}{{{degree}}}{{{institution}}}{{}}{{}}{{}}".format(
                year=_escape_latex(edu.get("graduation_year", "")),
                degree=_escape_latex(degree_field),
                institution=_escape_latex(edu.get("institution", "")),
            )
        )
    return "\n".join(parts) + "\n"


def _skills_section(data: dict) -> str:
    skills = data.get("skills") or []
    if not skills:
        return ""
    return "\\section{Skills}\n\\cvline{}{" + _escape_latex(", ".join(skills)) + "}\n"


def _certifications_section(data: dict) -> str:
    certs = data.get("certifications") or []
    if not certs:
        return ""
    return "\\section{Certifications}\n\\cvline{}{" + _escape_latex(", ".join(certs)) + "}\n"


def build_latex_cv(structured_data: dict, font_id: str | None = None) -> str:
    """Render a moderncv "banking" style LaTeX source for the given CV data."""
    font = _font(font_id)
    full_name = (structured_data.get("full_name") or "").strip()
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    headline = ""
    experience = structured_data.get("experience") or []
    if experience:
        headline = experience[0].get("title", "")

    return _MODERNCV_TEMPLATE.format(
        font_preamble=font["latex_font"],
        first_name=_escape_latex(first_name),
        last_name=_escape_latex(last_name),
        headline=_escape_latex(headline),
        contact_lines=_contact_lines(structured_data),
        summary_section=_summary_section(structured_data),
        experience_section=_experience_section(structured_data),
        education_section=_education_section(structured_data),
        skills_section=_skills_section(structured_data),
        certifications_section=_certifications_section(structured_data),
    )


def render_cv_pdf(structured_data: dict, font_id: str | None = None) -> bytes:
    """Render the CV as a PDF using reportlab (no system LaTeX required)."""
    font = _font(font_id)
    base_font = "Times-Roman" if font["preview_style"] == "font-serif" else "Helvetica"
    bold_font = "Times-Bold" if font["preview_style"] == "font-serif" else "Helvetica-Bold"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "CVName", parent=styles["Title"], fontName=bold_font, fontSize=20,
        alignment=TA_LEFT, textColor=colors.HexColor("#1E3A8A"), spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "CVContact", parent=styles["Normal"], fontName=base_font, fontSize=9,
        textColor=colors.HexColor("#475569"), spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CVHeading", parent=styles["Heading2"], fontName=bold_font, fontSize=12,
        textColor=colors.HexColor("#1E3A8A"), spaceBefore=10, spaceAfter=4,
        borderWidth=0, borderColor=colors.HexColor("#1E3A8A"),
    )
    body_style = ParagraphStyle(
        "CVBody", parent=styles["Normal"], fontName=base_font, fontSize=10, leading=14,
    )
    item_style = ParagraphStyle(
        "CVItemTitle", parent=styles["Normal"], fontName=bold_font, fontSize=10, leading=14,
    )
    bullet_style = ParagraphStyle(
        "CVBullet", parent=styles["Normal"], fontName=base_font, fontSize=9.5, leading=13,
    )

    story = []
    full_name = structured_data.get("full_name") or ""
    story.append(Paragraph(full_name, name_style))

    contact_bits = [b for b in [structured_data.get("email"), structured_data.get("phone")] if b]
    if contact_bits:
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_bits), contact_style))

    if structured_data.get("summary"):
        story.append(Paragraph("SUMMARY", heading_style))
        story.append(Paragraph(structured_data["summary"], body_style))

    experience = structured_data.get("experience") or []
    if experience:
        story.append(Paragraph("EXPERIENCE", heading_style))
        for exp in experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            dates = f"{exp.get('start_date', '')} – {exp.get('end_date') or 'Present'}"
            story.append(Paragraph(f"{title}, {company} <i>({dates})</i>", item_style))
            bullets = exp.get("bullets") or []
            if bullets:
                story.append(
                    ListFlowable(
                        [ListItem(Paragraph(b, bullet_style)) for b in bullets],
                        bulletType="bullet", leftIndent=14,
                    )
                )
            story.append(Spacer(1, 4))

    education = structured_data.get("education") or []
    if education:
        story.append(Paragraph("EDUCATION", heading_style))
        for edu in education:
            degree_field = ", ".join(filter(None, [edu.get("degree"), edu.get("field")]))
            story.append(
                Paragraph(
                    f"{degree_field}, {edu.get('institution', '')} "
                    f"<i>({edu.get('graduation_year', '')})</i>",
                    body_style,
                )
            )

    skills = structured_data.get("skills") or []
    if skills:
        story.append(Paragraph("SKILLS", heading_style))
        story.append(Paragraph(", ".join(skills), body_style))

    certs = structured_data.get("certifications") or []
    if certs:
        story.append(Paragraph("CERTIFICATIONS", heading_style))
        story.append(Paragraph(", ".join(certs), body_style))

    doc.build(story)
    return buffer.getvalue()
