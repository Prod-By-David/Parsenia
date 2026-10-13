
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/api/projects/{project_id}/images",
    tags=["images"],
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BACKEND_DIR / "parsenia.db"
UPLOADS_DIR = BACKEND_DIR / "storage" / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_project
            ON images(project_id, created_at)
        """)


initialize_database()


def project_exists(project_id: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

    return row is not None


@router.get("")
def get_project_images(project_id: str):
    if not project_exists(project_id):
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado.",
        )

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, filename, content_type,
                   size, created_at
            FROM images
            WHERE project_id = ?
            ORDER BY rowid ASC
            """,
            (project_id,),
        ).fetchall()

    images = []

    for row in rows:
        image = dict(row)
        image["url"] = (
            f"/api/projects/{project_id}/images/{image['id']}/file"
        )
        images.append(image)

    return {"success": True, "images": images}


@router.post("")
async def upload_project_image(
    project_id: str,
    file: UploadFile = File(...),
):
    if not project_exists(project_id):
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado.",
        )

    content_type = (file.content_type or "").lower()

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Usa JPG, PNG, WEBP o GIF.",
        )

    # Leer como máximo 10 MB más un byte para detectar archivos grandes.
    contents = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera el límite de 10 MB.",
        )

    # Comprobar la firma real del archivo, no solo su extensión o MIME.
    signatures = {
        "image/jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
        "image/png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda b: (
            len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP"
        ),
        "image/gif": lambda b: b.startswith((b"GIF87a", b"GIF89a")),
    }

    if not signatures[content_type](contents):
        raise HTTPException(
            status_code=400,
            detail="El contenido del archivo no coincide con su formato.",
        )

    image_id = str(uuid4())
    extension = ALLOWED_TYPES[content_type]

    project_dir = UPLOADS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    destination = project_dir / f"{image_id}{extension}"

    try:
        destination.write_bytes(contents)

        image = {
            "id": image_id,
            "project_id": project_id,
            "filename": Path(file.filename or "imagen").name,
            "content_type": content_type,
            "size": len(contents),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

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
                    image["id"],
                    image["project_id"],
                    image["filename"],
                    image["content_type"],
                    str(destination),
                    image["size"],
                    image["created_at"],
                ),
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    image["url"] = (
        f"/api/projects/{project_id}/images/{image_id}/file"
    )

    return {"success": True, "image": image}


@router.get("/{image_id}/file")
def get_image_file(project_id: str, image_id: str):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT file_path, content_type, filename
            FROM images
            WHERE id = ? AND project_id = ?
            """,
            (image_id, project_id),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Imagen no encontrada.",
        )

    path = Path(row["file_path"])

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="El archivo de imagen no está disponible.",
        )

    return FileResponse(
        path=path,
        media_type=row["content_type"],
        filename=row["filename"],
        content_disposition_type="inline",
    )