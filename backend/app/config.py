from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings. Load from environment variables.
    """
    app_name: str = "ChatCPG v2"
    debug: bool = False
    testing: bool = False


settings = Settings()
