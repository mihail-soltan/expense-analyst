from pydantic import BaseModel
from typing import Literal
from google import genai
from dotenv import load_dotenv
from rag_evaluator import llm_structured_retry

class RelevanceVerdict(BaseModel):
    relevance: Literal["NON_RELEVANT", "PARTLY_RELEVANT", "RELEVANT"]
    explanation: str

judge_instructions = """
You are an expert evaluator for a RAG system.
Analyze the relevance of the generated answer to the given question.

Classify the answer as:
- RELEVANT: the answer addresses the question
- PARTLY_RELEVANT: the answer partially addresses the question
- NON_RELEVANT: the answer does not address the question
""".strip()

judge_prompt = """
Question: {question}
Generated Answer: {answer}
""".strip()

def evaluate_relevance(question, answer, llm_client=None):
    if llm_client is None:
        llm_client = genai.Client()

    prompt = judge_prompt.format(
        question=question,
        answer=answer
    )
    result, usage = llm_structured_retry(
        llm_client,
        judge_instructions,
        prompt,
        RelevanceVerdict.model_json_schema()   
    )
    return result["relevance"], result["explanation"]

if __name__ == "__main__":
    load_dotenv()

    question = "Compare how much I spent on groceries in August 2025 vs September 2025 "
    answer = "You spent 1000$ in August and 800$ in September."

    relevance, explanation = evaluate_relevance(question, answer)
    print(relevance)
    print(explanation)