import os
import tempfile
import re
from pathlib import Path

from gradio_client import Client, handle_file

SPACE_ID = "devalenya/qwen-image-2-1-studio"

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
    
    if "logo" in base_prompt.lower() or "minimalista" in base_prompt.lower():
        return f"{base_prompt}, minimalist vector graphic, clean lines, flat design, professional branding, 8k"
    
    return f"{base_prompt}, {high_end_modifiers}"

def parse_aspect_ratio(aspect_ratio_input: str) -> str:
    """
    Mapea los formatos cortos o del frontend al formato exacto que espera Gradio.
    """
    if "16:9" in aspect_ratio_input:
        return "Landscape · 16:9"
    if "9:16" in aspect_ratio_input:
        return "Portrait · 9:16"
    return "Square · 1:1"

def generate_image(
    prompt: str,
    mode: str = "Create an image",
    reference_path: str | None = None,
    aspect_ratio: str = "Square · 1:1",
    steps: int = 25,
    seed: int = 42,
    randomize_seed: bool = True,
) -> dict:
    """
    Genera o edita una imagen usando el espacio público de Qwen.
    Integra el enriquecimiento de prompts y el parseo de aspect ratio.
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

    # 1. Limpiar la etiqueta --ar si viniera en el texto y extraer el ratio
    ar_match = re.search(r"--ar\s+(\d+:\d+|\S+)", prompt)
    if ar_match:
        clean_user_prompt = re.sub(r"--ar\s+\S+", "", prompt).strip()
        aspect_ratio = parse_aspect_ratio(ar_match.group(1))
    else:
        clean_user_prompt = prompt
        aspect_ratio = parse_aspect_ratio(aspect_ratio)

    # 2. Aplicar ingeniería de prompts automática
    enhanced_prompt = enhance_prompt(clean_user_prompt)
    print(f"\n[Prompt Original]: {prompt}")
    print(f"[Prompt Mejorado]: {enhanced_prompt}")
    print(f"[Aspect Ratio]: {aspect_ratio}\n")

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
        prompt=enhanced_prompt,
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

    # Copiar el resultado a una ruta temporal propia
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