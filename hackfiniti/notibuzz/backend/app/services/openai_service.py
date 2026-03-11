import openai
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings
from app.models.email import Email, PriorityLevel, EmailCategory

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for given text using OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        raise


async def summarize_email(email: Email) -> str:
    """Generate AI summary for email"""
    try:
        prompt = f"""
        Summarize the following email in 2-3 sentences:
        
        Subject: {email.subject}
        From: {email.sender}
        To: {', '.join(email.recipients)}
        
        Body:
        {email.body_text[:2000]}  # Limit text length
        
        Focus on the key information, action items, and main points.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes emails concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Failed to summarize email: {str(e)}")
        raise


async def classify_email_priority(email: Email) -> PriorityLevel:
    """Classify email priority using AI"""
    try:
        prompt = f"""
        Classify the priority of this email as one of: urgent, important, normal, low
        
        Subject: {email.subject}
        From: {email.sender}
        Body: {email.body_text[:1000]}
        
        Consider:
        - Time sensitivity
        - Importance of sender
        - Action items or deadlines
        - Urgency indicators (ASAP, urgent, immediately, etc.)
        
        Respond with only the priority level.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an email priority classifier."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        priority_str = response.choices[0].message.content.strip().lower()
        
        priority_map = {
            "urgent": PriorityLevel.URGENT,
            "important": PriorityLevel.IMPORTANT,
            "normal": PriorityLevel.NORMAL,
            "low": PriorityLevel.LOW
        }
        
        return priority_map.get(priority_str, PriorityLevel.NORMAL)
        
    except Exception as e:
        logger.error(f"Failed to classify email priority: {str(e)}")
        return PriorityLevel.NORMAL


async def categorize_email(email: Email) -> EmailCategory:
    """Categorize email using AI"""
    try:
        prompt = f"""
        Categorize this email into one of: work, personal, financial, marketing, social, newsletter, other
        
        Subject: {email.subject}
        From: {email.sender}
        Body: {email.body_text[:1000]}
        
        Consider:
        - Sender domain and type
        - Content and purpose
        - Keywords and phrases
        
        Respond with only the category.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an email categorizer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=15,
            temperature=0.1
        )
        
        category_str = response.choices[0].message.content.strip().lower()
        
        category_map = {
            "work": EmailCategory.WORK,
            "personal": EmailCategory.PERSONAL,
            "financial": EmailCategory.FINANCIAL,
            "marketing": EmailCategory.MARKETING,
            "social": EmailCategory.SOCIAL,
            "newsletter": EmailCategory.NEWSLETTER,
            "other": EmailCategory.OTHER
        }
        
        return category_map.get(category_str, EmailCategory.OTHER)
        
    except Exception as e:
        logger.error(f"Failed to categorize email: {str(e)}")
        return EmailCategory.OTHER


async def analyze_sentiment(email: Email) -> float:
    """Analyze email sentiment score (-1 to 1)"""
    try:
        prompt = f"""
        Analyze the sentiment of this email and provide a score from -1 (very negative) to 1 (very positive).
        
        Subject: {email.subject}
        Body: {email.body_text[:1000]}
        
        Respond with only a number between -1 and 1.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analyzer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        try:
            sentiment_score = float(response.choices[0].message.content.strip())
            return max(-1.0, min(1.0, sentiment_score))  # Clamp between -1 and 1
        except ValueError:
            return 0.0
        
    except Exception as e:
        logger.error(f"Failed to analyze sentiment: {str(e)}")
        return 0.0


async def extract_action_items(email: Email) -> List[str]:
    """Extract action items from email"""
    try:
        prompt = f"""
        Extract action items from this email. Return as a JSON array of strings.
        
        Subject: {email.subject}
        Body: {email.body_text[:2000]}
        
        Look for:
        - Tasks that need to be done
        - Deadlines
        - Requests for action
        - Commitments
        
        Return only the JSON array.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an action item extractor. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        import json
        try:
            action_items = json.loads(response.choices[0].message.content.strip())
            if isinstance(action_items, list):
                return action_items
            return []
        except json.JSONDecodeError:
            return []
        
    except Exception as e:
        logger.error(f"Failed to extract action items: {str(e)}")
        return []
