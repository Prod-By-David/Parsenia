const API_URL = "/api/projects";

export interface ProjectImage {
  id: string;
  project_id: string;
  filename: string;
  content_type: string;
  size: number;
  created_at: string;
  url: string;
}

interface ImagesResponse {
  success: boolean;
  images: ProjectImage[];
}

interface UploadImageResponse {
  success: boolean;
  image: ProjectImage;
}

export interface EditImageResponse {
  success: boolean;
  image: ProjectImage;
  seed: number;
  details: string;
}

async function checkResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Error de API: ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Mantener el mensaje genérico si la respuesta no es JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

/**
 * Obtiene las imágenes guardadas en un proyecto.
 */
export async function getProjectImages(
  projectId: string,
): Promise<ProjectImage[]> {
  const response = await fetch(
    `${API_URL}/${encodeURIComponent(projectId)}/images`,
  );

  const data = await checkResponse<ImagesResponse>(response);

  return data.images;
}

/**
 * Sube una imagen al proyecto seleccionado.
 */
export async function uploadProjectImage(
  projectId: string,
  file: File,
): Promise<ProjectImage> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/${encodeURIComponent(projectId)}/images`,
    {
      method: "POST",
      body: formData,
    },
  );

  const data = await checkResponse<UploadImageResponse>(response);

  return data.image;
}

/**
 * Edita una imagen existente utilizando una instrucción de texto.
 */
export async function editProjectImage(
  projectId: string,
  referenceImageId: string,
  prompt: string,
): Promise<EditImageResponse> {
  const response = await fetch(
    `${API_URL}/${encodeURIComponent(projectId)}/images/edit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reference_image_id: referenceImageId,
        prompt: prompt,
      }),
    },
  );

  return checkResponse<EditImageResponse>(response);
}

export function getProjectImageUrl(
  projectId: string,
  imageId: string,
): string {
  return `${API_URL}/${encodeURIComponent(projectId)}/images/${encodeURIComponent(imageId)}/file`;
}