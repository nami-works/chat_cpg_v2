# ChatCPG v2 - MVP Version

## 🎯 MVP Overview

This is a **Minimum Viable Product (MVP)** version of ChatCPG v2 that focuses on core functionality while commenting out complex features. The goal is to get a working AI chat system with authentication and brand context for GE Beauty as quickly as possible.

## ✅ Features ENABLED in MVP

### 🔐 Authentication
- User registration (signup)
- User login  
- JWT token-based authentication
- Auto-verification (no email confirmation needed for MVP)
- User profile access

### 💬 AI Chat
- Create chat conversations
- Send messages and receive AI responses
- Basic conversation management (list, view, delete)
- Simple AI response generation
- Conversation title management

### 🏷️ Brand Support
- GE Beauty brand loaded with complete data
- Brand context integration in chat responses
- Read brand information (name, products, style guide, etc.)

## ❌ Features DISABLED (Commented Out)

### 🔒 Advanced Auth
```python
# OAuth login (Google) - Lines commented in auth.py
# Password reset functionality - Lines commented in auth.py
# Email verification - Simplified to auto-verify
```

### 💼 Content Management
```python
# Content creation (Redação CPG) - Router disabled in main.py
# Project management - Models commented in chat.py
# Creative output parsing - Service methods commented
```

### 📚 Knowledge Management
```python
# Knowledge base uploads - Router disabled in main.py
# File upload handling - Service methods commented
# Vector search functionality - Advanced features disabled
```

### 💳 Business Features
```python
# Subscription management - Router disabled in main.py
# Usage tracking - Service methods commented
# Stripe integration - Service methods commented
```

### 🏷️ Brand Management
```python
# Brand CRUD operations - Create/Update/Delete commented in brands.py
# Only READ operations enabled for MVP
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Activate the virtual environment
C:\venvs\chat_cpg_v2\Scripts\activate

# Navigate to backend
cd chat_cpg_v2/backend
```

### 2. Run MVP Setup
```bash
# Initialize database and create GE Beauty brand
python setup_mvp.py
```

### 3. Start Backend
```bash
# Start the API server
python -m uvicorn app.main:app --reload
```

### 4. Access API
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Root Info: http://localhost:8000

## 📋 API Endpoints Available

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get user info
- `POST /api/v1/auth/logout` - Logout

### Chat
- `GET /api/v1/chat/context` - Get chat options
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/chat/conversations/{id}` - Get conversation
- `POST /api/v1/chat/conversations/{id}/messages` - Send message
- `GET /api/v1/chat/conversations/{id}/messages` - Get messages
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Brands
- `GET /api/v1/brands/` - List brands
- `GET /api/v1/brands/{id}` - Get brand by ID
- `GET /api/v1/brands/slug/gebeauty` - Get GE Beauty brand

## 🧪 Testing the MVP

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### 2. Create a Chat Conversation
```bash
curl -X POST "http://localhost:8000/api/v1/chat/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Chat",
    "brand_id": "GEBEAUTY_BRAND_ID"
  }'
```

### 3. Send a Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat/conversations/CONV_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me about GE Beauty products"
  }'
```

## 🏷️ Brand Context

The MVP includes GE Beauty with:
- Complete product information (boosters, primers, bases)
- Style guide and brand voice
- Format recommendations for content
- Knowledge base about hair care

When chatting with `brand_id` set to GE Beauty, the AI will have context about:
- Brand description and values
- Product portfolio and benefits
- Target audience and positioning

## 🔧 Development Notes

### File Changes Made
- `app/main.py` - Disabled non-essential routers
- `app/api/auth.py` - Commented OAuth and password reset
- `app/api/chat.py` - Simplified to basic chat functionality
- `app/api/brands.py` - Disabled CRUD operations, kept read-only
- `app/services/ai_service.py` - Added simple response method
- `app/services/chat_service.py` - Added add_message alias

### Database Models
All models are preserved but some relationships are simplified:
- User model - Full functionality
- Brand model - Read-only in API
- Conversation/Message models - Basic functionality
- Other models - Present but API disabled

### Reactivating Features

To reactivate any commented feature:
1. Find the commented code sections
2. Uncomment the relevant lines
3. Add back the router in `main.py`
4. Test the functionality

Example - Reactivating OAuth:
```python
# In main.py, uncomment:
# from .auth.oauth import google_oauth

# In auth.py, uncomment OAuth endpoints
```

## 🎯 Next Steps for Full Version

1. **Uncomment OAuth**: Enable Google login
2. **Enable Content Creation**: Activate Redação CPG functionality  
3. **Add Knowledge Management**: Enable file uploads and vector search
4. **Activate Subscriptions**: Enable payment and usage tracking
5. **Enable Brand Management**: Allow brand CRUD operations
6. **Add Email Services**: Enable verification and password reset

## 📞 Support

If you encounter issues with the MVP:
1. Check that the virtual environment is activated
2. Verify database connection settings
3. Ensure all dependencies are installed
4. Check the logs for specific error messages

The MVP is designed to be simple and stable - if something doesn't work, it's likely a configuration issue rather than a code problem. 