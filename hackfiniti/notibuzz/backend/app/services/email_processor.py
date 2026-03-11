from typing import List, Dict, Any
import logging
from datetime import datetime
from app.models.email import Email
from app.services.openai_service import (
    generate_embedding,
    summarize_email,
    classify_email_priority,
    categorize_email,
    analyze_sentiment,
    extract_action_items
)
from app.services.pinecone_service import upsert_email_embedding
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Service for processing emails with AI analysis"""
    
    async def process_email(self, email: Email) -> Email:
        """Process a single email with AI analysis"""
        try:
            logger.info(f"Processing email: {email.id}")
            
            # Generate summary
            if not email.summary:
                email.summary = await summarize_email(email)
            
            # Classify priority
            email.priority = await classify_email_priority(email)
            
            # Categorize email
            email.category = await categorize_email(email)
            
            # Analyze sentiment
            email.sentiment_score = await analyze_sentiment(email)
            
            # Generate embedding
            text_to_embed = f"{email.subject} {email.body_text}"
            email.embedding = await generate_embedding(text_to_embed)
            
            # Store in Pinecone
            if email.embedding:
                await upsert_email_embedding(email, email.embedding)
            
            # Update processing metadata
            email.processed_at = datetime.utcnow()
            
            logger.info(f"Successfully processed email: {email.id}")
            return email
            
        except Exception as e:
            logger.error(f"Failed to process email {email.id}: {str(e)}")
            raise
    
    async def process_emails_batch(self, emails: List[Email]) -> List[Email]:
        """Process multiple emails in batch"""
        processed_emails = []
        
        for email in emails:
            try:
                processed_email = await self.process_email(email)
                processed_emails.append(processed_email)
            except Exception as e:
                logger.error(f"Failed to process email {email.id}: {str(e)}")
                # Continue processing other emails
                continue
        
        return processed_emails
    
    async def reprocess_email(self, email_id: str) -> Email:
        """Reprocess an existing email with updated AI models"""
        try:
            db = get_db()
            
            # Get email from Firestore
            email_doc = db.collection('emails').document(email_id).get()
            if not email_doc.exists:
                raise ValueError(f"Email {email_id} not found")
            
            email_data = email_doc.to_dict()
            email = Email(**email_data)
            
            # Process with updated AI
            processed_email = await self.process_email(email)
            
            # Update in Firestore
            await self._save_email_to_firestore(processed_email)
            
            return processed_email
            
        except Exception as e:
            logger.error(f"Failed to reprocess email {email_id}: {str(e)}")
            raise
    
    async def _save_email_to_firestore(self, email: Email):
        """Save processed email to Firestore"""
        try:
            db = get_db()
            
            email_dict = email.model_dump(exclude={'embedding'})  # Exclude embedding from Firestore
            
            db.collection('emails').document(email.id).set(email_dict)
            
            logger.info(f"Saved email {email.id} to Firestore")
            
        except Exception as e:
            logger.error(f"Failed to save email to Firestore: {str(e)}")
            raise
    
    async def get_email_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for user's emails"""
        try:
            db = get_db()
            
            # Get all emails for user
            emails_ref = db.collection('emails').where('user_id', '==', user_id)
            emails = emails_ref.stream()
            
            total_emails = 0
            unread_count = 0
            urgent_count = 0
            important_count = 0
            category_breakdown = {}
            daily_volume = {}
            top_senders = {}
            
            for email_doc in emails:
                email_data = email_doc.to_dict()
                total_emails += 1
                
                if not email_data.get('read', True):
                    unread_count += 1
                
                if email_data.get('priority') == 'urgent':
                    urgent_count += 1
                
                if email_data.get('priority') == 'important':
                    important_count += 1
                
                # Category breakdown
                category = email_data.get('category', 'other')
                category_breakdown[category] = category_breakdown.get(category, 0) + 1
                
                # Daily volume (last 7 days)
                timestamp = email_data.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = timestamp.strftime('%Y-%m-%d')
                    daily_volume[date_key] = daily_volume.get(date_key, 0) + 1
                
                # Top senders
                sender = email_data.get('sender_email', 'unknown')
                top_senders[sender] = top_senders.get(sender, 0) + 1
            
            # Sort and limit results
            top_senders = dict(sorted(top_senders.items(), key=lambda x: x[1], reverse=True)[:10])
            
            return {
                'total_emails': total_emails,
                'unread_count': unread_count,
                'urgent_count': urgent_count,
                'important_count': important_count,
                'category_breakdown': category_breakdown,
                'daily_volume': daily_volume,
                'top_senders': top_senders
            }
            
        except Exception as e:
            logger.error(f"Failed to get email analytics: {str(e)}")
            raise


email_processor = EmailProcessor()
