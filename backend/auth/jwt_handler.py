from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from core.config import settings

def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
    """create JWT access token"""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "token_type": "access",
    }
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

def create_refresh_token(subject: str) -> str:
    """create JWT refresh token"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "token_type": "refresh",
    }
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> Dict[str, Any]:
    """decode and verify JWT token"""
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )