
import os
import tempfile
from pathlib import Path

from gradio_client import Client, handle_file


SPACE_ID = "devalenya/qwen-image-2-1-studio"


def generate_image(
    prompt: str,
    mode: str = "Create an image",
    reference_path: str | None = None,
    aspect_ratio: str = "Square · 1:1",
    steps: int = 20,
    seed: int = 42,
    randomize_seed: bool = True,
) -> dict:
    """
    Genera o edita una imagen usando el espacio público de Qwen.

    Devuelve la ruta temporal de la imagen y los detalles de generación.
    """

    prompt = prompt.strip()

    if not prompt:
        raise ValueError("La descripción de la imagen no puede estar vacía.")

    if mode not in {
        "Create an image",
        "Edit an image",
        "Transparent PNG",
    }:
        raise ValueError("El modo de generación no es válido.")

    if mode == "Edit an image" and not reference_path:
        raise ValueError("Para editar una imagen debes proporcionar una foto.")

    if reference_path and not Path(reference_path).is_file():
        raise ValueError("No se encuentra la imagen de referencia.")

    token = os.getenv("HF_TOKEN")

    client = Client(
        SPACE_ID,
        token=token or None,
    )

    reference = (
        handle_file(reference_path)
        if reference_path
        else None
    )

    result = client.predict(
        prompt=prompt,
        mode=mode,
        reference=reference,
        aspect_ratio=aspect_ratio,
        steps=steps,
        seed=seed,
        randomize_seed=randomize_seed,
        api_name="/generate",
    )

    if not isinstance(result, (tuple, list)) or len(result) < 4:
        raise RuntimeError(
            "El modelo devolvió una respuesta inesperada."
        )

    image_path = Path(result[0])

    if not image_path.is_file():
        raise RuntimeError(
            "El modelo no devolvió un archivo de imagen disponible."
        )

    # Copiar el resultado a una ruta temporal propia para no depender
    # de que el cliente elimine o cambie su archivo temporal.
    with tempfile.NamedTemporaryFile(
        prefix="parsenia_",
        suffix=".png",
        delete=False,
    ) as temporary_file:
        output_path = Path(temporary_file.name)

    try:
        output_path.write_bytes(image_path.read_bytes())
    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    return {
        "image_path": str(output_path),
        "seed": result[2],
        "details": result[3],
    }

def enhance_prompt(user_prompt: str) -> str:
    """
    Enriquece automáticamente el prompt del usuario con modificadores 
    de calidad profesional de gama alta (estilo Midjourney / Flux / OpenAI).
    """
    base_prompt = user_prompt.strip()
    
    # Modificadores estándar de alta fidelidad
    high_end_modifiers = (
        "masterpiece, highly detailed, 8k resolution, photorealistic, "
        "cinematic volumetric lighting, sharp focus, professional color grading"
    )
    
    # Si el usuario busca algo específico de diseño o arte, adaptamos el sufijo
    if "logo" in base_prompt.lower() or "minimalista" in base_prompt.lower():
        return f"{base_prompt}, minimalist vector graphic, clean lines, flat design, professional branding, 8k"
    
    return f"{base_prompt}, {high_end_modifiers}"

def generate_image(prompt: str, mode: str = "Create an image", steps: int = 25):
    # 1. Mejoramos el prompt automáticamente
    enhanced = enhance_prompt(prompt)
    print(f"\n[Prompt Original]: {prompt}")
    print(f"[Prompt Mejorado]: {enhanced}\n")