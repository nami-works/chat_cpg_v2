from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
import logging

# Initialize FastAPI application
app = FastAPI(title=settings.app_name, debug=settings.debug)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "OK"}

@app.get("/status")
async def status_check():
    """
    Status check endpoint
    """
    return {"status": "Running", "app_name": settings.app_name}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions
    """
    logger.error(f"Error occurred: {exc.detail}")
    return {"error": exc.detail}

To run the server, navigate to the `backend` directory and run the command `uvicorn app.main:app --reload`. This will start the FastAPI server on port 8000. You can check the health and status of the server by navigating to `http://localhost:8000/health` and `http://localhost:8000/status` respectively.