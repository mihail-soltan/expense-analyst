import sqlite3

expenses_db = "expenses.db"
create_table = """CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    purchase_date DATE NOT NULL,
                    item TEXT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL
                    )
                """

def get_db_connection(uri=True):
    conn = sqlite3.connect("file:expenses.db?mode=ro", uri=uri)
    return conn


if __name__ == '__main__':
    try:
        with sqlite3.connect("expenses.db") as conn:
            cursor = conn.cursor()
            cursor.execute(create_table)

            conn.commit()
            print("Table successfully created")
    except sqlite3.OperationalError as e:
        print("Failed to create table: ", e)
