"""
This file is used to create the FastAPI application and to define the application routes.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings
import logging

# Load settings
settings = Settings()

# Create FastAPI instance
app = FastAPI(title=settings.APP_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.get("/status")
async def status():
    """
    Status endpoint
    """
    return {"status": "running"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP exception handler
    """
    logger.error(f"Error occurred: {exc.detail}")
    return {"error": exc.detail}

To run the application, navigate to the backend directory and run the following command:
uvicorn app.main:app --reload
This will start the FastAPI server on port 8000. You can access the health and status endpoints at `http://localhost:8000/health` and `http://localhost:8000/status` respectively.