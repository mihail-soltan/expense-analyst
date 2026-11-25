# from backend.db.db_init import get_sqlite_connection
from db.db_init import get_sqlite_connection, get_pg_connection
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from decimal import Decimal
import time
import json

import pandas as pd


INSTRUCTIONS = '''
You are a financial assistant who analyses data related to expenses. 
You answer questions based on the context from an expenses table in an POSTGRESQL database.
Your tasks are: 

- Turn the prompt into a valid POSTGRESQL query based on the provided schema. 
- Call a SQL query function.
- Respond to the question using human language based on the output of the query.

If the prompt isn't relevant or is asking for data that doesn't exist in the provided schema, let the user know.

SCHEMA:
CREATE TABLE categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE incomes (
    income_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    date DATE,
    source TEXT,
    amount NUMERIC(10,2) CONSTRAINT income_chk_positive CHECK (amount > 0),
    description TEXT,
    invoice_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE expenses (
    expense_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    date DATE,
    item TEXT,
    amount NUMERIC(10,2) CONSTRAINT expense_chk_positive CHECK (amount > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
'''

@dataclass
class LLMCallRecord:
    model: str
    prompt: str
    instructions: str
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)

class Question(BaseModel):
    question: str = Field(description="The question a user may ask in regards to their expense records")
    ground_truth_sql: str = Field(description="The valid SQLITE SQL query that can be used to retrieve the requested information from the database")

class GoldenDataSet(BaseModel):
    questions: List[Question]

class SQLString(BaseModel):
    sql: str = Field(description="A valid SQLite SQL string")

class SQLStringList(BaseModel):
    queries: List[SQLString]

def calc_price(usage):
    input_price_per_million =  1.50
    output_price_per_million = 9.00

    input_cost = (usage.total_input_tokens / 1_000_000) * input_price_per_million
    output_cost = (usage.total_output_tokens / 1_000_000) * output_price_per_million
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }

def calc_total_price(usages):
    total_cost = 0.0

    for usage in usages:
        cost = calc_price(usage)
        total_cost = total_cost + cost["total_cost"]

    return total_cost

def serialize(obj):
    if isinstance(obj, datetime) or isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type not serializable: {type(obj)!r}")

class RAGBase:
    def __init__(
      self,
      llm_client,
      conn,
      tools=None,
      instructions=INSTRUCTIONS,
      model='gemini-3.5-flash',
    ):
        self.llm_client = llm_client
        self.conn = conn
        self.instructions = instructions
        self.model=model
        self.tools=tools
        self.usages = []
        self.last_usage = None
        self.last_call: LLMCallRecord = None

    async def execute_query(self, query):
        async with self.conn.cursor() as cur:
            await cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = await cur.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            
            return results

    def llm(self, input, previous_interaction_id=None):
        input_messages = []
        input_messages.extend(input)

        start_time = time.time()
        response = self.llm_client.interactions.create(
            system_instruction=self.instructions,
            model=self.model,
            input=input_messages,
            tools=self.tools, 
            previous_interaction_id=previous_interaction_id
        )
        response_time = time.time() - start_time
        self._log_response(input_messages, response, response_time)
        self.usages.append(response.usage)
        self.last_usage = response.usage
        
        return response

    def llm_structured_response(self, input, schema, previous_interaction_id=None):

        response = self.llm_client.interactions.create(
            system_instruction=self.instructions,
            model=self.model,
            input=input,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": schema
            },
            previous_interaction_id=previous_interaction_id
            )
        self.usages.append(response.usage)
        self.last_usage = response.usage 
        return response

    def get_function_call(self, step):
        args = step.arguments
        function_call = {
            "type": "function_result",
            "name": step.name,
            "call_id": step.id,
        }
        return function_call, args

    async def rag(self, query):
        llm_response = self.llm(query)
        current_interaction = {
            "id": llm_response.id,
            "status": llm_response.status,
            "steps": llm_response.steps,
            "output": llm_response.output_text

        }
        while current_interaction["status"] == 'requires_action':
            results_to_send = []
            for step in current_interaction["steps"]:
                if step.type == "model_output":
                    for content_block in step.content:
                        if content_block.type == "text":
                            print(content_block.text)
                elif step.type == "function_call":
                    function_call, args = self.get_function_call(step)
                    sql_result = await self.execute_query(**args)
                    sql_result = json.dumps(sql_result, default=serialize)
                    function_call["result"] = [{"type": "text", "text": sql_result}]
                    results_to_send.append(function_call)
            if len(results_to_send) > 0:
                new_interaction = self.llm(results_to_send, current_interaction["id"])
                current_interaction["status"] = new_interaction.status
                current_interaction["id"] = new_interaction.id
                current_interaction["steps"] = new_interaction.steps
                current_interaction["output"] = new_interaction.output_text

        return current_interaction

    def total_cost(self):
        return calc_total_price(self.usages)


    def _log_response(self, prompt, response, response_time):
        usage = response.usage
        cost = calc_price(usage)

        call_record = LLMCallRecord(
            model=self.model,
            prompt=prompt,
            instructions=self.instructions,
            answer=response.output_text,
            prompt_tokens=usage.total_input_tokens,
            completion_tokens=usage.total_output_tokens,
            total_tokens=usage.total_tokens,
            response_time=response_time,
            cost=cost["total_cost"]
        )
    
        print(call_record)
        self.last_call = call_record