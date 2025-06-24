"""
This module is used for managing the configuration of the application.
It uses Pydantic's BaseSettings for environment configuration.
"""

from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    Application settings
    """
    app_name: str = "ChatCPG v2"
    debug: bool = False
    testing: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
