import psycopg 
from psycopg.errors import UniqueViolation

from auth.utils import verify_password, hash_password
from schemas.user import User
from fastapi import status, HTTPException

async def authenticate_user(conn, username, password):
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id, username, email, password_hash FROM users WHERE username = %s", 
                (username,)
            )
            result = await cur.fetchone()
            if not result or not verify_password(password, result[3]):
                return None
            
            result_dict: User = {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "hashed_password": result[3]
            }
            return result_dict
    except Exception as e:
        print(f"Error authenticating user: {e}")

async def register_user(conn, user_data):
    hashed_password = hash_password(user_data.password)
    try:
        
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id, username, email",
                (user_data.username, user_data.email, hashed_password)
            )
            result = await cur.fetchone()
            await conn.commit()
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2]
            }
    
    except UniqueViolation as e:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists."
        )
    except Exception as e:
        await conn.rollback()
        print(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")