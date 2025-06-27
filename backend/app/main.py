from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
import uvicorn
import logging

# Enable minimal imports for MVP functionality
from .api.chat import router as chat_router
from .api.auth import router as auth_router
from .api.brands import router as brands_router
# Other imports temporarily disabled for MVP
# from .api.subscription import router as subscription_router
# from .api.knowledge import router as knowledge_router
# from .api.content import router as content_router
from .core.config import settings
from .db.database import init_db, close_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - MVP with database.
    """
    # Startup
    print("Starting up ChatCPG v2 MVP...")
    await init_db()
    print("Database initialized.")
    
    yield
    
    # Shutdown
    print("Shutting down ChatCPG v2 MVP...")
    await close_db()
    print("Database connections closed.")


# Create FastAPI application
app = FastAPI(
    title="ChatCPG v2 MVP",
    description="MVP: AI-powered chat system with authentication and brand support for GE Beauty",
    version="2.0.0-mvp",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "localhost"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "environment": "mvp"}


# Enable essential routers for MVP functionality
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(brands_router, prefix="/api/v1", tags=["brands"])
# Other routers temporarily disabled for MVP
# app.include_router(subscription_router, prefix="/api/v1/subscription", tags=["Subscription"])
# app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["Knowledge Base"])
# app.include_router(content_router, prefix="/api/v1/content", tags=["content"])


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "ChatCPG v2 MVP",
        "version": "2.0.0-mvp",
        "status": "running",
        "features": [
            "Authentication (Login/Signup)",
            "AI chat with brand context", 
            "GE Beauty brand support"
        ]
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unexpected errors.
    """
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 