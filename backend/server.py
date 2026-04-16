from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import base64
import json
import re
import bcrypt
import jwt
import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Password & JWT helpers ───

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─── Pydantic models ───

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    course: Optional[str] = "CA"

class LoginRequest(BaseModel):
    email: str
    password: str

class AnalysisRequest(BaseModel):
    question_paper: str
    answer_key: str
    answer_script: str
    question_mime: str = "image/png"
    key_mime: str = "image/png"
    script_mime: str = "image/png"

class BatchAnalysisRequest(BaseModel):
    question_paper: str
    answer_key: str
    answer_scripts: List[str]
    question_mime: str = "image/png"
    key_mime: str = "image/png"
    script_mimes: List[str] = []

class CareerAdvisorRequest(BaseModel):
    question: str
    course: Optional[str] = None

class ReportRequest(BaseModel):
    analysis_result: Dict[str, Any]
    student_name: Optional[str] = "Student"

# ─── Auth endpoints ───

@api_router.post("/auth/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "name": req.name.strip(),
        "email": email,
        "password_hash": hash_password(req.password),
        "course": req.course or "CA",
        "role": "student",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return {"id": user_id, "name": req.name, "email": email, "course": req.course, "role": "student"}

@api_router.post("/auth/login")
async def login(req: LoginRequest, response: Response, request: Request):
    email = req.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    # Brute force check
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_until = attempts.get("locked_until")
        if lockout_until and datetime.now(timezone.utc) < datetime.fromisoformat(lockout_until):
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
        else:
            await db.login_attempts.delete_one({"identifier": identifier})

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await db.login_attempts.delete_one({"identifier": identifier})
    user_id = str(user["_id"])
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return {"id": user_id, "name": user["name"], "email": email, "course": user.get("course", "CA"), "role": user.get("role", "student")}

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user_id = str(user["_id"])
        new_access = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=new_access, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
        return {"message": "Token refreshed"}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ─── Health & Root ───

@api_router.get("/")
async def root():
    return {"message": "ArivuPro AI - South India's No. 1 Commerce Academy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ArivuPro AI"}

# ─── Claude Analysis (FIXED) ───

def extract_json_from_text(text: str) -> dict:
    """Robustly extract JSON from Claude's response text."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code blocks
    patterns = [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'\{[\s\S]*\}']
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if '```' in pattern else match.group(0))
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract valid JSON from AI response")

@api_router.post("/analyze")
async def analyze_answer_script(request: AnalysisRequest, req: Request):
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        chat = LlmChat(
            api_key=api_key,
            session_id=f"analysis_{datetime.now(timezone.utc).timestamp()}",
            system_message="""You are an expert examiner for professional courses (CA, CS, ACCA, CMA US, CMA India).
Your task is to grade student answer scripts by comparing them with the official answer key.

You will receive 3 images:
1. Question Paper
2. Official Answer Key
3. Student's Handwritten Answer Script

Perform OCR on the handwritten script. Compare semantically with the answer key. Identify Working Notes (WN1, WN2...).

IMPORTANT: Return ONLY a valid JSON object with NO additional text, NO markdown, NO explanation. Just the JSON:
{
  "total_marks": <number>,
  "obtained_marks": <number>,
  "errors": [
    {
      "question_number": "Q1",
      "error_type": "incorrect",
      "student_answer": "what student wrote",
      "correct_answer": "what should be written",
      "marks_deducted": 2,
      "feedback": "specific feedback"
    }
  ],
  "strengths": ["strength 1"],
  "improvements": ["improvement 1"],
  "working_notes_found": ["WN1"],
  "overall_feedback": "comprehensive feedback"
}

error_type must be one of: "incorrect", "missing_wn", "partial"
If you cannot read the handwriting clearly, still provide your best assessment.
All fields are required. Return valid JSON only."""
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        # Build image contents
        images = []
        for b64_data in [request.question_paper, request.answer_key, request.answer_script]:
            # Clean base64 - remove data URI prefix if present
            clean_b64 = b64_data
            if ',' in clean_b64:
                clean_b64 = clean_b64.split(',')[1]
            # Remove whitespace
            clean_b64 = clean_b64.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            images.append(ImageContent(image_base64=clean_b64))

        user_message = UserMessage(
            text="""Analyze these three documents:
1. QUESTION PAPER (first image)
2. OFFICIAL ANSWER KEY (second image)
3. STUDENT'S HANDWRITTEN ANSWER SCRIPT (third image)

Perform OCR on the handwritten script, compare semantically with the answer key, grade it, and return ONLY valid JSON.""",
            file_contents=images
        )

        response_text = await chat.send_message(user_message)
        logger.info(f"Claude raw response (first 500 chars): {response_text[:500]}")

        analysis_data = extract_json_from_text(response_text)

        total_marks = float(analysis_data.get("total_marks", 100))
        obtained_marks = float(analysis_data.get("obtained_marks", 0))
        score_pct = round((obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2)

        result = {
            "score_percentage": score_pct,
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "errors": analysis_data.get("errors", []),
            "strengths": analysis_data.get("strengths", []),
            "improvements": analysis_data.get("improvements", []),
            "working_notes_found": analysis_data.get("working_notes_found", []),
            "overall_feedback": analysis_data.get("overall_feedback", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Save to user's performance history if authenticated
        try:
            user = await get_current_user(req)
            if user:
                perf_doc = {
                    "user_id": user["_id"],
                    "score_percentage": score_pct,
                    "obtained_marks": obtained_marks,
                    "total_marks": total_marks,
                    "errors_count": len(result["errors"]),
                    "strengths_count": len(result["strengths"]),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await db.performance.insert_one(perf_doc)
        except Exception:
            pass  # User not authenticated, skip saving

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"AI response parsing failed. Please try again.")
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ─── Batch Analysis ───

@api_router.post("/analyze-batch")
async def analyze_batch(request: BatchAnalysisRequest, req: Request):
    results = []
    for idx, script_b64 in enumerate(request.answer_scripts):
        try:
            single_req = AnalysisRequest(
                question_paper=request.question_paper,
                answer_key=request.answer_key,
                answer_script=script_b64,
                question_mime=request.question_mime,
                key_mime=request.key_mime,
                script_mime=request.script_mimes[idx] if idx < len(request.script_mimes) else "image/png"
            )
            result = await analyze_answer_script(single_req, req)
            results.append({"index": idx, "status": "success", "result": result})
        except Exception as e:
            results.append({"index": idx, "status": "error", "error": str(e)})
    return {"results": results, "total": len(request.answer_scripts)}

# ─── Career Advisor ───

@api_router.post("/career-advisor")
async def career_advisor(request: CareerAdvisorRequest):
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        course_context = f"The student is pursuing {request.course}. " if request.course else ""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"career_{datetime.now(timezone.utc).timestamp()}",
            system_message=f"""You are an expert commerce career advisor at ArivuPro Academy, South India's No. 1 Commerce Academy.
You have deep knowledge of these professional courses:
- CA (Chartered Accountant) - Foundation, Intermediate, Final
- CS (Company Secretary) - CSEET, Executive, Professional
- ACCA (Association of Chartered Certified Accountants)
- CMA India (Cost and Management Accountant)
- CMA US (Certified Management Accountant - US)
- CPA US (Certified Public Accountant)
- CFA (Chartered Financial Analyst)
- FRM (Financial Risk Manager)

{course_context}

Provide helpful, encouraging, and specific advice. Include study tips, career prospects, exam strategies, and motivational guidance. Keep responses concise but informative. Be warm and supportive like a mentor."""
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        user_message = UserMessage(text=request.question)
        response = await chat.send_message(user_message)
        return {"response": response, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Career advisor error: {e}")
        raise HTTPException(status_code=500, detail=f"Career advisor failed: {str(e)}")

# ─── Performance History ───

@api_router.get("/performance")
async def get_performance(request: Request):
    user = await get_current_user(request)
    records = await db.performance.find(
        {"user_id": user["_id"]}, {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    return {"records": records}

# ─── PDF Report ───

@api_router.post("/generate-report")
async def generate_pdf_report(request: ReportRequest):
    try:
        analysis = request.analysis_result
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=1*inch, bottomMargin=0.75*inch)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#0D9488'), spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0D9488'), spaceAfter=8, fontName='Helvetica-Bold')

        elements.append(Paragraph("ArivuPro Academy - Assessment Report", title_style))
        elements.append(Paragraph("Think Commerce? Think ArivuPro!", ParagraphStyle('Tagline', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#9CA3AF'), alignment=TA_CENTER, spaceAfter=20)))
        elements.append(Spacer(1, 0.2*inch))

        info_data = [
            ["Student:", request.student_name],
            ["Date:", datetime.now(timezone.utc).strftime("%B %d, %Y")],
            ["Score:", f"{analysis.get('obtained_marks', 0)}/{analysis.get('total_marks', 100)} ({analysis.get('score_percentage', 0):.1f}%)"],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))

        if analysis.get('errors'):
            elements.append(Paragraph("Detailed Correction Log", heading_style))
            error_data = [["Q#", "Type", "Marks Lost", "Feedback"]]
            for error in analysis['errors']:
                fb = error.get('feedback', '')
                if len(fb) > 80:
                    fb = fb[:80] + '...'
                error_data.append([error.get('question_number', ''), error.get('error_type', '').replace('_', ' ').title(), str(error.get('marks_deducted', 0)), fb])
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

        for section_title, items, bullet_color in [
            ("Strengths", analysis.get('strengths', []), '#10B981'),
            ("Areas for Improvement", analysis.get('improvements', []), '#F59E0B')
        ]:
            if items:
                elements.append(Paragraph(section_title, heading_style))
                for item in items:
                    elements.append(Paragraph(f"&bull; {item}", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

        if analysis.get('overall_feedback'):
            elements.append(Paragraph("Overall Feedback", heading_style))
            elements.append(Paragraph(analysis['overall_feedback'], styles['Normal']))

        doc.build(elements)
        pdf_path = Path("/tmp/arivupro_report.pdf")
        with open(pdf_path, "wb") as f:
            f.write(buffer.getvalue())
        return FileResponse(path=pdf_path, filename=f"ArivuPro_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf", media_type="application/pdf")
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# ─── App Setup ───

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@arivupro.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "ArivuPro2026!")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "course": "CA",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin seeded: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.performance.create_index("user_id")
    await seed_admin()
    logger.info("ArivuPro AI Backend started successfully")

@app.on_event("shutdown")
async def shutdown():
    client.close()
