# ChatCPG v2 - Advanced AI-Powered CPG Business Assistant

A comprehensive AI-powered business assistant designed specifically for Consumer Packaged Goods (CPG) companies, featuring automated solution development, subscription management, and intelligent knowledge base systems.

## 🚀 Features Overview

### Phase 1 ✅ - Foundation & Authentication
- **Modern Tech Stack**: FastAPI + React + TypeScript + PostgreSQL + Redis
- **Secure Authentication**: JWT tokens with Google OAuth integration
- **User Management**: Complete registration, login, and profile management
- **Responsive UI**: Beautiful, modern interface with Tailwind CSS

### Phase 2 ✅ - Payment & Subscription System
- **Stripe Integration**: Complete payment processing with webhooks
- **Subscription Tiers**: Free, Pro, and Enterprise plans with usage limits
- **Usage Tracking**: Real-time monitoring and limit enforcement
- **Customer Portal**: Self-service subscription management

### Phase 3 ✅ - Knowledge Base System
- **Document Upload**: Support for PDF, DOCX, XLSX, CSV, TXT, MD, JSON files
- **Content Processing**: Automatic text extraction and chunking
- **Vector Embeddings**: OpenAI-powered semantic search capabilities
- **Pinecone Integration**: Scalable vector database for similarity search
- **Smart Search**: AI-powered document search with relevance scoring
- **Usage Integration**: Knowledge base size limits based on subscription tier

### Upcoming Phases
- **Phase 4**: Enhanced Chat Interface with knowledge base integration
- **Phase 5**: Cursor API Integration & Automated Solution Development
- **Phase 6**: Advanced Features & Polish
- **Phase 7**: Testing & Deployment

## 🏗️ Architecture

```
Frontend (React + TypeScript)
├── Authentication System
├── Subscription Management UI
├── Knowledge Base Interface
├── Usage Dashboard
└── Responsive Design

Backend (FastAPI + Python)
├── Authentication APIs (JWT + OAuth)
├── Subscription APIs (Stripe Integration)
├── Knowledge Base APIs
├── Vector Search APIs
└── Usage Tracking APIs

Databases & Services
├── PostgreSQL (User data, subscriptions, documents)
├── Redis (Caching & sessions)
├── Pinecone (Vector embeddings)
├── OpenAI (Text embeddings)
└── Stripe (Payment processing)
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- OpenAI API key
- Pinecone account (optional for vector search)
- Stripe account (for payments)
- Google OAuth credentials

### Environment Variables

Create `.env` files in both `backend/` and `frontend/` directories:

#### Backend `.env`
```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=chat_cpg_v2
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Pinecone (optional - for vector search)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=chat-cpg-knowledge

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=uploads

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Frontend `.env`
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id
```

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd chat_cpg_v2
```

2. **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database setup
python -m app.db.database

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

4. **Database Setup**
```bash
# Create PostgreSQL database
createdb chat_cpg_v2

# Run the backend - it will automatically create tables and seed data
```

5. **Pinecone Setup (Optional)**
```bash
# Create a Pinecone index with the following settings:
# - Dimension: 1536 (for OpenAI ada-002 embeddings)
# - Metric: cosine
# - Name: chat-cpg-knowledge (or your chosen name)
```

## 🧪 Testing

### Automated Test Suites

We provide comprehensive test scripts for each phase:

```bash
# Test Phase 1 (Authentication)
python test_phase1.py

# Test Phase 2 (Subscription System)
python test_phase2.py

# Test Phase 3 (Knowledge Base System)
python test_phase3.py
```

### Manual Testing Checklist

#### Phase 1 - Authentication
- [ ] User registration with email/password
- [ ] User login with credentials
- [ ] Google OAuth login flow
- [ ] Password reset functionality
- [ ] Token refresh and expiration
- [ ] User profile management

#### Phase 2 - Subscription System
- [ ] View subscription plans
- [ ] Subscribe to Pro/Enterprise plans
- [ ] Payment processing with Stripe
- [ ] Usage tracking and limits
- [ ] Subscription management (cancel/upgrade)
- [ ] Customer portal access

#### Phase 3 - Knowledge Base System
- [ ] Create/edit/delete knowledge bases
- [ ] Upload various file types (PDF, DOCX, etc.)
- [ ] Document processing and status tracking
- [ ] Text extraction and chunking
- [ ] Vector embedding creation
- [ ] Semantic search functionality
- [ ] Document download
- [ ] Usage limit integration

## 📚 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/google/login` - Google OAuth URL
- `POST /api/v1/auth/google/callback` - Google OAuth callback
- `GET /api/v1/auth/me` - Get current user

#### Subscription
- `GET /api/v1/subscription/plans` - Get available plans
- `POST /api/v1/subscription/checkout` - Create checkout session
- `GET /api/v1/subscription/usage` - Get usage summary
- `GET /api/v1/subscription/check/conversations` - Check conversation limits
- `GET /api/v1/subscription/check/file-uploads` - Check file upload limits
- `GET /api/v1/subscription/check/knowledge-base` - Check KB size limits

#### Knowledge Base
- `GET /api/v1/knowledge/knowledge-bases` - List knowledge bases
- `POST /api/v1/knowledge/knowledge-bases` - Create knowledge base
- `GET /api/v1/knowledge/knowledge-bases/{id}` - Get KB details
- `POST /api/v1/knowledge/knowledge-bases/{id}/upload` - Upload document
- `GET /api/v1/knowledge/documents/{id}` - Get document details
- `POST /api/v1/knowledge/search` - Search knowledge base
- `GET /api/v1/knowledge/supported-formats` - Get supported file formats

## 🎯 Usage Limits by Tier

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Conversations/month | 10 | 100 | Unlimited |
| File uploads/month | 5 | 50 | Unlimited |
| Knowledge base size | 10 MB | 100 MB | 1 GB |
| Vector search | ✅ | ✅ | ✅ |
| Priority support | ❌ | ✅ | ✅ |
| API access | ❌ | ✅ | ✅ |

## 🔧 Development

### Project Structure
```
chat_cpg_v2/
├── backend/
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   │   ├── auth/         # Authentication logic
│   │   │   ├── core/         # Configuration
│   │   │   ├── db/           # Database setup
│   │   │   ├── models/       # SQLAlchemy models
│   │   │   ├── services/     # Business logic
│   │   │   └── utils/        # Utilities
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/   # React components
│   │   │   ├── hooks/        # Custom hooks
│   │   │   ├── pages/        # Page components
│   │   │   ├── services/     # API services
│   │   │   ├── types/        # TypeScript types
│   │   │   └── utils/        # Utilities
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
```

### Adding New Features

1. **Backend**: Add models in `models/`, business logic in `services/`, and endpoints in `api/`
2. **Frontend**: Add types in `types/`, API calls in `services/`, and UI in `components/`
3. **Testing**: Add test cases to the relevant test script
4. **Documentation**: Update this README and API documentation

### Code Quality

- **Backend**: Use Black for formatting, pylint for linting
- **Frontend**: Use Prettier for formatting, ESLint for linting
- **Types**: Maintain strict TypeScript typing
- **Testing**: Aim for >80% test coverage

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Production Considerations

1. **Security**:
   - Use strong secret keys
   - Enable HTTPS
   - Configure CORS properly
   - Use production Stripe keys

2. **Database**:
   - Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Set up database backups
   - Configure connection pooling

3. **File Storage**:
   - Use cloud storage (AWS S3, Google Cloud Storage)
   - Configure CDN for file delivery
   - Set up backup and archival policies

4. **Monitoring**:
   - Set up application monitoring
   - Configure error tracking
   - Monitor API performance
   - Track usage metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the [documentation](http://localhost:8000/docs)
- Run the test scripts to verify your setup
- Review the error logs for debugging information
- Open an issue for bug reports or feature requests

---

**ChatCPG v2** - Empowering CPG businesses with AI-driven solutions and intelligent automation. 