from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.logger import logger
from psycopg_pool import AsyncConnectionPool
from routers import rag, auth
from core.config import settings

dev_host = "0.0.0.0"
@asynccontextmanager
async def lifespan(app: FastAPI):
    # conn_string = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    conn_string = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{dev_host}:{settings.DB_PORT}/{settings.DB_NAME}"
    app.state.pool = AsyncConnectionPool(conninfo=conn_string, min_size=2, max_size=10)
    yield 
    await app.state.pool.close()
    print("Database pool closed.")
    logger.debug(conn_string)
app = FastAPI(lifespan=lifespan)

app.include_router(rag.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Expense Analyst Backend is Running"}