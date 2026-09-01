
import os
from dotenv import load_dotenv
import psycopg
import sqlite3
from datetime import datetime

load_dotenv()

DB_TIMEZONE = datetime.now().astimezone().tzinfo
print(f'Using timezone: {DB_TIMEZONE}')

expenses_db = "expenses.db"
create_expenses_table = """CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    purchase_date DATE NOT NULL,
                    item TEXT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL
                    )
                """

def get_sqlite_connection(path, uri=True):
    conn = sqlite3.connect(path, uri=uri)
    return conn

def get_pg_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "expense_analyst"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

def init_sqlite_db(path):
    conn = get_sqlite_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(create_expenses_table)
            conn.commit()
    finally:
        conn.close()

def init_pg_db(drop=False):
    conn = get_pg_connection()
    try:
        if drop:
            cur.execute("DROP TABLE IF NOT EXISTS conversations")
        with conn.cursor() as cur:
            cur.execute("""
                        CREATE TABLE conversations (
                        id SERIAL PRIMARY KEY,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        course TEXT NOT NULL,
                        model TEXT NOT NULL,
                        instructions TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        prompt_tokens INTEGER NOT NULL,
                        completion_tokens INTEGER NOT NULL,
                        total_tokens INTEGER NOT NULL,
                        response_time FLOAT NOT NULL,
                        cost FLOAT NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                    )
            """)
            conn.commit()
    finally:
        conn.close()

def init_feedback_table():
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")

            cur.execute("""
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    source TEXT NOT NULL,
                    relevance TEXT,
                    explanation TEXT,
                    score INTEGER,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    try:
        # init_sqlite_db("file:expenses.db?mode=ro")
        init_pg_db()
        init_feedback_table()
        print("Postgres DB initialized")
    except Exception as e:
        print("Failed to create table: ", e)
