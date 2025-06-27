from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..db.database import Base


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(200), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Status
    status = Column(String(50), default=UserStatus.ACTIVE.value)
    last_login_at = Column(DateTime, nullable=True)
    
    # User preferences
    preferences = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # OAuth fields
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_oauth_user = Column(Boolean, default=False)
    
    # Subscription
    subscription_tier = Column(String(50), default=SubscriptionTier.FREE.value)
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), nullable=True)
    subscription_current_period_end = Column(DateTime, nullable=True)
    
    # Usage tracking (for quick access)
    current_month_conversations = Column(Integer, default=0)
    current_month_file_uploads = Column(Integer, default=0)
    current_knowledge_base_size = Column(Integer, default=0)  # in bytes
    last_usage_reset = Column(DateTime, default=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    content_projects = relationship("ContentProject", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    subscription_events = relationship("SubscriptionEvent", back_populates="user")
    usage_tracking = relationship("UsageTracking", back_populates="user")
    user_usage = relationship("UserUsage", back_populates="user")
    knowledge_bases = relationship("KnowledgeBase", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status={self.status})>"
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return self.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.ENTERPRISE.value]
    
    @property
    def conversation_limit(self) -> int:
        """Get conversation limit based on subscription tier"""
        from ..core.config import settings
        
        if self.subscription_tier == SubscriptionTier.FREE.value:
            return settings.FREE_TIER_CONVERSATIONS
        elif self.subscription_tier == SubscriptionTier.PRO.value:
            return settings.PRO_TIER_CONVERSATIONS
        elif self.subscription_tier == SubscriptionTier.ENTERPRISE.value:
            return settings.ENTERPRISE_TIER_CONVERSATIONS
        return 0
    
    @property
    def file_upload_limit(self) -> int:
        """Get file upload limit based on subscription tier"""
        from ..core.config import settings
        
        if self.subscription_tier == SubscriptionTier.FREE.value:
            return settings.FREE_TIER_FILE_UPLOADS
        elif self.subscription_tier == SubscriptionTier.PRO.value:
            return settings.PRO_TIER_FILE_UPLOADS
        elif self.subscription_tier == SubscriptionTier.ENTERPRISE.value:
            return settings.ENTERPRISE_TIER_FILE_UPLOADS
        return 0
    
    @property
    def knowledge_base_size_limit(self) -> int:
        """Get knowledge base size limit based on subscription tier"""
        from ..core.config import settings
        
        if self.subscription_tier == SubscriptionTier.FREE.value:
            return settings.FREE_TIER_KNOWLEDGE_BASE_SIZE
        elif self.subscription_tier == SubscriptionTier.PRO.value:
            return settings.PRO_TIER_KNOWLEDGE_BASE_SIZE
        elif self.subscription_tier == SubscriptionTier.ENTERPRISE.value:
            return settings.ENTERPRISE_TIER_KNOWLEDGE_BASE_SIZE
        return 0


# Note: UserUsage and UserSession models are now defined in subscription.py to avoid duplication 