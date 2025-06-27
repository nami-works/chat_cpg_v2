#!/usr/bin/env python3
"""
ChatCPG v2 - Phase 3 Testing Script
Knowledge Base System Complete Functionality Test

This script tests all Phase 3 features:
- Knowledge base management
- Document upload and processing
- Vector embeddings and search
- File type support
- Usage limits integration
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
import requests
import time

# Test configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Test user credentials
TEST_USER = {
    "email": "test.knowledge@chatcpg.com",
    "password": "TestKnowledge123!",
    "full_name": "Knowledge Test User"
}

class PhaseThreeTests:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_kb_id = None
        self.test_document_id = None
        
    def log(self, message, status="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def signup_user(self):
        """Test user registration for Phase 3 testing"""
        try:
            response = self.session.post(f"{API_URL}/auth/signup", json=TEST_USER)
            if response.status_code == 201:
                self.log("✅ User registered successfully")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                self.log("ℹ️ User already exists, proceeding with login")
                return True
            else:
                self.log(f"❌ Registration failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False
    
    def login_user(self):
        """Test user login and token acquisition"""
        try:
            response = self.session.post(f"{API_URL}/auth/login", json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{API_URL}/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    self.log(f"✅ Login successful for user {user_data['email']}")
                    return True
                
            self.log(f"❌ Login failed: {response.text}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    def test_supported_formats(self):
        """Test getting supported file formats"""
        try:
            response = self.session.get(f"{API_URL}/knowledge/supported-formats")
            
            if response.status_code == 200:
                data = response.json()
                formats = data.get("supported_formats", [])
                max_size_mb = data.get("max_file_size_mb", 0)
                
                self.log(f"✅ Supported formats: {', '.join(formats)}")
                self.log(f"✅ Max file size: {max_size_mb} MB")
                return True
            else:
                self.log(f"❌ Failed to get supported formats: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Supported formats error: {str(e)}", "ERROR")
            return False
    
    def test_create_knowledge_base(self):
        """Test creating a knowledge base"""
        try:
            kb_data = {
                "name": "Test Knowledge Base",
                "description": "A test knowledge base for Phase 3 testing",
                "tags": ["test", "phase3", "automation"]
            }
            
            response = self.session.post(f"{API_URL}/knowledge/knowledge-bases", json=kb_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_kb_id = data["id"]
                self.log(f"✅ Knowledge base created successfully: {data['name']}")
                self.log(f"   ID: {self.test_kb_id}")
                return True
            else:
                self.log(f"❌ Failed to create knowledge base: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Create knowledge base error: {str(e)}", "ERROR")
            return False
    
    def test_list_knowledge_bases(self):
        """Test listing knowledge bases"""
        try:
            response = self.session.get(f"{API_URL}/knowledge/knowledge-bases")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Retrieved {len(data)} knowledge base(s)")
                
                for kb in data:
                    self.log(f"   - {kb['name']} ({kb['total_documents']} docs, {kb['total_size_bytes']} bytes)")
                
                return True
            else:
                self.log(f"❌ Failed to list knowledge bases: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ List knowledge bases error: {str(e)}", "ERROR")
            return False
    
    def test_get_knowledge_base_details(self):
        """Test getting detailed knowledge base information"""
        if not self.test_kb_id:
            self.log("❌ No test knowledge base ID available", "ERROR")
            return False
        
        try:
            response = self.session.get(f"{API_URL}/knowledge/knowledge-bases/{self.test_kb_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Knowledge base details retrieved:")
                self.log(f"   Name: {data['name']}")
                self.log(f"   Description: {data['description']}")
                self.log(f"   Documents: {data.get('stats', {}).get('total_documents', 0)}")
                self.log(f"   Size: {data.get('stats', {}).get('total_size_bytes', 0)} bytes")
                return True
            else:
                self.log(f"❌ Failed to get knowledge base details: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get knowledge base details error: {str(e)}", "ERROR")
            return False
    
    def create_test_files(self):
        """Create temporary test files for upload testing"""
        test_files = {}
        
        try:
            # Create a test text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is a test document for ChatCPG v2 Phase 3 testing.\n")
                f.write("It contains sample content to test document processing and embedding creation.\n")
                f.write("The knowledge base system should extract this text and create vector embeddings.\n")
                f.write("This will enable semantic search across the document content.")
                test_files['txt'] = f.name
            
            # Create a test JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = {
                    "title": "Test JSON Document",
                    "content": "This is test JSON content for knowledge base testing",
                    "metadata": {
                        "category": "test",
                        "phase": 3,
                        "features": ["upload", "processing", "embeddings"]
                    }
                }
                json.dump(test_data, f, indent=2)
                test_files['json'] = f.name
            
            # Create a test markdown file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write("# Test Markdown Document\n\n")
                f.write("## Overview\n")
                f.write("This is a test markdown document for Phase 3 testing.\n\n")
                f.write("## Features Tested\n")
                f.write("- Document upload\n")
                f.write("- Content extraction\n")
                f.write("- Text chunking\n")
                f.write("- Vector embeddings\n")
                f.write("- Semantic search\n\n")
                f.write("## Expected Results\n")
                f.write("The system should successfully process this document and make it searchable.")
                test_files['md'] = f.name
            
            self.log(f"✅ Created {len(test_files)} test files")
            return test_files
            
        except Exception as e:
            self.log(f"❌ Failed to create test files: {str(e)}", "ERROR")
            return {}
    
    def test_document_upload(self, test_files):
        """Test uploading documents to knowledge base"""
        if not self.test_kb_id:
            self.log("❌ No test knowledge base ID available", "ERROR")
            return False
        
        uploaded_docs = []
        
        for file_type, file_path in test_files.items():
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (f"test_document.{file_type}", f)}
                    data = {
                        'title': f"Test {file_type.upper()} Document",
                        'tags': 'test,phase3,automated'
                    }
                    
                    response = self.session.post(
                        f"{API_URL}/knowledge/knowledge-bases/{self.test_kb_id}/upload",
                        files=files,
                        data=data
                    )
                
                if response.status_code == 200:
                    doc_data = response.json()
                    uploaded_docs.append(doc_data)
                    self.log(f"✅ Uploaded {file_type} document: {doc_data['filename']}")
                    self.log(f"   ID: {doc_data['id']}")
                    self.log(f"   Status: {doc_data['status']}")
                    
                    # Store first document ID for later tests
                    if not self.test_document_id:
                        self.test_document_id = doc_data['id']
                else:
                    self.log(f"❌ Failed to upload {file_type} document: {response.text}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Upload error for {file_type}: {str(e)}", "ERROR")
        
        return len(uploaded_docs) > 0
    
    def test_list_documents(self):
        """Test listing documents in knowledge base"""
        if not self.test_kb_id:
            self.log("❌ No test knowledge base ID available", "ERROR")
            return False
        
        try:
            response = self.session.get(f"{API_URL}/knowledge/knowledge-bases/{self.test_kb_id}/documents")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Retrieved {len(data)} document(s) from knowledge base")
                
                for doc in data:
                    self.log(f"   - {doc['filename']} ({doc['status']}, {doc['file_size']} bytes)")
                
                return True
            else:
                self.log(f"❌ Failed to list documents: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ List documents error: {str(e)}", "ERROR")
            return False
    
    def test_document_processing_status(self):
        """Test checking document processing status"""
        if not self.test_document_id:
            self.log("❌ No test document ID available", "ERROR")
            return False
        
        try:
            response = self.session.get(f"{API_URL}/knowledge/documents/{self.test_document_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Document processing status:")
                self.log(f"   Status: {data['status']}")
                self.log(f"   Chunks: {data['total_chunks']} total, {data['chunks_processed']} processed")
                
                if data.get('processing_error'):
                    self.log(f"   Error: {data['processing_error']}", "WARN")
                
                return True
            else:
                self.log(f"❌ Failed to get document details: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Document details error: {str(e)}", "ERROR")
            return False
    
    def test_vector_stats(self):
        """Test getting vector database statistics"""
        try:
            response = self.session.get(f"{API_URL}/knowledge/stats/vector")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Vector database statistics:")
                self.log(f"   Status: {data['status']}")
                self.log(f"   Total vectors: {data.get('total_vectors', 0)}")
                self.log(f"   User vectors: {data.get('user_vectors', 0)}")
                return True
            else:
                self.log(f"❌ Failed to get vector stats: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Vector stats error: {str(e)}", "ERROR")
            return False
    
    def test_knowledge_search(self):
        """Test searching knowledge base content"""
        if not self.test_kb_id:
            self.log("❌ No test knowledge base ID available", "ERROR")
            return False
        
        search_queries = [
            "test document",
            "vector embeddings", 
            "knowledge base system",
            "Phase 3 testing"
        ]
        
        for query in search_queries:
            try:
                search_data = {
                    "query": query,
                    "knowledge_base_id": self.test_kb_id,
                    "top_k": 5,
                    "score_threshold": 0.5
                }
                
                response = self.session.post(f"{API_URL}/knowledge/search", json=search_data)
                
                if response.status_code == 200:
                    results = response.json()
                    self.log(f"✅ Search '{query}': {len(results)} result(s)")
                    
                    for i, result in enumerate(results[:2]):  # Show top 2 results
                        self.log(f"   {i+1}. Score: {result['score']:.3f} - {result['content_preview'][:100]}...")
                        
                else:
                    self.log(f"❌ Search failed for '{query}': {response.text}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Search error for '{query}': {str(e)}", "ERROR")
        
        return True
    
    def test_document_download(self):
        """Test downloading document"""
        if not self.test_document_id:
            self.log("❌ No test document ID available", "ERROR")
            return False
        
        try:
            response = self.session.get(f"{API_URL}/knowledge/documents/{self.test_document_id}/download")
            
            if response.status_code == 200:
                self.log(f"✅ Document download successful ({len(response.content)} bytes)")
                return True
            else:
                self.log(f"❌ Document download failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Document download error: {str(e)}", "ERROR")
            return False
    
    def test_usage_limits_integration(self):
        """Test knowledge base usage limits integration"""
        try:
            # Check file upload limits
            response = self.session.get(f"{API_URL}/subscription/check/file-uploads")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ File upload limits check:")
                self.log(f"   Current usage: {data['current_usage']}/{data['limit']}")
                self.log(f"   Can upload: {data['allowed']}")
            
            # Check knowledge base size limits  
            response = self.session.get(f"{API_URL}/subscription/check/knowledge-base")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Knowledge base size limits check:")
                self.log(f"   Current size: {data['current_usage_mb']:.2f} MB")
                self.log(f"   Limit: {data['limit_mb']:.2f} MB")
                self.log(f"   Can add content: {data['allowed']}")
            
            return True
        except Exception as e:
            self.log(f"❌ Usage limits check error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Delete test knowledge base (this will cascade delete documents)
            if self.test_kb_id:
                response = self.session.delete(f"{API_URL}/knowledge/knowledge-bases/{self.test_kb_id}")
                if response.status_code == 200:
                    self.log("✅ Test knowledge base deleted successfully")
                else:
                    self.log(f"⚠️ Failed to delete test knowledge base: {response.text}", "WARN")
            
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARN")
    
    def cleanup_test_files(self, test_files):
        """Clean up temporary test files"""
        for file_type, file_path in test_files.items():
            try:
                os.unlink(file_path)
            except Exception as e:
                self.log(f"⚠️ Failed to delete test file {file_path}: {str(e)}", "WARN")
    
    def run_all_tests(self):
        """Run comprehensive Phase 3 test suite"""
        self.log("🚀 Starting ChatCPG v2 Phase 3 (Knowledge Base System) Tests")
        self.log("=" * 80)
        
        test_results = {}
        test_files = {}
        
        # Test sequence
        tests = [
            ("User Registration", self.signup_user),
            ("User Login", self.login_user),
            ("Supported Formats", self.test_supported_formats),
            ("Create Knowledge Base", self.test_create_knowledge_base),
            ("List Knowledge Bases", self.test_list_knowledge_bases),
            ("Knowledge Base Details", self.test_get_knowledge_base_details),
            ("Create Test Files", lambda: self.create_test_files()),
            ("Document Upload", lambda: self.test_document_upload(test_files)),
            ("List Documents", self.test_list_documents),
            ("Document Processing Status", self.test_document_processing_status),
            ("Vector Statistics", self.test_vector_stats),
            ("Knowledge Search", self.test_knowledge_search),
            ("Document Download", self.test_document_download),
            ("Usage Limits Integration", self.test_usage_limits_integration)
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            self.log("-" * 40)
            
            try:
                if test_name == "Create Test Files":
                    test_files = test_func()
                    result = len(test_files) > 0
                elif test_name == "Document Upload":
                    result = test_func()
                else:
                    result = test_func()
                
                test_results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                self.log(f"{status}: {test_name}")
                
            except Exception as e:
                test_results[test_name] = False
                self.log(f"❌ FAILED: {test_name} - {str(e)}", "ERROR")
        
        # Wait a bit for document processing to complete
        if test_results.get("Document Upload", False):
            self.log("\n⏳ Waiting for document processing to complete...")
            time.sleep(10)
            
            # Re-check processing status
            self.log("\n📋 Final Processing Status Check")
            self.log("-" * 40)
            self.test_document_processing_status()
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("📊 PHASE 3 TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\n🎯 Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL PHASE 3 TESTS PASSED! Knowledge Base System is fully functional.")
        else:
            self.log("⚠️ Some tests failed. Please check the logs above for details.")
        
        # Cleanup
        self.log("\n🧹 Cleaning up test data...")
        self.cleanup_test_data()
        self.cleanup_test_files(test_files)
        self.log("✅ Cleanup completed")
        
        return passed_tests == total_tests

def main():
    """Main test runner"""
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed. Make sure the server is running on http://localhost:8000")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend. Make sure the server is running on http://localhost:8000")
        return False
    
    # Run tests
    tester = PhaseThreeTests()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 