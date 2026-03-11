from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from app.models.email import EmailSearch, EmailSearchResult
from app.models.user import User
from app.services.openai_service import generate_embedding
from app.services.pinecone_service import search_similar_emails
from app.api.routes.auth import get_current_user
from app.core.database import get_db
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/semantic", response_model=EmailSearchResult)
async def semantic_search(
    search_query: EmailSearch,
    current_user: User = Depends(get_current_user)
) -> EmailSearchResult:
    """Perform semantic search on emails"""
    try:
        start_time = time.time()
        
        # Generate embedding for search query
        query_embedding = await generate_embedding(search_query.query)
        
        # Add user filter to search
        filters = search_query.filters or {}
        filters['user_id'] = current_user.id
        
        # Search in Pinecone
        search_results = await search_similar_emails(
            query_embedding=query_embedding,
            top_k=search_query.limit,
            filters=filters
        )
        
        # Get full email documents from Firestore
        db = get_db()
        emails = []
        email_ids = [result['email_id'] for result in search_results]
        
        if email_ids:
            # Batch get emails
            email_docs = []
            for email_id in email_ids:
                email_doc = db.collection('emails').document(email_id).get()
                if email_doc.exists:
                    email_data = email_doc.to_dict()
                    # Verify ownership
                    if email_data.get('user_id') == current_user.id:
                        email_docs.append((email_id, email_data))
            
            # Sort by Pinecone score
            email_dict = {email_id: data for email_id, data in email_docs}
            
            for result in search_results:
                email_id = result['email_id']
                if email_id in email_dict:
                    email_data = email_dict[email_id]
                    email_data['similarity_score'] = result['score']
                    emails.append(email_data)
        
        processing_time = time.time() - start_time
        
        return EmailSearchResult(
            emails=emails,
            total_count=len(emails),
            query=search_query.query,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Semantic search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform semantic search"
        )


@router.get("/text", response_model=List[Dict[str, Any]])
async def text_search(
    query: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Perform text-based search on emails"""
    try:
        db = get_db()
        
        # Simple text search using Firestore's where clauses
        # Note: This is a basic implementation. For production, consider using
        # Algolia or Elasticsearch for better text search capabilities
        
        # Search in subject and body
        emails_ref = db.collection('emails').where('user_id', '==', current_user.id)
        
        # Get all emails (limit for performance)
        all_emails = emails_ref.limit(1000).stream()
        
        matching_emails = []
        query_lower = query.lower()
        
        for email_doc in all_emails:
            email_data = email_doc.to_dict()
            
            # Check if query matches subject or body
            subject_match = query_lower in email_data.get('subject', '').lower()
            body_match = query_lower in email_data.get('body_text', '').lower()
            sender_match = query_lower in email_data.get('sender', '').lower()
            
            if subject_match or body_match or sender_match:
                matching_emails.append(email_data)
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_results = matching_emails[start_idx:end_idx]
        
        return paginated_results
        
    except Exception as e:
        logger.error(f"Text search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform text search"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str,
    current_user: User = Depends(get_current_user)
) -> List[str]:
    """Get search suggestions based on user's email content"""
    try:
        db = get_db()
        
        # Get recent emails for suggestions
        emails_ref = db.collection('emails').where('user_id', '==', current_user.id)
        recent_emails = emails_ref.order_by('timestamp', direction='DESCENDING').limit(50).stream()
        
        # Extract keywords from subjects and bodies
        keywords = set()
        query_lower = query.lower()
        
        for email_doc in recent_emails:
            email_data = email_doc.to_dict()
            
            # Extract words from subject
            subject_words = email_data.get('subject', '').lower().split()
            # Extract words from body (first 200 chars)
            body_text = email_data.get('body_text', '')[:200].lower()
            body_words = body_text.split()
            
            # Find words that start with query
            for word in subject_words + body_words:
                word = word.strip('.,!?()[]{}"\'')
                if word.startswith(query_lower) and len(word) > 2:
                    keywords.add(word)
        
        # Return top suggestions
        suggestions = sorted(list(keywords))[:10]
        return suggestions
        
    except Exception as e:
        logger.error(f"Search suggestions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search suggestions"
        )


@router.get("/filters")
async def get_available_filters(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available filter options for search"""
    try:
        db = get_db()
        
        # Get unique categories for user
        emails_ref = db.collection('emails').where('user_id', '==', current_user.id)
        emails = emails_ref.stream()
        
        categories = set()
        senders = set()
        priorities = set()
        
        for email_doc in emails:
            email_data = email_doc.to_dict()
            
            if 'category' in email_data:
                categories.add(email_data['category'])
            
            if 'sender' in email_data:
                senders.add(email_data['sender'])
            
            if 'priority' in email_data:
                priorities.add(email_data['priority'])
        
        return {
            "categories": sorted(list(categories)),
            "senders": sorted(list(senders))[:20],  # Limit to top 20
            "priorities": sorted(list(priorities)),
            "date_ranges": [
                {"label": "Today", "value": "today"},
                {"label": "This Week", "value": "week"},
                {"label": "This Month", "value": "month"},
                {"label": "This Year", "value": "year"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Get filters error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get filter options"
        )
