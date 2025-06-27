# ChatCPG v2 - Usage Guide

## 🚀 Quick Start

Your ChatCPG v2 application is now running! Here's how to use it:

### Access the Application

1. **Frontend (Chat Interface)**: http://localhost:3000
2. **Backend API Documentation**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/health

## 🔐 Authentication

### Creating an Account

1. Go to http://localhost:3000
2. You'll be redirected to the login page
3. Click "Sign up here" to create a new account
4. Fill in:
   - Full Name
   - Email Address
   - Password (must contain uppercase, lowercase, and number)
   - Confirm Password
5. Click "Create Account"

### Logging In

1. Enter your email and password
2. Click "Sign In"
3. You'll be redirected to the chat interface

## 💬 Using the Chat Interface

### Main Interface Components

1. **Sidebar (Left)**:
   - ChatCPG logo and new conversation button
   - List of your conversations
   - User profile and logout button

2. **Main Chat Area (Right)**:
   - Chat header with conversation title and AI model
   - Message history
   - Message input area

### Starting a Conversation

1. Click the "+" button in the sidebar, OR
2. Click "Start New Conversation" in the welcome screen
3. A new conversation will be created automatically
4. Start typing your message in the input area
5. Press Enter or click the Send button

### Chat Features

- **Real-time AI responses**: Messages are processed by AI and responses appear automatically
- **Conversation history**: All your conversations are saved and accessible
- **Multiple AI models**: Switch between different AI providers (when API keys are configured)
- **Message formatting**: Supports multi-line messages (Shift+Enter for new line)

## 🤖 AI Models Available

### With OpenAI API Key
- GPT-3.5 Turbo (fast, cost-effective)
- GPT-4 (more capable, slower)
- GPT-4 Turbo Preview (latest model)

### With Groq API Key
- Mixtral 8x7B (fast inference)
- LLaMA 2 70B (large model)

### Setting Up AI Keys

1. See `env_setup_guide.md` for detailed instructions
2. Get API keys from OpenAI and/or Groq
3. Add them to your `.env` file
4. Restart the application: `docker-compose down && docker-compose up -d`

## 🛠️ Backend API Features

Access the full API documentation at http://localhost:8000/docs

### Available Endpoints

1. **Authentication**:
   - POST `/api/auth/signup` - Create account
   - POST `/api/auth/login` - Login
   - GET `/api/auth/me` - Get user info
   - POST `/api/auth/logout` - Logout

2. **Chat Management**:
   - GET `/api/chat/conversations` - List conversations
   - POST `/api/chat/conversations` - Create conversation
   - GET `/api/chat/conversations/{id}` - Get conversation
   - POST `/api/chat/conversations/{id}/messages` - Send message

3. **AI Models**:
   - GET `/api/chat/models` - List available models
   - GET `/api/chat/models/{model}` - Get model info

4. **System**:
   - GET `/api/health` - Health check

## 🔧 Advanced Features

### Conversation Management

- **Multiple Conversations**: Create and manage multiple chat sessions
- **Conversation History**: All messages are automatically saved
- **Conversation Switching**: Click on any conversation in the sidebar to switch

### User Management

- **Profile Information**: View your account details in the sidebar
- **Subscription Tiers**: Backend supports different subscription levels
- **Usage Tracking**: All API calls are tracked (ready for billing)

### Technical Features

- **Real-time Updates**: Messages appear instantly
- **Error Handling**: Graceful error messages for failed requests
- **Responsive Design**: Works on desktop and mobile
- **Security**: JWT-based authentication with secure token handling

## 🐛 Troubleshooting

### Common Issues

1. **AI not responding**:
   - Check if API keys are configured in `.env`
   - Restart services: `docker-compose restart`
   - Check backend logs: `docker-compose logs backend`

2. **Login issues**:
   - Ensure database is running: `docker-compose ps`
   - Check if containers are healthy
   - Clear browser cache/localStorage

3. **Connection errors**:
   - Verify all services are running: `docker-compose ps`
   - Check ports 3000 and 8000 are not in use by other applications

### Checking Service Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis

# Restart specific service
docker-compose restart backend
```

## 🚀 Next Steps

### Phase 3: Knowledge Base
- Upload documents for context-aware AI responses
- Vector search capabilities
- Document management

### Phase 4: Enhanced Features
- File attachments
- Advanced conversation settings
- Model comparison

### Phase 5: Cursor Integration
- Automated code generation
- Solution development assistance
- Project management features

## 📊 Current System Status

✅ **Completed Features**:
- User authentication and registration
- Real-time AI chat interface
- Conversation management
- Multiple AI model support
- Secure API with full documentation
- Database persistence
- Docker containerization

🔄 **Ready to Implement**:
- Knowledge base integration
- File upload functionality
- Advanced AI features
- Subscription management UI
- Cursor API integration

## 💡 Tips for Best Experience

1. **Use descriptive conversation titles** when creating new chats
2. **Try different AI models** to see which works best for your use case
3. **Keep conversations organized** by topic or project
4. **Use the API documentation** to understand all available features
5. **Monitor your usage** through the backend API endpoints

---

**Need Help?** Check the logs with `docker-compose logs` or refer to the API documentation at http://localhost:8000/docs 

## 🚀 Quick Start

Your ChatCPG v2 application is now running! Here's how to use it:

### Access the Application

1. **Frontend (Chat Interface)**: http://localhost:3000
2. **Backend API Documentation**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/health

## 🔐 Authentication

### Creating an Account

1. Go to http://localhost:3000
2. You'll be redirected to the login page
3. Click "Sign up here" to create a new account
4. Fill in:
   - Full Name
   - Email Address
   - Password (must contain uppercase, lowercase, and number)
   - Confirm Password
5. Click "Create Account"

### Logging In

1. Enter your email and password
2. Click "Sign In"
3. You'll be redirected to the chat interface

## 💬 Using the Chat Interface

### Main Interface Components

1. **Sidebar (Left)**:
   - ChatCPG logo and new conversation button
   - List of your conversations
   - User profile and logout button

2. **Main Chat Area (Right)**:
   - Chat header with conversation title and AI model
   - Message history
   - Message input area

### Starting a Conversation

1. Click the "+" button in the sidebar, OR
2. Click "Start New Conversation" in the welcome screen
3. A new conversation will be created automatically
4. Start typing your message in the input area
5. Press Enter or click the Send button

### Chat Features

- **Real-time AI responses**: Messages are processed by AI and responses appear automatically
- **Conversation history**: All your conversations are saved and accessible
- **Multiple AI models**: Switch between different AI providers (when API keys are configured)
- **Message formatting**: Supports multi-line messages (Shift+Enter for new line)

## 🤖 AI Models Available

### With OpenAI API Key
- GPT-3.5 Turbo (fast, cost-effective)
- GPT-4 (more capable, slower)
- GPT-4 Turbo Preview (latest model)

### With Groq API Key
- Mixtral 8x7B (fast inference)
- LLaMA 2 70B (large model)

### Setting Up AI Keys

1. See `env_setup_guide.md` for detailed instructions
2. Get API keys from OpenAI and/or Groq
3. Add them to your `.env` file
4. Restart the application: `docker-compose down && docker-compose up -d`

## 🛠️ Backend API Features

Access the full API documentation at http://localhost:8000/docs

### Available Endpoints

1. **Authentication**:
   - POST `/api/auth/signup` - Create account
   - POST `/api/auth/login` - Login
   - GET `/api/auth/me` - Get user info
   - POST `/api/auth/logout` - Logout

2. **Chat Management**:
   - GET `/api/chat/conversations` - List conversations
   - POST `/api/chat/conversations` - Create conversation
   - GET `/api/chat/conversations/{id}` - Get conversation
   - POST `/api/chat/conversations/{id}/messages` - Send message

3. **AI Models**:
   - GET `/api/chat/models` - List available models
   - GET `/api/chat/models/{model}` - Get model info

4. **System**:
   - GET `/api/health` - Health check

## 🔧 Advanced Features

### Conversation Management

- **Multiple Conversations**: Create and manage multiple chat sessions
- **Conversation History**: All messages are automatically saved
- **Conversation Switching**: Click on any conversation in the sidebar to switch

### User Management

- **Profile Information**: View your account details in the sidebar
- **Subscription Tiers**: Backend supports different subscription levels
- **Usage Tracking**: All API calls are tracked (ready for billing)

### Technical Features

- **Real-time Updates**: Messages appear instantly
- **Error Handling**: Graceful error messages for failed requests
- **Responsive Design**: Works on desktop and mobile
- **Security**: JWT-based authentication with secure token handling

## 🐛 Troubleshooting

### Common Issues

1. **AI not responding**:
   - Check if API keys are configured in `.env`
   - Restart services: `docker-compose restart`
   - Check backend logs: `docker-compose logs backend`

2. **Login issues**:
   - Ensure database is running: `docker-compose ps`
   - Check if containers are healthy
   - Clear browser cache/localStorage

3. **Connection errors**:
   - Verify all services are running: `docker-compose ps`
   - Check ports 3000 and 8000 are not in use by other applications

### Checking Service Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis

# Restart specific service
docker-compose restart backend
```

## 🚀 Next Steps

### Phase 3: Knowledge Base
- Upload documents for context-aware AI responses
- Vector search capabilities
- Document management

### Phase 4: Enhanced Features
- File attachments
- Advanced conversation settings
- Model comparison

### Phase 5: Cursor Integration
- Automated code generation
- Solution development assistance
- Project management features

## 📊 Current System Status

✅ **Completed Features**:
- User authentication and registration
- Real-time AI chat interface
- Conversation management
- Multiple AI model support
- Secure API with full documentation
- Database persistence
- Docker containerization

🔄 **Ready to Implement**:
- Knowledge base integration
- File upload functionality
- Advanced AI features
- Subscription management UI
- Cursor API integration

## 💡 Tips for Best Experience

1. **Use descriptive conversation titles** when creating new chats
2. **Try different AI models** to see which works best for your use case
3. **Keep conversations organized** by topic or project
4. **Use the API documentation** to understand all available features
5. **Monitor your usage** through the backend API endpoints

---

**Need Help?** Check the logs with `docker-compose logs` or refer to the API documentation at http://localhost:8000/docs 