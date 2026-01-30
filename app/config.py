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
    # sandbox | production; "techtribe" accepted and treated as sandbox (e.g. username used as env label)
    AT_ENV: Literal["sandbox", "production", "techtribe"] = "sandbox"
    # SMS sender: numeric shortcode (e.g. "384", "13636") OR alphanumeric sender_id (e.g. "PriceChekRider")
    # Shortcodes: for two-way SMS (users can reply). Sender IDs: for one-way branded SMS.
    # Leave empty to use default from dashboard or shortcode from incoming SMS
    AT_SHORTCODE: str | None = None
    # Alternative: Use AT_SENDER_ID for alphanumeric sender IDs (overrides AT_SHORTCODE if both set)
    AT_SENDER_ID: str | None = None
    # Set to false only for sandbox if you hit SSL cert verify errors (e.g. Windows). Default True.
    AT_SSL_VERIFY: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @property
    def is_production(self) -> bool:
        """True if AT environment is production."""
        return self.AT_ENV == "production"
    
    @property
    def sms_sender(self) -> str | None:
        """SMS sender for two-way SMS (replies). Prefers shortcode so users can reply; fallback to sender_id."""
        return self.AT_SHORTCODE or self.AT_SENDER_ID


# Global settings instance
settings = Settings()
