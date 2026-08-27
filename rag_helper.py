import json
import pandas as pd
from pydantic import BaseModel, Field
from typing import List
from sqlite_db import get_db_connection

INSTRUCTIONS = '''
You are a financial assistant who analyses data related to expenses. 
You answer questions based on the context from an expenses table in an SQLITE database.
Your tasks are: 

- Turn the prompt into a valid SQLITE SQL query based on the provided schema. 
- Call a SQL query function.
- Respond to the question using human language based on the output of the query.

If the prompt isn't relevant or is asking for data that doesn't exist in the provided schema, let the user know.

SCHEMA:
CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    purchase_date DATE NOT NULL,
                    item TEXT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL
                    )
'''
class Question(BaseModel):
    question: str = Field(description="The question a user may ask in regards to their expense records")
    ground_truth_sql: str = Field(description="The valid SQLITE SQL query that can be used to retrieve the requested information from the database")

class GoldenDataSet(BaseModel):
    questions: List[Question]

class SQLString(BaseModel):
    sql: str = Field(description="A valid SQLite SQL string")

class SQLStringList(BaseModel):
    queries: List[SQLString]

class RAGBase:
    def __init__(
      self,
      llm_client,
      tools=None,
      instructions=INSTRUCTIONS,
      model='gemini-3.5-flash',
            
    ):
        self.llm_client = llm_client
        self.instructions = instructions
        self.model=model
        self.tools=tools
        self.usages = []
        self.last_usage = None


    def execute_query(self, query):
        db_conn = get_db_connection()
        results_df = pd.read_sql(query, db_conn)

        results = results_df.to_dict(orient="records")
        db_conn.close()
        return results

    def llm(self, input, previous_interaction_id=None):
        input_messages = []
        input_messages.extend(input)

        response = self.llm_client.interactions.create(
            system_instruction=self.instructions,
            model=self.model,
            input=input_messages,
            tools=self.tools, 
            previous_interaction_id=previous_interaction_id
        )
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

    def rag(self, query):
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
                    sql_result = self.execute_query(**args)
                    sql_result = json.dumps(sql_result)
                    function_call["result"] = [{"type": "text", "text": sql_result}]
                    results_to_send.append(function_call)
            if len(results_to_send) > 0:
                new_interaction = self.llm(results_to_send, current_interaction["id"])
                current_interaction["status"] = new_interaction.status
                current_interaction["id"] = new_interaction.id
                current_interaction["steps"] = new_interaction.steps
                current_interaction["output"] = new_interaction.output_text

        return current_interaction