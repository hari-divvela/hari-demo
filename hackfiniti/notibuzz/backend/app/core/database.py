import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global variables
db = None
firebase_app = None


async def init_db():
    """Initialize Firebase Firestore connection"""
    global db, firebase_app
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "client_id": settings.FIREBASE_CLIENT_ID,
                "auth_uri": settings.FIREBASE_AUTH_URI,
                "token_uri": settings.FIREBASE_TOKEN_URI,
            })
            
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase app initialized successfully")
        
        db = firestore.client()
        logger.info("Firestore database connection established")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise


def get_db():
    """Get Firestore database instance"""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db


def get_firebase_app():
    """Get Firebase app instance"""
    if firebase_app is None:
        raise RuntimeError("Firebase app not initialized. Call init_db() first.")
    return firebase_app
