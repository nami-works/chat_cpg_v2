from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

# from ..auth.oauth import google_oauth  # MVP: Comment out OAuth for now
from ..auth.security import (
    authenticate_user,
    create_access_token,
    create_user_account,
    # generate_password_reset_token,  # MVP: Comment out for now
    get_password_hash,
    get_user_by_email,
    # get_user_by_google_id,  # MVP: Comment out OAuth for now
    get_user_by_id,
    # verify_password_reset_token,  # MVP: Comment out for now
    verify_token,
)
from ..core.config import settings
from ..db.database import get_db
from ..models.user import User

router = APIRouter()
security = HTTPBearer()


# Pydantic models for API requests/responses
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
    is_verified: bool
    is_oauth_user: bool
    created_at: str
    
    class Config:
        from_attributes = True


# MVP: Comment out OAuth and password reset models for now
# class PasswordResetRequest(BaseModel):
#     email: EmailStr
#
#
# class PasswordReset(BaseModel):
#     token: str
#     new_password: str
#
#
# class GoogleOAuthCallback(BaseModel):
#     code: str
#     state: Optional[str] = None


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_uuid = UUID(user_id)
        user = await get_user_by_id(db, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )


@router.post("/signup", response_model=Token)
async def signup(
    user_data: UserSignup,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user account with email and password - MVP version.
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await create_user_account(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        is_verified=True,  # MVP: Auto-verify for simplicity
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    """
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# MVP: Comment out OAuth endpoints for now
# @router.get("/google/login")
# async def google_login():
#     """
#     Get Google OAuth login URL.
#     """
#     authorization_url = google_oauth.get_authorization_url()
#     return {"url": authorization_url}
#
#
# @router.post("/google/callback", response_model=Token)
# async def google_callback(
#     callback_data: GoogleOAuthCallback,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Handle Google OAuth callback.
#     """
#     try:
#         # Exchange code for tokens
#         token_data = google_oauth.exchange_code_for_tokens(callback_data.code)
#         
#         # Get user info from Google
#         user_info = google_oauth.get_user_info(token_data["access_token"])
#         
#         # Check if user exists
#         user = await get_user_by_google_id(db, user_info["id"])
#         
#         if not user:
#             # Check if email already exists
#             existing_user = await get_user_by_email(db, user_info["email"])
#             if existing_user:
#                 # Link Google account to existing user
#                 existing_user.google_id = user_info["id"]
#                 existing_user.is_oauth_user = True
#                 existing_user.avatar_url = user_info.get("picture")
#                 existing_user.is_verified = True
#                 await db.commit()
#                 user = existing_user
#             else:
#                 # Create new user
#                 user = await create_user_account(
#                     db=db,
#                     email=user_info["email"],
#                     full_name=user_info.get("name"),
#                     google_id=user_info["id"],
#                     avatar_url=user_info.get("picture"),
#                     is_oauth_user=True,
#                     is_verified=True,
#                 )
#         else:
#             # Update existing OAuth user info
#             user.avatar_url = user_info.get("picture")
#             user.last_login = datetime.utcnow()
#             await db.commit()
#         
#         # Create access token
#         access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#             subject=str(user.id), expires_delta=access_token_expires
#         )
#         
#         return {
#             "access_token": access_token,
#             "token_type": "bearer"
#         }
#         
#     except Exception as e:
#         logger.error(f"OAuth callback error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="OAuth authentication failed"
#         )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        subscription_tier=current_user.subscription_tier,
        is_verified=current_user.is_verified,
        is_oauth_user=current_user.is_oauth_user,
        created_at=current_user.created_at.isoformat()
    )


# MVP: Comment out password reset endpoints for now
# @router.post("/password-reset-request")
# async def request_password_reset(
#     request_data: PasswordResetRequest,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Request password reset email.
#     """
#     user = await get_user_by_email(db, request_data.email)
#     
#     if user:
#         # Generate reset token
#         reset_token = generate_password_reset_token(user.email)
#         
#         # TODO: Send reset email
#         # For now, just log the token (in production, send email)
#         logger.info(f"Password reset token for {user.email}: {reset_token}")
#     
#     # Always return success to prevent email enumeration
#     return {"message": "If your email is registered, you will receive a password reset link."}
#
#
# @router.post("/password-reset")
# async def reset_password(
#     reset_data: PasswordReset,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Reset password using token.
#     """
#     email = verify_password_reset_token(reset_data.token)
#     
#     if not email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired reset token"
#         )
#     
#     user = await get_user_by_email(db, email)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#     
#     # Update password
#     user.hashed_password = get_password_hash(reset_data.new_password)
#     await db.commit()
#     
#     return {"message": "Password reset successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (in a JWT system, this is mainly for client-side cleanup).
    """
    return {"message": "Logged out successfully"} 