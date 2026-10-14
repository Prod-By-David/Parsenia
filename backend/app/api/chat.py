
from pathlib import Path
import shutil

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.image_generator import generate_image

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

    print("\n--- HISTORIAL RECIBIDO ---")
    for message in data.messages:
        print(f"{message.role}: {message.content}")
    print("--- FIN DEL HISTORIAL ---\n")

    try:
        result = generate_image(
            prompt=last_message,
            mode="Create an image",
            steps=20,
        )

        source_path = Path(result["image_path"])

        # Guardamos una copia en el almacenamiento temporal del backend.
        generated_dir = (
            Path(__file__).resolve().parents[2]
            / "storage"
            / "generated"
        )
        generated_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{source_path.stem}.png"
        destination = generated_dir / filename
        shutil.copy2(source_path, destination)

        return {
            "success": True,
            "reply": "He generado una imagen a partir de tu descripción.",
            "image_url": f"/api/generated/{filename}",
            "seed": result["seed"],
            "details": result["details"],
            "message_count": len(data.messages),
        }

    except Exception as error:
        print(f"Error generando imagen: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=502,
            detail=(
                "No se pudo generar la imagen. "
                "Comprueba que el espacio de Qwen esté disponible "
                "e inténtalo de nuevo."
            ),
        ) from error