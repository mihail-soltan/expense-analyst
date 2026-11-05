# app/auth/jwt_bearer.py
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional, List
from schemas.token import TokenPayload
from core.config import settings
from auth.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/auth/login"
)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Validates token and returns the username
    """
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        # Check token expiration
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_data.sub
    
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )