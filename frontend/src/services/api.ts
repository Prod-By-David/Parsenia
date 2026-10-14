const API_URL = "/api";

export interface HealthResponse {
  status: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  success: boolean;
  reply: string;
  message_count: number;
  image_url?: string;
  seed?: number | string;
  details?: unknown;
}

export async function checkBackend(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error("No se pudo conectar con Parsenia API");
  }

  return response.json();
}

export async function sendMessage(
  messages: ChatMessage[],
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messages,
    }),
  });

  if (!response.ok) {
    let errorMessage = "No se pudo generar la imagen";

    try {
      const errorData = await response.json();

      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      }
    } catch {
      // Conservamos el mensaje de error predeterminado.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}