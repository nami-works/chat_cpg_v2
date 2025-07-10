"""
FastAPI application with CORS middleware, health check, and status endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from .config import settings

app = FastAPI(title=settings.app_name, version=settings.api_version)

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
    return {"status": "running"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP exception handler
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

To run the server, navigate to the backend directory and run the command:
uvicorn app.main:app --reload

This will start the FastAPI server on `http://localhost:8000`. You can check the health and status of the server by navigating to `http://localhost:8000/health` and `http://localhost:8000/status` respectively.