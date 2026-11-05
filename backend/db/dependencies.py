from fastapi import Request
from typing import AsyncGenerator
from psycopg import AsyncConnection

async def get_db_connection(request: Request) -> AsyncGenerator[AsyncConnection, None]:
    """
    FastAPI Dependency that yields a connection from the pool.
    When the route is finished, it automatically returns the connection to the pool.
    """
    pool = request.app.state.pool
    async with pool.connection() as conn:
        yield conn