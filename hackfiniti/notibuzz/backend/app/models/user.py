from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class User(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    email_verified: bool = False
    
    # Gmail integration
    gmail_connected: bool = False
    gmail_access_token: Optional[str] = None
    gmail_refresh_token: Optional[str] = None
    gmail_token_expires_at: Optional[datetime] = None
    
    # Preferences
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "urgent_emails": True,
        "meeting_invites": True,
        "deadlines": True,
        "financial_emails": True,
        "daily_digest": True
    })
    
    # Settings
    sync_frequency_minutes: int = 15
    auto_categorize: bool = True
    auto_summarize: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    last_sync: Optional[datetime] = None


class UserCreate(BaseModel):
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None
    sync_frequency_minutes: Optional[int] = None
    auto_categorize: Optional[bool] = None
    auto_summarize: Optional[bool] = None


class UserPreferences(BaseModel):
    notification_preferences: Dict[str, bool]
    sync_frequency_minutes: int
    auto_categorize: bool
    auto_summarize: bool
