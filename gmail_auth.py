#!/usr/bin/env python3
"""
Simplified Gmail authentication for PolicyEdge.
"""

import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GmailSender:
    """Simplified Gmail sender that handles authentication automatically."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, sender_email: str = None):
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL')
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.pickle'
        self.service = None
        
        if not self.sender_email:
            raise ValueError("Sender email must be provided")
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Please download credentials.json from Google Cloud Console")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authentication successful")
        return True
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        """Send email via Gmail."""
        try:
            if not self.service:
                self.authenticate()
            
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Add body
            body_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, body_type))
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully to {to_email}")
            return send_message['id']
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
    
    def test_connection(self):
        """Test Gmail connection."""
        try:
            if not self.service:
                self.authenticate()
            
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Connected to Gmail: {profile.get('emailAddress')}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail connection test failed: {str(e)}")
            return False
