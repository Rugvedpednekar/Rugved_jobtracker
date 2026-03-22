import io
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
from urllib.parse import urlparse

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, String, Text, create_engine, desc, func, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

APP_TITLE = "JobTracker Personal Career Assistant"
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
SCRIPT_FILE = BASE_DIR / "script.js"
STYLE_FILE = BASE_DIR / "style.css"

RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
DASHBOARD_EMAIL = os.getenv("DASHBOARD_EMAIL", "").strip().lower()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")
BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", DASHBOARD_EMAIL).strip().lower()
BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", DASHBOARD_PASSWORD)
BOOTSTRAP_ADMIN_PASSWORD_HASH = os.getenv("BOOTSTRAP_ADMIN_PASSWORD_HASH", DASHBOARD_PASSWORD_HASH)
BOOTSTRAP_ADMIN_FULL_NAME = os.getenv("BOOTSTRAP_ADMIN_FULL_NAME", "Admin User").strip()
AUTH_SEED_EMAILS = [email.strip().lower() for email in os.getenv("AUTH_SEED_EMAILS", "").split(",") if email.strip()]
AUTH_SEED_DEFAULT_PASSWORD = os.getenv("AUTH_SEED_DEFAULT_PASSWORD", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
NOVA_MODEL_ID = os.getenv("NOVA_MODEL_ID", "us.amazon.nova-lite-v1:0")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
REQUIRE_NOVA = os.getenv("REQUIRE_NOVA", "false").strip().lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
REQUEST_TIMEOUT = int(os.getenv("FETCH_TIMEOUT_SECONDS", "20"))

STATUS_ORDER = ["Wishlist", "Applied", "Interview", "Offered", "Accepted", "Rejected", "Archived", "Later"]
STATUS_MAP = {
    "wishlist": "Wishlist",
    "saved": "Wishlist",
    "save to wishlist": "Wishlist",
    "applied": "Applied",
    "application": "Applied",
    "submitted": "Applied",
    "interview": "Interview",
    "interviewing": "Interview",
    "offer": "Offered",
    "offered": "Offered",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "archived": "Archived",
    "later": "Later",
    "save for later": "Later",
}
ACTION_TO_STATUS = {
    "mark_applied": "Applied",
    "save_wishlist": "Wishlist",
    "save_later": "Later",
}
DOCUMENT_TYPES = ["resume", "cover_letter", "tailored_resume", "generated_cover_letter", "other"]
TASK_STATUSES = ["open", "in_progress", "done"]
TASK_TYPES = ["follow_up", "resume", "cover_letter", "interview_prep", "briefing", "research", "other"]

DEFAULT_PARSED_PROFILE = {
    "skills": [],
    "roles": [],
    "experienceLevel": "",
    "domains": [],
    "locations": [],
    "education": [],
    "summary": "",
}
DEFAULT_SETTINGS = {
    "sync_window_hours": 24,
    "preferred_location": "",
    "preferred_locations": [],
    "target_roles": [],
    "sponsorship_required": False,
    "minimum_job_match_score": 72,
    "user_notes": "",
    "tone": "concise",
}
STATE_DEFAULTS = {
    "resume_text": "",
    "parsed_profile": DEFAULT_PARSED_PROFILE,
    "keywords": [],
    "settings": DEFAULT_SETTINGS,
    "last_sync": None,
    "gmail_sync": {"enabled": False, "provider": "gmail", "status": "placeholder"},
}


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
logger = logging.getLogger("jobtracker")
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

REQUIRED_COLUMNS = {
    "jobs": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "company": "VARCHAR(255) DEFAULT ''",
        "role": "VARCHAR(255) DEFAULT ''",
        "status": "VARCHAR(32) DEFAULT 'Applied'",
        "date": "DATE",
        "field": "VARCHAR(120) DEFAULT ''",
        "sponsor": "VARCHAR(120) DEFAULT ''",
        "notes": "TEXT DEFAULT ''",
        "link": "TEXT DEFAULT ''",
        "salary": "VARCHAR(120) DEFAULT ''",
        "location": "VARCHAR(255) DEFAULT ''",
        "job_summary": "TEXT DEFAULT ''",
        "skills": "JSON",
        "source": "VARCHAR(64) DEFAULT 'manual'",
        "intake_id": "VARCHAR(32)",
        "ai_match_score": "INTEGER",
        "ai_match_summary": "TEXT DEFAULT ''",
        "metadata_json": "JSON",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "app_state": {
        "key": "VARCHAR(64) PRIMARY KEY",
        "value": "JSON",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "documents": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "name": "VARCHAR(255) DEFAULT ''",
        "doc_type": "VARCHAR(64) DEFAULT 'other'",
        "content_text": "TEXT DEFAULT ''",
        "linked_job_id": "VARCHAR(32)",
        "metadata_json": "JSON",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "tasks": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "title": "VARCHAR(255) DEFAULT ''",
        "details": "TEXT DEFAULT ''",
        "status": "VARCHAR(32) DEFAULT 'open'",
        "task_type": "VARCHAR(64) DEFAULT 'other'",
        "linked_job_id": "VARCHAR(32)",
        "due_date": "DATE",
        "metadata_json": "JSON",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "chat_history": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "role": "VARCHAR(16)",
        "message": "TEXT",
        "context_type": "VARCHAR(64) DEFAULT 'general'",
        "linked_job_id": "VARCHAR(32)",
        "created_at": "TIMESTAMP WITH TIME ZONE",
    },
    "job_intakes": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "url": "TEXT DEFAULT ''",
        "source_host": "VARCHAR(255) DEFAULT ''",
        "raw_html": "TEXT DEFAULT ''",
        "raw_text": "TEXT DEFAULT ''",
        "parse_status": "VARCHAR(32) DEFAULT 'parsed'",
        "parsed_job": "JSON",
        "suggested_actions": "JSON",
        "selected_action": "VARCHAR(64) DEFAULT ''",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "recommended_jobs": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "run_id": "VARCHAR(32)",
        "source": "VARCHAR(64) DEFAULT 'scout'",
        "source_job_id": "VARCHAR(255) DEFAULT ''",
        "company": "VARCHAR(255) DEFAULT ''",
        "role": "VARCHAR(255) DEFAULT ''",
        "location": "VARCHAR(255) DEFAULT ''",
        "job_type": "VARCHAR(64) DEFAULT ''",
        "salary": "VARCHAR(120) DEFAULT ''",
        "link": "TEXT DEFAULT ''",
        "summary": "TEXT DEFAULT ''",
        "posted_at": "TIMESTAMP WITH TIME ZONE",
        "skills": "JSON",
        "sponsorship": "VARCHAR(120) DEFAULT ''",
        "domain": "VARCHAR(120) DEFAULT ''",
        "score": "INTEGER DEFAULT 0",
        "score_breakdown": "JSON",
        "match_reasons": "JSON",
        "missing_points": "JSON",
        "job_metadata": "JSON",
        "status": "VARCHAR(32) DEFAULT 'recommended'",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "job_search_runs": {
        "id": "VARCHAR(32) PRIMARY KEY",
        "user_id": "INTEGER",
        "trigger_mode": "VARCHAR(32) DEFAULT 'manual'",
        "status": "VARCHAR(32) DEFAULT 'started'",
        "source_count": "INTEGER DEFAULT 0",
        "discovered_count": "INTEGER DEFAULT 0",
        "recommended_count": "INTEGER DEFAULT 0",
        "rejected_count": "INTEGER DEFAULT 0",
        "minimum_score": "INTEGER DEFAULT 72",
        "query_context": "JSON",
        "error_message": "TEXT DEFAULT ''",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    },
    "users": {
        "id": "INTEGER PRIMARY KEY",
        "email": "VARCHAR(255)",
        "password_hash": "VARCHAR(255)",
        "full_name": "VARCHAR(255) DEFAULT ''",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "created_at": "TIMESTAMP WITH TIME ZONE",
    },
}


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class JobRecord(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    company: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="Applied")
    date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(timezone.utc).date())
    field: Mapped[str] = mapped_column(String(120), default="")
    sponsor: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(Text, default="")
    salary: Mapped[str] = mapped_column(String(120), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    job_summary: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(64), default="manual")
    intake_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ai_match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_match_summary: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)


class JobIntakeRecord(TimestampMixin, Base):
    __tablename__ = "job_intakes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    url: Mapped[str] = mapped_column(Text, default="")
    source_host: Mapped[str] = mapped_column(String(255), default="")
    raw_html: Mapped[str] = mapped_column(Text, default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parse_status: Mapped[str] = mapped_column(String(32), default="parsed")
    parsed_job: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    suggested_actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    selected_action: Mapped[str] = mapped_column(String(64), default="")


class DocumentRecord(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    doc_type: Mapped[str] = mapped_column(String(64), default="other")
    content_text: Mapped[str] = mapped_column(Text, default="")
    linked_job_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TaskRecord(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="open")
    task_type: Mapped[str] = mapped_column(String(64), default="other")
    linked_job_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)


class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    context_type: Mapped[str] = mapped_column(String(64), default="general")
    linked_job_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AppStateRecord(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RecommendedJobRecord(TimestampMixin, Base):
    __tablename__ = "recommended_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="scout")
    source_job_id: Mapped[str] = mapped_column(String(255), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    job_type: Mapped[str] = mapped_column(String(64), default="")
    salary: Mapped[str] = mapped_column(String(120), default="")
    link: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    sponsorship: Mapped[str] = mapped_column(String(120), default="")
    domain: Mapped[str] = mapped_column(String(120), default="")
    score: Mapped[int] = mapped_column(Integer, default=0)
    score_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    match_reasons: Mapped[List[str]] = mapped_column(JSON, default=list)
    missing_points: Mapped[List[str]] = mapped_column(JSON, default=list)
    job_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="recommended")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class JobSearchRunRecord(TimestampMixin, Base):
    __tablename__ = "job_search_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    trigger_mode: Mapped[str] = mapped_column(String(32), default="manual")
    status: Mapped[str] = mapped_column(String(32), default="started")
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    minimum_score: Mapped[int] = mapped_column(Integer, default=72)
    query_context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine = None
SessionLocal = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


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
    location: str = ""
    job_summary: str = ""
    skills: List[str] = Field(default_factory=list)
    source: str = "manual"
    intake_id: Optional[str] = None
    ai_match_score: Optional[int] = None
    ai_match_summary: str = ""
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


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
    location: Optional[str] = None
    job_summary: Optional[str] = None
    skills: Optional[List[str]] = None
    ai_match_score: Optional[int] = None
    ai_match_summary: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str


class ResumeSaveRequest(BaseModel):
    resume_text: str
    parsed_profile: Optional[Dict[str, Any]] = None


class DocumentUpdateRequest(BaseModel):
    name: Optional[str] = None
    content_text: str


class DocumentPdfRequest(BaseModel):
    title: str = "Document"
    content_text: str
    file_name: Optional[str] = None


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
    preferred_locations: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    sponsorship_required: bool = False
    minimum_job_match_score: int = 72
    user_notes: str = ""
    tone: str = "concise"


class ParseJobLinkRequest(BaseModel):
    url: HttpUrl


class JobActionRequest(BaseModel):
    intake_id: str
    action: str
    company: Optional[str] = None
    role: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    status: str


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company: str
    role: str
    status: str
    date: date
    field: str
    sponsor: str
    notes: str
    link: str
    salary: str
    location: str
    job_summary: str
    skills: List[str]
    source: str
    intake_id: Optional[str]
    ai_match_score: Optional[int]
    ai_match_summary: str
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    details: str
    status: str
    task_type: str
    linked_job_id: Optional[str]
    due_date: Optional[date]
    metadata_json: Dict[str, Any]


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    doc_type: str
    content_text: str
    linked_job_id: Optional[str]
    metadata_json: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RecommendedJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: Optional[str]
    source: str
    source_job_id: str
    company: str
    role: str
    location: str
    job_type: str
    salary: str
    link: str
    summary: str
    posted_at: Optional[datetime]
    skills: List[str]
    sponsorship: str
    domain: str
    score: int
    score_breakdown: Dict[str, Any]
    match_reasons: List[str]
    missing_points: List[str]
    job_metadata: Dict[str, Any]
    status: str
    is_active: bool


class GmailSyncService:
    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": False,
            "provider": "gmail",
            "status": "placeholder",
            "message": "Gmail sync architecture is scaffolded. OAuth and mailbox sync are intentionally not implemented yet.",
            "next_steps": [
                "Create a dedicated gmail_accounts table",
                "Store encrypted refresh tokens",
                "Schedule sync jobs with Railway cron or worker",
            ],
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


def deep_copy_default(value: Any) -> Any:
    return json.loads(json.dumps(value))


def safe_json_value(value: Any, fallback: Any) -> Any:
    if value is None:
        return deep_copy_default(fallback)
    if isinstance(fallback, dict):
        return value if isinstance(value, dict) else deep_copy_default(fallback)
    if isinstance(fallback, list):
        return value if isinstance(value, list) else deep_copy_default(fallback)
    return value


def get_bootstrap_credentials() -> Optional[Tuple[str, str, str]]:
    email = BOOTSTRAP_ADMIN_EMAIL or DASHBOARD_EMAIL
    password_hash = BOOTSTRAP_ADMIN_PASSWORD_HASH or DASHBOARD_PASSWORD_HASH
    if not password_hash and (BOOTSTRAP_ADMIN_PASSWORD or DASHBOARD_PASSWORD):
        password_hash = pwd_context.hash(BOOTSTRAP_ADMIN_PASSWORD or DASHBOARD_PASSWORD)
    if not email or not password_hash:
        return None
    return email, password_hash, BOOTSTRAP_ADMIN_FULL_NAME or "Admin User"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except (ValueError, TypeError):
        return False


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        normalized = (email or "").strip().lower()
        if not normalized:
            return None
        return self.db.scalar(select(UserRecord).where(func.lower(UserRecord.email) == normalized))

    def authenticate(self, email: str, password: str) -> Optional[UserRecord]:
        user = self.get_by_email(email)
        if not user or not user.is_active:
            return None
        return user if verify_password(password, user.password_hash) else None

    def create_user(self, email: str, password_hash: str, full_name: str = "", is_active: bool = True) -> UserRecord:
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("Email is required")
        existing = self.get_by_email(normalized)
        if existing:
            existing.password_hash = password_hash
            existing.full_name = full_name or existing.full_name
            existing.is_active = is_active
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        user = UserRecord(email=normalized, password_hash=password_hash, full_name=full_name or "", is_active=is_active)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_bootstrap_admin(self) -> Optional[UserRecord]:
        if self.db.scalar(select(func.count()).select_from(UserRecord)):
            return None
        bootstrap = get_bootstrap_credentials()
        if not bootstrap:
            logger.warning("Users table is empty and no bootstrap admin credentials were provided.")
            return None
        email, password_hash, full_name = bootstrap
        logger.info("Bootstrapping initial admin user for %s", email)
        return self.create_user(email=email, password_hash=password_hash, full_name=full_name, is_active=True)

    def seed_users(self, emails: List[str], default_password: str) -> List[UserRecord]:
        if not default_password:
            raise ValueError("AUTH_SEED_DEFAULT_PASSWORD is required to seed users safely")
        created = []
        for email in emails:
            normalized = (email or "").strip().lower()
            if not normalized or self.get_by_email(normalized):
                continue
            full_name = normalized.split("@")[0].replace(".", " ").replace("_", " ").title()
            created.append(self.create_user(normalized, password_hash=hash_password(default_password), full_name=full_name, is_active=True))
        return created


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    dialect = engine.dialect.name
    with engine.begin() as connection:
        for table_name, columns in REQUIRED_COLUMNS.items():
            if not inspector.has_table(table_name):
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_sql in columns.items():
                if column_name in existing_columns:
                    continue
                statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                if dialect == "postgresql":
                    statement = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_sql}"
                logger.warning("Adding missing column %s.%s during startup schema reconciliation", table_name, column_name)
                connection.execute(text(statement))


def serialize_job(job: JobRecord) -> Dict[str, Any]:
    payload = JobResponse.model_validate(job).model_dump(mode="json")
    payload["skills"] = safe_json_value(payload.get("skills"), [])
    payload["metadata_json"] = safe_json_value(payload.get("metadata_json"), {})
    return payload


def handle_database_exception(route_name: str, exc: Exception) -> None:
    logger.exception("Database error in %s: %s", route_name, exc)
    raise HTTPException(status_code=500, detail=f"{route_name} failed because of a database error. Check Railway logs for details.") from exc


def normalize_status(status: str) -> str:
    return STATUS_MAP.get((status or "").strip().lower(), status.strip().title() if status else "Applied")


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


def nova_converse(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 2200) -> str:
    try:
        response = bedrock.converse(
            modelId=NOVA_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature, "topP": 0.9},
        )
        text = extract_text_from_bedrock_response(response)
        if not text:
            raise RuntimeError("Empty response from Nova")
        return text
    except (ClientError, BotoCoreError, Exception) as exc:
        if REQUIRE_NOVA:
            raise HTTPException(status_code=500, detail=f"Nova error: {exc}") from exc
        raise RuntimeError(f"Nova error: {exc}") from exc


class StateService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def _scope_key(self, key: str) -> str:
        return f"user:{self.user_id}:{key}"

    def get(self, key: str) -> Any:
        record = self.db.get(AppStateRecord, self._scope_key(key))
        if record:
            return safe_json_value(record.value, STATE_DEFAULTS.get(key))
        default = STATE_DEFAULTS.get(key)
        return deep_copy_default(default) if default is not None else None

    def set(self, key: str, value: Any) -> None:
        default = STATE_DEFAULTS.get(key)
        stored_value = safe_json_value(value, default) if default is not None else value
        scoped_key = self._scope_key(key)
        record = self.db.get(AppStateRecord, scoped_key)
        if record is None:
            self.db.add(AppStateRecord(key=scoped_key, value=stored_value))
        else:
            record.value = stored_value
            record.updated_at = datetime.now(timezone.utc)

    def ensure_defaults(self) -> None:
        changed = False
        for key, value in STATE_DEFAULTS.items():
            scoped_key = self._scope_key(key)
            if self.db.get(AppStateRecord, scoped_key) is None:
                self.db.add(AppStateRecord(key=scoped_key, value=deep_copy_default(value)))
                changed = True
        if changed:
            self.db.commit()


class JobService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def list(self) -> List[JobRecord]:
        stmt = select(JobRecord).where(JobRecord.user_id == self.user_id).order_by(desc(JobRecord.updated_at), desc(JobRecord.created_at))
        return list(self.db.scalars(stmt))

    def create(self, payload: JobCreate) -> JobRecord:
        job = JobRecord(
            user_id=self.user_id,
            company=payload.company.strip(),
            role=payload.role.strip(),
            status=normalize_status(payload.status),
            date=date.fromisoformat(payload.date),
            field=payload.field.strip(),
            sponsor=payload.sponsor.strip(),
            notes=payload.notes.strip(),
            link=payload.link.strip(),
            salary=payload.salary.strip(),
            location=payload.location.strip(),
            job_summary=payload.job_summary.strip(),
            skills=payload.skills,
            source=payload.source,
            intake_id=payload.intake_id,
            ai_match_score=payload.ai_match_score,
            ai_match_summary=payload.ai_match_summary.strip(),
            metadata_json=payload.metadata_json,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update(self, job_id: str, payload: JobUpdate) -> JobRecord:
        job = self.db.scalar(select(JobRecord).where(JobRecord.id == job_id, JobRecord.user_id == self.user_id))
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            if isinstance(value, str):
                value = value.strip()
            if field == "status" and value is not None:
                value = normalize_status(value)
            if field == "date" and value:
                value = date.fromisoformat(value)
            setattr(job, field, value)
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job_id: str) -> None:
        job = self.db.scalar(select(JobRecord).where(JobRecord.id == job_id, JobRecord.user_id == self.user_id))
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        self.db.delete(job)
        self.db.commit()


class ChatService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def append(self, role: str, message: str, context_type: str = "general", linked_job_id: Optional[str] = None) -> None:
        self.db.add(ChatHistoryRecord(user_id=self.user_id, role=role, message=message.strip(), context_type=context_type, linked_job_id=linked_job_id))
        self.db.commit()

    def tail(self, limit: int = 12) -> List[Dict[str, Any]]:
        stmt = select(ChatHistoryRecord).where(ChatHistoryRecord.user_id == self.user_id).order_by(desc(ChatHistoryRecord.created_at)).limit(limit)
        rows = list(self.db.scalars(stmt))
        rows.reverse()
        return [
            {
                "role": row.role,
                "message": row.message,
                "context_type": row.context_type,
                "linked_job_id": row.linked_job_id,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


class DocumentService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def list(self) -> List[DocumentRecord]:
        stmt = select(DocumentRecord).where(DocumentRecord.user_id == self.user_id, DocumentRecord.is_active.is_(True)).order_by(desc(DocumentRecord.updated_at))
        return list(self.db.scalars(stmt))

    def get(self, document_id: str) -> DocumentRecord:
        record = self.db.scalar(select(DocumentRecord).where(DocumentRecord.id == document_id, DocumentRecord.user_id == self.user_id))
        if record is None or not record.is_active:
            raise HTTPException(status_code=404, detail="Document not found")
        return record

    def upsert_text_document(self, name: str, doc_type: str, content_text: str, linked_job_id: Optional[str] = None, metadata_json: Optional[Dict[str, Any]] = None) -> DocumentRecord:
        stmt = select(DocumentRecord).where(DocumentRecord.user_id == self.user_id, DocumentRecord.doc_type == doc_type, DocumentRecord.linked_job_id == linked_job_id, DocumentRecord.is_active.is_(True))
        record = self.db.scalar(stmt)
        if record is None:
            record = DocumentRecord(user_id=self.user_id, name=name, doc_type=doc_type, linked_job_id=linked_job_id)
            self.db.add(record)
        record.content_text = content_text.strip()
        record.name = name
        record.metadata_json = metadata_json or {}
        record.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, document_id: str, content_text: str, name: Optional[str] = None) -> DocumentRecord:
        record = self.get(document_id)
        record.content_text = content_text.strip()
        if name is not None:
            record.name = name.strip() or record.name
        record.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(record)
        return record


class TaskService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def list(self) -> List[TaskRecord]:
        stmt = select(TaskRecord).where(TaskRecord.user_id == self.user_id).order_by(TaskRecord.status.asc(), TaskRecord.due_date.asc(), desc(TaskRecord.created_at))
        return list(self.db.scalars(stmt))

    def create_many(self, tasks: List[Dict[str, Any]], linked_job_id: Optional[str] = None) -> List[TaskRecord]:
        created: List[TaskRecord] = []
        for task in tasks:
            title = (task.get("title") or "").strip()
            if not title:
                continue
            due = task.get("due_date")
            due_date = None
            if due:
                try:
                    due_date = date.fromisoformat(due)
                except ValueError:
                    due_date = None
            record = TaskRecord(
                user_id=self.user_id,
                title=title,
                details=(task.get("details") or "").strip(),
                status=task.get("status", "open") if task.get("status") in TASK_STATUSES else "open",
                task_type=task.get("task_type", "other") if task.get("task_type") in TASK_TYPES else "other",
                linked_job_id=linked_job_id or task.get("linked_job_id"),
                due_date=due_date,
                metadata_json=task.get("metadata_json") or {},
            )
            self.db.add(record)
            created.append(record)
        self.db.commit()
        for item in created:
            self.db.refresh(item)
        return created

    def update_status(self, task_id: str, status: str) -> TaskRecord:
        task = self.db.scalar(select(TaskRecord).where(TaskRecord.id == task_id, TaskRecord.user_id == self.user_id))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = status if status in TASK_STATUSES else "open"
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task


class IntakeService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def create(self, url: str, raw_html: str, raw_text: str, parsed_job: Dict[str, Any], suggested_actions: List[Dict[str, Any]]) -> JobIntakeRecord:
        intake = JobIntakeRecord(
            user_id=self.user_id,
            url=url,
            source_host=urlparse(url).netloc,
            raw_html=raw_html,
            raw_text=raw_text,
            parsed_job=parsed_job,
            suggested_actions=suggested_actions,
            parse_status="parsed",
        )
        self.db.add(intake)
        self.db.commit()
        self.db.refresh(intake)
        return intake

    def set_action(self, intake_id: str, action: str) -> JobIntakeRecord:
        intake = self.db.scalar(select(JobIntakeRecord).where(JobIntakeRecord.id == intake_id, JobIntakeRecord.user_id == self.user_id))
        if intake is None:
            raise HTTPException(status_code=404, detail="Job intake not found")
        intake.selected_action = action
        intake.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(intake)
        return intake

    def recent(self, limit: int = 8) -> List[JobIntakeRecord]:
        stmt = select(JobIntakeRecord).where(JobIntakeRecord.user_id == self.user_id).order_by(desc(JobIntakeRecord.created_at)).limit(limit)
        return list(self.db.scalars(stmt))


class RecommendedJobService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def list_active(self, limit: int = 12) -> List[RecommendedJobRecord]:
        stmt = (
            select(RecommendedJobRecord)
            .where(RecommendedJobRecord.user_id == self.user_id, RecommendedJobRecord.is_active.is_(True), RecommendedJobRecord.status == "recommended")
            .order_by(desc(RecommendedJobRecord.score), desc(RecommendedJobRecord.created_at))
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def dismiss(self, recommended_job_id: str) -> RecommendedJobRecord:
        job = self.db.scalar(select(RecommendedJobRecord).where(RecommendedJobRecord.id == recommended_job_id, RecommendedJobRecord.user_id == self.user_id))
        if job is None:
            raise HTTPException(status_code=404, detail="Recommended job not found")
        job.status = "dismissed"
        job.is_active = False
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def save_run_results(self, run_id: str, jobs: List[Dict[str, Any]]) -> None:
        if jobs:
            existing = list(self.db.scalars(select(RecommendedJobRecord).where(RecommendedJobRecord.user_id == self.user_id, RecommendedJobRecord.is_active.is_(True))))
            existing_keys = {(item.company.strip().lower(), item.role.strip().lower(), item.link.strip()) for item in existing}
            for item in jobs:
                dedupe_key = (item["company"].strip().lower(), item["role"].strip().lower(), item["link"].strip())
                if dedupe_key in existing_keys:
                    continue
                record = RecommendedJobRecord(
                    user_id=self.user_id,
                    run_id=run_id,
                    source=item["source"],
                    source_job_id=item["source_job_id"],
                    company=item["company"],
                    role=item["role"],
                    location=item["location"],
                    job_type=item["job_type"],
                    salary=item["salary"],
                    link=item["link"],
                    summary=item["summary"],
                    posted_at=item["posted_at"],
                    skills=item["skills"],
                    sponsorship=item["sponsorship"],
                    domain=item["domain"],
                    score=item["score"],
                    score_breakdown=item["score_breakdown"],
                    match_reasons=item["match_reasons"],
                    missing_points=item["missing_points"],
                    job_metadata=item["job_metadata"],
                )
                self.db.add(record)
        self.db.commit()


class JobScoutService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.state = StateService(db, user_id)

    def discover(self, trigger_mode: str = "manual") -> Dict[str, Any]:
        settings = self.state.get("settings") or DEFAULT_SETTINGS
        parsed_profile = self.state.get("parsed_profile") or DEFAULT_PARSED_PROFILE
        context = {
            "resume_text": self.state.get("resume_text") or "",
            "parsed_profile": parsed_profile,
            "keywords": self.state.get("keywords") or [],
            "settings": settings,
            "preferred_locations": self._preferred_locations(settings, parsed_profile),
            "target_roles": self._target_roles(settings, parsed_profile),
        }
        minimum_score = max(50, min(int(settings.get("minimum_job_match_score", 72) or 72), 95))
        run = JobSearchRunRecord(user_id=self.user_id, trigger_mode=trigger_mode, status="started", minimum_score=minimum_score, query_context=context)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            discovered = self.fetch_fresh_jobs(context)
            recommended = []
            for job in discovered:
                scored = self.score_job(job, context)
                if scored["score"] >= minimum_score:
                    recommended.append({**job, **scored})

            run.status = "completed"
            run.source_count = len({item["source"] for item in discovered})
            run.discovered_count = len(discovered)
            run.recommended_count = len(recommended)
            run.rejected_count = max(0, len(discovered) - len(recommended))
            run.updated_at = datetime.now(timezone.utc)
            RecommendedJobService(self.db, self.user_id).save_run_results(run.id, recommended)
            self.state.set("last_sync", {"status": "job_scout_manual", "updated_at": utc_now(), "run_id": run.id})
            self.db.commit()
            return {
                "run_id": run.id,
                "status": run.status,
                "discovered_count": run.discovered_count,
                "recommended_count": run.recommended_count,
                "minimum_score": minimum_score,
                "recommended_jobs": [RecommendedJobResponse.model_validate(item).model_dump(mode="json") for item in RecommendedJobService(self.db, self.user_id).list_active(limit=12)],
                "scheduler_ready": {
                    "trigger_mode": trigger_mode,
                    "next_step": "Call POST /api/jobs/discover from a Railway cron service each morning.",
                },
            }
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    def fetch_fresh_jobs(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        roles = context["target_roles"]
        locations = context["preferred_locations"]
        all_jobs: List[Dict[str, Any]] = []
        for role in roles[:4] or ["Software Engineer"]:
            for location in locations[:3] or ["Remote"]:
                all_jobs.extend(self._fetch_remotive(role, location))
        if not all_jobs:
            all_jobs = self._fallback_seed_jobs(roles, locations)

        fresh_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        fresh_jobs = []
        seen = set()
        for job in all_jobs:
            posted_at = job.get("posted_at")
            if posted_at and posted_at < fresh_cutoff:
                continue
            dedupe_key = (job["company"].strip().lower(), job["role"].strip().lower(), job["link"].strip())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            fresh_jobs.append(job)
        return fresh_jobs

    def _fetch_remotive(self, role: str, location: str) -> List[Dict[str, Any]]:
        try:
            response = requests.get("https://remotive.com/api/remote-jobs", params={"search": role}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            jobs = []
            for item in payload.get("jobs", [])[:25]:
                jobs.append({
                    "source": "remotive",
                    "source_job_id": str(item.get("id", "")),
                    "company": (item.get("company_name") or "").strip(),
                    "role": (item.get("title") or "").strip(),
                    "location": (item.get("candidate_required_location") or location or "Remote").strip(),
                    "job_type": (item.get("job_type") or "").strip(),
                    "salary": (item.get("salary") or "").strip(),
                    "link": (item.get("url") or "").strip(),
                    "summary": self._strip_html(item.get("description") or "")[:900],
                    "posted_at": self._parse_datetime(item.get("publication_date")),
                    "skills": self._extract_skills(f"{item.get('title', '')} {item.get('description', '')}"),
                    "sponsorship": "unknown",
                    "domain": (item.get("category") or "").strip(),
                    "job_metadata": {"provider": "remotive", "search_role": role},
                })
            return jobs
        except Exception:
            return []

    def _fallback_seed_jobs(self, roles: List[str], locations: List[str]) -> List[Dict[str, Any]]:
        base_roles = roles or ["Software Engineer", "Data Analyst"]
        base_locations = locations or ["Remote", "New York, NY"]
        now = datetime.now(timezone.utc)
        templates = [
            ("Northstar Labs", base_roles[0], base_locations[0], ["Python", "FastAPI", "Postgres", "AWS"], "B2B SaaS"),
            ("Orbit Health", base_roles[0], base_locations[0], ["SQL", "Python", "APIs", "Docker"], "HealthTech"),
            ("Signal Commerce", base_roles[min(1, len(base_roles)-1)], base_locations[min(1, len(base_locations)-1)], ["JavaScript", "Analytics", "SQL", "Experimentation"], "E-commerce"),
        ]
        return [
            {
                "source": "seed",
                "source_job_id": f"seed-{index}",
                "company": company,
                "role": role,
                "location": location,
                "job_type": "Full-time",
                "salary": "",
                "link": f"https://example.com/jobs/{index}",
                "summary": f"{company} is hiring a {role} with emphasis on {', '.join(skills[:3])}.",
                "posted_at": now - timedelta(hours=6 * (index + 1)),
                "skills": skills,
                "sponsorship": "unknown",
                "domain": domain,
                "job_metadata": {"provider": "seed", "future_ready": True},
            }
            for index, (company, role, location, skills, domain) in enumerate(templates)
        ]

    def score_job(self, job: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        parsed_profile = context["parsed_profile"]
        keywords = [item.lower() for item in context["keywords"]]
        role_targets = [item.lower() for item in context["target_roles"]]
        preferred_locations = [item.lower() for item in context["preferred_locations"]]
        profile_skills = {item.lower() for item in parsed_profile.get("skills", [])}
        profile_domains = {item.lower() for item in parsed_profile.get("domains", [])}
        job_role = job["role"].lower()
        job_location = job["location"].lower()
        job_skills = [item.lower() for item in job.get("skills", [])]
        job_domain = (job.get("domain") or "").lower()
        sponsorship_required = bool(context["settings"].get("sponsorship_required"))

        role_score = 25 if any(target in job_role or job_role in target for target in role_targets) else 8 if role_targets else 16
        matched_skills = sorted({skill for skill in job_skills if skill in profile_skills or skill in keywords})
        missing_skills = sorted({skill.title() for skill in job_skills if skill not in matched_skills})[:6]
        skills_score = min(25, 6 * len(matched_skills) + (3 if len(matched_skills) >= 3 else 0))

        experience_level = (parsed_profile.get("experienceLevel") or "").lower()
        experience_fit = 15
        if experience_level and any(token in job_role for token in ["senior", "staff", "principal"]) and "entry" in experience_level:
            experience_fit = 4
        elif experience_level and any(token in job_role for token in ["intern", "junior", "associate"]) and "experienced" in experience_level:
            experience_fit = 10

        location_fit = 15 if not preferred_locations else 4
        if preferred_locations and any(pref in job_location or job_location in pref for pref in preferred_locations):
            location_fit = 15
        elif "remote" in job_location and any("remote" in pref for pref in preferred_locations):
            location_fit = 15

        sponsorship_fit = 10
        sponsorship_value = (job.get("sponsorship") or "unknown").lower()
        if sponsorship_required:
            sponsorship_fit = 10 if sponsorship_value in {"supports", "yes", "unknown"} else 2

        domain_fit = 10 if job_domain and (job_domain in profile_domains or any(domain in job_domain for domain in profile_domains)) else 5
        if not profile_domains:
            domain_fit = 7

        score = max(0, min(100, role_score + skills_score + experience_fit + location_fit + sponsorship_fit + domain_fit))
        match_reasons = []
        if role_score >= 20:
            match_reasons.append("Role title is closely aligned with your target roles.")
        if matched_skills:
            match_reasons.append(f"Strong skill overlap: {', '.join(skill.title() for skill in matched_skills[:5])}.")
        if location_fit >= 12:
            match_reasons.append("Location matches your preferred search geography.")
        if domain_fit >= 8 and job.get("domain"):
            match_reasons.append(f"Domain overlap is strong for {job.get('domain')}.")

        missing_points = []
        if role_score < 18:
            missing_points.append("Role title is adjacent but not an exact target-role match.")
        if missing_skills:
            missing_points.append(f"Missing or unproven skills: {', '.join(missing_skills[:4])}.")
        if location_fit < 10:
            missing_points.append("Location is outside your preferred locations.")
        if sponsorship_required and sponsorship_fit < 10:
            missing_points.append("Sponsorship support is unclear or unavailable.")

        return {
            "score": score,
            "score_breakdown": {
                "role_title_match": role_score,
                "skills_match": skills_score,
                "experience_fit": experience_fit,
                "location_fit": location_fit,
                "sponsorship_fit": sponsorship_fit,
                "domain_fit": domain_fit,
            },
            "match_reasons": match_reasons or ["General profile alignment is promising."],
            "missing_points": missing_points or ["No major blockers detected from the available job data."],
        }

    def _preferred_locations(self, settings: Dict[str, Any], parsed_profile: Dict[str, Any]) -> List[str]:
        values = settings.get("preferred_locations") or []
        if settings.get("preferred_location"):
            values = [settings["preferred_location"], *values]
        if not values:
            values = parsed_profile.get("locations") or []
        return [item.strip() for item in values if str(item).strip()]

    def _target_roles(self, settings: Dict[str, Any], parsed_profile: Dict[str, Any]) -> List[str]:
        values = settings.get("target_roles") or parsed_profile.get("roles") or []
        return [item.strip() for item in values if str(item).strip()]

    def _extract_skills(self, text: str) -> List[str]:
        bank = ["Python", "SQL", "FastAPI", "AWS", "Postgres", "Docker", "JavaScript", "React", "APIs", "Analytics"]
        blob = text.lower()
        return [skill for skill in bank if skill.lower() in blob]

    def _strip_html(self, value: str) -> str:
        soup = BeautifulSoup(value, "html.parser")
        return " ".join(soup.get_text(" ").split())

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def compute_job_stats(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {status: 0 for status in STATUS_ORDER}
    for job in jobs:
        status = normalize_status(job.get("status", "Applied"))
        counts[status] = counts.get(status, 0) + 1
    return {
        "total_jobs": len(jobs),
        "wishlist_count": counts.get("Wishlist", 0),
        "applied_count": counts.get("Applied", 0),
        "interview_count": counts.get("Interview", 0),
        "offered_count": counts.get("Offered", 0),
        "accepted_count": counts.get("Accepted", 0),
        "rejected_count": counts.get("Rejected", 0),
        "later_count": counts.get("Later", 0),
        "by_status": counts,
    }


def fallback_resume_parse(resume_text: str) -> Dict[str, Any]:
    text = resume_text.lower()
    common_skills = [
        "python", "sql", "java", "javascript", "typescript", "react", "node", "aws", "excel", "tableau",
        "power bi", "pandas", "scikit-learn", "fastapi", "docker", "git", "linux", "c++", "machine learning",
        "data analysis", "postgresql", "css", "html",
    ]
    roles = [
        "data analyst", "software engineer", "data engineer", "business analyst", "machine learning engineer",
        "product analyst", "full stack engineer", "backend engineer",
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
        "summary": "Fallback profile parse generated locally.",
    }


def ai_parse_resume(resume_text: str) -> Dict[str, Any]:
    system_prompt = (
        "You are an expert resume parser. Return ONLY valid JSON with schema "
        '{"skills":[string],"roles":[string],"experienceLevel":string,"domains":[string],"locations":[string],"education":[string],"summary":string}'
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


def fallback_parse_job_text(raw_text: str, url: str) -> Dict[str, Any]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    host = urlparse(url).netloc
    role = lines[0][:120] if lines else "Unknown role"
    company = next((line for line in lines[:15] if len(line.split()) <= 6 and line.lower() not in role.lower()), host or "Unknown company")
    location_match = re.search(r"(remote|hybrid|on-site|onsite|[A-Z][a-z]+,\s?[A-Z]{2})", raw_text, re.IGNORECASE)
    salary_match = re.search(r"\$[\d,]+(?:\s*-\s*\$[\d,]+)?", raw_text)
    skill_bank = ["Python", "SQL", "FastAPI", "AWS", "Postgres", "JavaScript", "HTML", "CSS", "Docker", "React"]
    skills = [skill for skill in skill_bank if skill.lower() in raw_text.lower()]
    summary = " ".join(lines[:6])[:900]
    return {
        "company": company,
        "role": role,
        "location": location_match.group(0) if location_match else "",
        "employment_type": "",
        "salary": salary_match.group(0) if salary_match else "",
        "skills": skills,
        "summary": summary,
        "responsibilities": lines[6:12],
        "qualifications": lines[12:18],
        "keywords": skills,
        "field": "",
        "source_url": url,
    }


def ai_parse_job_description(raw_text: str, url: str) -> Dict[str, Any]:
    system_prompt = (
        "You parse job descriptions into structured JSON. Return ONLY valid JSON with schema "
        '{"company":string,"role":string,"location":string,"employment_type":string,"salary":string,'
        '"skills":[string],"summary":string,"responsibilities":[string],"qualifications":[string],"keywords":[string],"field":string,"source_url":string}'
    )
    try:
        parsed = safe_json_loads(nova_converse(system_prompt, f"Job URL: {url}\n\nRaw job text:\n{raw_text[:20000]}", 0.1, 2500))
        if parsed:
            parsed.setdefault("source_url", url)
            parsed.setdefault("skills", [])
            parsed.setdefault("responsibilities", [])
            parsed.setdefault("qualifications", [])
            parsed.setdefault("keywords", parsed.get("skills", []))
            parsed.setdefault("summary", "")
            parsed.setdefault("field", "")
            return parsed
    except Exception:
        pass
    return fallback_parse_job_text(raw_text, url)


def fallback_match_analysis(parsed_job: Dict[str, Any], resume_text: str, parsed_profile: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
    resume_blob = f"{resume_text}\n{json.dumps(parsed_profile)}\n{' '.join(keywords)}".lower()
    job_skills = parsed_job.get("skills", [])
    matched = [skill for skill in job_skills if skill.lower() in resume_blob]
    missing = [skill for skill in job_skills if skill not in matched]
    score = min(98, 45 + len(matched) * 12 - len(missing) * 4)
    score = max(28, score)
    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "summary": f"You match {len(matched)} of {len(job_skills)} highlighted skills.",
        "tailoring_notes": [
            "Emphasize quantified impact in recent projects.",
            "Mirror the job title and core platform keywords in your summary.",
            "Add the most relevant tools near the top of the resume.",
        ],
    }


def ai_match_resume(parsed_job: Dict[str, Any], resume_text: str, parsed_profile: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
    payload = {
        "job": parsed_job,
        "resume_text": resume_text[:12000],
        "parsed_profile": parsed_profile,
        "keywords": keywords,
    }
    system_prompt = (
        "You are a career assistant. Return ONLY valid JSON with schema "
        '{"score":number,"matched_skills":[string],"missing_skills":[string],"summary":string,"tailoring_notes":[string]}'
    )
    try:
        parsed = safe_json_loads(nova_converse(system_prompt, json.dumps(payload), 0.2, 1800))
        if parsed and isinstance(parsed.get("score"), (int, float)):
            return parsed
    except Exception:
        pass
    return fallback_match_analysis(parsed_job, resume_text, parsed_profile, keywords)


def ai_generate_tailored_resume(parsed_job: Dict[str, Any], resume_text: str, parsed_profile: Dict[str, Any]) -> str:
    system_prompt = "You rewrite resumes into a tailored plain-text resume. Keep it concise, factual, ATS-friendly, and structured with sections."
    fallback = (
        f"TARGET ROLE\n{parsed_job.get('role', '')} at {parsed_job.get('company', '')}\n\n"
        f"PROFESSIONAL SUMMARY\nTailored toward {parsed_job.get('role', 'the target role')} with emphasis on {', '.join(parsed_job.get('skills', [])[:6]) or 'core matching skills'}.\n\n"
        f"EXPERIENCE HIGHLIGHTS\n- Reorder your strongest accomplishments to match the role requirements.\n"
        f"- Highlight measurable impact, ownership, and tools such as {', '.join(parsed_job.get('skills', [])[:5]) or 'relevant technologies'}.\n\n"
        f"BASE RESUME\n{resume_text[:4000]}"
    )
    try:
        return nova_converse(system_prompt, json.dumps({"job": parsed_job, "resume_text": resume_text[:12000], "parsed_profile": parsed_profile}), 0.35, 2400)
    except Exception:
        return fallback


def ai_generate_cover_letter(parsed_job: Dict[str, Any], resume_text: str, parsed_profile: Dict[str, Any], settings: Dict[str, Any]) -> str:
    system_prompt = "You write concise, modern, personalized cover letters in plain text."
    fallback = (
        f"Dear Hiring Team,\n\n"
        f"I'm excited to apply for the {parsed_job.get('role', 'role')} position at {parsed_job.get('company', 'your company')}. "
        f"My background aligns well with your needs in {', '.join(parsed_job.get('skills', [])[:4]) or 'the listed requirements'}.\n\n"
        f"In my recent work, I have focused on delivering measurable outcomes, collaborating effectively, and learning quickly in fast-moving environments. "
        f"I would welcome the chance to bring that same approach to {parsed_job.get('company', 'your team')}.\n\n"
        f"Thank you for your time and consideration.\n"
    )
    try:
        return nova_converse(system_prompt, json.dumps({"job": parsed_job, "resume_text": resume_text[:12000], "parsed_profile": parsed_profile, "settings": settings}), 0.45, 1800)
    except Exception:
        return fallback


def extract_resume_text_from_upload(upload: UploadFile) -> Dict[str, str]:
    filename = upload.filename or "resume"
    extension = Path(filename).suffix.lower()
    raw = upload.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty")
    if extension in {".txt", ".md", ".rtf"}:
        text_content = raw.decode("utf-8", errors="ignore")
        parser = "text"
    elif extension == ".pdf":
        reader = PdfReader(io.BytesIO(raw))
        text_content = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        parser = "pdf"
    elif extension == ".docx":
        document = DocxDocument(io.BytesIO(raw))
        text_content = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
        parser = "docx"
    else:
        raise HTTPException(status_code=400, detail="Unsupported resume format. Upload a TXT, PDF, or DOCX file.")
    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from the uploaded resume.")
    return {"filename": filename, "text": text_content.strip(), "parser": parser}


def build_text_pdf(title: str, content_text: str) -> io.BytesIO:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    import re

    buffer = io.BytesIO()
    # Set standard professional resume margins (0.5 inch = 36 points)
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Create custom resume styles
    resume_normal = ParagraphStyle('ResumeNormal', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
    resume_heading = ParagraphStyle('ResumeHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, spaceAfter=4, spaceBefore=12, textColor="#000000")
    resume_name = ParagraphStyle('ResumeName', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, alignment=TA_CENTER, spaceAfter=12)

    story = []

    # Helper to convert Markdown **bold** to ReportLab <b>bold</b>
    def format_line(line):
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        if line.startswith('- '):
            line = '&bull; ' + line[2:]
        return line

    lines = content_text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            # Add a small spacer for empty lines
            story.append(Spacer(1, 4))
            continue

        # Detect section headings (e.g., **Experience** on its own line)
        if line.startswith('**') and line.endswith('**') and len(line.split()) < 5:
            clean_heading = line.replace('**', '').upper()
            story.append(Paragraph(clean_heading, resume_heading))
            continue

        # Standard line
        story.append(Paragraph(format_line(line), resume_normal))

    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def fallback_tasks(parsed_job: Dict[str, Any], action: Optional[str] = None) -> List[Dict[str, Any]]:
    base = [
        {"title": f"Review {parsed_job.get('company', 'company')} job requirements", "details": "Validate skills, location, and seniority before applying.", "status": "open", "task_type": "research"},
        {"title": f"Tailor resume for {parsed_job.get('role', 'target role')}", "details": "Move the most relevant impact bullets to the top.", "status": "open", "task_type": "resume"},
    ]
    if action == "mark_applied":
        base.append({"title": f"Send follow-up for {parsed_job.get('company', 'company')}", "details": "Follow up in 5 business days if there is no response.", "status": "open", "task_type": "follow_up", "due_date": (datetime.now(timezone.utc).date() + timedelta(days=5)).isoformat()})
    else:
        base.append({"title": f"Prepare interview stories for {parsed_job.get('role', 'role')}", "details": "Draft STAR examples tied to role requirements.", "status": "open", "task_type": "interview_prep"})
    return base


def ai_suggest_tasks(parsed_job: Dict[str, Any], match_analysis: Dict[str, Any], action: Optional[str] = None) -> List[Dict[str, Any]]:
    system_prompt = (
        "Return ONLY valid JSON as an array of tasks. Each task schema: "
        '{"title":string,"details":string,"status":"open","task_type":"follow_up|resume|cover_letter|interview_prep|briefing|research|other","due_date":string|null}'
    )
    try:
        text = nova_converse(system_prompt, json.dumps({"job": parsed_job, "match": match_analysis, "action": action}), 0.2, 1600)
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return fallback_tasks(parsed_job, action)


def fetch_job_url(url: str) -> Dict[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.extract()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    if len(text) < 120:
        raise HTTPException(status_code=422, detail="Could not extract enough readable job description text from that page")
    return {"html": html[:200000], "text": text[:60000]}


def compact_jobs_for_prompt(jobs: List[Dict[str, Any]], limit: int = 60) -> List[Dict[str, Any]]:
    return [
        {
            "id": job.get("id", ""),
            "company": job.get("company", ""),
            "role": job.get("role", ""),
            "status": normalize_status(job.get("status", "Applied")),
            "date": str(job.get("date", "")),
            "notes": job.get("notes", "")[:240],
            "salary": job.get("salary", ""),
            "location": job.get("location", ""),
            "skills": job.get("skills", []),
            "ai_match_score": job.get("ai_match_score"),
        }
        for job in jobs[:limit]
    ]


def generate_daily_briefing(jobs: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    stale = [job for job in jobs if job["status"] == "Applied" and (datetime.now(timezone.utc).date() - date.fromisoformat(str(job["date"]))).days >= 7]
    return {
        "summary": f"You have {len(stale)} potentially stale applications and {len(jobs)} tracked jobs in motion.",
        "stale_applications": stale[:5],
        "focus_today": [f"Review status for {job['company']} — {job['role']}" for job in stale[:3]],
        "follow_up_suggestions": [f"Check in on {job['company']} for {job['role']}" for job in stale[:3]],
    }


def load_context(db: Session, user_id: int) -> Dict[str, Any]:
    state = StateService(db, user_id)
    jobs = [serialize_job(job) for job in JobService(db, user_id).list()]
    tasks = [TaskResponse.model_validate(task).model_dump(mode="json") for task in TaskService(db, user_id).list()]
    parsed_jobs = [safe_json_value(item.parsed_job, {}) for item in IntakeService(db, user_id).recent(limit=6)]
    documents = [DocumentResponse.model_validate(doc).model_dump(mode="json") for doc in DocumentService(db, user_id).list()][:6]
    recommended_jobs = [RecommendedJobResponse.model_validate(item).model_dump(mode="json") for item in RecommendedJobService(db, user_id).list_active(limit=8)]
    return {
        "stats": compute_job_stats(jobs),
        "jobs": compact_jobs_for_prompt(jobs),
        "parsed_jobs": parsed_jobs,
        "resume_text": state.get("resume_text") or "",
        "parsed_profile": state.get("parsed_profile") or DEFAULT_PARSED_PROFILE,
        "keywords": state.get("keywords") or [],
        "settings": state.get("settings") or DEFAULT_SETTINGS,
        "tasks": tasks,
        "documents": documents,
        "recommended_jobs": recommended_jobs,
        "last_sync": state.get("last_sync"),
        "chat_history": ChatService(db, user_id).tail(limit=10),
        "gmail_sync": gmail_sync_service.get_status(),
        "daily_briefing": generate_daily_briefing(jobs, tasks),
    }


def deterministic_chat_answer(message: str, context: Dict[str, Any]) -> Optional[str]:
    msg = message.lower().strip()
    stats = context["stats"]
    jobs = context["jobs"]
    tasks = context["tasks"]
    briefing = context["daily_briefing"]
    if "daily briefing" in msg:
        return f"{briefing['summary']} Focus today: {', '.join(briefing['focus_today']) or 'No urgent tasks.'}"
    if "stale" in msg and "application" in msg:
        items = briefing["stale_applications"]
        if not items:
            return "You have no stale applied jobs based on the current 7-day rule."
        return "Potentially stale applications:\n" + "\n".join(f"- {job['company']} — {job['role']}" for job in items)
    if "how many jobs" in msg or ("how many" in msg and "applied" in msg):
        return f"You have {stats['total_jobs']} tracked jobs, including {stats['applied_count']} applied and {stats['wishlist_count']} wishlist items."
    if "open tasks" in msg or ("how many" in msg and "tasks" in msg):
        open_tasks = sum(1 for task in tasks if task["status"] != "done")
        return f"You have {open_tasks} open tasks."
    if "list my jobs" in msg or "show my jobs" in msg:
        if not jobs:
            return "You do not have any tracked jobs yet."
        return "Here are your current jobs:\n" + "\n".join(f"- {job['company']} — {job['role']} [{job['status']}]" for job in jobs[:15])
    return None


def ai_chat(message: str, context: Dict[str, Any]) -> str:
    shortcut = deterministic_chat_answer(message, context)
    if shortcut:
        return shortcut
    system_prompt = (
        "You are JobTracker AI, a private single-user career assistant. Answer only from the stored context. "
        "Be practical, concise, and context-aware across jobs, parsed jobs, documents, profile, settings, keywords, chat history, and tasks. "
        "If information is missing, say so clearly."
    )
    try:
        return nova_converse(system_prompt, f"Stored context JSON:\n{json.dumps(context, ensure_ascii=False)}\n\nUser question: {message}", 0.1, 2000)
    except Exception:
        return "Nova is unavailable right now. I can still help with deterministic stats, stale applications, and task summaries from your saved data."


def initialize_database() -> None:
    init_engine()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    with SessionLocal() as db:
        user_service = UserService(db)
        user_service.ensure_bootstrap_admin()
        if AUTH_SEED_DEFAULT_PASSWORD and AUTH_SEED_EMAILS:
            seeded = user_service.seed_users(AUTH_SEED_EMAILS, AUTH_SEED_DEFAULT_PASSWORD)
            if seeded:
                logger.info("Seeded %s additional auth users", len(seeded))


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


def create_access_token(user: UserRecord) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user.email, "user_id": user.id, "exp": expire, "type": "access"}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_token_from_request(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[str]:
    return request.cookies.get(COOKIE_NAME) or (credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else None)


def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    token = get_token_from_request(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(token)
    email = (payload.get("sub") or "").strip().lower()
    user_id = payload.get("user_id")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = None
    if user_id is not None:
        user = db.get(UserRecord, user_id)
        if user and user.email.lower() != email:
            user = None
    if user is None:
        user = UserService(db).get_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized user")
    payload["user_id"] = user.id
    payload["sub"] = user.email
    payload["full_name"] = user.full_name
    return payload


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
    return {"ok": True, "app": APP_TITLE, "database": "connected", "region": AWS_REGION, "model": NOVA_MODEL_ID}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return PlainTextResponse("User-agent: *\nDisallow:\n")


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = UserService(db).authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user)
    response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, secure=IS_PRODUCTION, samesite="lax", max_age=JWT_EXPIRE_HOURS * 3600, path="/")
    return {"ok": True, "email": user.email, "full_name": user.full_name}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(user: Dict[str, Any] = Depends(require_auth)):
    return {"authenticated": True, "email": user["sub"], "full_name": user.get("full_name", "") or ""}


@app.get("/api/dashboard/simple")
def simple_dashboard(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        jobs = [serialize_job(job) for job in JobService(db, user_id).list()]
        tasks = [TaskResponse.model_validate(task).model_dump(mode="json") for task in TaskService(db, user_id).list()]
        stats = compute_job_stats(jobs)
        columns = {status: [] for status in ["Wishlist", "Applied", "Interview", "Offered", "Accepted", "Later"]}
        for job in jobs:
            if job["status"] in columns:
                columns[job["status"]].append(job)
        return {
            "stats": stats,
            "columns": columns,
            "recent_jobs": jobs[:8],
            "recommended_today": [RecommendedJobResponse.model_validate(item).model_dump(mode="json") for item in RecommendedJobService(db, user_id).list_active(limit=6)],
            "recent_intakes": [safe_json_value(item.parsed_job, {}) for item in IntakeService(db, user_id).recent(limit=4)],
            "profile_summary": StateService(db, user_id).get("parsed_profile") or DEFAULT_PARSED_PROFILE,
            "keywords": StateService(db, user_id).get("keywords") or [],
            "daily_briefing": generate_daily_briefing(jobs, tasks),
            "gmail_sync": gmail_sync_service.get_status(),
        }
    except Exception as exc:
        handle_database_exception("/api/dashboard/simple", exc)


@app.get("/api/jobs")
def get_jobs(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        return [serialize_job(job) for job in JobService(db, user["user_id"]).list()]
    except Exception as exc:
        handle_database_exception("/api/jobs", exc)


@app.post("/api/jobs/discover")
def discover_jobs(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return JobScoutService(db, user["user_id"]).discover(trigger_mode="manual")


@app.get("/api/jobs/recommended")
def get_recommended_jobs(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return [RecommendedJobResponse.model_validate(job).model_dump(mode="json") for job in RecommendedJobService(db, user["user_id"]).list_active(limit=18)]


@app.post("/api/jobs")
def add_job(payload: JobCreate, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    if not payload.company.strip() or not payload.role.strip():
        raise HTTPException(status_code=400, detail="Company and role are required")
    return JobResponse.model_validate(JobService(db, user["user_id"]).create(payload)).model_dump(mode="json")


@app.put("/api/jobs/{job_id}")
def update_job(job_id: str, payload: JobUpdate, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return JobResponse.model_validate(JobService(db, user["user_id"]).update(job_id, payload)).model_dump(mode="json")


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    JobService(db, user["user_id"]).delete(job_id)
    return {"ok": True}


@app.post("/api/jobs/parse-link")
def parse_job_link(payload: ParseJobLinkRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    fetched = fetch_job_url(str(payload.url))
    parsed_job = ai_parse_job_description(fetched["text"], str(payload.url))
    state = StateService(db, user_id)
    match_analysis = ai_match_resume(
        parsed_job,
        state.get("resume_text") or "",
        state.get("parsed_profile") or DEFAULT_PARSED_PROFILE,
        state.get("keywords") or [],
    )
    suggested_actions = [
        {"id": "mark_applied", "label": "I applied", "description": "Create a tracked application and follow-up task."},
        {"id": "save_wishlist", "label": "Save to wishlist", "description": "Save this opportunity for active review."},
        {"id": "match_resume", "label": "Match my resume", "description": "Review fit, strengths, and gaps."},
        {"id": "generate_resume", "label": "Generate resume", "description": "Draft a tailored resume version."},
        {"id": "generate_cover_letter", "label": "Generate cover letter", "description": "Draft a targeted cover letter."},
        {"id": "save_later", "label": "Save for later", "description": "Store the job with minimal follow-up pressure."},
    ]
    tasks = ai_suggest_tasks(parsed_job, match_analysis)
    intake = IntakeService(db, user_id).create(str(payload.url), fetched["html"], fetched["text"], parsed_job, suggested_actions)
    return {
        "intake_id": intake.id,
        "parsed_job": parsed_job,
        "match_analysis": match_analysis,
        "suggested_actions": suggested_actions,
        "suggested_tasks": tasks,
    }


@app.post("/api/jobs/action")
def apply_job_action(payload: JobActionRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    intake_service = IntakeService(db, user_id)
    intake = db.scalar(select(JobIntakeRecord).where(JobIntakeRecord.id == payload.intake_id, JobIntakeRecord.user_id == user_id))
    if intake is None:
        raise HTTPException(status_code=404, detail="Job intake not found")
    parsed_job = intake.parsed_job or {}
    state = StateService(db, user_id)
    match_analysis = ai_match_resume(parsed_job, state.get("resume_text") or "", state.get("parsed_profile") or DEFAULT_PARSED_PROFILE, state.get("keywords") or [])
    response: Dict[str, Any] = {"action": payload.action, "job": None, "document": None}
    linked_job: Optional[JobRecord] = None

    if payload.action in ACTION_TO_STATUS:
        linked_job = JobService(db, user_id).create(JobCreate(
            company=payload.company or parsed_job.get("company", "Unknown company"),
            role=payload.role or parsed_job.get("role", "Unknown role"),
            status=ACTION_TO_STATUS[payload.action],
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            field=parsed_job.get("field", ""),
            notes=parsed_job.get("summary", ""),
            link=intake.url,
            salary=parsed_job.get("salary", ""),
            location=parsed_job.get("location", ""),
            job_summary=parsed_job.get("summary", ""),
            skills=parsed_job.get("skills", []),
            source="parsed_link",
            intake_id=intake.id,
            ai_match_score=int(match_analysis.get("score", 0)) if match_analysis.get("score") is not None else None,
            ai_match_summary=match_analysis.get("summary", ""),
            metadata_json={"match_analysis": match_analysis},
        ))
        response["job"] = JobResponse.model_validate(linked_job).model_dump(mode="json")

    if payload.action == "match_resume":
        response["match_analysis"] = match_analysis
    elif payload.action == "generate_resume":
        content = ai_generate_tailored_resume(parsed_job, state.get("resume_text") or "", state.get("parsed_profile") or DEFAULT_PARSED_PROFILE)
        document = DocumentService(db, user_id).upsert_text_document(
            name=f"Tailored Resume - {parsed_job.get('company', 'Target')}",
            doc_type="tailored_resume",
            content_text=content,
            linked_job_id=linked_job.id if linked_job else None,
            metadata_json={"intake_id": intake.id, "source_url": intake.url},
        )
        response["document"] = DocumentResponse.model_validate(document).model_dump(mode="json")
        response["match_analysis"] = match_analysis
    elif payload.action == "generate_cover_letter":
        content = ai_generate_cover_letter(parsed_job, state.get("resume_text") or "", state.get("parsed_profile") or DEFAULT_PARSED_PROFILE, state.get("settings") or DEFAULT_SETTINGS)
        document = DocumentService(db, user_id).upsert_text_document(
            name=f"Cover Letter - {parsed_job.get('company', 'Target')}",
            doc_type="generated_cover_letter",
            content_text=content,
            linked_job_id=linked_job.id if linked_job else None,
            metadata_json={"intake_id": intake.id, "source_url": intake.url},
        )
        response["document"] = DocumentResponse.model_validate(document).model_dump(mode="json")
    intake_service.set_action(payload.intake_id, payload.action)
    response["tasks"] = []
    return response


@app.post("/api/jobs/recommended/{recommended_job_id}/action")
def recommended_job_action(recommended_job_id: str, payload: Dict[str, str], user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    recommended = db.scalar(select(RecommendedJobRecord).where(RecommendedJobRecord.id == recommended_job_id, RecommendedJobRecord.user_id == user_id))
    if recommended is None:
        raise HTTPException(status_code=404, detail="Recommended job not found")
    action = (payload.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="Action is required")

    parsed_job = {
        "company": recommended.company,
        "role": recommended.role,
        "location": recommended.location,
        "salary": recommended.salary,
        "summary": recommended.summary,
        "skills": recommended.skills,
        "field": recommended.domain,
        "source_url": recommended.link,
    }
    state = StateService(db, user_id)
    match_analysis = {
        "score": recommended.score,
        "summary": "High-match recommendation from Morning Job Scout.",
        "matched_skills": recommended.match_reasons,
        "missing_skills": recommended.missing_points,
    }

    if action == "dismiss":
        job = RecommendedJobService(db, user_id).dismiss(recommended_job_id)
        return {"ok": True, "recommended_job": RecommendedJobResponse.model_validate(job).model_dump(mode="json")}

    linked_job = None
    document = None
    
    # Clean up role and company strings to remove spaces for the filename
    role_clean = recommended.role.replace(' ', '')
    company_clean = recommended.company.replace(' ', '')
    
    if action in {"apply", "save_to_wishlist"}:
        linked_job = JobService(db, user_id).create(JobCreate(
            company=recommended.company,
            role=recommended.role,
            status="Applied" if action == "apply" else "Wishlist",
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            field=recommended.domain,
            notes=recommended.summary,
            link=recommended.link,
            salary=recommended.salary,
            location=recommended.location,
            job_summary=recommended.summary,
            skills=recommended.skills,
            source="morning_job_scout",
            ai_match_score=recommended.score,
            ai_match_summary="; ".join(recommended.match_reasons[:2]),
            metadata_json={"recommended_job_id": recommended.id, "score_breakdown": recommended.score_breakdown},
        ))
    elif action == "generate_resume":
        content = ai_generate_tailored_resume(parsed_job, state.get("resume_text") or "", state.get("parsed_profile") or DEFAULT_PARSED_PROFILE)
        document = DocumentService(db, user_id).upsert_text_document(
            name=f"Rugved({role_clean}_{company_clean})",
            doc_type="tailored_resume",
            content_text=content,
            metadata_json={"recommended_job_id": recommended.id, "source_url": recommended.link},
        )
    elif action == "generate_cover_letter":
        content = ai_generate_cover_letter(parsed_job, state.get("resume_text") or "", state.get("parsed_profile") or DEFAULT_PARSED_PROFILE, state.get("settings") or DEFAULT_SETTINGS)
        document = DocumentService(db, user_id).upsert_text_document(
            name=f"Rugved_CL({role_clean}_{company_clean})",
            doc_type="generated_cover_letter",
            content_text=content,
            metadata_json={"recommended_job_id": recommended.id, "source_url": recommended.link},
        )
    elif action == "match_resume":
        pass
    else:
        raise HTTPException(status_code=400, detail="Unsupported recommended job action")

    return {
        "ok": True,
        "action": action,
        "job": JobResponse.model_validate(linked_job).model_dump(mode="json") if linked_job else None,
        "document": DocumentResponse.model_validate(document).model_dump(mode="json") if document else None,
        "match_analysis": match_analysis,
        "tasks": [],
    }

@app.get("/api/tasks")
def list_tasks(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return [TaskResponse.model_validate(task).model_dump(mode="json") for task in TaskService(db, user["user_id"]).list()]


@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdateRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return TaskResponse.model_validate(TaskService(db, user["user_id"]).update_status(task_id, payload.status)).model_dump(mode="json")


@app.get("/api/documents")
def list_documents(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return [DocumentResponse.model_validate(doc).model_dump(mode="json") for doc in DocumentService(db, user["user_id"]).list()]


@app.put("/api/documents/{document_id}")
def update_document(document_id: str, payload: DocumentUpdateRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    document = DocumentService(db, user["user_id"]).update(document_id, payload.content_text, payload.name)
    return DocumentResponse.model_validate(document).model_dump(mode="json")


@app.post("/api/documents/export-pdf")
def export_document_pdf(payload: DocumentPdfRequest, _: Dict[str, Any] = Depends(require_auth)):
    pdf_buffer = build_text_pdf(payload.title.strip() or "Document", payload.content_text)
    file_name = (payload.file_name or payload.title or "document").strip() or "document"
    safe_file_name = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name).strip("_") or "document"
    if not safe_file_name.lower().endswith(".pdf"):
        safe_file_name = f"{safe_file_name}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{safe_file_name}"'}
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)


@app.post("/api/resume/analyze")
def analyze_resume(req: ResumeAnalyzeRequest, _: Dict[str, Any] = Depends(require_auth)):
    parsed = ai_parse_resume(req.resume_text)
    return {"resume_text": req.resume_text, "parsed_profile": parsed}


@app.post("/api/resume/upload")
def upload_resume(file: UploadFile = File(...), _: Dict[str, Any] = Depends(require_auth)):
    extracted = extract_resume_text_from_upload(file)
    parsed = ai_parse_resume(extracted["text"])
    return {
        "filename": extracted["filename"],
        "parser": extracted["parser"],
        "resume_text": extracted["text"],
        "parsed_profile": parsed,
    }


@app.post("/api/resume/save")
def save_resume(req: ResumeSaveRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    state = StateService(db, user_id)
    state.set("resume_text", req.resume_text)
    parsed_profile = req.parsed_profile or ai_parse_resume(req.resume_text)
    state.set("parsed_profile", parsed_profile)
    DocumentService(db, user_id).upsert_text_document("Primary Resume", "resume", req.resume_text, metadata_json={"active": True})
    db.commit()
    return {"ok": True, "parsed_profile": parsed_profile}


@app.get("/api/profile")
def get_profile(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        state = StateService(db, user_id)
        documents = [DocumentResponse.model_validate(doc).model_dump(mode="json") for doc in DocumentService(db, user_id).list()]
        current_resume_document = next((doc for doc in documents if doc["doc_type"] == "resume"), None)
        return {
            "resume_text": state.get("resume_text") or "",
            "parsed_profile": state.get("parsed_profile") or DEFAULT_PARSED_PROFILE,
            "chat_history": ChatService(db, user_id).tail(limit=12),
            "documents": documents,
            "current_resume_document": current_resume_document,
        }
    except Exception as exc:
        handle_database_exception("/api/profile", exc)


@app.get("/api/keywords")
def get_keywords(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return {"keywords": StateService(db, user["user_id"]).get("keywords") or []}


@app.post("/api/keywords")
def save_keywords(req: KeywordsRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    cleaned = [item.strip() for item in req.keywords if item.strip()]
    StateService(db, user["user_id"]).set("keywords", cleaned)
    db.commit()
    return {"keywords": cleaned}


@app.get("/api/settings")
def get_settings(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return {"settings": StateService(db, user["user_id"]).get("settings") or DEFAULT_SETTINGS, "gmail_sync": gmail_sync_service.get_status()}


@app.post("/api/settings")
def save_settings(req: SettingsRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    payload = {
        "sync_window_hours": max(1, min(req.sync_window_hours, 168)),
        "preferred_location": req.preferred_location.strip(),
        "preferred_locations": [item.strip() for item in req.preferred_locations if item.strip()],
        "target_roles": [item.strip() for item in req.target_roles if item.strip()],
        "sponsorship_required": bool(req.sponsorship_required),
        "minimum_job_match_score": max(50, min(req.minimum_job_match_score, 95)),
        "user_notes": req.user_notes.strip(),
        "tone": req.tone.strip() or "concise",
    }
    state = StateService(db, user["user_id"])
    state.set("settings", payload)
    state.set("last_sync", {"status": "manual", "updated_at": utc_now()})
    db.commit()
    return {"settings": payload, "gmail_sync": gmail_sync_service.get_status()}


@app.post("/api/email/parse")
def parse_email(req: EmailParseRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    result = ai_parse_email(req.email_text)
    linked_job = None
    if req.job_id:
        job = db.scalar(select(JobRecord).where(JobRecord.id == req.job_id, JobRecord.user_id == user["user_id"]))
        if job:
            job.status = result["status"]
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            linked_job = JobResponse.model_validate(job).model_dump(mode="json")
    return {"parsed": result, "job": linked_job}


@app.get("/api/assistant/context")
def assistant_context(user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    return load_context(db, user["user_id"])


@app.post("/api/chat")
def chat(req: ChatRequest, user: Dict[str, Any] = Depends(require_auth), db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    user_id = user["user_id"]
    context = load_context(db, user_id)
    answer = ai_chat(req.message.strip(), context)
    chat_service = ChatService(db, user_id)
    chat_service.append("user", req.message.strip(), context_type="chat")
    chat_service.append("assistant", answer, context_type="chat")
    return {"answer": answer, "history": chat_service.tail(limit=12)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
