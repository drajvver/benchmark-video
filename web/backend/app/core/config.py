"""Application configuration."""

import json
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DATABASE_URL: str = "postgresql://benchmark:benchmark@localhost:5432/benchmark"
    SECRET_KEY: str = "change-me-in-production"
    TOKEN_EXPIRE_MINUTES: int = 60
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Handle CORS_ORIGINS as JSON list, comma-separated string, or plain string."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            if "," in v:
                return [origin.strip() for origin in v.split(",")]
            return [v]
        return [str(v)]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
