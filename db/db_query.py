from dataclasses import dataclass
from db.db_init import get_pg_connection, get_sqlite_connection
from rag_helper import LLMCallRecord

@dataclass
class Stats:
    total: int
    avg_response_time: float
    total_cost: float
    avg_tokens: float


def row_to_record(row):
    return LLMCallRecord(
        model=row[4],
        prompt=row[6],
        instructions=row[5],
        answer=row[2],
        prompt_tokens=row[6],
        completion_tokens=row[7],
        total_tokens=row[8],
        response_time=row[9],
        cost=row[10],
        timestamp=row[11],
    )

###### Expense stats
def get_monthly_total_spending_trend():
    conn = get_sqlite_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH formatted_expenses AS 
                (SELECT amount, 
                    SUBSTR(purchase_date, -4) || '-' || 
                    SUBSTR('0' || SUBSTR(purchase_date, 1, INSTR(purchase_date, '/') - 1), -2) || '-' || 
                    SUBSTR('0' || SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1, INSTR(SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1), '/') - 1), -2) AS formatted_date FROM expenses) 
                SELECT strftime('%Y-%m', formatted_date) AS month, ROUND(SUM(amount), 2) AS total_spending FROM formatted_expenses 
                GROUP BY month
                ORDER BY month;
                """
            )
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

def get_weekly_total_spending_trend():
    conn = get_sqlite_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
            WITH formatted_expenses AS 
            (SELECT amount, 
                SUBSTR(purchase_date, -4) || '-' || SUBSTR('0' || SUBSTR(purchase_date, 1, INSTR(purchase_date, '/') - 1), -2) || '-' || SUBSTR('0' || SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1, INSTR(SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1), '/') - 1), -2) AS formatted_date FROM expenses)
                SELECT strftime('%Y-%W', formatted_date) AS week, 
                ROUND(SUM(amount), 2) AS total_spending
                FROM formatted_expenses
                GROUP BY week
                ORDER BY week;
            """)
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

def get_monthly_spending_breakdown_by_category():
    conn = get_sqlite_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH formatted_expenses AS 
                    (SELECT 
                        amount, 
                        category, 
                        SUBSTR(purchase_date, -4) || '-' 
                        || SUBSTR('0' || SUBSTR(purchase_date, 1, INSTR(purchase_date, '/') - 1), -2) || '-' 
                        || SUBSTR('0' || SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1, INSTR(SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1), '/') - 1), -2) 
                    AS formatted_date FROM expenses) 

                SELECT 
                    strftime('%Y-%m', formatted_date) AS month, 
                    category, 
                    ROUND(SUM(amount), 2) AS total_spending 
                FROM formatted_expenses 
                GROUP BY month, category 
                ORDER BY month, total_spending DESC;
            """)
    finally:
            conn.close()

def get_overall_category_expense_proportions():
    conn = get_sqlite_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    category, 
                    ROUND(SUM(amount), 2) AS total_spending, 
                    ROUND(100.0 * SUM(amount) / (SELECT SUM(amount) FROM expenses), 2) AS percentage 
                FROM expenses 
                GROUP BY category 
                ORDER BY total_spending DESC;
                """)
    finally:
        conn.close()

def get_transaction_frequency_vs_avg_spend_size_by_month():
    conn = get_sqlite_connection()
    try:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH formatted_expenses 
                        AS (SELECT 
                                amount, 
                                SUBSTR(purchase_date, -4) || '-' 
                                || SUBSTR('0' || SUBSTR(purchase_date, 1, INSTR(purchase_date, '/') - 1), -2) || '-' 
                                || SUBSTR('0' || SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1, INSTR(SUBSTR(purchase_date, INSTR(purchase_date, '/') + 1), '/') - 1), -2) AS formatted_date 
                            FROM expenses) 

                    SELECT 
                        strftime('%Y-%m', formatted_date) AS month,
                        COUNT(*) AS transaction_count, 
                        ROUND(AVG(amount), 2) AS avg_transaction_amount 
                    FROM formatted_expenses 
                    GROUP BY month 
                    ORDER BY month;
                    """)
    finally:
        conn.close()
    #Transaction Frequency vs. Average Spend Size by Month
###### MONITORING

def get_conversations(limit=10):
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, question, answer, model,
                       instructions, prompt,
                       prompt_tokens, completion_tokens, total_tokens,
                       response_time, cost, timestamp
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [row_to_record(row) for row in rows]


def get_stats():
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*),
                    AVG(response_time),
                    SUM(cost),
                    AVG(total_tokens)
                FROM conversations
            """)
            row = cur.fetchone()
    finally:
        conn.close()

    return Stats(
        total=row[0],
        avg_response_time=row[1],
        total_cost=row[2],
        avg_tokens=row[3]
    )

def get_relevance_stats():
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT relevance, COUNT(*)
                FROM feedback
                WHERE source = 'judge'
                GROUP BY relevance
            """)
            rows = cur.fetchall()
    finally:
        conn.close()
    return dict(rows)

def get_user_feedback_stats():
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN score < 0 THEN 1 ELSE 0 END)
                FROM feedback
                WHERE source = 'user'
            """)
            row = cur.fetchone()
    finally:
        conn.close()
    return row

if __name__ == "__main__":
    records = get_conversations()
    for record in records:
        print(record)

    