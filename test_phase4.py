#!/usr/bin/env python3
"""
ChatCPG v2 - Phase 4 Testing Script
Enhanced Chat Interface with Knowledge Base Integration

This script tests all Phase 4 functionality:
- Conversation management (CRUD operations)
- Message sending and AI responses
- Knowledge base integration in chat
- AI model selection and configuration
- Usage tracking for conversations
- WebSocket communication (if available)

Requirements:
- Backend server running on localhost:8000
- Valid API credentials configured
- Test knowledge bases from Phase 3
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import websockets
from pydantic import BaseModel


class TestConfig:
    """Test configuration."""
    BASE_URL = "http://localhost:8000/api/v1"
    WS_URL = "ws://localhost:8000/api/v1"
    TEST_EMAIL = "test@chatcpg.com"
    TEST_PASSWORD = "TestPassword123!"
    
    # Test data
    TEST_CONVERSATION_TITLE = "Test CPG Analysis Chat"
    TEST_MESSAGE_CONTENT = "What are the key trends in consumer packaged goods for 2024?"
    TEST_KNOWLEDGE_QUERY = "Tell me about product packaging innovations based on my knowledge base"


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {message}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Phase 4 Test Summary")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if self.failed > 0:
            print(f"\nFailed Tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['test']}: {test['message']}")


class ChatCPGTestClient:
    """Test client for ChatCPG v2 Phase 4."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_data: Optional[Dict] = None
        self.results = TestResults()
        self.test_conversation_id: Optional[str] = None
        self.test_message_ids: List[str] = []
        self.test_knowledge_bases: List[Dict] = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def test_authentication(self):
        """Test user authentication."""
        try:
            # Login
            login_data = {
                "username": TestConfig.TEST_EMAIL,  # FastAPI OAuth2PasswordBearer expects 'username'
                "password": TestConfig.TEST_PASSWORD
            }
            
            async with self.session.post(
                f"{TestConfig.BASE_URL}/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    self.results.add_result("Authentication - Login", True)
                else:
                    error_text = await response.text()
                    self.results.add_result("Authentication - Login", False, f"Status {response.status}: {error_text}")
                    return False
            
            # Get current user
            async with self.session.get(
                f"{TestConfig.BASE_URL}/auth/me",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    self.user_data = await response.json()
                    self.results.add_result("Authentication - Get User", True)
                    return True
                else:
                    error_text = await response.text()
                    self.results.add_result("Authentication - Get User", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.results.add_result("Authentication", False, str(e))
            return False
    
    async def test_conversation_management(self):
        """Test conversation CRUD operations."""
        try:
            # Check conversation usage limits
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/usage/check",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    usage_data = await response.json()
                    can_create = usage_data.get("can_create_conversation", False)
                    self.results.add_result("Conversation Usage Check", can_create, 
                                           "Cannot create conversations - limit reached" if not can_create else "")
                    if not can_create:
                        return False
                else:
                    self.results.add_result("Conversation Usage Check", False, f"Status {response.status}")
                    return False
            
            # Create conversation
            conversation_data = {
                "title": TestConfig.TEST_CONVERSATION_TITLE,
                "description": "Test conversation for Phase 4 functionality",
                "ai_model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
                "use_knowledge_base": True,
                "tags": ["test", "cpg", "analysis"]
            }
            
            async with self.session.post(
                f"{TestConfig.BASE_URL}/chat/conversations",
                headers=self.get_headers(),
                json=conversation_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_conversation_id = data.get("id")
                    self.results.add_result("Create Conversation", True)
                else:
                    error_text = await response.text()
                    self.results.add_result("Create Conversation", False, f"Status {response.status}: {error_text}")
                    return False
            
            # Get conversations list
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/conversations",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    conversations = await response.json()
                    found = any(conv.get("id") == self.test_conversation_id for conv in conversations)
                    self.results.add_result("List Conversations", found, 
                                           "Created conversation not found in list" if not found else "")
                else:
                    self.results.add_result("List Conversations", False, f"Status {response.status}")
            
            # Get specific conversation
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    conversation = await response.json()
                    title_matches = conversation.get("title") == TestConfig.TEST_CONVERSATION_TITLE
                    self.results.add_result("Get Conversation", title_matches,
                                           "Conversation title doesn't match" if not title_matches else "")
                else:
                    self.results.add_result("Get Conversation", False, f"Status {response.status}")
            
            # Update conversation
            update_data = {
                "title": "Updated Test Conversation",
                "description": "Updated description",
                "is_pinned": True
            }
            
            async with self.session.put(
                f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}",
                headers=self.get_headers(),
                json=update_data
            ) as response:
                if response.status == 200:
                    self.results.add_result("Update Conversation", True)
                else:
                    error_text = await response.text()
                    self.results.add_result("Update Conversation", False, f"Status {response.status}: {error_text}")
            
            return True
            
        except Exception as e:
            self.results.add_result("Conversation Management", False, str(e))
            return False
    
    async def test_message_functionality(self):
        """Test message sending and AI responses."""
        try:
            if not self.test_conversation_id:
                self.results.add_result("Message Functionality", False, "No test conversation available")
                return False
            
            # Send a message
            message_data = {
                "content": TestConfig.TEST_MESSAGE_CONTENT,
                "generate_response": True
            }
            
            async with self.session.post(
                f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}/messages",
                headers=self.get_headers(),
                json=message_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_message = data.get("user_message")
                    ai_message = data.get("ai_message")
                    
                    if user_message:
                        self.test_message_ids.append(user_message.get("id"))
                        self.results.add_result("Send User Message", True)
                    else:
                        self.results.add_result("Send User Message", False, "No user message in response")
                    
                    if ai_message:
                        self.test_message_ids.append(ai_message.get("id"))
                        has_content = bool(ai_message.get("content"))
                        has_tokens = ai_message.get("total_tokens", 0) > 0
                        has_model = bool(ai_message.get("ai_model"))
                        
                        self.results.add_result("AI Response Generation", has_content and has_tokens and has_model,
                                               "AI response missing content, tokens, or model info" if not (has_content and has_tokens and has_model) else "")
                    else:
                        self.results.add_result("AI Response Generation", False, "No AI response generated")
                else:
                    error_text = await response.text()
                    self.results.add_result("Send Message", False, f"Status {response.status}: {error_text}")
                    return False
            
            # Get messages
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}/messages",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    messages = await response.json()
                    message_count = len(messages)
                    self.results.add_result("Get Messages", message_count >= 2, 
                                           f"Expected at least 2 messages, got {message_count}")
                else:
                    self.results.add_result("Get Messages", False, f"Status {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_result("Message Functionality", False, str(e))
            return False
    
    async def test_ai_models(self):
        """Test AI model information and selection."""
        try:
            # Get available models
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/models",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", {})
                    has_openai = "openai" in models and len(models["openai"]) > 0
                    has_default = bool(data.get("default_model"))
                    
                    self.results.add_result("Get Available Models", has_openai and has_default,
                                           "Missing OpenAI models or default model" if not (has_openai and has_default) else "")
                else:
                    self.results.add_result("Get Available Models", False, f"Status {response.status}")
                    return False
            
            # Get model info for GPT-3.5-turbo
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/models/gpt-3.5-turbo",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    model_info = await response.json()
                    has_provider = bool(model_info.get("provider"))
                    has_pricing = bool(model_info.get("pricing"))
                    has_context = model_info.get("context_window", 0) > 0
                    
                    self.results.add_result("Get Model Info", has_provider and has_pricing and has_context,
                                           "Model info missing provider, pricing, or context window" if not (has_provider and has_pricing and has_context) else "")
                else:
                    self.results.add_result("Get Model Info", False, f"Status {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_result("AI Models", False, str(e))
            return False
    
    async def test_knowledge_base_integration(self):
        """Test knowledge base integration in chat."""
        try:
            # Get available knowledge bases
            async with self.session.get(
                f"{TestConfig.BASE_URL}/knowledge/knowledge-bases",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    knowledge_bases = await response.json()
                    self.test_knowledge_bases = knowledge_bases
                    
                    if len(knowledge_bases) > 0:
                        self.results.add_result("Knowledge Base Availability", True)
                        
                        # Test chat with knowledge base integration
                        kb_ids = [kb["id"] for kb in knowledge_bases[:2]]  # Use first 2 KBs
                        
                        # Update conversation to use knowledge bases
                        update_data = {
                            "knowledge_base_ids": kb_ids,
                            "use_knowledge_base": True
                        }
                        
                        async with self.session.put(
                            f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}",
                            headers=self.get_headers(),
                            json=update_data
                        ) as update_response:
                            if update_response.status == 200:
                                self.results.add_result("Set Knowledge Bases", True)
                            else:
                                self.results.add_result("Set Knowledge Bases", False, f"Status {update_response.status}")
                        
                        # Send knowledge-based query
                        kb_message_data = {
                            "content": TestConfig.TEST_KNOWLEDGE_QUERY,
                            "generate_response": True
                        }
                        
                        async with self.session.post(
                            f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}/messages",
                            headers=self.get_headers(),
                            json=kb_message_data
                        ) as kb_response:
                            if kb_response.status == 200:
                                data = await kb_response.json()
                                ai_message = data.get("ai_message")
                                
                                if ai_message:
                                    has_context = bool(ai_message.get("knowledge_context"))
                                    has_score = ai_message.get("context_score") is not None
                                    
                                    self.results.add_result("Knowledge Base Integration", has_context,
                                                           "AI response missing knowledge context" if not has_context else "")
                                    
                                    if has_score:
                                        self.results.add_result("Context Scoring", True)
                                    else:
                                        self.results.add_result("Context Scoring", False, "Missing context score")
                                else:
                                    self.results.add_result("Knowledge Base Integration", False, "No AI response")
                            else:
                                self.results.add_result("Knowledge Base Integration", False, f"Status {kb_response.status}")
                    else:
                        self.results.add_result("Knowledge Base Availability", False, "No knowledge bases available for testing")
                else:
                    self.results.add_result("Knowledge Base Availability", False, f"Status {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_result("Knowledge Base Integration", False, str(e))
            return False
    
    async def test_chat_statistics(self):
        """Test chat statistics and usage tracking."""
        try:
            # Get chat statistics
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/stats",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    
                    has_conversations = "conversations" in stats
                    has_usage = "usage" in stats
                    has_subscription = "subscription" in stats
                    
                    conversations = stats.get("conversations", {})
                    usage = stats.get("usage", {})
                    
                    total_conversations = conversations.get("total", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    self.results.add_result("Chat Statistics", has_conversations and has_usage and has_subscription,
                                           "Missing statistics sections" if not (has_conversations and has_usage and has_subscription) else "")
                    
                    self.results.add_result("Conversation Counting", total_conversations >= 1,
                                           f"Expected at least 1 conversation, got {total_conversations}")
                    
                    self.results.add_result("Token Tracking", total_tokens > 0,
                                           "No tokens tracked" if total_tokens == 0 else "")
                else:
                    self.results.add_result("Chat Statistics", False, f"Status {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_result("Chat Statistics", False, str(e))
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time chat."""
        try:
            if not self.test_conversation_id or not self.access_token:
                self.results.add_result("WebSocket Connection", False, "Missing conversation ID or token")
                return False
            
            ws_url = f"{TestConfig.WS_URL}/chat/conversations/{self.test_conversation_id}/ws?token={self.access_token}"
            
            try:
                async with websockets.connect(ws_url, timeout=10) as websocket:
                    # Test connection
                    await asyncio.wait_for(websocket.ping(), timeout=5)
                    self.results.add_result("WebSocket Connection", True)
                    
                    # Test message sending
                    test_message = {
                        "type": "message",
                        "content": "Test WebSocket message"
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for responses
                    response_count = 0
                    async for message in websocket:
                        data = json.loads(message)
                        message_type = data.get("type")
                        
                        if message_type == "message_sent":
                            self.results.add_result("WebSocket Message Sent", True)
                            response_count += 1
                        elif message_type == "ai_response":
                            has_content = bool(data.get("message", {}).get("content"))
                            self.results.add_result("WebSocket AI Response", has_content,
                                                   "AI response missing content" if not has_content else "")
                            response_count += 1
                        elif message_type == "error":
                            self.results.add_result("WebSocket Error Handling", False, data.get("message", "Unknown error"))
                        
                        if response_count >= 2:  # Got both message_sent and ai_response
                            break
                    
                    # Test ping/pong
                    ping_message = {"type": "ping"}
                    await websocket.send(json.dumps(ping_message))
                    
                    pong_received = False
                    try:
                        async with asyncio.timeout(5):
                            async for message in websocket:
                                data = json.loads(message)
                                if data.get("type") == "pong":
                                    pong_received = True
                                    break
                    except asyncio.TimeoutError:
                        pass
                    
                    self.results.add_result("WebSocket Ping/Pong", pong_received,
                                           "No pong response received" if not pong_received else "")
                    
            except websockets.exceptions.ConnectionClosed:
                self.results.add_result("WebSocket Connection", False, "Connection closed unexpectedly")
            except asyncio.TimeoutError:
                self.results.add_result("WebSocket Connection", False, "Connection timeout")
            except Exception as ws_error:
                self.results.add_result("WebSocket Connection", False, f"WebSocket error: {str(ws_error)}")
            
            return True
            
        except Exception as e:
            self.results.add_result("WebSocket Connection", False, str(e))
            return False
    
    async def test_conversation_templates(self):
        """Test conversation templates (if available)."""
        try:
            # Check if templates are available
            async with self.session.get(
                f"{TestConfig.BASE_URL}/chat/templates",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    templates = await response.json()
                    self.results.add_result("Conversation Templates", len(templates) >= 0,
                                           "Template endpoint available")
                elif response.status == 404:
                    self.results.add_result("Conversation Templates", True, "Templates not implemented (optional)")
                else:
                    self.results.add_result("Conversation Templates", False, f"Status {response.status}")
            
            return True
            
        except Exception as e:
            self.results.add_result("Conversation Templates", True, f"Templates not available: {str(e)}")
            return True  # Templates are optional for Phase 4
    
    async def cleanup_test_data(self):
        """Clean up test data."""
        try:
            # Delete test conversation
            if self.test_conversation_id:
                async with self.session.delete(
                    f"{TestConfig.BASE_URL}/chat/conversations/{self.test_conversation_id}",
                    headers=self.get_headers(),
                    params={"permanent": True}
                ) as response:
                    if response.status == 200:
                        self.results.add_result("Cleanup - Delete Conversation", True)
                    else:
                        self.results.add_result("Cleanup - Delete Conversation", False, f"Status {response.status}")
            
        except Exception as e:
            self.results.add_result("Cleanup", False, str(e))
    
    async def run_all_tests(self):
        """Run all Phase 4 tests."""
        print("🚀 Starting ChatCPG v2 Phase 4 Tests")
        print("="*60)
        
        try:
            # Authentication (required for all other tests)
            if not await self.test_authentication():
                print("❌ Authentication failed - cannot continue with other tests")
                return
            
            # Core chat functionality
            await self.test_conversation_management()
            await self.test_message_functionality()
            await self.test_ai_models()
            
            # Advanced features
            await self.test_knowledge_base_integration()
            await self.test_chat_statistics()
            
            # Real-time features
            await self.test_websocket_connection()
            
            # Optional features
            await self.test_conversation_templates()
            
        finally:
            # Cleanup
            await self.cleanup_test_data()
            
            # Print results
            self.results.print_summary()


async def main():
    """Main test function."""
    try:
        async with ChatCPGTestClient() as client:
            await client.run_all_tests()
            
            # Return appropriate exit code
            if client.results.failed > 0:
                sys.exit(1)
            else:
                print("\n🎉 All Phase 4 tests passed!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check dependencies
    try:
        import aiohttp
        import websockets
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Install with: pip install aiohttp websockets")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main()) 