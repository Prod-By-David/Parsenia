const API_URL = "/api";

export interface HealthResponse {
  status: string;
}

export interface ChatResponse {
  success: boolean;
  reply: string;
}

export async function checkBackend(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error("No se pudo conectar con Parsenia API");
  }

  return response.json();
}

export async function sendMessage(
  message: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

  if (!response.ok) {
    throw new Error("No se pudo enviar el mensaje");
  }

  return response.json();
}