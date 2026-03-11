from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import base64
import email
from datetime import datetime, timedelta
import logging
from app.core.config import settings
from app.models.email import Email, EmailAttachment, PriorityLevel, EmailCategory

logger = logging.getLogger(__name__)


class GmailService:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
    def get_auth_flow(self) -> Flow:
        """Create OAuth flow for Gmail authentication"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GMAIL_CLIENT_ID,
                    "client_secret": settings.GMAIL_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GMAIL_REDIRECT_URI]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = settings.GMAIL_REDIRECT_URI
        return flow
    
    def get_credentials(self, access_token: str, refresh_token: str) -> Credentials:
        """Create credentials object from tokens"""
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=self.scopes
        )
    
    async def get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user information from Google"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise
    
    async def fetch_emails(self, credentials: Credentials, max_results: int = 50) -> List[Email]:
        """Fetch emails from Gmail"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            emails = []
            
            # Get messages from inbox
            results = service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                try:
                    email_data = await self._get_full_message(service, message['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Failed to process message {message['id']}: {str(e)}")
                    continue
            
            return emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {str(e)}")
            raise
    
    async def _get_full_message(self, service, message_id: str) -> Optional[Email]:
        """Get full email message details"""
        try:
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = ""
            sender = ""
            sender_email = ""
            recipients = []
            cc = []
            date_str = ""
            
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'from':
                    sender_info = header['value']
                    # Extract name and email
                    if '<' in sender_info:
                        sender = sender_info.split('<')[0].strip().strip('"')
                        sender_email = sender_info.split('<')[1].strip('>')
                    else:
                        sender = sender_info
                        sender_email = sender_info
                elif header['name'].lower() == 'to':
                    recipients = [addr.strip() for addr in header['value'].split(',')]
                elif header['name'].lower() == 'cc':
                    cc = [addr.strip() for addr in header['value'].split(',')]
                elif header['name'].lower() == 'date':
                    date_str = header['value']
            
            # Parse date
            timestamp = datetime.utcnow()
            if date_str:
                try:
                    # Gmail date format: "Tue, 15 Nov 2022 12:34:56 +0000"
                    timestamp = datetime.strptime(date_str[:25], '%a, %d %b %Y %H:%M:%S')
                except ValueError:
                    try:
                        timestamp = datetime.strptime(date_str, '%d %b %Y %H:%M:%S %z')
                    except ValueError:
                        pass
            
            # Extract body
            body_text, body_html = self._extract_body(message['payload'])
            
            # Extract attachments
            attachments = self._extract_attachments(service, message_id, message['payload'])
            
            # Get labels
            labels = message.get('labelIds', [])
            
            # Create Email object
            email_obj = Email(
                id=message_id,
                thread_id=message['threadId'],
                subject=subject,
                sender=sender,
                sender_email=sender_email,
                recipients=recipients,
                cc=cc,
                body_text=body_text,
                body_html=body_html,
                timestamp=timestamp,
                read='UNREAD' not in labels,
                starred='STARRED' in labels,
                important='IMPORTANT' in labels,
                attachments=attachments,
                labels=labels
            )
            
            return email_obj
            
        except Exception as e:
            logger.error(f"Failed to get full message {message_id}: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """Extract text and HTML body from email payload"""
        body_text = ""
        body_html = None
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
                elif mime_type == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            data = payload['body'].get('data', '')
            
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                if mime_type == 'text/html':
                    body_html = decoded
                else:
                    body_text = decoded
        
        return body_text, body_html
    
    def _extract_attachments(self, service, message_id: str, payload: Dict[str, Any]) -> List[EmailAttachment]:
        """Extract attachments from email"""
        attachments = []
        
        def process_parts(parts):
            for part in parts:
                if part.get('filename'):
                    # This is an attachment
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id:
                        try:
                            attachment = service.users().messages().attachments().get(
                                userId='me',
                                messageId=message_id,
                                id=attachment_id
                            ).execute()
                            
                            attachments.append(EmailAttachment(
                                filename=part['filename'],
                                size=attachment['size'],
                                content_type=part.get('mimeType', 'application/octet-stream'),
                                attachment_id=attachment_id
                            ))
                        except Exception as e:
                            logger.error(f"Failed to get attachment {attachment_id}: {str(e)}")
                
                # Recursively process nested parts
                if 'parts' in part:
                    process_parts(part['parts'])
        
        if 'parts' in payload:
            process_parts(payload['parts'])
        
        return attachments
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=self.scopes
            )
            
            credentials.refresh(Request())
            return credentials.token
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            return None


gmail_service = GmailService()
