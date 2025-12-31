"""
Resume Generation API Endpoint

Vercel Python serverless function that:
1. Accepts a PDF resume and job description
2. Uses Claude AI to tailor the resume
3. Generates a PDF using ReportLab
4. Returns the tailored PDF
"""

import os
import re
import json
from io import BytesIO
from http.server import BaseHTTPRequestHandler
import anthropic
from PyPDF2 import PdfReader
from pdf_generator import generate_pdf_resume


def parse_multipart(content_type: str, body: bytes) -> dict:
    """
    Parse multipart/form-data request body.

    Args:
        content_type: Content-Type header value
        body: Request body bytes

    Returns:
        dict: Parsed form fields and files
    """
    # Extract boundary from content-type
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

    result = {
        'fields': {},
        'files': {}
    }

    for part in parts:
        if not part or part == b'--\r\n' or part == b'--':
            continue

        # Split headers from content
        try:
            header_end = part.index(b'\r\n\r\n')
            headers_raw = part[:header_end].decode('utf-8', errors='ignore')
            content = part[header_end + 4:]

            # Remove trailing \r\n
            if content.endswith(b'\r\n'):
                content = content[:-2]
        except ValueError:
            continue

        # Parse Content-Disposition header
        name = None
        filename = None
        for line in headers_raw.split('\r\n'):
            if line.lower().startswith('content-disposition:'):
                # Extract name
                name_match = re.search(r'name="([^"]*)"', line)
                if name_match:
                    name = name_match.group(1)

                # Extract filename
                filename_match = re.search(r'filename="([^"]*)"', line)
                if filename_match:
                    filename = filename_match.group(1)

        if name:
            if filename:
                result['files'][name] = {
                    'filename': filename,
                    'content': content
                }
            else:
                result['fields'][name] = content.decode('utf-8', errors='ignore')

    return result


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        str: Extracted text content
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract PDF text: {str(e)}")


def extract_job_details(client: anthropic.Anthropic, job_description: str) -> tuple:
    """
    Use Claude API to extract company name and job title from job description.

    Args:
        client: Anthropic client
        job_description: Full job description text

    Returns:
        tuple: (company_name, job_title)
    """
    prompt = f"""Analyze this job description and extract the company name and job title.

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON object with this exact structure (no markdown, no code blocks):
{{
  "company_name": "Company Name",
  "job_title": "Job Title/Position"
}}

If you cannot find the company name or job title, use "Unknown Company" or "Unknown Position" respectively."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    data = json.loads(response_text)
    return data.get('company_name', 'Unknown Company'), data.get('job_title', 'Unknown Position')


def tailor_resume(client: anthropic.Anthropic, resume_text: str, job_description: str,
                  company_name: str, job_title: str) -> dict:
    """
    Use Claude API to tailor resume content for a specific job.

    Args:
        client: Anthropic client
        resume_text: Original resume text
        job_description: Job description
        company_name: Company name
        job_title: Job title

    Returns:
        dict: Tailored resume data structure
    """
    prompt = f"""You are an expert resume writer and ATS optimization specialist. Your task is to tailor a resume for a specific job application.

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
2. **Keyword Integration**: Identify key skills, technologies, and requirements from the job description and weave them naturally into bullet points
3. **Strategic Bolding**: Mark items to be bolded by wrapping them in **bold markers**. Bold the following:
   - Technologies and tools (e.g., **Python**, **React**, **AWS**)
   - Programming languages from tech stack
   - Frameworks and libraries
   - Key performance indicators and metrics (e.g., **50% improvement**, **$2M revenue**, **10,000 users**)
   - Important achievements that should pop to hiring managers
   - Quantifiable results and impact numbers
4. **Relevance**: Emphasize experiences and skills most relevant to this position
5. **ATS-Friendly**: Use standard section headings and formatting
6. **Achievements**: Quantify achievements where possible
7. **Keep it truthful**: Only include information that was in the original resume - do not fabricate experience

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

IMPORTANT: Wrap items to be bolded with **double asterisks** in the bullet points. Include all relevant sections that exist in the original resume. Focus on making this resume highly tailored to the {job_title} position at {company_name}."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    return json.loads(response_text)


class handler(BaseHTTPRequestHandler):
    """Vercel Python serverless function handler."""

    def do_POST(self):
        """Handle POST requests for resume generation."""
        try:
            # Get API key from environment
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                self.send_error_response(500, "ANTHROPIC_API_KEY not configured")
                return

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error_response(400, "Expected multipart/form-data")
                return

            form_data = parse_multipart(content_type, body)

            # Validate required fields
            if 'resume' not in form_data['files']:
                self.send_error_response(400, "Resume file is required")
                return

            job_description = form_data['fields'].get('job_description', '')
            if not job_description:
                self.send_error_response(400, "Job description is required")
                return

            # Get optional fields
            company_name = form_data['fields'].get('company_name', '')
            job_title = form_data['fields'].get('job_title', '')

            # Extract PDF content
            resume_file = form_data['files']['resume']
            resume_bytes = resume_file['content']

            # Extract text from PDF
            resume_text = extract_text_from_pdf(resume_bytes)
            if not resume_text:
                self.send_error_response(400, "Could not extract text from resume PDF")
                return

            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=api_key)

            # Extract job details if not provided
            if not company_name or not job_title:
                extracted_company, extracted_title = extract_job_details(client, job_description)
                if not company_name:
                    company_name = extracted_company
                if not job_title:
                    job_title = extracted_title

            # Tailor resume using Claude
            tailored_data = tailor_resume(
                client, resume_text, job_description, company_name, job_title
            )

            # Generate PDF
            pdf_bytes = generate_pdf_resume(tailored_data, company_name, job_title)

            # Create safe filename
            safe_company = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
            safe_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
            filename = f"Resume_{safe_company}_{safe_title}.pdf"

            # Send PDF response
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(pdf_bytes)))
            self.send_header('X-Keywords-Added', ','.join(tailored_data.get('keywords_added', [])))
            self.end_headers()
            self.wfile.write(pdf_bytes)

        except json.JSONDecodeError as e:
            self.send_error_response(500, f"Failed to parse AI response: {str(e)}")
        except anthropic.APIError as e:
            self.send_error_response(500, f"AI API error: {str(e)}")
        except Exception as e:
            self.send_error_response(500, f"Internal error: {str(e)}")

    def send_error_response(self, status_code: int, message: str):
        """Send a JSON error response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = json.dumps({'error': message})
        self.wfile.write(error_response.encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
