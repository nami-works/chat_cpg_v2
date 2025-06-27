#!/usr/bin/env python3
"""
Script to seed subscription plans in ChatCPG v2 database
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.database import AsyncSessionLocal
from app.models.subscription import SubscriptionPlan, PlanType
from app.core.config import settings
from sqlalchemy import select


async def create_subscription_plans():
    """Create default subscription plans"""
    
    plans_data = [
        {
            "name": "Free",
            "plan_type": PlanType.FREE,
            "price_monthly": 0.0,
            "price_yearly": None,
            "currency": "USD",
            "conversations_limit": settings.FREE_TIER_CONVERSATIONS,
            "file_uploads_limit": settings.FREE_TIER_FILE_UPLOADS,
            "knowledge_base_size_limit": settings.FREE_TIER_KNOWLEDGE_BASE_SIZE,
            "description": "Perfect for getting started with basic CPG assistance",
            "is_popular": False,
            "features": [
                f"{settings.FREE_TIER_CONVERSATIONS} conversations per month",
                f"{settings.FREE_TIER_FILE_UPLOADS} file uploads per month",
                f"{settings.FREE_TIER_KNOWLEDGE_BASE_SIZE // (1024*1024)}MB knowledge base storage",
                "Basic AI assistance",
                "Email support"
            ]
        },
        {
            "name": "Pro",
            "plan_type": PlanType.PRO,
            "price_monthly": 29.99,
            "price_yearly": 299.99,  # 2 months free
            "currency": "USD",
            "conversations_limit": settings.PRO_TIER_CONVERSATIONS,
            "file_uploads_limit": settings.PRO_TIER_FILE_UPLOADS,
            "knowledge_base_size_limit": settings.PRO_TIER_KNOWLEDGE_BASE_SIZE,
            "description": "Advanced features for growing CPG businesses",
            "is_popular": True,
            "features": [
                f"{settings.PRO_TIER_CONVERSATIONS} conversations per month",
                f"{settings.PRO_TIER_FILE_UPLOADS} file uploads per month",
                f"{settings.PRO_TIER_KNOWLEDGE_BASE_SIZE // (1024*1024)}MB knowledge base storage",
                "Advanced AI models",
                "Brand knowledge base",
                "Content generation",
                "Priority support",
                "Advanced analytics"
            ]
        },
        {
            "name": "Enterprise",
            "plan_type": PlanType.ENTERPRISE,
            "price_monthly": 99.99,
            "price_yearly": 999.99,  # 2 months free
            "currency": "USD",
            "conversations_limit": settings.ENTERPRISE_TIER_CONVERSATIONS,
            "file_uploads_limit": settings.ENTERPRISE_TIER_FILE_UPLOADS,
            "knowledge_base_size_limit": settings.ENTERPRISE_TIER_KNOWLEDGE_BASE_SIZE,
            "description": "Complete solution for enterprise CPG companies",
            "is_popular": False,
            "features": [
                "Unlimited conversations",
                "Unlimited file uploads", 
                f"{settings.ENTERPRISE_TIER_KNOWLEDGE_BASE_SIZE // (1024*1024*1024)}GB knowledge base storage",
                "Premium AI models",
                "Custom brand training",
                "Automated solution development",
                "Custom integrations",
                "Dedicated support manager",
                "Custom analytics & reporting",
                "White-label options"
            ]
        }
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 Seeding subscription plans...")
            
            for plan_data in plans_data:
                # Check if plan already exists
                result = await session.execute(
                    select(SubscriptionPlan).where(
                        SubscriptionPlan.plan_type == plan_data["plan_type"]
                    )
                )
                existing_plan = result.scalar_one_or_none()
                
                if existing_plan:
                    print(f"⚠️  Plan '{plan_data['name']}' already exists. Updating...")
                    
                    # Update existing plan
                    for key, value in plan_data.items():
                        if hasattr(existing_plan, key):
                            setattr(existing_plan, key, value)
                    
                    existing_plan.updated_at = datetime.utcnow()
                    
                else:
                    print(f"✅ Creating plan '{plan_data['name']}'...")
                    
                    # Create new plan
                    new_plan = SubscriptionPlan(**plan_data)
                    session.add(new_plan)
                
            await session.commit()
            
            # Display created plans
            result = await session.execute(
                select(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly)
            )
            plans = result.scalars().all()
            
            print(f"\n📋 Subscription Plans Summary:")
            print("=" * 50)
            
            for plan in plans:
                print(f"""
Plan: {plan.name} ({plan.plan_type.value.upper()})
Price: ${plan.price_monthly}/month
Conversations: {plan.conversations_limit if plan.conversations_limit != -1 else 'Unlimited'}
File Uploads: {plan.file_uploads_limit if plan.file_uploads_limit != -1 else 'Unlimited'}
Knowledge Base: {plan.knowledge_base_size_limit // (1024*1024) if plan.knowledge_base_size_limit != -1 else 'Unlimited'}MB
Features: {len(plan.features)} features
Popular: {'Yes' if plan.is_popular else 'No'}
""")
            
            print("✅ Subscription plans seeded successfully!")
            
        except Exception as e:
            print(f"❌ Error seeding subscription plans: {e}")
            await session.rollback()
            raise


async def verify_plans():
    """Verify that plans were created correctly"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(SubscriptionPlan))
            plans = result.scalars().all()
            
            print(f"\n🔍 Verification: Found {len(plans)} subscription plans")
            
            # Check that we have all required plan types
            plan_types = {plan.plan_type for plan in plans}
            required_types = {PlanType.FREE, PlanType.PRO, PlanType.ENTERPRISE}
            
            if plan_types == required_types:
                print("✅ All required plan types are present")
            else:
                missing = required_types - plan_types
                print(f"❌ Missing plan types: {missing}")
                return False
                
            # Check that limits are correct
            for plan in plans:
                if plan.plan_type == PlanType.FREE:
                    assert plan.conversations_limit == settings.FREE_TIER_CONVERSATIONS
                    assert plan.file_uploads_limit == settings.FREE_TIER_FILE_UPLOADS
                    assert plan.knowledge_base_size_limit == settings.FREE_TIER_KNOWLEDGE_BASE_SIZE
                elif plan.plan_type == PlanType.PRO:
                    assert plan.conversations_limit == settings.PRO_TIER_CONVERSATIONS
                    assert plan.file_uploads_limit == settings.PRO_TIER_FILE_UPLOADS
                    assert plan.knowledge_base_size_limit == settings.PRO_TIER_KNOWLEDGE_BASE_SIZE
                elif plan.plan_type == PlanType.ENTERPRISE:
                    assert plan.conversations_limit == settings.ENTERPRISE_TIER_CONVERSATIONS
                    assert plan.file_uploads_limit == settings.ENTERPRISE_TIER_FILE_UPLOADS
                    assert plan.knowledge_base_size_limit == settings.ENTERPRISE_TIER_KNOWLEDGE_BASE_SIZE
            
            print("✅ All plan limits are correctly configured")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False


async def main():
    """Main function"""
    print("🚀 ChatCPG v2 - Subscription Plans Seeder")
    print("=" * 50)
    
    try:
        await create_subscription_plans()
        await verify_plans()
        
        print("\n✅ Subscription plans setup completed successfully!")
        print("🎉 Phase 2 (Payment & Subscription System) is ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 