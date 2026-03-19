import os
import re
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from passlib.context import CryptContext


# =========================================================
# Config
# =========================================================

APP_TITLE = "JobTracker Personal Dashboard"
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "careerpath_data.json"

INDEX_FILE = BASE_DIR / "index.html"
SCRIPT_FILE = BASE_DIR / "script.js"
STYLE_FILE = BASE_DIR / "style.css"

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
NOVA_MODEL_ID = os.getenv("NOVA_MODEL_ID", "us.amazon.nova-lite-v1:0")
REQUIRE_NOVA = os.getenv("REQUIRE_NOVA", "false").lower() == "true"

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-railway")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

DASHBOARD_EMAIL = os.getenv("DASHBOARD_EMAIL", "").strip().lower()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")

COOKIE_NAME = "jobtracker_token"
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Bedrock Client
# =========================================================

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    config=Config(
        connect_timeout=30,
        read_timeout=3600,
        retries={"max_attempts": 2},
    ),
)

# =========================================================
# Models
# =========================================================

class LoginRequest(BaseModel):
    email: str
    password: str


class Job(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    company: str
    role: str
    status: str = "Applied"
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    field: str = "Tech"
    sponsor: str = "Unknown"
    notes: str = ""
    link: str = ""
    salary: str = ""


class JobUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None
    field: Optional[str] = None
    sponsor: Optional[str] = None
    notes: Optional[str] = None
    link: Optional[str] = None
    salary: Optional[str] = None


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str


class ResumeSaveRequest(BaseModel):
    resume_text: str
    parsed_profile: Optional[Dict[str, Any]] = None


class KeywordsRequest(BaseModel):
    keywords: List[str]


class EmailParseRequest(BaseModel):
    email_text: str
    job_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class SettingsRequest(BaseModel):
    sync_window_hours: Optional[int] = 24
    preferred_location: Optional[str] = ""
    user_notes: Optional[str] = ""


# =========================================================
# Persistence
# =========================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_db() -> Dict[str, Any]:
    return {
        "jobs": [],
        "resume_text": "",
        "parsed_profile": {
            "skills": [],
            "roles": [],
            "experienceLevel": "",
            "domains": [],
            "locations": [],
            "education": [],
        },
        "keywords": [],
        "settings": {
            "sync_window_hours": 24,
            "preferred_location": "",
            "user_notes": "",
        },
        "chat_history": [],
        "last_sync": None,
        "updated_at": utc_now(),
    }


def load_db() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        db = default_db()
        save_db(db)
        return db
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        db = default_db()
        save_db(db)
        return db


def save_db(db: Dict[str, Any]) -> None:
    db["updated_at"] = utc_now()
    DATA_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


# =========================================================
# Auth Helpers
# =========================================================

def verify_password(plain_password: str) -> bool:
    if not DASHBOARD_EMAIL:
        raise HTTPException(status_code=500, detail="DASHBOARD_EMAIL is not configured")

    if DASHBOARD_PASSWORD_HASH:
        return pwd_context.verify(plain_password, DASHBOARD_PASSWORD_HASH)

    if DASHBOARD_PASSWORD:
        return plain_password == DASHBOARD_PASSWORD

    raise HTTPException(
        status_code=500,
        detail="Set DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH in your environment",
    )


def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    token = get_token_from_request(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(token)
    if payload.get("sub", "").lower() != DASHBOARD_EMAIL:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    return payload


# =========================================================
# Helpers
# =========================================================

STATUS_MAP = {
    "wishlist": "Wishlist",
    "applied": "Applied",
    "application": "Applied",
    "submitted": "Applied",
    "interview": "Interview",
    "interviewing": "Interview",
    "screen": "Interview",
    "screening": "Interview",
    "offer": "Offered",
    "offered": "Offered",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "declined": "Rejected",
    "archived": "Archived",
    "archive": "Archived",
}


def normalize_status(status: str) -> str:
    s = (status or "").strip().lower()
    return STATUS_MAP.get(s, "Applied")


def compute_job_stats(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {
        "Wishlist": 0,
        "Applied": 0,
        "Interview": 0,
        "Offered": 0,
        "Accepted": 0,
        "Rejected": 0,
        "Archived": 0,
    }

    for job in jobs:
        st = normalize_status(job.get("status", "Applied"))
        counts[st] = counts.get(st, 0) + 1

    return {
        "total_jobs": len(jobs),
        "wishlist_count": counts["Wishlist"],
        "applied_count": counts["Applied"],
        "interview_count": counts["Interview"],
        "offered_count": counts["Offered"],
        "accepted_count": counts["Accepted"],
        "rejected_count": counts["Rejected"],
        "archived_count": counts["Archived"],
        "by_status": counts,
    }


def compact_jobs_for_prompt(jobs: List[Dict[str, Any]], limit: int = 60) -> List[Dict[str, Any]]:
    result = []
    for j in jobs[:limit]:
        result.append({
            "company": j.get("company", ""),
            "role": j.get("role", ""),
            "status": normalize_status(j.get("status", "Applied")),
            "date": j.get("date", ""),
            "notes": j.get("notes", "")[:300],
            "salary": j.get("salary", ""),
            "sponsor": j.get("sponsor", ""),
            "field": j.get("field", ""),
            "link": j.get("link", ""),
        })
    return result


def build_context(db: Dict[str, Any]) -> Dict[str, Any]:
    jobs = db.get("jobs", [])
    return {
        "stats": compute_job_stats(jobs),
        "jobs": compact_jobs_for_prompt(jobs),
        "resume_excerpt": db.get("resume_text", "")[:7000],
        "parsed_profile": db.get("parsed_profile", {}),
        "keywords": db.get("keywords", []),
        "settings": db.get("settings", {}),
        "last_sync": db.get("last_sync"),
        "chat_history_tail": db.get("chat_history", [])[-8:],
    }


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def extract_text_from_bedrock_response(resp: Dict[str, Any]) -> str:
    try:
        content = resp["output"]["message"]["content"]
        parts = []
        for item in content:
            if "text" in item:
                parts.append(item["text"])
        return "\n".join(parts).strip()
    except Exception:
        return ""


def nova_converse(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    try:
        resp = bedrock.converse(
            modelId=NOVA_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ],
            inferenceConfig={
                "maxTokens": 1800,
                "temperature": temperature,
                "topP": 0.9,
            },
        )
        text = extract_text_from_bedrock_response(resp)
        if not text:
            raise RuntimeError("Empty response from Nova")
        return text
    except (ClientError, BotoCoreError, Exception) as e:
        if REQUIRE_NOVA:
            raise HTTPException(status_code=500, detail=f"Nova error: {str(e)}")
        raise RuntimeError(f"Nova error: {str(e)}")


# =========================================================
# Fallback AI
# =========================================================

def fallback_resume_parse(resume_text: str) -> Dict[str, Any]:
    text = resume_text.lower()

    common_skills = [
        "python", "sql", "java", "javascript", "typescript", "react",
        "node", "aws", "excel", "tableau", "power bi", "pandas",
        "scikit-learn", "tensorflow", "fastapi", "firebase", "docker",
        "git", "linux", "c++", "machine learning", "data analysis",
    ]
    found_skills = [s for s in common_skills if s in text]

    possible_roles = [
        "data analyst", "software engineer", "data engineer",
        "business analyst", "machine learning engineer",
        "research assistant", "teaching assistant", "it analyst",
    ]
    found_roles = [r.title() for r in possible_roles if r in text]

    exp_level = ""
    years = re.findall(r"(\d+)\+?\s+year", text)
    if years:
        try:
            y = max(int(x) for x in years)
            if y <= 1:
                exp_level = "Entry Level"
            elif y <= 3:
                exp_level = "Early Career"
            else:
                exp_level = "Experienced"
        except Exception:
            exp_level = ""
    elif "intern" in text or "graduate" in text or "student" in text:
        exp_level = "Entry Level"

    return {
        "skills": sorted(set(s.title() for s in found_skills)),
        "roles": sorted(set(found_roles)),
        "experienceLevel": exp_level,
        "domains": [],
        "locations": [],
        "education": [],
    }


def fallback_email_parse(email_text: str) -> Dict[str, Any]:
    t = email_text.lower()

    if any(x in t for x in ["we'd like to interview", "interview", "schedule a call", "next round", "phone screen"]):
        return {"status": "Interview", "reason": "The email mentions an interview or screening."}
    if any(x in t for x in ["offer", "pleased to offer", "compensation package"]):
        return {"status": "Offered", "reason": "The email contains offer-related language."}
    if any(x in t for x in ["accepted", "welcome aboard", "glad to welcome"]):
        return {"status": "Accepted", "reason": "The email indicates acceptance or onboarding."}
    if any(x in t for x in ["regret to inform", "not moving forward", "unfortunately", "rejected"]):
        return {"status": "Rejected", "reason": "The email contains rejection language."}

    return {"status": "Applied", "reason": "No clear lifecycle change detected."}


def deterministic_chat_answer(message: str, db: Dict[str, Any]) -> Optional[str]:
    msg = message.lower().strip()
    jobs = db.get("jobs", [])
    stats = compute_job_stats(jobs)

    if "how many jobs" in msg or ("how many" in msg and "applied" in msg):
        return (
            f"You have {stats['total_jobs']} total tracked jobs. "
            f"Wishlist: {stats['wishlist_count']}, Applied: {stats['applied_count']}, "
            f"Interview: {stats['interview_count']}, Offered: {stats['offered_count']}, "
            f"Accepted: {stats['accepted_count']}, Rejected: {stats['rejected_count']}."
        )

    if "how many interviews" in msg:
        return f"You currently have {stats['interview_count']} jobs in Interview."

    if "how many offers" in msg or "how many offered" in msg:
        return f"You currently have {stats['offered_count']} jobs in Offered."

    if "how many accepted" in msg:
        return f"You currently have {stats['accepted_count']} jobs in Accepted."

    if "list my jobs" in msg or "show my jobs" in msg:
        if not jobs:
            return "You do not have any tracked jobs yet."
        lines = [
            f"- {j.get('company', '')} — {j.get('role', '')} [{normalize_status(j.get('status', 'Applied'))}]"
            for j in jobs[:15]
        ]
        return "Here are your tracked jobs:\n" + "\n".join(lines)

    return None


# =========================================================
# AI Tasks
# =========================================================

def ai_parse_resume(resume_text: str) -> Dict[str, Any]:
    system_prompt = (
        "You are an expert resume parser. "
        "Return ONLY valid JSON in this schema: "
        '{"skills":[string],"roles":[string],"experienceLevel":string,"domains":[string],"locations":[string],"education":[string]}'
    )
    user_prompt = f"Parse this resume text:\n\n{resume_text}"

    try:
        raw = nova_converse(system_prompt, user_prompt, temperature=0.1)
        parsed = safe_json_loads(raw)
        if parsed:
            parsed.setdefault("skills", [])
            parsed.setdefault("roles", [])
            parsed.setdefault("experienceLevel", "")
            parsed.setdefault("domains", [])
            parsed.setdefault("locations", [])
            parsed.setdefault("education", [])
            return parsed
    except Exception:
        pass

    return fallback_resume_parse(resume_text)


def ai_parse_email(email_text: str) -> Dict[str, Any]:
    system_prompt = (
        "You classify recruiter emails into a job pipeline stage. "
        'Return ONLY valid JSON: {"status":"Wishlist|Applied|Interview|Offered|Accepted|Rejected","reason":"short explanation"}'
    )
    user_prompt = f"Classify this email:\n\n{email_text}"

    try:
        raw = nova_converse(system_prompt, user_prompt, temperature=0.0)
        parsed = safe_json_loads(raw)
        if parsed and "status" in parsed:
            parsed["status"] = normalize_status(parsed["status"])
            parsed["reason"] = parsed.get("reason", "")
            return parsed
    except Exception:
        pass

    return fallback_email_parse(email_text)


def ai_chat(message: str, db: Dict[str, Any]) -> str:
    shortcut = deterministic_chat_answer(message, db)
    if shortcut:
        return shortcut

    context = build_context(db)

    system_prompt = (
        "You are JobTracker AI, a private personal dashboard assistant. "
        "Answer only from the stored context. "
        "Do not invent jobs, counts, statuses, resume details, or preferences. "
        "If something is missing, say so clearly. "
        "Be concise and useful."
    )
    user_prompt = (
        "Stored context JSON:\n"
        f"{json.dumps(context, ensure_ascii=False)}\n\n"
        f"User question: {message}"
    )

    try:
        return nova_converse(system_prompt, user_prompt, temperature=0.1)
    except Exception:
        return "I could not reach Nova right now, but I still have your stored dashboard data."


# =========================================================
# Root Static Files
# =========================================================

@app.get("/", include_in_schema=False)
def root():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({"ok": True, "message": "index.html not found"})


@app.get("/index.html", include_in_schema=False)
def index_html():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/script.js", include_in_schema=False)
def script_js():
    if SCRIPT_FILE.exists():
        return FileResponse(SCRIPT_FILE, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="script.js not found")


@app.get("/style.css", include_in_schema=False)
def style_css():
    if STYLE_FILE.exists():
        return FileResponse(STYLE_FILE, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": APP_TITLE,
        "region": AWS_REGION,
        "model": NOVA_MODEL_ID,
        "auth_configured": bool(DASHBOARD_EMAIL and (DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH)),
    }


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return PlainTextResponse("User-agent: *\nDisallow:\n")


# =========================================================
# Auth
# =========================================================

@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response):
    email = payload.email.strip().lower()

    if email != DASHBOARD_EMAIL:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(email)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )

    return {
        "ok": True,
        "message": "Login successful",
        "user": {"email": email},
        "token": token,
    }


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True, "message": "Logged out"}


@app.get("/api/auth/me")
def auth_me(user=Depends(require_auth)):
    return {"ok": True, "user": {"email": user["sub"]}}


# =========================================================
# Dashboard / Context
# =========================================================

@app.get("/api/context")
def get_context(user=Depends(require_auth)):
    db = load_db()
    return build_context(db)


@app.get("/api/overview")
def get_overview(user=Depends(require_auth)):
    db = load_db()
    stats = compute_job_stats(db.get("jobs", []))
    parsed_profile = db.get("parsed_profile", {})
    return {
        "ok": True,
        "stats": stats,
        "last_sync": db.get("last_sync"),
        "has_resume": bool(db.get("resume_text", "").strip()),
        "top_skills": parsed_profile.get("skills", [])[:8],
        "top_roles": parsed_profile.get("roles", [])[:5],
        "keywords": db.get("keywords", []),
        "preferred_location": db.get("settings", {}).get("preferred_location", ""),
        "recent_jobs": db.get("jobs", [])[:8],
    }


@app.get("/api/dashboard/simple")
def simple_dashboard(user=Depends(require_auth)):
    db = load_db()
    jobs = db.get("jobs", [])
    stats = compute_job_stats(jobs)

    def jobs_by_status(name: str):
        return [j for j in jobs if normalize_status(j.get("status", "")) == name][:10]

    return {
        "ok": True,
        "hero": {
            "title": "JobTracker",
            "subtitle": "Private personal job dashboard",
            "last_sync": db.get("last_sync"),
        },
        "stats": stats,
        "columns": {
            "Wishlist": jobs_by_status("Wishlist"),
            "Applied": jobs_by_status("Applied"),
            "Interview": jobs_by_status("Interview"),
            "Offered": jobs_by_status("Offered"),
            "Accepted": jobs_by_status("Accepted"),
        },
        "profile": {
            "skills": db.get("parsed_profile", {}).get("skills", [])[:8],
            "roles": db.get("parsed_profile", {}).get("roles", [])[:5],
            "keywords": db.get("keywords", [])[:10],
        },
    }


# =========================================================
# Jobs
# =========================================================

@app.get("/api/jobs")
def get_jobs(user=Depends(require_auth)):
    db = load_db()
    return db.get("jobs", [])


@app.post("/api/jobs")
def add_job(job: Job, user=Depends(require_auth)):
    db = load_db()
    new_job = job.model_dump()
    new_job["status"] = normalize_status(new_job.get("status", "Applied"))
    db["jobs"].insert(0, new_job)
    save_db(db)
    return {"ok": True, "job": new_job}


@app.put("/api/jobs/{job_id}")
def update_job(job_id: str, payload: JobUpdate, user=Depends(require_auth)):
    db = load_db()
    jobs = db.get("jobs", [])
    idx = next((i for i, j in enumerate(jobs) if j["id"] == job_id), None)

    if idx is None:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = normalize_status(update_data["status"])

    jobs[idx].update(update_data)
    save_db(db)
    return {"ok": True, "job": jobs[idx]}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, user=Depends(require_auth)):
    db = load_db()
    jobs = db.get("jobs", [])
    new_jobs = [j for j in jobs if j["id"] != job_id]

    if len(new_jobs) == len(jobs):
        raise HTTPException(status_code=404, detail="Job not found")

    db["jobs"] = new_jobs
    save_db(db)
    return {"ok": True}


# =========================================================
# Resume / Profile
# =========================================================

@app.post("/api/resume/analyze")
def analyze_resume(req: ResumeAnalyzeRequest, user=Depends(require_auth)):
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text is required")

    parsed = ai_parse_resume(req.resume_text)
    return {"ok": True, "parsed_profile": parsed}


@app.post("/api/resume/save")
def save_resume(req: ResumeSaveRequest, user=Depends(require_auth)):
    db = load_db()
    db["resume_text"] = req.resume_text
    db["parsed_profile"] = req.parsed_profile or ai_parse_resume(req.resume_text)
    save_db(db)
    return {"ok": True, "parsed_profile": db["parsed_profile"]}


@app.get("/api/profile")
def get_profile(user=Depends(require_auth)):
    db = load_db()
    return {
        "ok": True,
        "resume_text": db.get("resume_text", ""),
        "parsed_profile": db.get("parsed_profile", {}),
    }


# =========================================================
# Keywords / Settings
# =========================================================

@app.get("/api/keywords")
def get_keywords(user=Depends(require_auth)):
    db = load_db()
    return {"ok": True, "keywords": db.get("keywords", [])}


@app.post("/api/keywords")
def save_keywords(req: KeywordsRequest, user=Depends(require_auth)):
    db = load_db()
    cleaned = [k.strip() for k in req.keywords if k.strip()]
    db["keywords"] = cleaned
    save_db(db)
    return {"ok": True, "keywords": cleaned}


@app.get("/api/settings")
def get_settings(user=Depends(require_auth)):
    db = load_db()
    return {"ok": True, "settings": db.get("settings", {})}


@app.post("/api/settings")
def save_settings(req: SettingsRequest, user=Depends(require_auth)):
    db = load_db()
    db["settings"] = {
        "sync_window_hours": req.sync_window_hours or 24,
        "preferred_location": req.preferred_location or "",
        "user_notes": req.user_notes or "",
    }
    save_db(db)
    return {"ok": True, "settings": db["settings"]}


# =========================================================
# Email Parsing / Chat
# =========================================================

@app.post("/api/email/parse")
def parse_email(req: EmailParseRequest, user=Depends(require_auth)):
    if not req.email_text.strip():
        raise HTTPException(status_code=400, detail="email_text is required")

    result = ai_parse_email(req.email_text)
    db = load_db()

    if req.job_id:
        for job in db.get("jobs", []):
            if job["id"] == req.job_id:
                job["status"] = result["status"]
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                note_line = f"[{stamp}] Email parser: {result.get('reason', '')}"
                existing = job.get("notes", "")
                job["notes"] = (existing + "\n" + note_line).strip()
                save_db(db)
                break

    return {"ok": True, **result}


@app.post("/api/chat")
def chat(req: ChatRequest, user=Depends(require_auth)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    db = load_db()
    answer = ai_chat(req.message, db)

    db.setdefault("chat_history", []).append({
        "role": "user",
        "text": req.message,
        "ts": utc_now(),
    })
    db["chat_history"].append({
        "role": "assistant",
        "text": answer,
        "ts": utc_now(),
    })
    save_db(db)

    return {
        "ok": True,
        "answer": answer,
        "summary": compute_job_stats(db.get("jobs", [])),
    }