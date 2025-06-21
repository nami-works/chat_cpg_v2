#!/usr/bin/env python3
"""
Test Setup Script for ChatCPG v2 AI Development System
This script verifies that all components are properly configured.
"""

import os
import json
import sys
from pathlib import Path

def test_development_plan():
    """Test if development plan exists and is valid"""
    print("🔍 Testing development plan...")
    
    plan_file = Path("../development_plan.json")
    if not plan_file.exists():
        print("❌ development_plan.json not found")
        return False
    
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)
        
        required_keys = ['project', 'version', 'phases', 'current_task']
        missing_keys = [key for key in required_keys if key not in plan]
        
        if missing_keys:
            print(f"❌ Missing keys in development plan: {missing_keys}")
            return False
        
        print(f"✅ Development plan loaded successfully")
        print(f"   Project: {plan['project']}")
        print(f"   Version: {plan['version']}")
        print(f"   Phases: {len(plan['phases'])}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading development plan: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment...")
    
    # Check for .env file
    env_file = Path("../.env")
    template_file = Path("../env_template.txt")
    
    if not env_file.exists():
        if template_file.exists():
            print("⚠️  .env file not found, but template exists")
            print("   Copy env_template.txt to .env and configure your API keys")
        else:
            print("❌ Neither .env nor env_template.txt found")
            return False
    else:
        print("✅ .env file found")
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("⚠️  OPENAI_API_KEY not set in environment")
    
    return True

def test_dependencies():
    """Test Python dependencies"""
    print("\n🔍 Testing dependencies...")
    
    required_packages = ['openai', 'json', 'pathlib', 'datetime']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} not available")
    
    if missing_packages:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def test_file_structure():
    """Test project file structure"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "../development_plan.json",
        "../README.md",
        "../.github/workflows/ai_development.yml",
        "ai_developer.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ {file_path} not found")
        else:
            print(f"✅ {file_path} exists")
    
    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    
    return True

def test_ai_developer():
    """Test AI Developer script"""
    print("\n🔍 Testing AI Developer script...")
    
    try:
        # Import without running
        sys.path.append('.')
        from ai_developer import AIDeveloper
        
        print("✅ AIDeveloper class can be imported")
        
        # Test initialization (without OpenAI key)
        try:
            developer = AIDeveloper(project_root="..")
            print("✅ AIDeveloper can be initialized")
            
            # Test status report
            status = developer.status_report()
            print(f"✅ Status report generated: {status}")
            
            return True
        except Exception as e:
            print(f"⚠️  AIDeveloper initialization failed: {e}")
            print("   This is expected if OPENAI_API_KEY is not set")
            return True
    
    except ImportError as e:
        print(f"❌ Cannot import AIDeveloper: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 ChatCPG v2 Setup Test\n")
    
    tests = [
        test_development_plan,
        test_environment,
        test_dependencies,
        test_file_structure,
        test_ai_developer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for AI development.")
        print("\nNext steps:")
        print("1. Set up your OpenAI API key in .env")
        print("2. Push to GitHub and set up repository secrets")
        print("3. Enable GitHub Actions")
        print("4. Watch the AI develop your application!")
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 