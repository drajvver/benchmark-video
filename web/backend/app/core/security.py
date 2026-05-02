"""Security utilities: JWT token creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def create_token() -> tuple[str, datetime]:
    """Create a new upload token."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {
        "type": "upload",
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, expires_at


def verify_token(token: str) -> bool:
    """Verify an upload token is valid and not expired."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("type") == "upload"
    except JWTError:
        return False
