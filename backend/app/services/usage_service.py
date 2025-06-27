import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from ..models.user import User
from ..models.subscription import UsageTracking

logger = logging.getLogger(__name__)


class UsageService:
    """Service for tracking and enforcing usage limits."""
    
    @staticmethod
    async def check_conversation_limit(db: AsyncSession, user: User) -> bool:
        """Check if user can start a new conversation."""
        try:
            limit = user.conversation_limit
            if limit == -1:  # Unlimited
                return True
            
            current_usage = user.current_month_conversations
            return current_usage < limit
            
        except Exception as e:
            logger.error(f"Error checking conversation limit for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def check_file_upload_limit(db: AsyncSession, user: User) -> bool:
        """Check if user can upload a new file."""
        try:
            limit = user.file_upload_limit
            if limit == -1:  # Unlimited
                return True
            
            current_usage = user.current_month_file_uploads
            return current_usage < limit
            
        except Exception as e:
            logger.error(f"Error checking file upload limit for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def check_knowledge_base_size_limit(
        db: AsyncSession, 
        user: User, 
        additional_size: int = 0
    ) -> bool:
        """Check if user can add more data to knowledge base."""
        try:
            limit = user.knowledge_base_size_limit
            if limit == -1:  # Unlimited
                return True
            
            current_usage = user.current_knowledge_base_size
            return (current_usage + additional_size) <= limit
            
        except Exception as e:
            logger.error(f"Error checking knowledge base limit for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def increment_conversation_usage(db: AsyncSession, user: User) -> bool:
        """Increment conversation usage counter."""
        try:
            if await UsageService.check_conversation_limit(db, user):
                user.current_month_conversations += 1
                await db.commit()
                
                # Log detailed usage
                await UsageService._log_usage(
                    db, user.id, "conversations", 1, "count"
                )
                
                logger.info(f"Incremented conversation usage for user {user.id}: {user.current_month_conversations}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing conversation usage for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def increment_file_upload_usage(db: AsyncSession, user: User) -> bool:
        """Increment file upload usage counter."""
        try:
            if await UsageService.check_file_upload_limit(db, user):
                user.current_month_file_uploads += 1
                await db.commit()
                
                # Log detailed usage
                await UsageService._log_usage(
                    db, user.id, "file_uploads", 1, "count"
                )
                
                logger.info(f"Incremented file upload usage for user {user.id}: {user.current_month_file_uploads}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing file upload usage for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def add_knowledge_base_usage(
        db: AsyncSession, 
        user: User, 
        size_bytes: int
    ) -> bool:
        """Add to knowledge base size usage."""
        try:
            if await UsageService.check_knowledge_base_size_limit(db, user, size_bytes):
                user.current_knowledge_base_size += size_bytes
                await db.commit()
                
                # Log detailed usage
                await UsageService._log_usage(
                    db, user.id, "knowledge_base", size_bytes, "bytes"
                )
                
                logger.info(f"Added knowledge base usage for user {user.id}: {size_bytes} bytes")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding knowledge base usage for user {user.id}: {e}")
            return False
    
    @staticmethod
    async def subtract_knowledge_base_usage(
        db: AsyncSession, 
        user: User, 
        size_bytes: int
    ):
        """Subtract from knowledge base size usage when files are deleted."""
        try:
            user.current_knowledge_base_size = max(0, user.current_knowledge_base_size - size_bytes)
            await db.commit()
            
            # Log detailed usage (negative amount)
            await UsageService._log_usage(
                db, user.id, "knowledge_base", -size_bytes, "bytes"
            )
            
            logger.info(f"Subtracted knowledge base usage for user {user.id}: {size_bytes} bytes")
            
        except Exception as e:
            logger.error(f"Error subtracting knowledge base usage for user {user.id}: {e}")
    
    @staticmethod
    async def get_user_usage_summary(db: AsyncSession, user: User) -> Dict:
        """Get comprehensive usage summary for user."""
        try:
            return {
                "conversations": {
                    "used": user.current_month_conversations,
                    "limit": user.conversation_limit,
                    "unlimited": user.conversation_limit == -1,
                    "percentage": (
                        (user.current_month_conversations / user.conversation_limit * 100) 
                        if user.conversation_limit > 0 
                        else 0
                    )
                },
                "file_uploads": {
                    "used": user.current_month_file_uploads,
                    "limit": user.file_upload_limit,
                    "unlimited": user.file_upload_limit == -1,
                    "percentage": (
                        (user.current_month_file_uploads / user.file_upload_limit * 100) 
                        if user.file_upload_limit > 0 
                        else 0
                    )
                },
                "knowledge_base": {
                    "used_bytes": user.current_knowledge_base_size,
                    "limit_bytes": user.knowledge_base_size_limit,
                    "used_mb": round(user.current_knowledge_base_size / (1024 * 1024), 2),
                    "limit_mb": round(user.knowledge_base_size_limit / (1024 * 1024), 2),
                    "unlimited": user.knowledge_base_size_limit == -1,
                    "percentage": (
                        (user.current_knowledge_base_size / user.knowledge_base_size_limit * 100) 
                        if user.knowledge_base_size_limit > 0 
                        else 0
                    )
                },
                "subscription": {
                    "tier": user.subscription_tier,
                    "status": user.subscription_status,
                    "current_period_end": user.subscription_current_period_end,
                    "is_premium": user.is_premium,
                    "last_reset": user.last_usage_reset
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary for user {user.id}: {e}")
            return {}
    
    @staticmethod
    async def reset_monthly_usage(db: AsyncSession, user: User):
        """Reset user's monthly usage counters."""
        try:
            user.current_month_conversations = 0
            user.current_month_file_uploads = 0
            user.current_knowledge_base_size = 0
            user.last_usage_reset = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Reset monthly usage for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage for user {user.id}: {e}")
    
    @staticmethod
    async def check_usage_limits_batch(db: AsyncSession, user_ids: list) -> Dict[str, Dict]:
        """Check usage limits for multiple users efficiently."""
        try:
            # Get all users at once
            result = await db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users = result.scalars().all()
            
            usage_data = {}
            for user in users:
                usage_data[str(user.id)] = await UsageService.get_user_usage_summary(db, user)
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Error checking batch usage limits: {e}")
            return {}
    
    @staticmethod
    async def _log_usage(
        db: AsyncSession,
        user_id: UUID,
        feature_type: str,
        amount: int,
        unit: str
    ):
        """Log detailed usage tracking."""
        try:
            now = datetime.utcnow()
            
            # Find or create usage tracking record for this month
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            result = await db.execute(
                select(UsageTracking).where(
                    and_(
                        UsageTracking.user_id == user_id,
                        UsageTracking.feature_type == feature_type,
                        UsageTracking.period_start == month_start,
                        UsageTracking.billing_period == "monthly"
                    )
                )
            )
            usage_record = result.scalar_one_or_none()
            
            if usage_record:
                usage_record.usage_amount += amount
                usage_record.updated_at = now
            else:
                usage_record = UsageTracking(
                    user_id=user_id,
                    feature_type=feature_type,
                    usage_amount=amount,
                    usage_unit=unit,
                    period_start=month_start,
                    period_end=month_end,
                    billing_period="monthly"
                )
                db.add(usage_record)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
    
    @staticmethod
    async def get_detailed_usage_history(
        db: AsyncSession,
        user_id: UUID,
        feature_type: Optional[str] = None,
        months: int = 6
    ) -> list:
        """Get detailed usage history for user."""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            # Build query
            query = select(UsageTracking).where(
                and_(
                    UsageTracking.user_id == user_id,
                    UsageTracking.period_start >= start_date
                )
            )
            
            if feature_type:
                query = query.where(UsageTracking.feature_type == feature_type)
            
            query = query.order_by(UsageTracking.period_start.desc())
            
            result = await db.execute(query)
            usage_records = result.scalars().all()
            
            return [
                {
                    "feature_type": record.feature_type,
                    "usage_amount": record.usage_amount,
                    "usage_unit": record.usage_unit,
                    "period_start": record.period_start,
                    "period_end": record.period_end,
                    "billing_period": record.billing_period
                }
                for record in usage_records
            ]
            
        except Exception as e:
            logger.error(f"Error getting usage history for user {user_id}: {e}")
            return [] 