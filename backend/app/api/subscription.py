from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..api.auth import get_current_user
from ..db.database import get_db
from ..models.user import User
from ..models.subscription import SubscriptionPlan, Payment
from ..services.stripe_service import StripeService
from ..services.usage_service import UsageService

router = APIRouter()


# Pydantic models for API requests/responses
class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    plan_type: str
    price_monthly: float
    price_yearly: Optional[float]
    currency: str
    conversations_limit: int
    file_uploads_limit: int
    knowledge_base_size_limit: int
    description: Optional[str]
    is_popular: bool
    features: Dict[str, Any]
    
    class Config:
        from_attributes = True


class CreateCheckoutRequest(BaseModel):
    plan_id: str
    billing_period: str = "monthly"  # "monthly" or "yearly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


class UsageSummaryResponse(BaseModel):
    conversations: Dict[str, Any]
    file_uploads: Dict[str, Any]
    knowledge_base: Dict[str, Any]
    subscription: Dict[str, Any]


class PaymentHistoryResponse(BaseModel):
    id: str
    amount: float
    currency: str
    status: str
    plan_name: Optional[str]
    billing_period: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    """Get all available subscription plans."""
    try:
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
        )
        plans = result.scalars().all()
        
        return [SubscriptionPlanResponse.from_orm(plan) for plan in plans]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription plans: {str(e)}"
        )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session for subscription."""
    try:
        # Validate plan exists
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == request.plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )
        
        # Create checkout session
        checkout_data = await StripeService.create_checkout_session(
            db=db,
            user=current_user,
            plan_id=request.plan_id,
            billing_period=request.billing_period,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutResponse(**checkout_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/portal", response_model=PortalResponse)
async def get_customer_portal(
    return_url: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get Stripe customer portal URL for subscription management."""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no active subscription"
            )
        
        portal_data = await StripeService.create_portal_session(
            user=current_user,
            return_url=return_url
        )
        
        return PortalResponse(**portal_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer portal: {str(e)}"
        )


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's current usage summary."""
    try:
        usage_data = await UsageService.get_user_usage_summary(db, current_user)
        return UsageSummaryResponse(**usage_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage summary: {str(e)}"
        )


@router.get("/payments", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's payment history."""
    try:
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        payments = result.scalars().all()
        
        return [PaymentHistoryResponse.from_orm(payment) for payment in payments]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment history: {str(e)}"
        )


@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user)
):
    """Get user's current subscription details."""
    try:
        subscription_data = {
            "tier": current_user.subscription_tier,
            "status": current_user.subscription_status,
            "current_period_end": current_user.subscription_current_period_end,
            "is_premium": current_user.is_premium,
            "stripe_customer_id": current_user.stripe_customer_id,
            "subscription_id": current_user.subscription_id
        }
        
        # Get Stripe subscription details if available
        if current_user.subscription_id:
            try:
                stripe_details = await StripeService.get_subscription_details(
                    current_user.subscription_id
                )
                subscription_data.update({
                    "stripe_details": stripe_details
                })
            except Exception as e:
                # Don't fail the whole request if Stripe is down
                subscription_data["stripe_error"] = str(e)
        
        return subscription_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription details: {str(e)}"
        )


@router.post("/cancel")
async def cancel_subscription(
    immediately: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel user's subscription."""
    try:
        if not current_user.subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel"
            )
        
        cancellation_data = await StripeService.cancel_subscription(
            current_user.subscription_id,
            immediately=immediately
        )
        
        # Update user record if immediate cancellation
        if immediately:
            current_user.subscription_tier = "free"
            current_user.subscription_status = "canceled"
            current_user.subscription_id = None
            current_user.subscription_current_period_end = None
            await db.commit()
        
        return {
            "message": "Subscription canceled successfully",
            "immediate": immediately,
            "details": cancellation_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events."""
    try:
        # Get raw body and signature
        raw_body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Handle webhook event
        success = await StripeService.handle_webhook_event(
            db=db,
            event_data=await request.json(),
            stripe_signature=stripe_signature,
            raw_body=raw_body
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook"
            )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/success")
async def subscription_success(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Handle successful subscription redirect."""
    try:
        # Refresh user data from database to get updated subscription
        await db.refresh(current_user)
        
        return {
            "message": "Subscription activated successfully!",
            "session_id": session_id,
            "subscription": {
                "tier": current_user.subscription_tier,
                "status": current_user.subscription_status,
                "current_period_end": current_user.subscription_current_period_end
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process success: {str(e)}"
        )


@router.get("/cancel")
async def subscription_cancel():
    """Handle subscription cancellation redirect."""
    return {
        "message": "Subscription cancelled. You can try again anytime.",
        "redirect_url": "/dashboard"
    }


# Usage limit checking endpoints for other services
@router.get("/check/conversations")
async def check_conversation_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if user can start a new conversation."""
    can_start = await UsageService.check_conversation_limit(db, current_user)
    
    return {
        "allowed": can_start,
        "current_usage": current_user.current_month_conversations,
        "limit": current_user.conversation_limit,
        "tier": current_user.subscription_tier
    }


@router.get("/check/file-uploads")
async def check_file_upload_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if user can upload a new file."""
    can_upload = await UsageService.check_file_upload_limit(db, current_user)
    
    return {
        "allowed": can_upload,
        "current_usage": current_user.current_month_file_uploads,
        "limit": current_user.file_upload_limit,
        "tier": current_user.subscription_tier
    }


@router.get("/check/knowledge-base")
async def check_knowledge_base_limit(
    additional_size: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if user can add data to knowledge base."""
    can_add = await UsageService.check_knowledge_base_size_limit(
        db, current_user, additional_size
    )
    
    return {
        "allowed": can_add,
        "current_usage_bytes": current_user.current_knowledge_base_size,
        "current_usage_mb": round(current_user.current_knowledge_base_size / (1024 * 1024), 2),
        "limit_bytes": current_user.knowledge_base_size_limit,
        "limit_mb": round(current_user.knowledge_base_size_limit / (1024 * 1024), 2),
        "tier": current_user.subscription_tier
    } 