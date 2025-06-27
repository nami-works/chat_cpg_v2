#!/usr/bin/env python3
"""
Docker MVP Setup Script for ChatCPG v2
This script prepares Docker environment and runs MVP setup inside containers.
"""
import os
import subprocess
import sys
from pathlib import Path

def create_env_file():
    """Create .env file for Docker with MVP settings"""
    env_content = """# ChatCPG v2 MVP Environment Variables
# Generated for Docker MVP testing

# Required API Keys (MVP needs at least one)
OPENAI_API_KEY=your-openai-api-key-here
GROQ_API_KEY=your-groq-api-key-here

# Optional API Keys (MVP doesn't use these but they're in docker-compose)
CURSOR_API_KEY=not-needed-for-mvp
GOOGLE_CLIENT_ID=not-needed-for-mvp
GOOGLE_CLIENT_SECRET=not-needed-for-mvp
STRIPE_SECRET_KEY=not-needed-for-mvp
STRIPE_PUBLISHABLE_KEY=not-needed-for-mvp
PINECONE_API_KEY=not-needed-for-mvp
PINECONE_ENVIRONMENT=not-needed-for-mvp

# Database Configuration (handled by Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@postgres:5432/chat_cpg_v2
REDIS_URL=redis://redis:6379

# Application Settings
SECRET_KEY=mvp-super-secret-key-for-development-only
ACCESS_TOKEN_EXPIRE_MINUTES=1440
"""
    
    env_path = Path(".env")
    if env_path.exists():
        print("📝 .env file already exists")
        response = input("Do you want to overwrite it for MVP? (y/N): ")
        if response.lower() != 'y':
            print("Using existing .env file...")
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file for MVP")
    print("⚠️  IMPORTANT: Add your actual API keys to .env file!")
    print("   At minimum, set OPENAI_API_KEY or GROQ_API_KEY")


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def main():
    """Main Docker MVP setup function"""
    print("🐳 ChatCPG v2 MVP - Docker Setup")
    print("="*50)
    
    # Step 1: Create .env file
    print("\n📋 Step 1: Environment Configuration")
    create_env_file()
    
    # Step 2: Check Docker
    print("\n📋 Step 2: Docker Check")
    if not run_command("docker --version", "Checking Docker installation"):
        print("❌ Docker is not installed or not running")
        print("Please install Docker and try again")
        sys.exit(1)
    
    if not run_command("docker-compose --version", "Checking Docker Compose"):
        print("❌ Docker Compose is not available")
        sys.exit(1)
    
    # Step 3: Clean up any existing containers
    print("\n📋 Step 3: Cleanup")
    run_command("docker-compose down", "Stopping existing containers")
    
    # Step 4: Build and start services
    print("\n📋 Step 4: Building and Starting Services")
    if not run_command("docker-compose up --build -d postgres redis", "Starting database services"):
        print("❌ Failed to start database services")
        sys.exit(1)
    
    # Wait for databases to be ready
    print("⏳ Waiting for databases to initialize...")
    if not run_command("docker-compose exec postgres pg_isready -U postgres", "Checking PostgreSQL"):
        print("⚠️  PostgreSQL might still be starting...")
    
    # Step 5: Build and start backend
    print("\n📋 Step 5: Starting Backend")
    if not run_command("docker-compose up --build -d backend", "Building and starting backend"):
        print("❌ Failed to start backend")
        sys.exit(1)
    
    # Step 6: Run MVP setup inside container
    print("\n📋 Step 6: MVP Initialization")
    setup_command = "docker-compose exec backend python setup_mvp.py"
    if not run_command(setup_command, "Running MVP setup in container"):
        print("⚠️  MVP setup had issues, but container might still work")
    
    # Step 7: Start frontend
    print("\n📋 Step 7: Starting Frontend")
    if not run_command("docker-compose up --build -d frontend", "Building and starting frontend"):
        print("❌ Failed to start frontend")
        print("Backend is still available at http://localhost:8000")
    
    # Final status
    print("\n" + "="*50)
    print("🎉 Docker MVP Setup Complete!")
    print("\n📍 Services Running:")
    print("   🔧 Backend API: http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("   🌐 Frontend: http://localhost:3000")
    print("   💾 PostgreSQL: localhost:5432")
    print("   ⚡ Redis: localhost:6379")
    
    print("\n🧪 Testing Commands:")
    print("   # Check service status")
    print("   docker-compose ps")
    print()
    print("   # View backend logs")
    print("   docker-compose logs -f backend")
    print()
    print("   # Access backend container")
    print("   docker-compose exec backend bash")
    print()
    print("   # Stop all services")
    print("   docker-compose down")
    
    print("\n⚠️  Remember to:")
    print("   1. Add your API keys to .env file")
    print("   2. Restart backend after updating .env:")
    print("      docker-compose restart backend")


if __name__ == "__main__":
    main() 