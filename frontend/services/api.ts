const API_URL = "/api";

export interface HealthResponse {
  status: string;
}

export async function checkBackend(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error("No se pudo conectar con Parsenia API");
  }

  return response.json();
}