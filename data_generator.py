import random
from datetime import datetime
import pandas as pd

SAMPLE_CATEGORY=[
    "Bills",
    "Entertainment",
    "Food&Drink",
    "Gifts",
    "Groceries",
    "Health&Wellbeing",
    "Shopping",
    "Other",
    "Subscriptions",
    "Transport",
    "Travel"
]

def random_timestamp(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d").timestamp()
    end = datetime.strptime(end_date, "%Y-%m-%d").timestamp()
    timestamp = int(random.uniform(start, end))
    date_with_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d, %H:%M:%S")
    purchase_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    return date_with_time, purchase_date

def get_mock_amount(category):
    match category:
        case "Bills":
            amount = random.uniform(1.0, 2.0)*1000
        case "Entertainment":
            amount = random.uniform(1.0, 3.0)*100
        case "Gifts":
            amount = random.uniform(1.0, 4.0)*100
        case "Subscriptions":
            amount = float(random.randint(1,50))
        case "Transport":
            amount = float(random.randint(1, 20))
        case "Travel":
            amount = random.uniform(1.0, 3.0)*1000
        case _:
            amount = random.uniform(1.0, 2.0)*100
    return round(amount, 2)

def generate_one(start_date, end_date):
    timestamp, purchase_date = random_timestamp(start_date, end_date)
    category = random.choice(SAMPLE_CATEGORY)
    amount = get_mock_amount(category)
    record = {
        "timestamp": timestamp,
        "purchase_date": purchase_date,
        "item": "N/A",
        "amount": amount,
        "category": category
    }

    return record


if __name__ == "__main__":
    records = []
    for i in range(0,1000):
        record = generate_one("2025-01-01", "2025-12-31")
        records.append(record)

    records_df = pd.DataFrame(records)
    records_df.to_csv("data/fake_expenses.csv", index=False)