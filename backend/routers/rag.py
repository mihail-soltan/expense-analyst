import sys
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from psycopg import AsyncConnection
from services.assistant import create_assistant
from auth.jwt_bearer import get_current_user
from db.db_save import save_conversation
from db.dependencies import get_db_connection
router = APIRouter(prefix="/rag")

@router.post("/{workspace_id}/chat")
async def rag(workspace_id,
              query: str = Form(...), 
              current_user: str = Depends(get_current_user),
              conn: AsyncConnection = Depends(get_db_connection)
              ):
    async with conn.transaction():
        async with conn.cursor() as cur:
            await cur.execute("SELECT set_config('rls.user_id', %s, true)", (str(current_user),))
            await cur.execute("SELECT set_config('rls.workspace_id', %s, true)", (str(workspace_id),))

        assistant = create_assistant(conn=conn)
        input_messages = [
            {'type': 'user_input', 'content': [{"type": "text", "text":query}]}
        ]
    
        answer = await assistant.rag(input_messages)
        record = assistant.last_call
        await save_conversation(conn, current_user, workspace_id, record, query)
    return answer