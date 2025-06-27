import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..core.config import settings
from ..models.user import User
from ..models.subscription import (
    SubscriptionPlan, Payment, PaymentStatus, 
    SubscriptionStatus, UsageTracking, SubscriptionEvent
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripeService:
    """Service class for handling Stripe operations."""
    
    @staticmethod
    async def create_customer(user: User) -> str:
        """Create a Stripe customer for the user."""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    "user_id": str(user.id),
                    "tier": user.subscription_tier
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise Exception(f"Failed to create customer: {str(e)}")
    
    @staticmethod
    async def create_checkout_session(
        db: AsyncSession,
        user: User,
        plan_id: str,
        billing_period: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        try:
            # Get subscription plan
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                raise Exception("Subscription plan not found")
            
            # Ensure user has a Stripe customer ID
            if not user.stripe_customer_id:
                customer_id = await StripeService.create_customer(user)
                user.stripe_customer_id = customer_id
                await db.commit()
            
            # Determine price based on billing period
            price_id = plan.stripe_price_id
            if billing_period == "yearly" and plan.price_yearly:
                # Assuming you have yearly price IDs stored separately
                price_id = f"{plan.stripe_price_id}_yearly"
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or f"{settings.SERVER_HOST}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url or f"{settings.SERVER_HOST}/subscription/cancel",
                metadata={
                    "user_id": str(user.id),
                    "plan_id": str(plan.id),
                    "billing_period": billing_period
                }
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    @staticmethod
    async def create_portal_session(user: User, return_url: str = None) -> Dict[str, Any]:
        """Create a Stripe customer portal session."""
        try:
            if not user.stripe_customer_id:
                raise Exception("User has no Stripe customer ID")
            
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url or f"{settings.SERVER_HOST}/dashboard"
            )
            
            return {
                "portal_url": session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            raise Exception(f"Failed to create portal session: {str(e)}")
    
    @staticmethod
    async def get_subscription_details(subscription_id: str) -> Dict[str, Any]:
        """Get subscription details from Stripe."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "items": subscription.items.data
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription details: {e}")
            raise Exception(f"Failed to get subscription: {str(e)}")
    
    @staticmethod
    async def cancel_subscription(subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    @staticmethod
    async def handle_webhook_event(
        db: AsyncSession,
        event_data: Dict[str, Any],
        stripe_signature: str,
        raw_body: bytes
    ) -> bool:
        """Handle Stripe webhook events."""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                raw_body,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Log the event
            await StripeService._log_webhook_event(db, event)
            
            # Handle different event types
            if event['type'] == 'customer.subscription.created':
                await StripeService._handle_subscription_created(db, event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                await StripeService._handle_subscription_updated(db, event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await StripeService._handle_subscription_deleted(db, event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                await StripeService._handle_payment_succeeded(db, event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                await StripeService._handle_payment_failed(db, event['data']['object'])
            elif event['type'] == 'checkout.session.completed':
                await StripeService._handle_checkout_completed(db, event['data']['object'])
            
            return True
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False
    
    @staticmethod
    async def _log_webhook_event(db: AsyncSession, event: Dict[str, Any]):
        """Log webhook event to database."""
        try:
            # Extract user_id from metadata if available
            user_id = None
            if 'object' in event['data'] and 'metadata' in event['data']['object']:
                user_id = event['data']['object']['metadata'].get('user_id')
            
            event_log = SubscriptionEvent(
                user_id=UUID(user_id) if user_id else None,
                event_type=event['type'],
                stripe_event_id=event['id'],
                event_data=event['data'],
                processed=False
            )
            
            db.add(event_log)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log webhook event: {e}")
    
    @staticmethod
    async def _handle_subscription_created(db: AsyncSession, subscription: Dict[str, Any]):
        """Handle subscription created event."""
        try:
            customer_id = subscription['customer']
            
            # Find user by Stripe customer ID
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.subscription_id = subscription['id']
                user.subscription_status = subscription['status']
                user.subscription_current_period_end = datetime.fromtimestamp(
                    subscription['current_period_end']
                )
                
                # Update subscription tier based on plan
                # This requires mapping Stripe price IDs to tiers
                await StripeService._update_user_tier_from_subscription(db, user, subscription)
                
                await db.commit()
                logger.info(f"Updated user {user.id} subscription: {subscription['id']}")
            
        except Exception as e:
            logger.error(f"Error handling subscription created: {e}")
    
    @staticmethod
    async def _handle_subscription_updated(db: AsyncSession, subscription: Dict[str, Any]):
        """Handle subscription updated event."""
        try:
            subscription_id = subscription['id']
            
            # Find user by subscription ID
            result = await db.execute(
                select(User).where(User.subscription_id == subscription_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.subscription_status = subscription['status']
                user.subscription_current_period_end = datetime.fromtimestamp(
                    subscription['current_period_end']
                )
                
                # Handle status changes
                if subscription['status'] in ['canceled', 'unpaid']:
                    user.subscription_tier = 'free'
                
                await db.commit()
                logger.info(f"Updated user {user.id} subscription status: {subscription['status']}")
            
        except Exception as e:
            logger.error(f"Error handling subscription updated: {e}")
    
    @staticmethod
    async def _handle_subscription_deleted(db: AsyncSession, subscription: Dict[str, Any]):
        """Handle subscription deleted event."""
        try:
            subscription_id = subscription['id']
            
            # Find user by subscription ID
            result = await db.execute(
                select(User).where(User.subscription_id == subscription_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.subscription_tier = 'free'
                user.subscription_status = 'canceled'
                user.subscription_id = None
                user.subscription_current_period_end = None
                
                await db.commit()
                logger.info(f"User {user.id} subscription canceled")
            
        except Exception as e:
            logger.error(f"Error handling subscription deleted: {e}")
    
    @staticmethod
    async def _handle_payment_succeeded(db: AsyncSession, invoice: Dict[str, Any]):
        """Handle successful payment."""
        try:
            customer_id = invoice['customer']
            subscription_id = invoice['subscription']
            
            # Find user
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Create payment record
                payment = Payment(
                    user_id=user.id,
                    stripe_payment_intent_id=invoice['payment_intent'],
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    amount=invoice['amount_paid'] / 100,  # Convert from cents
                    currency=invoice['currency'],
                    status=PaymentStatus.SUCCEEDED.value,
                    paid_at=datetime.fromtimestamp(invoice['status_transitions']['paid_at'])
                )
                
                db.add(payment)
                
                # Reset usage counters for new billing period
                await StripeService._reset_usage_counters(db, user)
                
                await db.commit()
                logger.info(f"Payment succeeded for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")
    
    @staticmethod
    async def _handle_payment_failed(db: AsyncSession, invoice: Dict[str, Any]):
        """Handle failed payment."""
        try:
            customer_id = invoice['customer']
            
            # Find user
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Create payment record
                payment = Payment(
                    user_id=user.id,
                    stripe_payment_intent_id=invoice['payment_intent'],
                    stripe_customer_id=customer_id,
                    amount=invoice['amount_due'] / 100,  # Convert from cents
                    currency=invoice['currency'],
                    status=PaymentStatus.FAILED.value,
                    failed_at=datetime.utcnow()
                )
                
                db.add(payment)
                await db.commit()
                logger.info(f"Payment failed for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling payment failed: {e}")
    
    @staticmethod
    async def _handle_checkout_completed(db: AsyncSession, session: Dict[str, Any]):
        """Handle completed checkout session."""
        try:
            customer_id = session['customer']
            subscription_id = session['subscription']
            
            # Find user
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user and subscription_id:
                # Get subscription details to update user
                subscription = stripe.Subscription.retrieve(subscription_id)
                
                user.subscription_id = subscription.id
                user.subscription_status = subscription.status
                user.subscription_current_period_end = datetime.fromtimestamp(
                    subscription.current_period_end
                )
                
                # Update tier based on subscription
                await StripeService._update_user_tier_from_subscription(db, user, subscription)
                
                await db.commit()
                logger.info(f"Checkout completed for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling checkout completed: {e}")
    
    @staticmethod
    async def _update_user_tier_from_subscription(db: AsyncSession, user: User, subscription):
        """Update user tier based on Stripe subscription."""
        try:
            # Get the price ID from subscription
            if subscription.items and subscription.items.data:
                price_id = subscription.items.data[0].price.id
                
                # Find subscription plan by price ID
                result = await db.execute(
                    select(SubscriptionPlan).where(SubscriptionPlan.stripe_price_id == price_id)
                )
                plan = result.scalar_one_or_none()
                
                if plan:
                    user.subscription_tier = plan.plan_type
                    logger.info(f"Updated user {user.id} to tier: {plan.plan_type}")
        except Exception as e:
            logger.error(f"Error updating user tier: {e}")
    
    @staticmethod
    async def _reset_usage_counters(db: AsyncSession, user: User):
        """Reset user usage counters for new billing period."""
        try:
            user.current_month_conversations = 0
            user.current_month_file_uploads = 0
            user.current_knowledge_base_size = 0
            user.last_usage_reset = datetime.utcnow()
            
            logger.info(f"Reset usage counters for user {user.id}")
        except Exception as e:
            logger.error(f"Error resetting usage counters: {e}") 