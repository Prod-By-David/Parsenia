from datetime import datetime, timezone
from pathlib import Path
import shutil
import sqlite3
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.image_generator import generate_image

router = APIRouter(prefix="/api/chat", tags=["chat"])

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BACKEND_DIR / "parsenia.db"
UPLOADS_DIR = BACKEND_DIR / "storage" / "uploads"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    project_id: str | None = None


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


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
    print(f"Project ID: {data.project_id}")
    print("--- FIN DEL HISTORIAL ---\n")

    try:
        result = generate_image(
            prompt=last_message,
            mode="Create an image",
            steps=20,
        )

        source_path = Path(result["image_path"])

        image_id = str(uuid4())
        filename = f"{image_id}.png"

        # Si se proporciona project_id, guardamos y registramos en la BD del proyecto
        if data.project_id:
            project_dir = UPLOADS_DIR / data.project_id
            project_dir.mkdir(parents=True, exist_ok=True)
            destination = project_dir / filename
            shutil.copy2(source_path, destination)

            file_size = destination.stat().st_size
            created_at = datetime.now(timezone.utc).isoformat()
            original_filename = f"generated_{source_path.stem}.png"

            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO images (
                        id, project_id, filename, content_type,
                        file_path, size, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        image_id,
                        data.project_id,
                        original_filename,
                        "image/png",
                        str(destination),
                        file_size,
                        created_at,
                    ),
                )

            image_url = f"/api/projects/{data.project_id}/images/{image_id}/file"
        else:
            # Fallback temporal si no se envía project_id
            generated_dir = BACKEND_DIR / "storage" / "generated"
            generated_dir.mkdir(parents=True, exist_ok=True)
            destination = generated_dir / filename
            shutil.copy2(source_path, destination)
            image_url = f"/api/generated/{filename}"

        return {
            "success": True,
            "reply": "He generado una imagen a partir de tu descripción.",
            "image_url": image_url,
            "image_id": image_id,
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