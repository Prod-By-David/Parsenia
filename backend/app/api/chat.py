from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str


@router.post("")
async def chat(data: ChatMessage):
    message = data.message.strip()

    if not message:
        return {
            "success": False,
            "message": "El mensaje no puede estar vacío.",
        }

    return {
        "success": True,
        "reply": f"He recibido tu mensaje: {message}",
    }