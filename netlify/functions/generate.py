"""
Resume Generation API Endpoint for Netlify Functions

Netlify Python serverless function that:
1. Accepts a PDF resume and job description
2. Uses OpenRouter API (Xiaomi MiMo v2 Flash) to tailor the resume
3. Generates a PDF using ReportLab
4. Returns the tailored PDF
"""

import os
import re
import json
import base64
from io import BytesIO

from openai import OpenAI
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle
)


# ============== PDF GENERATION FUNCTIONS ==============

def process_bold_markers(text: str) -> str:
    """Convert **bold** markers to ReportLab XML tags."""
    if not text:
        return ""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)


def create_styles():
    """Create paragraph styles for the resume."""
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        'ResumeName', parent=styles['Heading1'], fontSize=16,
        alignment=TA_CENTER, spaceAfter=4, textColor=black, fontName='Helvetica-Bold'
    )
    contact_style = ParagraphStyle(
        'ResumeContact', parent=styles['Normal'], fontSize=9,
        alignment=TA_CENTER, spaceAfter=12, textColor=black, fontName='Helvetica'
    )
    section_style = ParagraphStyle(
        'ResumeSection', parent=styles['Heading2'], fontSize=11,
        spaceBefore=10, spaceAfter=4, textColor=black, fontName='Helvetica-Bold'
    )
    bullet_style = ParagraphStyle(
        'ResumeBullet', parent=styles['Normal'], fontSize=9,
        spaceBefore=1, spaceAfter=1, leftIndent=15, textColor=black, fontName='Helvetica'
    )
    normal_style = ParagraphStyle(
        'ResumeNormal', parent=styles['Normal'], fontSize=9,
        spaceBefore=0, spaceAfter=2, textColor=black, fontName='Helvetica'
    )
    return {
        'name': name_style, 'contact': contact_style, 'section': section_style,
        'bullet': bullet_style, 'normal': normal_style
    }


def generate_pdf_resume(resume_data: dict, company_name: str, job_title: str) -> bytes:
    """Generate a professional PDF resume using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.5*inch,
                           rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = create_styles()
    elements = []

    # Header
    name = resume_data.get('name', 'Your Name')
    elements.append(Paragraph(name, styles['name']))

    # Contact line
    contact = resume_data.get('contact', {})
    contact_parts = []
    if contact.get('email'):
        contact_parts.append(f'<a href="mailto:{contact["email"]}" color="blue">{contact["email"]}</a>')
    if contact.get('phone'):
        contact_parts.append(contact['phone'])
    if contact.get('linkedin'):
        linkedin = contact['linkedin']
        display = linkedin.replace('https://', '').replace('http://', '')
        contact_parts.append(f'<a href="{linkedin}" color="blue">{display}</a>')
    if contact.get('github'):
        github = contact['github']
        display = github.replace('https://', '').replace('http://', '')
        contact_parts.append(f'<a href="{github}" color="blue">{display}</a>')
    if contact.get('location'):
        contact_parts.append(contact['location'])
    if contact_parts:
        elements.append(Paragraph(' | '.join(contact_parts), styles['contact']))

    # Education
    if resume_data.get('education'):
        elements.append(Paragraph('EDUCATION', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))
        for edu in resume_data['education']:
            inst_para = Paragraph(f"<b>{edu.get('institution', '')}</b>", styles['normal'])
            grad_para = Paragraph(f"<b>{edu.get('graduation', '')}</b>", styles['normal'])
            t = Table([[inst_para, grad_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 0),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            elements.append(t)
            if edu.get('degree'):
                elements.append(Paragraph(edu['degree'], styles['normal']))
            if edu.get('gpa'):
                elements.append(Paragraph(f"• <b>GPA:</b> {edu['gpa']}", styles['bullet']))
            if edu.get('relevant_coursework'):
                elements.append(Paragraph(f"• <b>Relevant Coursework:</b> {edu['relevant_coursework']}", styles['bullet']))
            elements.append(Spacer(1, 4))

    # Experience
    if resume_data.get('experience'):
        elements.append(Paragraph('EXPERIENCE', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))
        for exp in resume_data['experience']:
            comp_para = Paragraph(f"<b>{exp.get('company', '')}</b>", styles['normal'])
            loc_para = Paragraph(exp.get('location', ''), styles['normal'])
            t = Table([[comp_para, loc_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 0),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            elements.append(t)
            title_para = Paragraph(f"<i>{exp.get('title', '')}</i>", styles['normal'])
            dur_para = Paragraph(exp.get('duration', ''), styles['normal'])
            t2 = Table([[title_para, dur_para]], colWidths=['75%', '25%'])
            t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 0),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            elements.append(t2)
            for bullet in exp.get('bullets', []):
                elements.append(Paragraph(f"• {process_bold_markers(bullet)}", styles['bullet']))
            elements.append(Spacer(1, 4))

    # Projects
    if resume_data.get('projects'):
        elements.append(Paragraph('PROJECTS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))
        for proj in resume_data['projects']:
            name_para = Paragraph(f"<b>{proj.get('name', '')}</b>", styles['normal'])
            loc_para = Paragraph(proj.get('location', ''), styles['normal'])
            t = Table([[name_para, loc_para]], colWidths=['75%', '25%'])
            t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 0),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
            elements.append(t)
            if proj.get('technologies') or proj.get('duration'):
                tech_para = Paragraph(f"<i>{proj.get('technologies', '')}</i>", styles['normal'])
                dur_para = Paragraph(proj.get('duration', ''), styles['normal'])
                t2 = Table([[tech_para, dur_para]], colWidths=['75%', '25%'])
                t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 0),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
                elements.append(t2)
            for bullet in proj.get('bullets', []):
                elements.append(Paragraph(f"• {process_bold_markers(bullet)}", styles['bullet']))
            elements.append(Spacer(1, 4))

    # Skills
    if resume_data.get('skills'):
        elements.append(Paragraph('SKILLS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))
        skills = resume_data['skills']
        if skills.get('technical'):
            elements.append(Paragraph(f"• <b>Technical:</b> {', '.join(skills['technical'])}", styles['bullet']))
        if skills.get('tools'):
            elements.append(Paragraph(f"• <b>Tools &amp; Frameworks:</b> {', '.join(skills['tools'])}", styles['bullet']))
        if skills.get('programming_languages'):
            elements.append(Paragraph(f"• <b>Programming Languages:</b> {', '.join(skills['programming_languages'])}", styles['bullet']))
        elements.append(Spacer(1, 4))

    # Certifications
    if resume_data.get('certifications'):
        elements.append(Paragraph('CERTIFICATIONS', styles['section']))
        elements.append(HRFlowable(width="100%", thickness=1, color=black, spaceBefore=0, spaceAfter=6))
        for cert in resume_data['certifications']:
            elements.append(Paragraph(f"• {cert}", styles['bullet']))
        elements.append(Spacer(1, 4))

    doc.build(elements)
    return buffer.getvalue()


# ============== API HELPER FUNCTIONS ==============

def parse_multipart(content_type: str, body: bytes) -> dict:
    """Parse multipart/form-data request body."""
    boundary = None
    for part in content_type.split(';'):
        part = part.strip()
        if part.startswith('boundary='):
            boundary = part[9:].strip('"')
            break

    if not boundary:
        raise ValueError("No boundary found in Content-Type header")

    boundary = boundary.encode()
    parts = body.split(b'--' + boundary)

    result = {'fields': {}, 'files': {}}

    for part in parts:
        if not part or part == b'--\r\n' or part == b'--':
            continue

        try:
            header_end = part.index(b'\r\n\r\n')
            headers_raw = part[:header_end].decode('utf-8', errors='ignore')
            content = part[header_end + 4:]

            if content.endswith(b'\r\n'):
                content = content[:-2]
        except ValueError:
            continue

        name = None
        filename = None
        for line in headers_raw.split('\r\n'):
            if line.lower().startswith('content-disposition:'):
                name_match = re.search(r'name="([^"]*)"', line)
                if name_match:
                    name = name_match.group(1)
                filename_match = re.search(r'filename="([^"]*)"', line)
                if filename_match:
                    filename = filename_match.group(1)

        if name:
            if filename:
                result['files'][name] = {'filename': filename, 'content': content}
            else:
                result['fields'][name] = content.decode('utf-8', errors='ignore')

    return result


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract PDF text: {str(e)}")


def extract_job_details(client: OpenAI, job_description: str) -> tuple:
    """Use OpenRouter API to extract company name and job title from job description."""
    prompt = f"""Analyze this job description and extract the company name and job title.

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON object with this exact structure (no markdown, no code blocks):
{{
  "company_name": "Company Name",
  "job_title": "Job Title/Position"
}}

If you cannot find the company name or job title, use "Unknown Company" or "Unknown Position" respectively."""

    response = client.chat.completions.create(
        model="xiaomi/mimo-v2-flash:free",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.choices[0].message.content.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    data = json.loads(response_text)
    return data.get('company_name', 'Unknown Company'), data.get('job_title', 'Unknown Position')


def tailor_resume(client: OpenAI, resume_text: str, job_description: str,
                  company_name: str, job_title: str) -> dict:
    """Use OpenRouter API to tailor resume content for a specific job."""
    prompt = f"""You are an expert resume writer and ATS optimization specialist. Your task is to tailor a resume for a specific job application.

CRITICAL RULE - ABSOLUTE TRUTH REQUIREMENT:
You must ONLY use information that exists in the original resume below. DO NOT FABRICATE, INVENT, OR MAKE UP any information whatsoever. This includes:
- Do NOT invent job titles, companies, dates, or experiences
- Do NOT fabricate skills, technologies, or certifications the person doesn't have
- Do NOT make up metrics, numbers, or achievements
- Do NOT add education, degrees, or coursework not in the original
- If information is missing from the original resume, leave it out - DO NOT GUESS

ORIGINAL RESUME:
{resume_text}

JOB DETAILS:
Company: {company_name}
Position: {job_title}

JOB DESCRIPTION:
{job_description}

TASK:
Analyze the job description and tailor the resume to be ATS-optimized for this specific position. Follow these guidelines:

1. **NO PROFESSIONAL SUMMARY**: Do not include a professional summary section. Incorporate keywords naturally into experience and project bullet points instead.
2. **Keyword Integration**: Identify key skills, technologies, and requirements from the job description and weave them naturally into bullet points - BUT ONLY if those skills actually exist in the original resume
3. **Strategic Bolding**: Mark items to be bolded by wrapping them in **bold markers**. Bold the following:
   - Technologies and tools (e.g., **Python**, **React**, **AWS**) - only ones actually mentioned in original resume
   - Programming languages from tech stack
   - Frameworks and libraries
   - Key performance indicators and metrics (e.g., **50% improvement**, **$2M revenue**, **10,000 users**) - only real numbers from original
   - Important achievements that should pop to hiring managers
   - Quantifiable results and impact numbers
4. **Relevance**: Emphasize experiences and skills most relevant to this position
5. **ATS-Friendly**: Use standard section headings and formatting
6. **Achievements**: Quantify achievements where possible - USE ONLY REAL NUMBERS FROM THE ORIGINAL RESUME
7. **ABSOLUTELY NO FABRICATION**: You must ONLY include information that was explicitly stated in the original resume. Do NOT invent, fabricate, or make up ANY information. If something isn't in the original resume, DO NOT ADD IT. This is critically important - lying on a resume is illegal and unethical.

Return ONLY a JSON object with the following structure (no markdown, no code blocks):

{{
  "name": "Full Name",
  "contact": {{
    "email": "email@example.com",
    "phone": "phone number",
    "linkedin": "LinkedIn URL (optional)",
    "github": "GitHub URL (optional)",
    "location": "City, State (optional)"
  }},
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "University Name",
      "graduation": "Graduation Date",
      "gpa": "GPA (if mentioned)",
      "relevant_coursework": "Relevant courses (optional)"
    }}
  ],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start Date - End Date",
      "location": "City, State (optional)",
      "bullets": [
        "Achievement-focused bullet with **bolded tech** and **bolded metrics**",
        "Another achievement with **important keywords bolded**"
      ]
    }}
  ],
  "skills": {{
    "technical": ["Skill1", "Skill2", "Skill3"],
    "tools": ["Tool1", "Tool2", "Tool3"],
    "programming_languages": ["ProgrammingLanguage1", "ProgrammingLanguage2"]
  }},
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": "Technologies used",
      "duration": "Date range (optional)",
      "bullets": [
        "Key achievement with **bolded technologies** and **metrics**"
      ]
    }}
  ],
  "certifications": [
    "Certification Name 1",
    "Certification Name 2"
  ],
  "keywords_added": ["keyword1", "keyword2", "keyword3"]
}}

IMPORTANT: Wrap items to be bolded with **double asterisks** in the bullet points. Include all relevant sections that exist in the original resume. Focus on making this resume highly tailored to the {job_title} position at {company_name}.

FINAL REMINDER: DO NOT FABRICATE ANYTHING. Every single piece of information in your response MUST come directly from the original resume provided above. If you cannot find specific information in the original resume, DO NOT include it. Accuracy and truthfulness are more important than completeness."""

    response = client.chat.completions.create(
        model="xiaomi/mimo-v2-flash:free",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.choices[0].message.content.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    return json.loads(response_text)


def make_response(status_code: int, body: str, headers: dict = None, is_base64: bool = False):
    """Create a Netlify function response."""
    response = {
        "statusCode": status_code,
        "body": body,
        "headers": headers or {"Content-Type": "application/json"},
    }
    if is_base64:
        response["isBase64Encoded"] = True
    return response


def handler(event, context):
    """Netlify function handler."""
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return make_response(200, "", {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

    # Only accept POST
    if event.get("httpMethod") != "POST":
        return make_response(405, json.dumps({"error": "Method not allowed"}))

    try:
        # Get API key from environment
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return make_response(500, json.dumps({"error": "OPENROUTER_API_KEY not configured"}))

        # Get request body
        body = event.get("body", "")
        is_base64_encoded = event.get("isBase64Encoded", False)

        if is_base64_encoded:
            body = base64.b64decode(body)
        elif isinstance(body, str):
            body = body.encode('utf-8')

        # Get content type from headers (case-insensitive)
        headers = event.get("headers", {})
        content_type = None
        for key, value in headers.items():
            if key.lower() == "content-type":
                content_type = value
                break

        if not content_type or 'multipart/form-data' not in content_type:
            return make_response(400, json.dumps({"error": "Expected multipart/form-data"}))

        # Parse multipart form data
        form_data = parse_multipart(content_type, body)

        # Validate required fields
        if 'resume' not in form_data['files']:
            return make_response(400, json.dumps({"error": "Resume file is required"}))

        job_description = form_data['fields'].get('job_description', '')
        if not job_description:
            return make_response(400, json.dumps({"error": "Job description is required"}))

        # Get optional fields
        company_name = form_data['fields'].get('company_name', '')
        job_title = form_data['fields'].get('job_title', '')

        # Extract PDF content
        resume_file = form_data['files']['resume']
        resume_bytes = resume_file['content']

        # Extract text from PDF
        resume_text = extract_text_from_pdf(resume_bytes)
        if not resume_text:
            return make_response(400, json.dumps({"error": "Could not extract text from resume PDF"}))

        # Initialize OpenRouter client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        # Extract job details if not provided
        if not company_name or not job_title:
            extracted_company, extracted_title = extract_job_details(client, job_description)
            if not company_name:
                company_name = extracted_company
            if not job_title:
                job_title = extracted_title

        # Tailor resume using OpenRouter
        tailored_data = tailor_resume(
            client, resume_text, job_description, company_name, job_title
        )

        # Generate PDF
        pdf_bytes = generate_pdf_resume(tailored_data, company_name, job_title)

        # Create safe filename
        safe_company = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
        safe_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
        filename = f"Resume_{safe_company}_{safe_title}.pdf"

        # Return PDF as base64
        return make_response(
            200,
            base64.b64encode(pdf_bytes).decode('utf-8'),
            {
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Keywords-Added": ','.join(tailored_data.get('keywords_added', [])),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Disposition, X-Keywords-Added"
            },
            is_base64=True
        )

    except json.JSONDecodeError as e:
        return make_response(500, json.dumps({"error": f"Failed to parse AI response: {str(e)}"}))
    except Exception as e:
        return make_response(500, json.dumps({"error": f"Error: {str(e)}"}))
