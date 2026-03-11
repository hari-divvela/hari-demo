from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PriorityLevel(str, Enum):
    URGENT = "urgent"
    IMPORTANT = "important"
    NORMAL = "normal"
    LOW = "low"


class EmailCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    SOCIAL = "social"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class EmailAttachment(BaseModel):
    filename: str
    size: int
    content_type: str
    attachment_id: Optional[str] = None


class Email(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    recipients: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    body_text: str
    body_html: Optional[str] = None
    timestamp: datetime
    read: bool = False
    starred: bool = False
    important: bool = False
    attachments: List[EmailAttachment] = []
    labels: List[str] = []
    
    # AI-generated fields
    summary: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.NORMAL
    category: EmailCategory = EmailCategory.OTHER
    sentiment_score: Optional[float] = None
    embedding: Optional[List[float]] = None
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class EmailSearch(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: Optional[Dict[str, Any]] = None


class EmailSearchResult(BaseModel):
    emails: List[Email]
    total_count: int
    query: str
    processing_time: float


class EmailAnalytics(BaseModel):
    total_emails: int
    unread_count: int
    urgent_count: int
    important_count: int
    category_breakdown: Dict[str, int]
    daily_volume: List[Dict[str, Any]]
    top_senders: List[Dict[str, Any]]
