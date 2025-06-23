from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

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
    Health check endpoint. Returns status of the application.
    """
    return {"status": "ok"}

@app.get("/status")
async def status():
    """
    Status endpoint. Returns detailed status of the application.
    """
    return {"status": "ok", "environment": settings.dict()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

This code sets up a basic FastAPI application with CORS middleware and two endpoints for health checks and status checks. The application settings are loaded from environment variables using Pydantic's BaseSettings class. The application runs on port 8000.