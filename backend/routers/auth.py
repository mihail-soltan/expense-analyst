from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from auth.utils import verify_password
from schemas.token import Token
from core.config import settings
from schemas.user import UserBase, UserCreate
from db.dependencies import get_db_connection
from services.user import authenticate_user, register_user
from psycopg import AsyncConnection

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)

async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: AsyncConnection = Depends(get_db_connection)
) -> Any:
    """
    OAuth2 compatible token login, returns an access token
    """
    
    user = await authenticate_user(conn, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect username or password",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
    access_token_expires = timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        subject=user["email"],
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user["email"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register")
async def register(
        form_data: UserCreate = Depends(),
        conn: AsyncConnection = Depends(get_db_connection)):
    user  = await register_user(conn, form_data)
    if not user:
        raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Failed to register user {user}",
                                        headers={"WWW-Authenticate": "Bearer"},
                                    )
    return user