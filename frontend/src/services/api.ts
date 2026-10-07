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
    throw new Error("No se pudo enviar el mensaje");
  }

  return response.json();
}