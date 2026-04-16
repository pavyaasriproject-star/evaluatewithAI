from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import base64
import json
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class AnalysisRequest(BaseModel):
    question_paper: str  # base64
    answer_key: str      # base64
    answer_script: str   # base64
    question_mime: str
    key_mime: str
    script_mime: str

class ErrorDetail(BaseModel):
    question_number: str
    error_type: str  # "incorrect", "missing_wn", "partial"
    student_answer: str
    correct_answer: str
    marks_deducted: float
    feedback: str

class AnalysisResponse(BaseModel):
    score_percentage: float
    total_marks: float
    obtained_marks: float
    errors: List[ErrorDetail]
    strengths: List[str]
    improvements: List[str]
    working_notes_found: List[str]
    overall_feedback: str
    timestamp: str

class ReportRequest(BaseModel):
    analysis_result: Dict[str, Any]
    student_name: Optional[str] = "Student"

# Add your routes to the router
@api_router.get("/")
async def root():
    return {"message": "ArivuPro AI - Student Assessment Platform"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ArivuPro AI Backend",
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_answer_script(request: AnalysisRequest):
    """
    Analyze student's answer script using Claude Sonnet 4.5 with vision
    """
    try:
        # Initialize Claude chat with Emergent LLM key
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"analysis_{datetime.utcnow().timestamp()}",
            system_message="""
You are an expert examiner for professional courses (CA, CS, ACCA, CMA US). 
Your task is to grade student answer scripts with high accuracy using semantic understanding.

You will receive:
1. Question Paper
2. Official Answer Key
3. Student's Handwritten Answer Script

Your grading must:
- Perform OCR on handwritten text accurately
- Understand context and intent, not just keyword matching
- Identify Working Notes (WN1, WN2, WN3, etc.) and verify their correctness
- Apply professional exam marking schemes
- Provide specific, actionable feedback
- Calculate accurate scores

Return your analysis in this JSON format:
{
  "total_marks": <number>,
  "obtained_marks": <number>,
  "errors": [
    {
      "question_number": "Q1",
      "error_type": "incorrect|missing_wn|partial",
      "student_answer": "<what student wrote>",
      "correct_answer": "<what should be written>",
      "marks_deducted": <number>,
      "feedback": "<specific feedback>"
    }
  ],
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"],
  "working_notes_found": ["WN1", "WN2"],
  "overall_feedback": "<comprehensive feedback>"
}
"""
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        # Create image contents
        question_image = ImageContent(image_base64=request.question_paper)
        key_image = ImageContent(image_base64=request.answer_key)
        script_image = ImageContent(image_base64=request.answer_script)
        
        # Send message to Claude
        user_message = UserMessage(
            text="""
Please analyze these three documents:

1. QUESTION PAPER (first image)
2. OFFICIAL ANSWER KEY (second image)  
3. STUDENT'S HANDWRITTEN ANSWER SCRIPT (third image)

Perform OCR on the handwritten script, compare it semantically with the answer key, 
identify all errors, Working Notes (WN), and provide detailed grading feedback.

Return ONLY valid JSON in the specified format. No additional text.
""",
            file_contents=[question_image, key_image, script_image]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse response
        response_text = response.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```json")[1].split("```")[0] if "```json" in response_text else response_text.split("```")[1].split("```")[0]
        
        analysis_data = json.loads(response_text)
        
        # Calculate score percentage
        total_marks = analysis_data.get("total_marks", 100)
        obtained_marks = analysis_data.get("obtained_marks", 0)
        score_percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        return AnalysisResponse(
            score_percentage=round(score_percentage, 2),
            total_marks=total_marks,
            obtained_marks=obtained_marks,
            errors=[
                ErrorDetail(**error) for error in analysis_data.get("errors", [])
            ],
            strengths=analysis_data.get("strengths", []),
            improvements=analysis_data.get("improvements", []),
            working_notes_found=analysis_data.get("working_notes_found", []),
            overall_feedback=analysis_data.get("overall_feedback", ""),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.post("/generate-report")
async def generate_pdf_report(request: ReportRequest):
    """
    Generate a print-ready PDF report
    """
    try:
        analysis = request.analysis_result
        student_name = request.student_name
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                leftMargin=0.75*inch, rightMargin=0.75*inch,
                                topMargin=1*inch, bottomMargin=0.75*inch)
        
        # Container for elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0D9488'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0D9488'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        # Title
        elements.append(Paragraph("ArivuPro AI Assessment Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Student info
        info_data = [
            ["Student Name:", student_name],
            ["Date:", datetime.utcnow().strftime("%B %d, %Y")],
            ["Score:", f"{analysis.get('obtained_marks', 0)}/{analysis.get('total_marks', 100)} ({analysis.get('score_percentage', 0):.2f}%)"],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Errors section
        if analysis.get('errors'):
            elements.append(Paragraph("Detailed Correction Log", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            error_data = [["Q#", "Error Type", "Marks Lost", "Feedback"]]
            for error in analysis.get('errors', []):
                error_data.append([
                    error.get('question_number', ''),
                    error.get('error_type', '').replace('_', ' ').title(),
                    str(error.get('marks_deducted', 0)),
                    error.get('feedback', '')[:100] + '...' if len(error.get('feedback', '')) > 100 else error.get('feedback', '')
                ])
            
            error_table = Table(error_data, colWidths=[0.6*inch, 1.2*inch, 0.8*inch, 3.4*inch])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#374151')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(error_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Strengths
        if analysis.get('strengths'):
            elements.append(Paragraph("Strengths", heading_style))
            for strength in analysis.get('strengths', []):
                elements.append(Paragraph(f"• {strength}", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Areas for Improvement
        if analysis.get('improvements'):
            elements.append(Paragraph("Areas for Improvement", heading_style))
            for improvement in analysis.get('improvements', []):
                elements.append(Paragraph(f"• {improvement}", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Overall Feedback
        elements.append(Paragraph("Overall Feedback", heading_style))
        elements.append(Paragraph(analysis.get('overall_feedback', ''), styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        # Save to file
        pdf_path = Path("/tmp/arivupro_report.pdf")
        with open(pdf_path, "wb") as f:
            f.write(buffer.getvalue())
        
        return FileResponse(
            path=pdf_path,
            filename=f"ArivuPro_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        logging.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)