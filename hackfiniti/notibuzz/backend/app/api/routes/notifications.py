from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from app.models.user import User
from app.models.email import Email, PriorityLevel
from app.api.routes.auth import get_current_user
from app.core.database import get_db
import logging
import json
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)
    
    async def broadcast_notification(self, notification: Dict[str, Any], user_id: str):
        await self.send_personal_message(json.dumps(notification), user_id)

manager = ConnectionManager()


@router.get("/")
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get user's notifications"""
    try:
        db = get_db()
        notifications_ref = db.collection('notifications').where('user_id', '==', current_user.id)
        
        if unread_only:
            notifications_ref = notifications_ref.where('read', '==', False)
        
        notifications = notifications_ref.order_by('created_at', direction='DESCENDING').limit(limit).stream()
        
        notification_list = []
        for notif_doc in notifications:
            notif_data = notif_doc.to_dict()
            notif_data['id'] = notif_doc.id
            notification_list.append(notif_data)
        
        return notification_list
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Mark notification as read"""
    try:
        db = get_db()
        notif_doc = db.collection('notifications').document(notification_id).get()
        
        if not notif_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notif_data = notif_doc.to_dict()
        
        # Verify notification belongs to current user
        if notif_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update read status
        db.collection('notifications').document(notification_id).update({
            'read': True,
            'read_at': datetime.utcnow().isoformat()
        })
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete notification"""
    try:
        db = get_db()
        notif_doc = db.collection('notifications').document(notification_id).get()
        
        if not notif_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notif_data = notif_doc.to_dict()
        
        # Verify notification belongs to current user
        if notif_data.get('user_id') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete notification
        db.collection('notifications').document(notification_id).delete()
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Mark all notifications as read"""
    try:
        db = get_db()
        notifications_ref = db.collection('notifications').where('user_id', '==', current_user.id).where('read', '==', False)
        
        unread_notifications = notifications_ref.stream()
        
        batch = db.batch()
        for notif_doc in unread_notifications:
            batch.update(notif_doc.reference, {
                'read': True,
                'read_at': datetime.utcnow().isoformat()
            })
        
        batch.commit()
        
        return {"message": "All notifications marked as read"}
        
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications"
        )


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """Get user's notification preferences"""
    return current_user.notification_preferences


@router.put("/preferences")
async def update_notification_preferences(
    preferences: Dict[str, bool],
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update user's notification preferences"""
    try:
        db = get_db()
        
        # Validate preference keys
        valid_keys = set(current_user.notification_preferences.keys())
        provided_keys = set(preferences.keys())
        
        if not provided_keys.issubset(valid_keys):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid preference keys. Valid keys: {valid_keys}"
            )
        
        # Update preferences
        db.collection('users').document(current_user.id).update({
            'notification_preferences': preferences
        })
        
        return {"message": "Notification preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# Helper functions for creating notifications
async def create_notification(user_id: str, notification_type: str, title: str, message: str, email_id: str = None):
    """Create a new notification"""
    try:
        db = get_db()
        
        notification = {
            'user_id': user_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'email_id': email_id,
            'read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save to Firestore
        doc_ref = db.collection('notifications').document()
        doc_ref.set(notification)
        notification['id'] = doc_ref.id
        
        # Send real-time notification via WebSocket
        await manager.broadcast_notification(notification, user_id)
        
        logger.info(f"Created notification for user {user_id}: {title}")
        
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")


async def check_urgent_emails(user_id: str):
    """Check for urgent emails and create notifications"""
    try:
        db = get_db()
        
        # Get recent unread emails
        emails_ref = db.collection('emails').where('user_id', '==', user_id).where('read', '==', False)
        recent_emails = emails_ref.where('timestamp', '>', datetime.utcnow() - timedelta(hours=1)).stream()
        
        for email_doc in recent_emails:
            email_data = email_doc.to_dict()
            
            # Check if email is urgent
            if email_data.get('priority') == PriorityLevel.URGENT:
                await create_notification(
                    user_id=user_id,
                    notification_type='urgent_email',
                    title='Urgent Email Received',
                    message=f"Urgent email from {email_data.get('sender', 'Unknown')}: {email_data.get('subject', 'No Subject')}",
                    email_id=email_doc.id
                )
            
            # Check for meeting invites
            if 'meeting' in email_data.get('subject', '').lower() or 'invite' in email_data.get('subject', '').lower():
                await create_notification(
                    user_id=user_id,
                    notification_type='meeting_invite',
                    title='Meeting Invitation',
                    message=f"Meeting invite from {email_data.get('sender', 'Unknown')}: {email_data.get('subject', 'No Subject')}",
                    email_id=email_doc.id
                )
            
            # Check for financial emails
            if email_data.get('category') == 'financial':
                await create_notification(
                    user_id=user_id,
                    notification_type='financial_email',
                    title='Financial Email',
                    message=f"Financial email from {email_data.get('sender', 'Unknown')}: {email_data.get('subject', 'No Subject')}",
                    email_id=email_doc.id
                )
        
    except Exception as e:
        logger.error(f"Failed to check urgent emails: {str(e)}")
