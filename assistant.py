import sys

from dotenv import load_dotenv
from google import genai

from rag_helper import RAGBase
from tools import sql_function

tools = [{"type": "function", **sql_function}]

def create_assistant():
    load_dotenv()
  
    return RAGBase(
        llm_client=genai.Client(),
        tools=tools
    )

if __name__ == "__main__":
    assistant = create_assistant()

    prompt = "How much money did I spend on groceries in August 2025 vs October 2025? Also, what are all the categories I have in my expenses table?"
    input_messages = [
            {'type': 'user_input', 'content': [{"type": "text", "text":prompt}]}
        ]
    
    if len(sys.argv) > 1:
        input_messages = [
            {
            'type': 'user_input', 
            'content': [{"type": "text", "text":sys.argv[1]}]
            }
        ]

    answer = assistant.rag(input_messages)
    print(answer)