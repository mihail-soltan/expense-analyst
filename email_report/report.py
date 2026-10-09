import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.db_query import (
    get_monthly_total_spending_trend, 
    get_weekly_total_spending_trend, 
    get_monthly_spending_breakdown_by_category, 
    get_overall_category_expense_proportions, 
    get_transaction_frequency_vs_avg_spend_size_by_month
)
from visualizations import Visualizer
from email_report.email_utils import send_monthly_email
from rag_helper import RAGBase

from dotenv import load_dotenv
from google import genai
import markdown

load_dotenv()

llm_client = genai.Client()

INSTRUCTIONS = """
                You are a financial analyst whose task is to provide an overview for the given query results. 
                Each of these statistics will be accompanied by a plot generated in matplotlib.
               """

assistant = RAGBase(llm_client, instructions=INSTRUCTIONS)

monthly_total_spending_trend = get_monthly_total_spending_trend()
weekly_total_spending_trend = get_weekly_total_spending_trend()
monthly_spending_breakdown_by_category = get_monthly_spending_breakdown_by_category()
overall_category_expense_proportions = get_overall_category_expense_proportions()
transaction_frequency_vs_avg_spend_size_by_month = get_transaction_frequency_vs_avg_spend_size_by_month()

visualizer = Visualizer(
    monthly_total_spending_trend, 
    weekly_total_spending_trend,
    monthly_spending_breakdown_by_category,
    overall_category_expense_proportions,
    transaction_frequency_vs_avg_spend_size_by_month
)

plot_monthly_total_spending_trend = visualizer.plot_monthly_total_spending_trend()
plot_weekly_total_spending_trend = visualizer.plot_weekly_total_spending_trend()
plot_monthly_spending_breakdown_by_category = visualizer.plot_monthly_spending_breakdown_by_category()
plot_overall_category_expense_proportions = visualizer.plot_overall_category_expense_proportions()
plot_transaction_frequency_vs_avg_spend_size_by_month = visualizer.plot_transaction_frequency_vs_avg_spend_size_by_month()

prompt = f"""
    Please write a brief report for each of the following query results:
    monthly_total_spending_trend: {monthly_total_spending_trend},
    weekly_total_spending_trend: {weekly_total_spending_trend},
    monthly_spending_breakdown_by_category: {monthly_spending_breakdown_by_category},
    overall_category_expense_proportions: {overall_category_expense_proportions},
    transaction_frequency_vs_avg_spend_size_by_month: {transaction_frequency_vs_avg_spend_size_by_month}
"""
input_messages = [
            {'type': 'user_input', 'content': [{"type": "text", "text":prompt}]}
        ]

files_to_attach = [
    plot_monthly_total_spending_trend,
    plot_weekly_total_spending_trend,
    plot_monthly_spending_breakdown_by_category,
    plot_overall_category_expense_proportions,
    plot_transaction_frequency_vs_avg_spend_size_by_month
]

if __name__ == "__main__":
    print("--------------Generating report--------------")
    output = assistant.llm(input_messages)
    html = markdown.markdown(output.output_text)
    email_recipient = input("Please enter an email address: ")
    print("--------------Sending Email--------------")
    send_monthly_email(html, email_recipient, files_to_attach)
