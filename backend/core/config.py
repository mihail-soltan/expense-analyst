import os
import dotenv

dotenv.load_dotenv()

class Settings():
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    # DB_HOST = "0.0.0.0"
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("POSTGRES_DB")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)

settings = Settings()