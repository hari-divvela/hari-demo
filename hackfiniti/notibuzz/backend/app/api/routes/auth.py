from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from typing import Dict, Any
import firebase_admin
from firebase_admin import auth
from app.core.config import settings
from app.models.user import User, UserCreate
from app.services.gmail_service import gmail_service
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/firebase-login")
async def firebase_login(token: str) -> Dict[str, Any]:
    """Login with Firebase token"""
    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in token"
            )
        
        # Get or create user in Firestore
        db = get_db()
        user_doc = db.collection('users').document(uid).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user = User(**user_data)
        else:
            # Create new user
            user = User(
                id=uid,
                email=email,
                display_name=decoded_token.get('name'),
                photo_url=decoded_token.get('picture'),
                email_verified=decoded_token.get('email_verified', False)
            )
            
            # Save to Firestore
            db.collection('users').document(uid).set(user.model_dump())
        
        return {
            "user": user.model_dump(),
            "token": token
        }
        
    except firebase_admin.exceptions.FirebaseError as e:
        logger.error(f"Firebase authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/gmail/auth-url")
async def get_gmail_auth_url() -> Dict[str, str]:
    """Get Gmail OAuth authorization URL"""
    try:
        flow = gmail_service.get_auth_flow()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error(f"Failed to generate Gmail auth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/gmail/callback")
async def gmail_oauth_callback(code: str, state: str = None) -> RedirectResponse:
    """Handle Gmail OAuth callback"""
    try:
        flow = gmail_service.get_auth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        user_info = await gmail_service.get_user_info(credentials)
        
        # Get user ID from Firebase token (this would need to be passed in state)
        # For now, we'll use email as identifier
        
        # Update user with Gmail tokens
        db = get_db()
        users_ref = db.collection('users').where('email', '==', user_info['email'])
        users = users_ref.stream()
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            user_data.update({
                'gmail_connected': True,
                'gmail_access_token': credentials.token,
                'gmail_refresh_token': credentials.refresh_token,
                'gmail_token_expires_at': credentials.expiry.isoformat() if credentials.expiry else None
            })
            
            db.collection('users').document(user_doc.id).set(user_data)
            break
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/success?gmail_connected=true"
        )
        
    except Exception as e:
        logger.error(f"Gmail OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?message={str(e)}"
        )


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """Logout user"""
    return {"message": "Logged out successfully"}


async def get_current_user(token: str = Depends(security)) -> User:
    """Get current authenticated user"""
    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(token.credentials)
        uid = decoded_token['uid']
        
        # Get user from Firestore
        db = get_db()
        user_doc = db.collection('users').document(uid).get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_doc.to_dict()
        return User(**user_data)
        
    except firebase_admin.exceptions.FirebaseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )
