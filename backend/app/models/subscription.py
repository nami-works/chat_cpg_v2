import enum
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.database import Base


class PlanType(str, enum.Enum):
    """Subscription plan types."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, enum.Enum):
    """Payment status options."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class SubscriptionPlan(Base):
    """Subscription plan model."""
    __tablename__ = "subscription_plans"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False, unique=True)
    price_monthly = Column(Float, nullable=False, default=0.0)
    price_yearly = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Stripe integration
    stripe_price_id = Column(String(255), nullable=True)
    stripe_product_id = Column(String(255), nullable=True)
    
    # Feature limits
    conversations_limit = Column(Integer, nullable=False, default=10)  # -1 = unlimited
    file_uploads_limit = Column(Integer, nullable=False, default=5)    # -1 = unlimited
    knowledge_base_size_limit = Column(Integer, nullable=False, default=10 * 1024 * 1024)  # bytes, -1 = unlimited
    
    # Display information
    description = Column(Text, nullable=True)
    is_popular = Column(Boolean, default=False)
    features = Column(JSON, default=list)  # List of feature descriptions
    
    # Management
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payments = relationship("Payment", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan(name='{self.name}', type='{self.plan_type}', price=${self.price_monthly})>"


class Payment(Base):
    """Payment transaction model."""
    __tablename__ = "payments"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    billing_period = Column(String(20), nullable=True)  # "monthly" or "yearly"
    
    # Stripe integration
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_invoice_id = Column(String(255), nullable=True)
    stripe_checkout_session_id = Column(String(255), nullable=True)
    
    # Timestamps
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional data
    additional_data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="payments")
    plan = relationship("SubscriptionPlan", back_populates="payments")

    def __repr__(self):
        return f"<Payment(user_id='{self.user_id}', amount=${self.amount}, status='{self.status}')>"


class SubscriptionEvent(Base):
    """Subscription events for audit trail."""
    __tablename__ = "subscription_events"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # "subscription_created", "payment_succeeded", etc.
    event_data = Column(JSON, default=dict)
    stripe_event_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<SubscriptionEvent(user_id='{self.user_id}', type='{self.event_type}')>"


class UsageTracking(Base):
    """Detailed usage tracking for analytics."""
    __tablename__ = "usage_tracking"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Usage details
    feature_type = Column(String(50), nullable=False)  # "conversations", "file_uploads", "knowledge_base"
    amount = Column(Integer, nullable=False)  # Can be negative for decrements
    unit = Column(String(20), nullable=False)  # "count", "bytes", "tokens"
    
    # Context
    resource_id = Column(String(255), nullable=True)  # ID of the specific resource used
    additional_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UsageTracking(user_id='{self.user_id}', feature='{self.feature_type}', amount={self.amount})>"


class UserUsage(Base):
    """Monthly usage summary for users."""
    __tablename__ = "user_usage"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Time period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Usage counts
    conversations_count = Column(Integer, default=0)
    file_uploads_count = Column(Integer, default=0)
    knowledge_base_size = Column(Integer, default=0)  # bytes
    
    # Metadata
    subscription_tier = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")

    class Config:
        # Unique constraint on user_id + year + month
        __table_args__ = (
            {"unique": ["user_id", "year", "month"]},
        )

    def __repr__(self):
        return f"<UserUsage(user_id='{self.user_id}', period={self.year}-{self.month:02d})>"


class UserSession(Base):
    """User session tracking for analytics."""
    __tablename__ = "user_sessions"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', active={self.is_active})>" 