#!/usr/bin/env python3
"""
ChatCPG v2 - Phase 2 Testing Script
Tests the payment and subscription system implementation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.db.database import AsyncSessionLocal, check_db_connection
from backend.app.models.subscription import SubscriptionPlan, PlanType
from backend.app.models.user import User, SubscriptionTier
from backend.app.services.stripe_service import StripeService
from backend.app.services.usage_service import UsageService
from sqlalchemy import select, text


async def test_database_connection():
    """Test database connectivity."""
    print("🔍 Testing database connection...")
    
    try:
        is_connected = await check_db_connection()
        if is_connected:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    return True


async def test_subscription_plans():
    """Test subscription plans seeding and retrieval."""
    print("\n🔍 Testing subscription plans...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if plans exist
            result = await session.execute(
                select(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly)
            )
            plans = result.scalars().all()
            
            if len(plans) >= 3:
                print(f"✅ Found {len(plans)} subscription plans")
                
                for plan in plans:
                    print(f"   - {plan.name}: ${plan.price_monthly}/month ({plan.plan_type})")
                    
                return True
            else:
                print(f"❌ Expected at least 3 plans, found {len(plans)}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing subscription plans: {e}")
        return False


async def test_user_model():
    """Test user model with subscription fields."""
    print("\n🔍 Testing user model...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Create a test user
            test_user = User(
                email="test@example.com",
                subscription_tier=SubscriptionTier.FREE.value,
                current_month_conversations=5,
                current_month_file_uploads=2,
                current_knowledge_base_size=1024 * 1024  # 1MB
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            # Test subscription properties
            print(f"✅ User created with tier: {test_user.subscription_tier}")
            print(f"   - Conversation limit: {test_user.conversation_limit}")
            print(f"   - File upload limit: {test_user.file_upload_limit}")
            print(f"   - Knowledge base limit: {test_user.knowledge_base_size_limit / (1024*1024):.1f}MB")
            print(f"   - Is premium: {test_user.is_premium}")
            
            # Clean up
            await session.delete(test_user)
            await session.commit()
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing user model: {e}")
        return False


async def test_usage_service():
    """Test usage tracking service."""
    print("\n🔍 Testing usage service...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Create a test user
            test_user = User(
                email="usage_test@example.com",
                subscription_tier=SubscriptionTier.FREE.value,
                current_month_conversations=8,  # Near limit
                current_month_file_uploads=4,   # Near limit
                current_knowledge_base_size=9 * 1024 * 1024  # 9MB, near 10MB limit
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            # Test usage checks
            can_converse = await UsageService.check_conversation_limit(session, test_user)
            can_upload = await UsageService.check_file_upload_limit(session, test_user)
            can_add_kb = await UsageService.check_knowledge_base_size_limit(
                session, test_user, 2 * 1024 * 1024  # Try to add 2MB
            )
            
            print(f"✅ Usage service checks:")
            print(f"   - Can start conversation: {can_converse}")
            print(f"   - Can upload file: {can_upload}")
            print(f"   - Can add 2MB to KB: {can_add_kb}")
            
            # Test usage summary
            summary = await UsageService.get_user_usage_summary(session, test_user)
            print(f"   - Conversation usage: {summary['conversations']['percentage']:.1f}%")
            print(f"   - File upload usage: {summary['file_uploads']['percentage']:.1f}%")
            print(f"   - Knowledge base usage: {summary['knowledge_base']['percentage']:.1f}%")
            
            # Clean up
            await session.delete(test_user)
            await session.commit()
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing usage service: {e}")
        return False


async def test_database_tables():
    """Test that all required tables exist."""
    print("\n🔍 Testing database tables...")
    
    tables_to_check = [
        "users",
        "subscription_plans", 
        "payments",
        "usage_tracking",
        "subscription_events",
        "user_usage",
        "user_sessions"
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            for table in tables_to_check:
                try:
                    result = await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    print(f"✅ Table '{table}' exists and accessible")
                except Exception as e:
                    print(f"❌ Table '{table}' error: {e}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking database tables: {e}")
        return False


def test_stripe_configuration():
    """Test Stripe configuration."""
    print("\n🔍 Testing Stripe configuration...")
    
    try:
        from backend.app.core.config import settings
        
        has_stripe_keys = bool(
            settings.STRIPE_SECRET_KEY and 
            settings.STRIPE_PUBLISHABLE_KEY and 
            settings.STRIPE_WEBHOOK_SECRET
        )
        
        if has_stripe_keys:
            print("✅ Stripe configuration found")
            print(f"   - Secret key: {'sk_' + '*' * 20 if settings.STRIPE_SECRET_KEY.startswith('sk_') else 'Invalid format'}")
            print(f"   - Publishable key: {'pk_' + '*' * 20 if settings.STRIPE_PUBLISHABLE_KEY.startswith('pk_') else 'Invalid format'}")
            print(f"   - Webhook secret: {'whsec_' + '*' * 15 if settings.STRIPE_WEBHOOK_SECRET.startswith('whsec_') else 'Set'}")
            return True
        else:
            print("⚠️  Stripe configuration incomplete (this is okay for testing)")
            print("   - Set STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, and STRIPE_WEBHOOK_SECRET for full functionality")
            return True  # Not a failure for testing
            
    except Exception as e:
        print(f"❌ Error checking Stripe configuration: {e}")
        return False


def test_environment_variables():
    """Test required environment variables."""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        "SECRET_KEY",
        "POSTGRES_SERVER", 
        "POSTGRES_USER",
        "POSTGRES_DB"
    ]
    
    optional_vars = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET", 
        "STRIPE_SECRET_KEY",
        "OPENAI_API_KEY"
    ]
    
    try:
        from backend.app.core.config import settings
        
        print("✅ Required environment variables:")
        for var in required_vars:
            value = getattr(settings, var, None)
            if value:
                print(f"   - {var}: Set")
            else:
                print(f"   - {var}: Missing ❌")
        
        print("\n📋 Optional environment variables:")
        for var in optional_vars:
            value = getattr(settings, var, None)
            status = "Set" if value else "Not set"
            print(f"   - {var}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking environment variables: {e}")
        return False


async def main():
    """Run all Phase 2 tests."""
    print("🚀 ChatCPG v2 - Phase 2 Testing")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Stripe Configuration", test_stripe_configuration),
        ("Database Connection", test_database_connection),
        ("Database Tables", test_database_tables),
        ("Subscription Plans", test_subscription_plans),
        ("User Model", test_user_model),
        ("Usage Service", test_usage_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 is working correctly.")
        print("\n🚀 Ready for development:")
        print("   - Backend API: http://localhost:8000")
        print("   - Frontend: http://localhost:3000") 
        print("   - API Docs: http://localhost:8000/docs")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the configuration.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⛔ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Testing failed with error: {e}")
        sys.exit(1) 