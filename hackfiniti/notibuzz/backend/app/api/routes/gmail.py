from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from app.models.email import Email
from app.models.user import User
from app.services.gmail_service import gmail_service
from app.services.email_processor import email_processor
from app.api.routes.auth import get_current_user
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sync", response_model=List[Email])
async def sync_gmail_emails(
    max_results: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[Email]:
    """Sync emails from Gmail"""
    try:
        if not current_user.gmail_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected. Please connect your Gmail account first."
            )
        
        # Get Gmail credentials
        credentials = gmail_service.get_credentials(
            current_user.gmail_access_token,
            current_user.gmail_refresh_token
        )
        
        # Fetch emails from Gmail
        emails = await gmail_service.fetch_emails(credentials, max_results)
        
        # Process emails with AI
        processed_emails = await email_processor.process_emails_batch(emails)
        
        # Save to Firestore
        db = get_db()
        for email in processed_emails:
            email_dict = email.model_dump(exclude={'embedding'})
            email_dict['user_id'] = current_user.id
            db.collection('emails').document(email.id).set(email_dict)
        
        # Update user's last sync time
        db.collection('users').document(current_user.id).update({
            'last_sync': processed_emails[0].timestamp.isoformat() if processed_emails else None
        })
        
        logger.info(f"Synced {len(processed_emails)} emails for user {current_user.id}")
        return processed_emails
        
    except Exception as e:
        logger.error(f"Gmail sync error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync emails: {str(e)}"
        )


@router.get("/status")
async def get_gmail_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get Gmail connection status"""
    return {
        "gmail_connected": current_user.gmail_connected,
        "last_sync": current_user.last_sync,
        "sync_frequency_minutes": current_user.sync_frequency_minutes
    }


@router.post("/disconnect")
async def disconnect_gmail(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Disconnect Gmail account"""
    try:
        db = get_db()
        db.collection('users').document(current_user.id).update({
            'gmail_connected': False,
            'gmail_access_token': None,
            'gmail_refresh_token': None,
            'gmail_token_expires_at': None
        })
        
        return {"message": "Gmail disconnected successfully"}
        
    except Exception as e:
        logger.error(f"Failed to disconnect Gmail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Gmail"
        )


@router.post("/refresh-token")
async def refresh_gmail_token(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Refresh Gmail access token"""
    try:
        if not current_user.gmail_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token available"
            )
        
        new_token = await gmail_service.refresh_access_token(current_user.gmail_refresh_token)
        
        if new_token:
            db = get_db()
            db.collection('users').document(current_user.id).update({
                'gmail_access_token': new_token
            })
            
            return {"message": "Token refreshed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh token"
            )
        
    except Exception as e:
        logger.error(f"Failed to refresh Gmail token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )
