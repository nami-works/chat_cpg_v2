# 🐳 Docker MVP Testing Guide

## 🚀 Quick Start (Recommended)

### Option 1: Automated Setup
```bash
# 1. Navigate to project directory
cd chat_cpg_v2

# 2. Run automated MVP setup
python docker_mvp_setup.py

# 3. Add your API keys to .env file
# Edit .env and replace "your-openai-api-key-here" with actual key

# 4. Restart backend to pick up API keys
docker-compose restart backend
```

### Option 2: Manual Setup
```bash
# 1. Create .env file
cp .env.example .env  # or create manually

# 2. Edit .env with your API keys
# At minimum, set OPENAI_API_KEY or GROQ_API_KEY

# 3. Start services
docker-compose up --build
```

## 📋 Environment Setup

### Required API Keys
Add these to your `.env` file:
```bash
# Required (at least one)
OPENAI_API_KEY=your-actual-openai-key
GROQ_API_KEY=your-actual-groq-key

# Optional for MVP (can be left as placeholder)
CURSOR_API_KEY=not-needed-for-mvp
GOOGLE_CLIENT_ID=not-needed-for-mvp
GOOGLE_CLIENT_SECRET=not-needed-for-mvp
STRIPE_SECRET_KEY=not-needed-for-mvp
STRIPE_PUBLISHABLE_KEY=not-needed-for-mvp
PINECONE_API_KEY=not-needed-for-mvp
PINECONE_ENVIRONMENT=not-needed-for-mvp
```

## 🔧 Service Management

### Start All Services
```bash
# Build and start everything
docker-compose up --build

# Start in background
docker-compose up --build -d

# Start with MVP overrides
docker-compose -f docker-compose.yml -f docker-compose.mvp.yml up --build
```

### Start Services Individually
```bash
# 1. Start databases first
docker-compose up -d postgres redis

# 2. Wait for databases (optional)
docker-compose exec postgres pg_isready -U postgres

# 3. Start backend
docker-compose up --build -d backend

# 4. Initialize MVP data
docker-compose exec backend python setup_mvp.py

# 5. Start frontend
docker-compose up --build -d frontend
```

### Check Service Status
```bash
# View running services
docker-compose ps

# Check health status
docker-compose exec backend curl http://localhost:8000/health
docker-compose exec frontend curl http://localhost:80
```

## 📊 Database Management

### Initialize Database
```bash
# Run MVP setup (creates tables and GE Beauty brand)
docker-compose exec backend python setup_mvp.py

# Alternative: Manual database setup
docker-compose exec backend alembic upgrade head
docker-compose exec backend python create_brands.py
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d chat_cpg_v2

# View tables
\dt

# Check brand data
SELECT name, slug FROM brands;
```

### Reset Database
```bash
# Stop backend
docker-compose stop backend

# Remove database volume
docker-compose down
docker volume rm chat_cpg_v2_postgres_data

# Restart and reinitialize
docker-compose up -d postgres redis
docker-compose up --build -d backend
docker-compose exec backend python setup_mvp.py
```

## 🧪 Testing the MVP

### Access Points
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

### API Testing

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. User Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

#### 3. User Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

#### 4. Get Brands
```bash
# Get auth token first, then:
curl -X GET "http://localhost:8000/api/v1/brands/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 5. Create Chat Conversation
```bash
curl -X POST "http://localhost:8000/api/v1/chat/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Chat with GE Beauty",
    "brand_id": "GEBEAUTY_BRAND_ID_FROM_BRANDS_ENDPOINT"
  }'
```

#### 6. Send Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat/conversations/CONVERSATION_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me about GE Beauty hair care products"
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### "Backend not responding"
```bash
# Check backend logs
docker-compose logs backend

# Check if backend container is running
docker-compose ps

# Restart backend
docker-compose restart backend
```

#### "Database connection failed"
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

#### "AI responses not working"
```bash
# Check API keys are set
docker-compose exec backend env | grep API_KEY

# Add API keys to .env and restart
docker-compose restart backend
```

#### "Frontend can't connect to backend"
```bash
# Check both services are running
docker-compose ps

# Check backend is accessible
curl http://localhost:8000/health

# Check frontend environment
docker-compose exec frontend env | grep REACT_APP
```

### Service Logs
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Container Access
```bash
# Access backend container
docker-compose exec backend bash

# Access database container
docker-compose exec postgres bash

# Access frontend container
docker-compose exec frontend sh
```

## 🧹 Cleanup

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Clean Docker System
```bash
# Remove unused containers, networks, images
docker system prune

# Remove all stopped containers
docker container prune

# Remove unused volumes
docker volume prune
```

## 📈 Monitoring

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Check specific service
docker stats chat_cpg_v2_backend

# View system info
docker system df
```

### Health Monitoring
```bash
# Backend health
curl -s http://localhost:8000/health | jq

# Database health
docker-compose exec postgres pg_isready -U postgres

# Redis health
docker-compose exec redis redis-cli ping
```

## 🎯 MVP Features Available

### ✅ Working Features
- User registration and authentication
- Basic AI chat with brand context
- GE Beauty brand data loaded
- Conversation management
- Message history

### ❌ Disabled Features (preserved in code)
- OAuth login
- Password reset
- Content creation tools
- Subscription management
- File uploads

## 🚀 Production Considerations

For production deployment:
1. Use proper secret management
2. Enable HTTPS/SSL
3. Set up proper logging
4. Configure backups
5. Use production-grade database
6. Set up monitoring and alerting
7. Uncomment and configure disabled features as needed

## 📞 Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review service logs: `docker-compose logs [service_name]`
3. Verify environment variables are set correctly
4. Ensure Docker has enough resources allocated
5. Try restarting services: `docker-compose restart [service_name]` 