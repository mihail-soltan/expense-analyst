import sys
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from services.assistant import create_assistant
from auth.jwt_bearer import get_current_user
router = APIRouter(prefix="/rag")

@router.post("/")
async def rag(query: str = Form(...), current_user: str = Depends(get_current_user)):
    assistant = create_assistant()
    input_messages = [
            {'type': 'user_input', 'content': [{"type": "text", "text":query}]}
        ]
    answer = assistant.rag(input_messages)
    return answer