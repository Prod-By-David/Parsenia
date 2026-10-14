from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["generated images"])

GENERATED_DIR = (
    Path(__file__).resolve().parents[2]
    / "storage"
    / "generated"
)


@router.get("/api/generated/{filename}")
async def get_generated_image(filename: str):
    # Comprobar que el nombre corresponde a un archivo PNG
    # y que no contiene rutas adicionales.
    if (
        not filename.endswith(".png")
        or Path(filename).name != filename
        or filename in {".", ".."}
    ):
        raise HTTPException(
            status_code=400,
            detail="Nombre de archivo no válido.",
        )

    image_path = GENERATED_DIR / filename

    # Comprobar que la imagen existe.
    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="No se encuentra la imagen generada.",
        )

    # Devolver la imagen para que pueda mostrarse en el navegador.
    return FileResponse(
        path=image_path,
        media_type="image/png",
        content_disposition_type="inline",
    )