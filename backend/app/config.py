from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ChatCPG v2"
    debug: bool = False
    testing: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
