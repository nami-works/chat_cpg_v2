# Environment Setup Guide

To enable AI chat functionality, you need to set up API keys. Create a `.env` file in the project root with the following variables:

## Required for AI Chat

```bash
# OpenAI API Key (for GPT models)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Groq API Key (for fast LLaMA models)
GROQ_API_KEY=gsk_your-groq-api-key-here
```

## How to Get API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key and add it to your `.env` file

### Groq API Key
1. Go to https://console.groq.com/keys
2. Sign up or log in
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## Complete .env File Template

```bash
# Database Configuration (already working)
DATABASE_URL=postgresql://chatcpg_user:chatcpg_password@postgres:5432/chatcpg_db
REDIS_URL=redis://redis:6379

# JWT Configuration (already working)
SECRET_KEY=your-super-secret-jwt-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Provider API Keys (ADD YOUR KEYS HERE)
OPENAI_API_KEY=sk-your-openai-api-key-here
GROQ_API_KEY=gsk_your-groq-api-key-here

# Optional: Google OAuth (for social login)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional: Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key

# Optional: Vector Database (for knowledge base)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# Optional: Cursor API (for code generation)
CURSOR_API_KEY=your-cursor-api-key

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
```

## After Adding Keys

1. Create or update your `.env` file with the API keys
2. Restart the services: `docker-compose down && docker-compose up -d`
3. The AI chat will now work with your configured providers

## Testing

- Without API keys: You can still use the interface, but AI responses won't work
- With OpenAI key: GPT-3.5 and GPT-4 models will be available
- With Groq key: Fast LLaMA models will be available
- With both: You'll have access to all models and can switch between them 

To enable AI chat functionality, you need to set up API keys. Create a `.env` file in the project root with the following variables:

## Required for AI Chat

```bash
# OpenAI API Key (for GPT models)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Groq API Key (for fast LLaMA models)
GROQ_API_KEY=gsk_your-groq-api-key-here
```

## How to Get API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key and add it to your `.env` file

### Groq API Key
1. Go to https://console.groq.com/keys
2. Sign up or log in
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## Complete .env File Template

```bash
# Database Configuration (already working)
DATABASE_URL=postgresql://chatcpg_user:chatcpg_password@postgres:5432/chatcpg_db
REDIS_URL=redis://redis:6379

# JWT Configuration (already working)
SECRET_KEY=your-super-secret-jwt-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Provider API Keys (ADD YOUR KEYS HERE)
OPENAI_API_KEY=sk-your-openai-api-key-here
GROQ_API_KEY=gsk_your-groq-api-key-here

# Optional: Google OAuth (for social login)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional: Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key

# Optional: Vector Database (for knowledge base)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# Optional: Cursor API (for code generation)
CURSOR_API_KEY=your-cursor-api-key

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
```

## After Adding Keys

1. Create or update your `.env` file with the API keys
2. Restart the services: `docker-compose down && docker-compose up -d`
3. The AI chat will now work with your configured providers

## Testing

- Without API keys: You can still use the interface, but AI responses won't work
- With OpenAI key: GPT-3.5 and GPT-4 models will be available
- With Groq key: Fast LLaMA models will be available
- With both: You'll have access to all models and can switch between them 

env_backup

# API Settings
SECRET_KEY=your-super-secret-key
SERVER_NAME=localhost
SERVER_HOST=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Database (using Docker PostgreSQL)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=chat_cpg_v2
POSTGRES_PORT=5432

# Redis (using Docker Redis)
REDIS_URL=redis://localhost:6379


# Email Settings (optional)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=ChatCPG v2

# Google OAuth Settings
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Stripe Settings
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# AI API Keys
OPENAI_API_KEY=
# GROQ_API_KEY=your-groq-api-key
# CURSOR_API_KEY=your-cursor-api-key
# CURSOR_API_URL=https://api.cursor.com/v1

# Pinecone Settings
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=chat-cpg-knowledge

PINECONE_INDEX_NAME=chat-cpg-knowledge 