import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import PyJWTError
from psycopg import AsyncConnection

from auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from auth.utils import hash_token
from core.config import settings
from db.dependencies import get_db_connection

from schemas.token import Token
from schemas.user import UserCreate
from services.user import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: AsyncConnection = Depends(get_db_connection),
) -> Any:
    user = await authenticate_user(conn, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = str(user["user_id"])
    access_token = create_access_token(
        subject=user_id_str,
        expires_delta=timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    refresh_token = create_refresh_token(
        subject=user_id_str,
        # expires_delta=timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS)),
    )

    expires_at = datetime.now(timezone.utc) + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
    async with conn.cursor() as cur:
        await cur.execute("SELECT set_config('rls.user_id', %s, true)", (user_id_str,))
        await cur.execute(
            """
            INSERT INTO refresh_tokens (token_hash, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (hash_token(refresh_token), user["user_id"], expires_at),
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/register")
async def register(
    form_data: UserCreate = Depends(),
    conn: AsyncConnection = Depends(get_db_connection),
):
    user = await register_user(conn, form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register user",
        )
    return user

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_db_connection),
) -> Any:
    try:
        payload = decode_token(refresh_token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("token_type") != "refresh" or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = str(payload["sub"])
    new_access_token = create_access_token(
        subject=user_id_str,
        expires_delta=timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    new_refresh_token = create_refresh_token(
        subject=user_id_str,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT user_id, username, email, status FROM rotate_refresh_token(%s, %s, %s)",
            (hash_token(refresh_token), hash_token(new_refresh_token), new_expires_at),
        )
        row = await cur.fetchone()

    if not row or row[3] != "ok":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired; please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_db_connection),
) -> None:
    """Revokes the current refresh token so it can no longer mint access tokens."""
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = %s",
            (hash_token(refresh_token),),
        )