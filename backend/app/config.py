"""
Configuration management using Pydantic settings
"""
from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings
    """
    app_name: str = "ChatCPG v2"
    debug: bool = False
    testing: bool = False
    api_version: str = "v2"
    database_url: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"


settings = Settings()
