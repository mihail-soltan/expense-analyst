import sqlite3
import pandas as pd

records = pd.read_csv("data/fake_expenses.csv")
conn = sqlite3.connect("expenses.db")
try:
    records.to_sql("expenses",con=conn, schema="expenses", index=False, if_exists="delete_rows")
except Exception as e:
    print("Failed to save to schema: ", e)
finally:
    conn.close()
