"""
This file is used to manage the configuration settings of the application.
"""
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "ChatCPG v2"
    DEBUG_MODE: bool = False
    LOGGING_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
