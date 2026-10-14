
const API_URL = "/api/projects";

export interface Project {
  id: string;
  name: string;
  created_at: string;
}

export interface ProjectMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface ProjectsResponse {
  success: boolean;
  projects: Project[];
}

interface CreateProjectResponse {
  success: boolean;
  project: Project;
}

interface MessagesResponse {
  success: boolean;
  project_id: string;
  messages: ProjectMessage[];
}

interface SaveMessageResponse {
  success: boolean;
  message: ProjectMessage;
}

async function checkResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Error de API: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getProjects(): Promise<Project[]> {
  const response = await fetch(API_URL);
  const data = await checkResponse<ProjectsResponse>(response);

  return data.projects;
}

export async function createProject(name: string): Promise<Project> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  const data = await checkResponse<CreateProjectResponse>(response);

  return data.project;
}

export async function deleteProject(id: string): Promise<void> {
  const response = await fetch(
    `${API_URL}/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );

  await checkResponse<{ success: boolean }>(response);
}

export async function getProjectMessages(
  projectId: string,
): Promise<ProjectMessage[]> {
  const response = await fetch(
    `${API_URL}/${encodeURIComponent(projectId)}/messages`,
  );

  const data = await checkResponse<MessagesResponse>(response);

  return data.messages;
}

export async function addProjectMessage(
  projectId: string,
  role: ProjectMessage["role"],
  content: string,
): Promise<ProjectMessage> {
  const response = await fetch(
    `${API_URL}/${encodeURIComponent(projectId)}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        id: crypto.randomUUID(),
        role,
        content,
        created_at: new Date().toISOString(),
      }),
    },
  );

  const data = await checkResponse<SaveMessageResponse>(response);

  return data.message;
}