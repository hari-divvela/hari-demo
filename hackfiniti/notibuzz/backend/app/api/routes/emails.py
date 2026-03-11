from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from app.models.email import Email, EmailAnalytics, PriorityLevel, EmailCategory
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.services.email_processor import email_processor
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[Email])
async def get_emails(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    priority: Optional[PriorityLevel] = None,
    category: Optional[EmailCategory] = None,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
) -> List[Email]:
    """Get user's emails with optional filters"""
    try:
        db = get_db()
        emails_ref = db.collection('emails').where('user_id', '==', current_user.id)
        
        # Apply filters
        if priority:
            emails_ref = emails_ref.where('priority', '==', priority.value)
        
        if category:
            emails_ref = emails_ref.where('category', '==', category.value)
        
        if unread_only:
            emails_ref = emails_ref.where('read', '==', False)
        
        # Order by timestamp (most recent first)
        emails_ref = emails_ref.order_by('timestamp', direction='DESCENDING')
        
        # Apply pagination
        emails = emails_ref.limit(limit).offset(offset).stream()
        
        email_list = []
        for email_doc in emails:
            email_data = email_doc.to_dict()
            email_list.append(Email(**email_data))
        
        return email_list
        
    except Exception as e:
        logger.error(f"Failed to get emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve emails"
        )


@router.get("/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    current_user: User = Depends(get_current_user)
) -> Email:
    """Get specific email by ID"""
    try:
        db = get_db()
        email_doc = db.collection('emails').document(email_id).get()
        
        if not email_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email_data = email_doc.to_dict()
        
        # Verify email belongs to current user
        if email_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return Email(**email_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email {email_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email"
        )


@router.put("/{email_id}/read")
async def mark_email_read(
    email_id: str,
    read: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Mark email as read/unread"""
    try:
        db = get_db()
        email_doc = db.collection('emails').document(email_id).get()
        
        if not email_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email_data = email_doc.to_dict()
        
        # Verify email belongs to current user
        if email_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update read status
        db.collection('emails').document(email_id).update({
            'read': read,
            'last_updated': datetime.utcnow().isoformat()
        })
        
        return {"message": f"Email marked as {'read' if read else 'unread'}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email read status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email"
        )


@router.put("/{email_id}/star")
async def star_email(
    email_id: str,
    starred: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Star/unstar email"""
    try:
        db = get_db()
        email_doc = db.collection('emails').document(email_id).get()
        
        if not email_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email_data = email_doc.to_dict()
        
        # Verify email belongs to current user
        if email_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update starred status
        db.collection('emails').document(email_id).update({
            'starred': starred,
            'last_updated': datetime.utcnow().isoformat()
        })
        
        return {"message": f"Email {'starred' if starred else 'unstarred'}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email star status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email"
        )


@router.delete("/{email_id}")
async def delete_email(
    email_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete email"""
    try:
        db = get_db()
        email_doc = db.collection('emails').document(email_id).get()
        
        if not email_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email_data = email_doc.to_dict()
        
        # Verify email belongs to current user
        if email_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete from Firestore
        db.collection('emails').document(email_id).delete()
        
        # Delete from Pinecone (async)
        from app.services.pinecone_service import delete_email_embedding
        await delete_email_embedding(email_id)
        
        return {"message": "Email deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete email"
        )


@router.post("/{email_id}/reprocess")
async def reprocess_email(
    email_id: str,
    current_user: User = Depends(get_current_user)
) -> Email:
    """Reprocess email with updated AI models"""
    try:
        # Verify email belongs to current user
        db = get_db()
        email_doc = db.collection('emails').document(email_id).get()
        
        if not email_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email_data = email_doc.to_dict()
        
        if email_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Reprocess email
        processed_email = await email_processor.reprocess_email(email_id)
        
        return processed_email
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess email"
        )


@router.get("/analytics/summary", response_model=EmailAnalytics)
async def get_email_analytics(
    current_user: User = Depends(get_current_user)
) -> EmailAnalytics:
    """Get email analytics for current user"""
    try:
        analytics_data = await email_processor.get_email_analytics(current_user.id)
        return EmailAnalytics(**analytics_data)
        
    except Exception as e:
        logger.error(f"Failed to get email analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )
