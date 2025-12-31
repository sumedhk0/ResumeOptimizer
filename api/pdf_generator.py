"""
PDF Generator using ReportLab

Generates professional ATS-optimized resumes in PDF format,
replicating the layout from the original LaTeX template.
"""

import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib import colors


def process_bold_markers(text: str) -> str:
    """
    Convert **bold** markers to ReportLab XML tags.

    Args:
        text: Text that may contain **bold** markers

    Returns:
        str: Text with <b>bold</b> tags
    """
    if not text:
        return ""

    # Escape HTML entities first
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # Replace **text** with <b>text</b>
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)


def create_styles():
    """Create paragraph styles for the resume."""
    styles = getSampleStyleSheet()

    # Name style - large, centered, bold
    name_style = ParagraphStyle(
        'ResumeName',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=black,
        fontName='Helvetica-Bold'
    )

    # Contact line style - smaller, centered
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=black,
        fontName='Helvetica'
    )

    # Section heading style
    section_style = ParagraphStyle(
        'ResumeSection',
        parent=styles['Heading2'],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor=black,
        fontName='Helvetica-Bold'
    )

    # Company/Institution name style
    company_style = ParagraphStyle(
        'ResumeCompany',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=6,
        spaceAfter=0,
        textColor=black,
        fontName='Helvetica-Bold'
    )

    # Job title/degree style (italic)
    title_style = ParagraphStyle(
        'ResumeTitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=0,
        spaceAfter=2,
        textColor=black,
        fontName='Helvetica-Oblique'
    )

    # Bullet point style
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=styles['Normal'],
        fontSize=9,
        spaceBefore=1,
        spaceAfter=1,
        leftIndent=15,
        textColor=black,
        fontName='Helvetica'
    )

    # Normal text style
    normal_style = ParagraphStyle(
        'ResumeNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceBefore=0,
        spaceAfter=2,
        textColor=black,
        fontName='Helvetica'
    )

    return {
        'name': name_style,
        'contact': contact_style,
        'section': section_style,
        'company': company_style,
        'title': title_style,
        'bullet': bullet_style,
        'normal': normal_style
    }


def generate_pdf_resume(resume_data: dict, company_name: str, job_title: str) -> bytes:
    """
    Generate a professional PDF resume using ReportLab.
    Replicates the layout from the LaTeX template.

    Args:
        resume_data: Tailored resume data from Claude API
        company_name: Company name (for metadata)
        job_title: Job title (for metadata)

    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = create_styles()
    elements = []

    # ===== HEADER =====
    name = resume_data.get('name', 'Your Name')
    elements.append(Paragraph(name, styles['name']))

    # Contact line
    contact = resume_data.get('contact', {})
    contact_parts = []

    if contact.get('email'):
        email = contact['email']
        contact_parts.append(f'<a href="mailto:{email}" color="blue">{email}</a>')
    if contact.get('phone'):
        contact_parts.append(contact['phone'])
    if contact.get('linkedin'):
        linkedin = contact['linkedin']
        display_linkedin = linkedin.replace('https://', '').replace('http://', '')
        contact_parts.append(f'<a href="{linkedin}" color="blue">{display_linkedin}</a>')
    if contact.get('github'):
        github = contact['github']
        display_github = github.replace('https://', '').replace('http://', '')
        contact_parts.append(f'<a href="{github}" color="blue">{display_github}</a>')
    if contact.get('location'):
        contact_parts.append(contact['location'])

    if contact_parts:
        contact_line = ' | '.join(contact_parts)
        elements.append(Paragraph(contact_line, styles['contact']))

    # ===== EDUCATION SECTION =====
    if resume_data.get('education'):
        elements.append(Paragraph('EDUCATION', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))

        for edu in resume_data['education']:
            # Institution and graduation date on same line
            institution = edu.get('institution', '')
            graduation = edu.get('graduation', '')

            # Create a table for left-right alignment
            inst_para = Paragraph(f"<b>{institution}</b>", styles['normal'])
            grad_para = Paragraph(f"<b>{graduation}</b>", styles['normal'])

            t = Table([[inst_para, grad_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(t)

            # Degree
            degree = edu.get('degree', '')
            if degree:
                elements.append(Paragraph(degree, styles['normal']))

            # GPA and coursework as bullet points
            bullets = []
            if edu.get('gpa'):
                bullets.append(f"<b>GPA:</b> {edu['gpa']}")
            if edu.get('relevant_coursework'):
                bullets.append(f"<b>Relevant Coursework:</b> {edu['relevant_coursework']}")

            for bullet in bullets:
                elements.append(Paragraph(f"• {bullet}", styles['bullet']))

            elements.append(Spacer(1, 4))

    # ===== EXPERIENCE SECTION =====
    if resume_data.get('experience'):
        elements.append(Paragraph('EXPERIENCE', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))

        for exp in resume_data['experience']:
            # Company and location
            company = exp.get('company', '')
            location = exp.get('location', '')

            comp_para = Paragraph(f"<b>{company}</b>", styles['normal'])
            loc_para = Paragraph(location, styles['normal'])

            t = Table([[comp_para, loc_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(t)

            # Title and duration
            title = exp.get('title', '')
            duration = exp.get('duration', '')

            title_para = Paragraph(f"<i>{title}</i>", styles['normal'])
            dur_para = Paragraph(duration, styles['normal'])

            t2 = Table([[title_para, dur_para]], colWidths=['75%', '25%'])
            t2.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(t2)

            # Bullet points
            for bullet in exp.get('bullets', []):
                processed_bullet = process_bold_markers(bullet)
                elements.append(Paragraph(f"• {processed_bullet}", styles['bullet']))

            elements.append(Spacer(1, 4))

    # ===== PROJECTS SECTION =====
    if resume_data.get('projects'):
        elements.append(Paragraph('PROJECTS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))

        for proj in resume_data['projects']:
            # Project name and location/date
            proj_name = proj.get('name', '')
            location = proj.get('location', '')

            name_para = Paragraph(f"<b>{proj_name}</b>", styles['normal'])
            loc_para = Paragraph(location, styles['normal'])

            t = Table([[name_para, loc_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(t)

            # Technologies and duration
            technologies = proj.get('technologies', '')
            duration = proj.get('duration', '')

            if technologies or duration:
                tech_para = Paragraph(f"<i>{technologies}</i>", styles['normal'])
                dur_para = Paragraph(duration, styles['normal'])

                t2 = Table([[tech_para, dur_para]], colWidths=['75%', '25%'])
                t2.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(t2)

            # Description
            if proj.get('description'):
                elements.append(Paragraph(proj['description'], styles['normal']))

            # Bullet points
            for bullet in proj.get('bullets', []):
                processed_bullet = process_bold_markers(bullet)
                elements.append(Paragraph(f"• {processed_bullet}", styles['bullet']))

            elements.append(Spacer(1, 4))

    # ===== SKILLS SECTION =====
    if resume_data.get('skills'):
        elements.append(Paragraph('SKILLS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))

        skills = resume_data['skills']

        if skills.get('technical'):
            tech_list = ', '.join(skills['technical'])
            elements.append(Paragraph(f"• <b>Technical:</b> {tech_list}", styles['bullet']))

        if skills.get('tools'):
            tools_list = ', '.join(skills['tools'])
            elements.append(Paragraph(f"• <b>Tools &amp; Frameworks:</b> {tools_list}", styles['bullet']))

        if skills.get('programming_languages'):
            lang_list = ', '.join(skills['programming_languages'])
            elements.append(Paragraph(f"• <b>Programming Languages:</b> {lang_list}", styles['bullet']))

        elements.append(Spacer(1, 4))

    # ===== CERTIFICATIONS SECTION =====
    if resume_data.get('certifications'):
        elements.append(Paragraph('CERTIFICATIONS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))

        for cert in resume_data['certifications']:
            elements.append(Paragraph(f"• {cert}", styles['bullet']))

        elements.append(Spacer(1, 4))

    # Build PDF
    doc.build(elements)

    return buffer.getvalue()
