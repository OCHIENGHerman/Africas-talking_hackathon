"""
Configuration management using Pydantic Settings.
Loads Africa's Talking credentials from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    AT_USERNAME: str
    AT_API_KEY: str
    AT_ENV: Literal["sandbox", "production"] = "sandbox"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Global settings instance
settings = Settings()
