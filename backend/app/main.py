"""
This is the main entry point for our FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

# Initialize FastAPI application
app = FastAPI(title=settings.app_name)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.get("/status")
async def status():
    """
    Status endpoint
    """
    return {"status": "running", "app_name": settings.app_name}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP exception handler
    """
    return {"error": str(exc.detail)}

To run the server, navigate to the `backend` directory and run the following command:

uvicorn app.main:app --reload

This will start the FastAPI server on `http://localhost:8000`. The `/health` and `/status` endpoints can be accessed to check the health and status of the application respectively.