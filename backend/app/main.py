from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from .config import settings
import logging

# Initialize FastAPI application
app = FastAPI(title=settings.app_name)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.get("/status")
async def status_check():
    """
    Status check endpoint
    """
    return {"status": "running"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Exception handler for HTTP exceptions
    """
    logger.error(f"Error occurred: {exc.detail}")
    return {"error": f"An error occurred: {exc.detail}"}

To run the server, navigate to the backend directory and run the following command:
uvicorn app.main:app --reload
This will start the FastAPI server on port 8000. You can access the health and status endpoints at http://localhost:8000/health and http://localhost:8000/status respectively.