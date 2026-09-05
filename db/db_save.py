from datetime import datetime
from db.db_init import get_pg_connection, get_sqlite_connection, DB_TIMEZONE
from psycopg.types.json import Json
import pandas as pd

def save_conversation(record, question):
    timestamp = datetime.now(DB_TIMEZONE)

    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (
                    question, answer, model, instructions, prompt,
                    prompt_tokens, completion_tokens, total_tokens,
                    response_time, cost, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    question,
                    record.answer,
                    record.model,
                    record.instructions,
                    Json(record.prompt),
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,
                    record.response_time,
                    record.cost,
                    timestamp,
                ),
            )
            conversation_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()
    return conversation_id

def save_feedback(conversation_id, source, relevance=None,
                  explanation=None, score=None):
    timestamp = datetime.now(DB_TIMEZONE)

    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback (
                    conversation_id, source, relevance,
                    explanation, score, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                """,
                (conversation_id, source, relevance,
                 explanation, score, timestamp),
            )
        conn.commit()
    finally:
        conn.close()

def save_expenses_to_sqlite(csv_path):
    conn = get_sqlite_connection("file:expenses.db")
    records = pd.read_csv(csv_path, skip_blank_lines=True).dropna(how="all")
    records.columns=["timestamp","purchase_date","item","amount","category"]
    try:
        records.to_sql("expenses",con=conn, schema="expenses", index=False, if_exists="delete_rows")
        conn.commit()
    except Exception as e:
        print(records.head())
        print("Failed to save to schema: ", e)
    finally:
            conn.close()