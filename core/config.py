"""Configuration module for ClawBot."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://clawbot:clawbot@clawbot-db:5432/clawbot"

    # Ollama
    ollama_url: str = "http://clawbot-llm:11434"
    ollama_model: str = "qwen2.5:3b"

    # Encryption
    encryption_key: str = "your-32-byte-encryption-key-here-change-me"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Tenant
    default_tenant: str = "default"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
