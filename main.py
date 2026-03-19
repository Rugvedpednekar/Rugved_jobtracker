import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, Integer, String, Text, create_engine, desc, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

APP_TITLE = "JobTracker Personal Dashboard"
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
SCRIPT_FILE = BASE_DIR / "script.js"
STYLE_FILE = BASE_DIR / "style.css"

RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
DASHBOARD_EMAIL = os.getenv("DASHBOARD_EMAIL", "").strip().lower()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
NOVA_MODEL_ID = os.getenv("NOVA_MODEL_ID", "us.amazon.nova-lite-v1:0")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
REQUIRE_NOVA = os.getenv("REQUIRE_NOVA", "false").strip().lower() == "true"
PORT = int(os.getenv("PORT", "8000"))

def normalize_database_url(database_url: str) -> str:
    url = (database_url or "").strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = normalize_database_url(RAW_DATABASE_URL)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
COOKIE_NAME = "jobtracker_token"
IS_PRODUCTION = APP_ENV == "production"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

STATUS_ORDER = ["Wishlist", "Applied", "Interview", "Offered", "Accepted", "Rejected", "Archived"]
STATUS_MAP = {
    "wishlist": "Wishlist",
    "saved": "Wishlist",
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
DEFAULT_PARSED_PROFILE = {
    "skills": [],
    "roles": [],
    "experienceLevel": "",
    "domains": [],
    "locations": [],
    "education": [],
}
DEFAULT_SETTINGS = {
    "sync_window_hours": 24,
    "preferred_location": "",
    "user_notes": "",
}
STATE_DEFAULTS = {
    "resume_text": "",
    "parsed_profile": DEFAULT_PARSED_PROFILE,
    "keywords": [],
    "settings": DEFAULT_SETTINGS,
    "last_sync": None,
}


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    company: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="Applied")
    date: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    field: Mapped[str] = mapped_column(String(120), default="")
    sponsor: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(Text, default="")
    salary: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AppStateRecord(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine = None
SessionLocal = None


class LoginRequest(BaseModel):
    email: str
    password: str


class JobCreate(BaseModel):
    company: str
    role: str
    status: str = "Applied"
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    field: str = ""
    sponsor: str = ""
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
    sync_window_hours: int = 24
    preferred_location: str = ""
    user_notes: str = ""


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company: str
    role: str
    status: str
    date: str
    field: str
    sponsor: str
    notes: str
    link: str
    salary: str


class GmailSyncService:
    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": False,
            "provider": "gmail",
            "status": "not_configured",
            "message": "Gmail sync is intentionally not implemented yet. Add OAuth/configuration in a dedicated service later.",
        }


gmail_sync_service = GmailSyncService()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    config=Config(connect_timeout=30, read_timeout=3600, retries={"max_attempts": 2}),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_env() -> None:
    missing = []
    if not RAW_DATABASE_URL:
        missing.append("DATABASE_URL")
    if not JWT_SECRET:
        missing.append("JWT_SECRET")
    if not DASHBOARD_EMAIL:
        missing.append("DASHBOARD_EMAIL")
    if not (DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH):
        missing.append("DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def init_engine() -> None:
    global engine, SessionLocal
    if engine is not None:
        return
    require_env()
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class StateService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Any:
        record = self.db.get(AppStateRecord, key)
        if record:
            return record.value
        default = STATE_DEFAULTS.get(key)
        return json.loads(json.dumps(default)) if default is not None else None

    def set(self, key: str, value: Any) -> None:
        record = self.db.get(AppStateRecord, key)
        if record is None:
            record = AppStateRecord(key=key, value=value)
            self.db.add(record)
        else:
            record.value = value
            record.updated_at = datetime.now(timezone.utc)

    def ensure_defaults(self) -> None:
        changed = False
        for key, value in STATE_DEFAULTS.items():
            if self.db.get(AppStateRecord, key) is None:
                self.db.add(AppStateRecord(key=key, value=json.loads(json.dumps(value))))
                changed = True
        if changed:
            self.db.commit()


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> List[JobRecord]:
        return list(self.db.scalars(select(JobRecord).order_by(desc(JobRecord.date), desc(JobRecord.created_at))))

    def create(self, payload: JobCreate) -> JobRecord:
        job = JobRecord(
            company=payload.company.strip(),
            role=payload.role.strip(),
            status=normalize_status(payload.status),
            date=payload.date,
            field=payload.field.strip(),
            sponsor=payload.sponsor.strip(),
            notes=payload.notes.strip(),
            link=payload.link.strip(),
            salary=payload.salary.strip(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update(self, job_id: str, payload: JobUpdate) -> JobRecord:
        job = self.db.get(JobRecord, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            if isinstance(value, str):
                value = value.strip()
            if field == "status" and value is not None:
                value = normalize_status(value)
            setattr(job, field, value)
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job_id: str) -> None:
        job = self.db.get(JobRecord, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        self.db.delete(job)
        self.db.commit()


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def append(self, role: str, message: str) -> None:
        self.db.add(ChatHistoryRecord(role=role, message=message.strip()))
        self.db.commit()

    def tail(self, limit: int = 10) -> List[Dict[str, Any]]:
        rows = list(self.db.scalars(select(ChatHistoryRecord).order_by(desc(ChatHistoryRecord.created_at)).limit(limit)))
        rows.reverse()
        return [
            {"role": row.role, "message": row.message, "created_at": row.created_at.isoformat()}
            for row in rows
        ]


def initialize_database() -> None:
    init_engine()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        StateService(db).ensure_defaults()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        initialize_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str) -> bool:
    if DASHBOARD_PASSWORD_HASH:
        try:
            return pwd_context.verify(plain_password, DASHBOARD_PASSWORD_HASH)
        except (ValueError, TypeError):
            return False
    return plain_password == DASHBOARD_PASSWORD


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire, "type": "access"}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    return request.cookies.get(COOKIE_NAME) or (credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else None)


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


def normalize_status(status: str) -> str:
    return STATUS_MAP.get((status or "").strip().lower(), "Applied")


def compute_job_stats(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {status: 0 for status in STATUS_ORDER}
    for job in jobs:
        counts[normalize_status(job.get("status", "Applied"))] += 1
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
    return [
        {
            "id": job.get("id", ""),
            "company": job.get("company", ""),
            "role": job.get("role", ""),
            "status": normalize_status(job.get("status", "Applied")),
            "date": job.get("date", ""),
            "notes": job.get("notes", "")[:300],
            "salary": job.get("salary", ""),
            "sponsor": job.get("sponsor", ""),
            "field": job.get("field", ""),
            "link": job.get("link", ""),
        }
        for job in jobs[:limit]
    ]


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text or "", flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def extract_text_from_bedrock_response(resp: Dict[str, Any]) -> str:
    try:
        return "\n".join(item["text"] for item in resp["output"]["message"]["content"] if "text" in item).strip()
    except Exception:
        return ""


def nova_converse(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    try:
        response = bedrock.converse(
            modelId=NOVA_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 1800, "temperature": temperature, "topP": 0.9},
        )
        text = extract_text_from_bedrock_response(response)
        if not text:
            raise RuntimeError("Empty response from Nova")
        return text
    except (ClientError, BotoCoreError, Exception) as exc:
        if REQUIRE_NOVA:
            raise HTTPException(status_code=500, detail=f"Nova error: {exc}") from exc
        raise RuntimeError(f"Nova error: {exc}") from exc


def fallback_resume_parse(resume_text: str) -> Dict[str, Any]:
    text = resume_text.lower()
    common_skills = [
        "python", "sql", "java", "javascript", "typescript", "react", "node", "aws", "excel", "tableau",
        "power bi", "pandas", "scikit-learn", "tensorflow", "fastapi", "docker", "git", "linux", "c++",
        "machine learning", "data analysis",
    ]
    roles = [
        "data analyst", "software engineer", "data engineer", "business analyst", "machine learning engineer",
        "research assistant", "teaching assistant", "it analyst",
    ]
    years = re.findall(r"(\d+)\+?\s+year", text)
    experience = ""
    if years:
        value = max(int(item) for item in years)
        experience = "Entry Level" if value <= 1 else "Early Career" if value <= 3 else "Experienced"
    elif any(token in text for token in ["intern", "graduate", "student"]):
        experience = "Entry Level"
    return {
        "skills": sorted({skill.title() for skill in common_skills if skill in text}),
        "roles": sorted({role.title() for role in roles if role in text}),
        "experienceLevel": experience,
        "domains": [],
        "locations": [],
        "education": [],
    }


def fallback_email_parse(email_text: str) -> Dict[str, Any]:
    text = email_text.lower()
    if any(token in text for token in ["interview", "phone screen", "next round", "schedule a call"]):
        return {"status": "Interview", "reason": "The email mentions an interview or screening step."}
    if any(token in text for token in ["offer", "compensation package", "pleased to offer"]):
        return {"status": "Offered", "reason": "The email contains offer-related language."}
    if any(token in text for token in ["welcome aboard", "glad to welcome", "accepted"]):
        return {"status": "Accepted", "reason": "The email implies onboarding or acceptance."}
    if any(token in text for token in ["regret to inform", "not moving forward", "unfortunately", "rejected"]):
        return {"status": "Rejected", "reason": "The email contains rejection language."}
    return {"status": "Applied", "reason": "No clear lifecycle change detected."}


def load_context(db: Session) -> Dict[str, Any]:
    state = StateService(db)
    jobs = [JobResponse.model_validate(job).model_dump() for job in JobService(db).list()]
    return {
        "stats": compute_job_stats(jobs),
        "jobs": compact_jobs_for_prompt(jobs),
        "resume_text": state.get("resume_text") or "",
        "parsed_profile": state.get("parsed_profile") or DEFAULT_PARSED_PROFILE,
        "keywords": state.get("keywords") or [],
        "settings": state.get("settings") or DEFAULT_SETTINGS,
        "last_sync": state.get("last_sync"),
        "chat_history": ChatService(db).tail(limit=8),
        "gmail_sync": gmail_sync_service.get_status(),
    }


def deterministic_chat_answer(message: str, context: Dict[str, Any]) -> Optional[str]:
    msg = message.lower().strip()
    stats = context["stats"]
    jobs = context["jobs"]
    if "how many jobs" in msg or ("how many" in msg and "applied" in msg):
        return (
            f"You have {stats['total_jobs']} tracked jobs. Wishlist: {stats['wishlist_count']}, Applied: {stats['applied_count']}, "
            f"Interview: {stats['interview_count']}, Offered: {stats['offered_count']}, Accepted: {stats['accepted_count']}, Rejected: {stats['rejected_count']}."
        )
    if "how many interviews" in msg:
        return f"You currently have {stats['interview_count']} jobs in the Interview stage."
    if "how many offers" in msg:
        return f"You currently have {stats['offered_count']} jobs in the Offered stage."
    if "list my jobs" in msg or "show my jobs" in msg:
        if not jobs:
            return "You do not have any tracked jobs yet."
        return "Here are your current jobs:\n" + "\n".join(
            f"- {job['company']} — {job['role']} [{job['status']}]" for job in jobs[:15]
        )
    return None


def ai_parse_resume(resume_text: str) -> Dict[str, Any]:
    system_prompt = (
        "You are an expert resume parser. Return ONLY valid JSON using this schema: "
        '{"skills":[string],"roles":[string],"experienceLevel":string,"domains":[string],"locations":[string],"education":[string]}'
    )
    try:
        parsed = safe_json_loads(nova_converse(system_prompt, f"Parse this resume text:\n\n{resume_text}", 0.1))
        if parsed:
            for key, default in DEFAULT_PARSED_PROFILE.items():
                parsed.setdefault(key, default)
            return parsed
    except Exception:
        pass
    return fallback_resume_parse(resume_text)


def ai_parse_email(email_text: str) -> Dict[str, Any]:
    system_prompt = (
        "You classify recruiter emails into a job pipeline stage. Return ONLY valid JSON: "
        '{"status":"Wishlist|Applied|Interview|Offered|Accepted|Rejected","reason":"short explanation"}'
    )
    try:
        parsed = safe_json_loads(nova_converse(system_prompt, f"Classify this email:\n\n{email_text}", 0.0))
        if parsed and parsed.get("status"):
            return {"status": normalize_status(parsed["status"]), "reason": parsed.get("reason", "")}
    except Exception:
        pass
    return fallback_email_parse(email_text)


def ai_chat(message: str, context: Dict[str, Any]) -> str:
    shortcut = deterministic_chat_answer(message, context)
    if shortcut:
        return shortcut
    system_prompt = (
        "You are JobTracker AI, a private dashboard assistant. Answer only from the provided stored context. "
        "Do not invent jobs, settings, resume details, or counts. If data is missing, say so clearly."
    )
    user_prompt = f"Stored context JSON:\n{json.dumps(context, ensure_ascii=False)}\n\nUser question: {message}"
    try:
        return nova_converse(system_prompt, user_prompt, 0.1)
    except Exception:
        return "Nova is unavailable right now. Based on your saved dashboard context, I can still answer direct stats and job-list questions deterministically."


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(INDEX_FILE) if INDEX_FILE.exists() else JSONResponse({"ok": True, "message": "index.html not found"})


@app.get("/index.html", include_in_schema=False)
def index_html():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_FILE)


@app.get("/script.js", include_in_schema=False)
def script_js():
    if not SCRIPT_FILE.exists():
        raise HTTPException(status_code=404, detail="script.js not found")
    return FileResponse(SCRIPT_FILE, media_type="application/javascript")


@app.get("/style.css", include_in_schema=False)
def style_css():
    if not STYLE_FILE.exists():
        raise HTTPException(status_code=404, detail="style.css not found")
    return FileResponse(STYLE_FILE, media_type="text/css")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {
        "ok": True,
        "app": APP_TITLE,
        "environment": APP_ENV,
        "port": PORT,
        "database": "connected",
        "region": AWS_REGION,
        "model": NOVA_MODEL_ID,
        "auth_configured": bool(DASHBOARD_EMAIL and (DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH)),
    }


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return PlainTextResponse("User-agent: *\nDisallow:\n")


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response):
    email = payload.email.strip().lower()
    if email != DASHBOARD_EMAIL or not verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
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
    return {"ok": True, "email": email}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(user: Dict[str, Any] = Depends(require_auth)):
    return {"authenticated": True, "email": user["sub"]}


@app.get("/api/dashboard/simple")
def simple_dashboard(_: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    jobs = [JobResponse.model_validate(job).model_dump() for job in JobService(db).list()]
    stats = compute_job_stats(jobs)
    columns = {status: [] for status in STATUS_ORDER[:5]}
    for job in jobs:
        if job["status"] in columns:
            columns[job["status"]].append(job)
    return {
        "stats": stats,
        "columns": columns,
        "recent_jobs": jobs[:8],
        "profile_summary": StateService(db).get("parsed_profile") or DEFAULT_PARSED_PROFILE,
        "keywords": StateService(db).get("keywords") or [],
        "last_sync": StateService(db).get("last_sync"),
        "gmail_sync": gmail_sync_service.get_status(),
    }


@app.get("/api/jobs")
def get_jobs(_: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return [JobResponse.model_validate(job).model_dump() for job in JobService(db).list()]


@app.post("/api/jobs")
def add_job(payload: JobCreate, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    if not payload.company.strip() or not payload.role.strip():
        raise HTTPException(status_code=400, detail="Company and role are required")
    return JobResponse.model_validate(JobService(db).create(payload)).model_dump()


@app.put("/api/jobs/{job_id}")
def update_job(job_id: str, payload: JobUpdate, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return JobResponse.model_validate(JobService(db).update(job_id, payload)).model_dump()


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    JobService(db).delete(job_id)
    return {"ok": True}


@app.post("/api/resume/analyze")
def analyze_resume(req: ResumeAnalyzeRequest, _: Dict[str, Any] = Depends(require_auth)):
    parsed = ai_parse_resume(req.resume_text)
    return {"resume_text": req.resume_text, "parsed_profile": parsed}


@app.post("/api/resume/save")
def save_resume(req: ResumeSaveRequest, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    state = StateService(db)
    state.set("resume_text", req.resume_text)
    state.set("parsed_profile", req.parsed_profile or ai_parse_resume(req.resume_text))
    db.commit()
    return {"ok": True}


@app.get("/api/profile")
def get_profile(_: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    state = StateService(db)
    return {
        "resume_text": state.get("resume_text") or "",
        "parsed_profile": state.get("parsed_profile") or DEFAULT_PARSED_PROFILE,
        "chat_history": ChatService(db).tail(limit=12),
    }


@app.get("/api/keywords")
def get_keywords(_: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return {"keywords": StateService(db).get("keywords") or []}


@app.post("/api/keywords")
def save_keywords(req: KeywordsRequest, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    cleaned = [item.strip() for item in req.keywords if item.strip()]
    StateService(db).set("keywords", cleaned)
    db.commit()
    return {"keywords": cleaned}


@app.get("/api/settings")
def get_settings(_: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return {"settings": StateService(db).get("settings") or DEFAULT_SETTINGS, "gmail_sync": gmail_sync_service.get_status()}


@app.post("/api/settings")
def save_settings(req: SettingsRequest, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    payload = {
        "sync_window_hours": max(1, min(req.sync_window_hours, 168)),
        "preferred_location": req.preferred_location.strip(),
        "user_notes": req.user_notes.strip(),
    }
    state = StateService(db)
    state.set("settings", payload)
    state.set("last_sync", {"status": "manual", "updated_at": utc_now()})
    db.commit()
    return {"settings": payload, "gmail_sync": gmail_sync_service.get_status()}


@app.post("/api/email/parse")
def parse_email(req: EmailParseRequest, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    result = ai_parse_email(req.email_text)
    linked_job = None
    if req.job_id:
        job = db.get(JobRecord, req.job_id)
        if job:
            job.status = result["status"]
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            linked_job = JobResponse.model_validate(job).model_dump()
    return {"parsed": result, "job": linked_job}


@app.post("/api/chat")
def chat(req: ChatRequest, _: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    context = load_context(db)
    answer = ai_chat(req.message.strip(), context)
    chat_service = ChatService(db)
    chat_service.append("user", req.message.strip())
    chat_service.append("assistant", answer)
    return {"answer": answer, "history": chat_service.tail(limit=12)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
