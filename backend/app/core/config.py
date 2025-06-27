import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Server settings
    SERVER_NAME: str = "localhost"
    SERVER_HOST: str = "http://localhost"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chat_cpg_v2"
    POSTGRES_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    
    # Stripe settings
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    
    # Groq settings
    GROQ_API_KEY: str = ""
    
    # Anthropic settings
    ANTHROPIC_API_KEY: str = ""
    
    # Cursor API settings
    CURSOR_API_KEY: str = ""
    CURSOR_API_URL: str = "https://api.cursor.com/v1"
    
    # Pinecone settings
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "chat-cpg-knowledge"
    
    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "docx", "xlsx", "csv", "txt", "md", "json"
    ]
    UPLOAD_DIR: str = "uploads"
    
    # Usage limits
    FREE_TIER_CONVERSATIONS: int = 10
    FREE_TIER_FILE_UPLOADS: int = 5
    FREE_TIER_KNOWLEDGE_BASE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    PRO_TIER_CONVERSATIONS: int = 100
    PRO_TIER_FILE_UPLOADS: int = 50
    PRO_TIER_KNOWLEDGE_BASE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    ENTERPRISE_TIER_CONVERSATIONS: int = -1  # unlimited
    ENTERPRISE_TIER_FILE_UPLOADS: int = -1  # unlimited
    ENTERPRISE_TIER_KNOWLEDGE_BASE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    
    # Security
    ALGORITHM: str = "HS256"
    
    # Project metadata
    PROJECT_NAME: str = "ChatCPG v2"
    PROJECT_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "Advanced AI-powered CPG business assistant with automated solution development"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings() 