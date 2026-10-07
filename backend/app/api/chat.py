from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@router.post("")
async def chat(data: ChatRequest):
    if not data.messages:
        return {
            "success": False,
            "message": "La conversación está vacía.",
        }

    last_message = data.messages[-1].content.strip()

    if not last_message:
        return {
            "success": False,
            "message": "El último mensaje está vacío.",
        }

    # Mostramos temporalmente en la terminal
    # todo el historial recibido.
    print("\n--- HISTORIAL RECIBIDO ---")

    for message in data.messages:
        print(f"{message.role}: {message.content}")

    print("--- FIN DEL HISTORIAL ---\n")

    return {
        "success": True,
        "reply": f"He recibido tu mensaje: {last_message}",
        "message_count": len(data.messages),
    }