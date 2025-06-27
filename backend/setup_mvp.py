#!/usr/bin/env python3
"""
MVP Setup Script for ChatCPG v2
This script prepares the database and creates the GE Beauty brand for MVP testing.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def setup_mvp():
    """Setup MVP environment"""
    print("🚀 Setting up ChatCPG v2 MVP...")
    
    try:
        # Step 1: Initialize database
        print("\n📊 Step 1: Initializing database...")
        from app.db.database import init_db
        await init_db()
        print("✅ Database initialized successfully!")
        
        # Step 2: Create GE Beauty brand
        print("\n🏷️  Step 2: Creating GE Beauty brand...")
        from create_brands import create_ge_beauty_brand
        brand = create_ge_beauty_brand()
        print(f"✅ Brand created: {brand.name} (ID: {brand.id})")
        
        # Step 3: Display MVP status
        print(f"""
🎉 MVP Setup Complete!

📋 What's ready:
   ✅ Database initialized
   ✅ Authentication system (signup/login)
   ✅ Basic AI chat functionality
   ✅ GE Beauty brand loaded (@{brand.slug})
   
🚀 Next steps:
   1. Activate the virtual environment: C:\\venvs\\chat_cpg_v2
   2. Start the backend: python -m uvicorn app.main:app --reload
   3. Access API docs at: http://localhost:8000/docs
   4. Start the frontend and test chat with @gebeauty context
   
🔧 MVP Features Available:
   • User registration and login
   • Create chat conversations
   • Send messages with AI responses
   • Brand context for GE Beauty
   • Basic conversation management
   
❌ Features Disabled (preserved for later):
   • OAuth login (Google)
   • Password reset
   • Advanced content creation
   • Subscription management
   • File uploads
   • Knowledge base management
        """)
        
    except Exception as e:
        print(f"\n❌ Error during MVP setup: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure the virtual environment is activated")
        print("   2. Check database connection settings")
        print("   3. Verify all dependencies are installed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_mvp()) 