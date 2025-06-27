from datetime import datetime, timedelta
from typing import Any, Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import settings
from ..models.user import User
from ..db.database import get_db


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate password hash.
    """
    return pwd_context.hash(password)


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return user ID.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email.
    """
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    """
    Get user by Google ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """
    Authenticate user with email and password.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not user.hashed_password:  # OAuth user without password
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user_account(
    db: AsyncSession,
    email: str,
    password: Optional[str] = None,
    full_name: Optional[str] = None,
    google_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
    is_verified: bool = False,
) -> User:
    """
    Create new user account.
    """
    from uuid import uuid4
    
    hashed_password = None
    if password:
        hashed_password = get_password_hash(password)
    
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        google_id=google_id,
        avatar_url=avatar_url,
        is_oauth_user=bool(google_id),
        is_verified=is_verified,
        verification_token=str(uuid4()) if not is_verified else None,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


def generate_verification_token() -> str:
    """
    Generate email verification token.
    """
    from uuid import uuid4
    return str(uuid4())


def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token.
    """
    delta = timedelta(hours=1)  # Token expires in 1 hour
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email.
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token["sub"]
    except JWTError:
        return None


# FastAPI dependencies
security = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    token = credentials.credentials
    
    # Verify token
    user_id_str = verify_token(token)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    try:
        user_id = UUID(user_id_str)
        user = await get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_websocket(
    websocket: WebSocket,
    db: AsyncSession
) -> Optional[User]:
    """
    Get current authenticated user from WebSocket connection.
    Expects token in query parameters as 'token=<jwt_token>'.
    """
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            return None
        
        # Verify token
        user_id_str = verify_token(token)
        if user_id_str is None:
            return None
        
        # Get user
        try:
            user_id = UUID(user_id_str)
            user = await get_user_by_id(db, user_id)
            if user is None or not user.is_active:
                return None
            
            return user
            
        except ValueError:
            return None
            
    except Exception:
        return None 