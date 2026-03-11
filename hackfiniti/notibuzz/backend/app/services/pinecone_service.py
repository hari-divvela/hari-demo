import pinecone
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
import logging
from app.models.email import Email

logger = logging.getLogger(__name__)

# Global variables
pinecone_client = None
index = None


async def init_pinecone():
    """Initialize Pinecone connection"""
    global pinecone_client, index
    
    try:
        pinecone_client = pinecone.Pinecone(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        # Check if index exists, create if not
        if settings.PINECONE_INDEX_NAME not in pinecone_client.list_indexes().names():
            pinecone_client.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine"
            )
            logger.info(f"Created new Pinecone index: {settings.PINECONE_INDEX_NAME}")
        
        index = pinecone_client.Index(settings.PINECONE_INDEX_NAME)
        logger.info("Pinecone connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {str(e)}")
        raise


async def upsert_email_embedding(email: Email, embedding: List[float]):
    """Store email embedding in Pinecone"""
    try:
        if index is None:
            await init_pinecone()
        
        metadata = {
            "email_id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "sender_email": email.sender_email,
            "timestamp": email.timestamp.isoformat(),
            "priority": email.priority,
            "category": email.category,
            "summary": email.summary or "",
            "body_text": email.body_text[:1000],  # Truncate for metadata
        }
        
        index.upsert(
            vectors=[{
                "id": email.id,
                "values": embedding,
                "metadata": metadata
            }]
        )
        
        logger.info(f"Successfully upserted embedding for email {email.id}")
        
    except Exception as e:
        logger.error(f"Failed to upsert email embedding: {str(e)}")
        raise


async def search_similar_emails(query_embedding: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search for similar emails using vector similarity"""
    try:
        if index is None:
            await init_pinecone()
        
        search_params = {
            "vector": query_embedding,
            "top_k": top_k,
            "include_metadata": True
        }
        
        if filters:
            search_params["filter"] = filters
        
        response = index.query(**search_params)
        
        results = []
        for match in response.matches:
            results.append({
                "email_id": match.id,
                "score": match.score,
                "metadata": match.metadata
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to search similar emails: {str(e)}")
        raise


async def delete_email_embedding(email_id: str):
    """Delete email embedding from Pinecone"""
    try:
        if index is None:
            await init_pinecone()
        
        index.delete(ids=[email_id])
        logger.info(f"Successfully deleted embedding for email {email_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete email embedding: {str(e)}")
        raise


async def get_index_stats() -> Dict[str, Any]:
    """Get Pinecone index statistics"""
    try:
        if index is None:
            await init_pinecone()
        
        stats = index.describe_index_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {str(e)}")
        raise
