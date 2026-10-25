import sys
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.assistant import create_assistant

router = APIRouter(prefix="/rag")

@router.post("/")
async def rag(query: str = Form(...)):
    assistant = create_assistant()
    input_messages = [
            {'type': 'user_input', 'content': [{"type": "text", "text":query}]}
        ]
    answer = assistant.rag(input_messages)
    return answer