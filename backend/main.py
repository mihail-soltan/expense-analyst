from fastapi import FastAPI
from routers import rag

app = FastAPI()
app.include_router(rag.router)

@app.get("/")
def root():
    return {"message": "Expense Analyst Backend is Running"}