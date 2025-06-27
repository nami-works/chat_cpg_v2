from typing import Dict, Optional
import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from ..core.config import settings


class GoogleOAuth:
    """Google OAuth handler"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        # OAuth scopes
        self.scopes = [
            "openid",
            "email",
            "profile",
        ]
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.scopes,
        )
        flow.redirect_uri = self.redirect_uri
        
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent"
        )
        
        return authorization_url
    
    async def exchange_code_for_token(self, code: str, state: Optional[str] = None) -> Dict:
        """
        Exchange authorization code for access token and user info.
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.scopes,
        )
        flow.redirect_uri = self.redirect_uri
        
        # Exchange code for token
        flow.fetch_token(code=code)
        
        # Get user info from ID token
        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            self.client_id
        )
        
        return {
            "google_id": id_info.get("sub"),
            "email": id_info.get("email"),
            "full_name": id_info.get("name"),
            "avatar_url": id_info.get("picture"),
            "email_verified": id_info.get("email_verified", False),
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
        }
    
    async def verify_id_token(self, token: str) -> Optional[Dict]:
        """
        Verify Google ID token and extract user info.
        """
        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )
            
            # Check issuer
            if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Wrong issuer.")
            
            return {
                "google_id": id_info.get("sub"),
                "email": id_info.get("email"),
                "full_name": id_info.get("name"),
                "avatar_url": id_info.get("picture"),
                "email_verified": id_info.get("email_verified", False),
            }
        except ValueError:
            # Invalid token
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Google API using access token.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    return {
                        "google_id": user_info.get("id"),
                        "email": user_info.get("email"),
                        "full_name": user_info.get("name"),
                        "avatar_url": user_info.get("picture"),
                        "email_verified": user_info.get("verified_email", False),
                    }
                return None
            except Exception:
                return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh Google access token using refresh token.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception:
                return None


# Initialize Google OAuth instance
google_oauth = GoogleOAuth() 