import base64
import hashlib
import secrets
import time
from typing import Optional, Dict, Any, Tuple
from flask import request
import logging
import os
import jwt
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class AuthenticationService:
    """
    Authentication service for the CS 15 tutor system.
    Handles both web app (.htaccess) and VSCode extension authentication.
    """
    
    def __init__(self):
        # JWT secret for VSCode extension authentication
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')
        self.jwt_expiry_hours = 24
        logger.info("Authentication service initialized")
    
    def extract_utln_from_web_request(self, request) -> Optional[str]:
        """
        Extract UTLN from web request (Apache .htaccess authentication).
        Apache sets the REMOTE_USER environment variable after LDAP authentication.
        
        Args:
            request: Flask request object
        
        Returns:
            UTLN if authenticated, None otherwise
        """
        try:
            # Try multiple ways to get the authenticated user
            utln = None
            
            # Method 1: REMOTE_USER environment variable (most common)
            utln = os.environ.get('REMOTE_USER')
            
            # Method 2: Check request headers (if forwarded by proxy)
            if not utln:
                utln = request.headers.get('X-Remote-User')
                
            # Method 3: Check CGI environment variables
            if not utln:
                utln = request.environ.get('REMOTE_USER')
                
            # Method 4: Basic Auth header (for testing/development)
            if not utln and request.authorization:
                utln = request.authorization.username
            
            # Method 5: Development mode - check for development headers
            if not utln and request.headers.get('X-Development-Mode') == 'true':
                utln = request.headers.get('X-Remote-User')
                if utln:
                    logger.info(f"Development mode authentication: {utln}")
            
            if utln:
                logger.info(f"Authenticated web user: {utln}")
                return utln.lower().strip()
            
            logger.warning("No authenticated user found in web request")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting UTLN from web request: {e}")
            return None
    
    def create_vscode_auth_token(self, utln: str) -> str:
        """
        Create a JWT token for VSCode extension authentication.
        
        Args:
            utln: Tufts University Login Name
        
        Returns:
            JWT token string
        """
        try:
            payload = {
                'utln': utln.lower().strip(),
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
                'platform': 'vscode'
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            logger.info(f"Created VSCode auth token for user: {utln}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating VSCode auth token: {e}")
            raise
    
    def verify_vscode_auth_token(self, token: str) -> Optional[str]:
        """
        Verify a VSCode extension JWT token and extract UTLN.
        
        Args:
            token: JWT token string
        
        Returns:
            UTLN if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            utln = payload.get('utln')
            
            if utln:
                logger.info(f"Verified VSCode auth token for user: {utln}")
                return utln.lower().strip()
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("VSCode auth token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid VSCode auth token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying VSCode auth token: {e}")
            return None
    
    def authenticate_request(self, request) -> Tuple[Optional[str], str]:
        """
        Authenticate a request from either web app or VSCode extension.
        
        Args:
            request: Flask request object
        
        Returns:
            Tuple of (UTLN, platform) if authenticated, (None, '') otherwise
        """
        try:
            # Check for VSCode extension auth token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                utln = self.verify_vscode_auth_token(token)
                if utln:
                    return utln, 'vscode'
            
            # Check for web app authentication
            utln = self.extract_utln_from_web_request(request)
            if utln:
                return utln, 'web'
            
            return None, ''
            
        except Exception as e:
            logger.error(f"Error authenticating request: {e}")
            return None, ''
    
    def is_authorized_cs15_student(self, utln: str) -> bool:
        """
        Check if a user is authorized to use the CS 15 tutor system.
        This could be extended to check against a database or LDAP group.
        
        Args:
            utln: Tufts University Login Name
        
        Returns:
            True if authorized, False otherwise
        """
        try:
            # Check if development mode is explicitly enabled
            dev_mode = os.getenv('DEVELOPMENT_MODE', '').lower() == 'true'
            
            # For now, read from the .htgrp file like the web app
            htgrp_path = os.path.join(os.path.dirname(__file__), '../web-app/.htgrp')
            
            if os.path.exists(htgrp_path):
                with open(htgrp_path, 'r') as f:
                    content = f.read()
                    # Parse the .htgrp file format: "group: user1 user2 user3"
                    for line in content.strip().split('\n'):
                        if line.startswith('cs15_students:'):
                            authorized_users = line.split(':', 1)[1].strip().split()
                            if utln.lower() in [user.lower() for user in authorized_users]:
                                return True
            
            # Fallback: if file doesn't exist, check environment variable or default list
            authorized_users_env = os.getenv('CS15_AUTHORIZED_USERS', '')
            if authorized_users_env:
                authorized_users = [user.strip().lower() for user in authorized_users_env.split(',')]
                if utln.lower() in authorized_users:
                    return True
            
            # Development mode: allow any user that looks like a valid UTLN
            if dev_mode and re.match(r'^[a-zA-Z][a-zA-Z0-9]{2,15}$', utln):
                logger.info(f"Development mode: allowing user {utln}")
                return True
            
            logger.warning(f"User {utln} not authorized for CS 15 tutor")
            return False
            
        except Exception as e:
            logger.error(f"Error checking user authorization: {e}")
            return False
    
    def generate_vscode_login_url(self, base_url: str) -> str:
        """
        Generate a login URL for VSCode extension users.
        This would redirect to a web page where they can authenticate with Tufts LDAP.
        
        Args:
            base_url: Base URL of the web application
        
        Returns:
            Login URL for VSCode users
        """
        # Create a unique session ID for this login attempt
        session_id = secrets.token_urlsafe(32)
        
        # Store session temporarily (in production, use Redis or database)
        # For now, we'll use a simple in-memory store
        if not hasattr(self, '_vscode_sessions'):
            self._vscode_sessions = {}
        
        self._vscode_sessions[session_id] = {
            'created_at': datetime.utcnow(),
            'status': 'pending'
        }
        
        # Clean up old sessions (older than 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._vscode_sessions = {
            k: v for k, v in self._vscode_sessions.items() 
            if v['created_at'] > cutoff
        }
        
        return f"{base_url}/vscode-auth?session_id={session_id}"
    
    def handle_vscode_login_callback(self, session_id: str, utln: str) -> Optional[str]:
        """
        Handle the callback from VSCode authentication web page.
        
        Args:
            session_id: Session ID from login URL
            utln: Authenticated UTLN
        
        Returns:
            JWT token if successful, None otherwise
        """
        try:
            if not hasattr(self, '_vscode_sessions'):
                return None
            
            session = self._vscode_sessions.get(session_id)
            if not session or session['status'] != 'pending':
                return None
            
            # Check if user is authorized
            if not self.is_authorized_cs15_student(utln):
                logger.warning(f"Unauthorized VSCode login attempt: {utln}")
                return None
            
            # Create auth token
            token = self.create_vscode_auth_token(utln)
            
            # Mark session as completed
            session['status'] = 'completed'
            session['token'] = token
            session['utln'] = utln
            
            return token
            
        except Exception as e:
            logger.error(f"Error handling VSCode login callback: {e}")
            return None
    
    def get_vscode_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a VSCode authentication session.
        
        Args:
            session_id: Session ID from login URL
        
        Returns:
            Dictionary with session status
        """
        try:
            if not hasattr(self, '_vscode_sessions'):
                return {'status': 'not_found'}
            
            session = self._vscode_sessions.get(session_id)
            if not session:
                return {'status': 'not_found'}
            
            result = {'status': session['status']}
            if session['status'] == 'completed':
                result['token'] = session.get('token')
                result['utln'] = session.get('utln')
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting VSCode session status: {e}")
            return {'status': 'error'}

# Global authentication service instance
auth_service = AuthenticationService() 