# Expense Analyst - LLM Zoomcamp Capstone Project

An intelligent, agentic AI assistant that allows users to query their personal financial data using natural language. 

## 📝 Problem Statement

Standard RAG (Retrieval-Augmented Generation) pipelines rely on vector databases and semantic search. While this is great for text documents (like FAQs or wikis), vector databases are fundamentally incapable of performing exact math, aggregations, or date-range filtering. If a user asks, *"How much did I spend on Groceries in August 2025 compared to November 2025?"*, standard RAG fails.

**The Solution:** 
This project abandons standard Semantic RAG in favor of a **Text-to-SQL Agent**. 
Users upload their expense data (CSV), which is ingested into a relational database (SQLite). The LLM is provided with the database schema and acts as a dynamic tool-caller. It translates the user's natural language into valid SQLite queries, executes them against the database, and summarizes the factual results back to the user.

## 🏗️ Architecture & Technologies

* **LLM:** Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) via `google-genai`.
* **Knowledge Base (Agent Data):** SQLite (Read-Only URI sandboxed during evaluation).
* **Monitoring & Feedback DB:** PostgreSQL.
* **Orchestration / Interface:** Streamlit (UI) & Python.
* **Dashboards:** Streamlit native dashboard + Grafana.
* **Evaluation:** Custom programmatic evaluation (Valid Execution Rate & Execution Accuracy) + LLM-as-a-Judge (Faithfulness/Relevance).

## 🚀 How to Run the Project

### 1. Prerequisites
* Python 3.10+ (using `uv` or `pip`)
* Docker and Docker Compose
* A Google Gemini API Key (`GEMINI_API_KEY`)

### 2. Setup Environment
Clone the repository and set up your `.env` file in the root directory:
```bash
GEMINI_API_KEY="your_google_api_key_here"
POSTGRES_USER="user"
POSTGRES_PASSWORD="password"
POSTGRES_DB="expense_analyst"
POSTGRES_HOST="localhost"
```
### 3. Start Dependencies (Database & Grafana)

```bash
docker-compose up -d
```
### 4. Install Dependencies
```bash
pip install -r requirements.txt
# OR if using uv:
uv pip install -r requirements.txt
```
### 5. Initialize Databases and Generate Fake Data
This will create the SQLite schema, Postgres tables, and generate a sample dataset.
```bash
python data_generator.py
python db/db_init.py
```

### 6. Run the Application UI
```bash
streamlit run app.py
```
- Once the app is running, upload the data/fake_expenses.csv file to ingest the data into the agent's knowledge base.
- You can also view the built-in analytics dashboard by running streamlit run dashboard.py.