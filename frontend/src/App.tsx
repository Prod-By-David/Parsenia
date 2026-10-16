import { useEffect, useState } from "react";
import {
  createProject,
  deleteProject,
  getProjects,
  getProjectMessages,
  addProjectMessage,
  type Project,
  type ProjectMessage,
} from "./services/projects";
import {
  checkBackend,
  sendMessage,
  type ChatMessage,
} from "./services/api";
import {
  getProjectImages,
  uploadProjectImage,
  editProjectImage,
  type ProjectImage,
} from "./services/images";
import "./App.css";

const MAX_IMAGE_SIZE = 10 * 1024 * 1024;

const ALLOWED_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
];

function App() {
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null,
  );
  const [messages, setMessages] = useState<ProjectMessage[]>([]);
  const [generatedImages, setGeneratedImages] = useState<Record<string, string>>({});
  const [images, setImages] = useState<ProjectImage[]>([]);

  const [projectName, setProjectName] = useState("");
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [editingImage, setEditingImage] = useState<ProjectImage | null>(null);

  const [isCreating, setIsCreating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingImages, setIsLoadingImages] = useState(false);
  const [error, setError] = useState("");

  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? null;

  // Crear una vista previa local del archivo seleccionado.
  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [selectedFile]);

  // Comprobar el backend y cargar los proyectos.
  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        await checkBackend();
        const data = await getProjects();

        if (!cancelled) {
          setProjects(data);
          setSelectedProjectId((current) => {
            if (current && data.some((project) => project.id === current)) {
              return current;
            }
            return data[0]?.id ?? null;
          });
          setBackendStatus("online");
        }
      } catch {
        if (!cancelled) {
          setBackendStatus("offline");
          setError("No se ha podido conectar con el servidor.");
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  // Cargar los mensajes del proyecto seleccionado.
  useEffect(() => {
    if (!selectedProjectId) {
      setMessages([]);
      setIsLoadingMessages(false);
      setEditingImage(null);
      return;
    }

    const projectId = selectedProjectId;
    let cancelled = false;

    async function loadMessages() {
      setIsLoadingMessages(true);
      setMessages([]);
      setEditingImage(null);
      setError("");

      try {
        const data = await getProjectMessages(projectId);

        if (!cancelled) {
          setMessages(data);
        }
      } catch {
        if (!cancelled) {
          setError("No se ha podido cargar la conversación del proyecto.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingMessages(false);
        }
      }
    }

    void loadMessages();

    return () => {
      cancelled = true;
    };
  }, [selectedProjectId]);

  // Cargar las imágenes guardadas del proyecto seleccionado.
  useEffect(() => {
    if (!selectedProjectId) {
      setImages([]);
      setIsLoadingImages(false);
      return;
    }

    const projectId = selectedProjectId;
    let cancelled = false;

    async function loadImages() {
      setImages([]);
      setIsLoadingImages(true);

      try {
        const data = await getProjectImages(projectId);

        if (!cancelled) {
          setImages(data);
        }
      } catch {
        if (!cancelled) {
          setError("No se han podido cargar las imágenes del proyecto.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingImages(false);
        }
      }
    }

    void loadImages();

    return () => {
      cancelled = true;
    };
  }, [selectedProjectId]);

  async function handleCreateProject() {
    const name = projectName.trim();

    if (!name || isCreating || isSending || isUploadingImage) {
      return;
    }

    setIsCreating(true);
    setError("");

    try {
      const project = await createProject(name);

      setProjects((current) => [...current, project]);
      setProjectName("");
      setSelectedFile(null);
      setEditingImage(null);
      setSelectedProjectId(project.id);
    } catch {
      setError("No se ha podido crear el proyecto.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeleteProject(project: Project) {
    if (
      isSending ||
      isUploadingImage ||
      isLoadingMessages ||
      isLoadingImages
    ) {
      return;
    }

    const confirmed = window.confirm(
      `¿Seguro que quieres eliminar "${project.name}" y sus mensajes e imágenes?`,
    );

    if (!confirmed) {
      return;
    }

    setError("");

    try {
      await deleteProject(project.id);

      const remaining = projects.filter((item) => item.id !== project.id);

      setProjects(remaining);

      if (selectedProjectId === project.id) {
        setSelectedFile(null);
        setEditingImage(null);
        setSelectedProjectId(remaining[0]?.id ?? null);
      }
    } catch {
      setError("No se ha podido eliminar el proyecto.");
    }
  }

  function handleSelectImage(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setError("Formato no permitido. Selecciona JPG, PNG, WEBP o GIF.");
      return;
    }

    if (file.size > MAX_IMAGE_SIZE) {
      setError("La imagen no puede superar los 10 MB.");
      return;
    }

    if (file.size === 0) {
      setError("El archivo seleccionado está vacío.");
      return;
    }

    setError("");
    setSelectedFile(file);
  }

  async function handleUploadImage() {
    const projectId = selectedProjectId;
    const file = selectedFile;

    if (!projectId || !file || isUploadingImage) {
      return;
    }

    setIsUploadingImage(true);
    setError("");

    try {
      const uploadedImage = await uploadProjectImage(projectId, file);

      setImages((current) => [...current, uploadedImage]);
      setSelectedFile(null);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "No se ha podido subir la imagen.",
      );
    } finally {
      setIsUploadingImage(false);
    }
  }

  async function handleSendMessage() {
    const content = input.trim();
    const projectId = selectedProjectId;

    if (
      !content ||
      !projectId ||
      isSending ||
      isLoadingMessages ||
      isUploadingImage
    ) {
      return;
    }

    setIsSending(true);
    setError("");
    setInput("");

    try {
      if (editingImage) {
        // Flujo de edición de imagen existente
        const userMessage = await addProjectMessage(
          projectId,
          "user",
          `Editar "${editingImage.filename}": ${content}`,
        );

        setMessages((current) => [...current, userMessage]);

        const response = await editProjectImage(
          projectId,
          editingImage.id,
          content,
        );

        const assistantMessage = await addProjectMessage(
          projectId,
          "assistant",
          `He editado la imagen a partir de tu instrucción.`,
        );

        setMessages((current) => [...current, assistantMessage]);
        setImages((current) => [...current, response.image]);
        setGeneratedImages((current) => ({
          ...current,
          [String(assistantMessage.id)]: response.image.url,
        }));
        setEditingImage(null);
      } else {
        // Flujo normal de chat/creación
        const userMessage = await addProjectMessage(
          projectId,
          "user",
          content,
        );

        const updatedHistory: ProjectMessage[] = [
          ...messages,
          userMessage,
        ];

        setMessages(updatedHistory);

        const conversationForAI: ChatMessage[] = updatedHistory.map(
          (message) => ({
            role: message.role,
            content: message.content,
          }),
        );

        const response = await sendMessage(conversationForAI);

        const assistantMessage = await addProjectMessage(
          projectId,
          "assistant",
          response.reply,
        );

        setMessages((current) => [...current, assistantMessage]);

        if (response.image_url) {
          setGeneratedImages((current) => ({
            ...current,
            [String(assistantMessage.id)]: response.image_url!,
          }));
        }
      }
    } catch {
      setError(
        "No se ha podido completar la operación. Comprueba la conexión con el servidor.",
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>,
  ) {
    if (event.key === "Enter") {
      event.preventDefault();
      void handleSendMessage();
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Parsenia</h1>
          <p>AI Image Creation & Editing</p>
        </div>

        <div className={`status status-${backendStatus}`}>
          <span className="status-dot" />
          {backendStatus === "checking" && "Conectando..."}
          {backendStatus === "online" && "API conectada"}
          {backendStatus === "offline" && "API desconectada"}
        </div>
      </header>

      <main className="projects-workspace">
        <aside className="projects-sidebar">
          <div className="panel-header">
            <h2>Mis proyectos</h2>
          </div>

          <form
            className="new-project-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateProject();
            }}
          >
            <input
              type="text"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              placeholder="Nombre del proyecto..."
              maxLength={100}
            />

            <button
              type="submit"
              disabled={
                !projectName.trim() ||
                isCreating ||
                isSending ||
                isUploadingImage
              }
            >
              {isCreating ? "Creando..." : "+ Crear proyecto"}
            </button>
          </form>

          <div className="projects-list">
            {projects.length === 0 ? (
              <p className="projects-empty">
                Todavía no tienes proyectos. Crea el primero arriba.
              </p>
            ) : (
              projects.map((project) => (
                <div
                  key={project.id}
                  className={`project-item ${
                    selectedProjectId === project.id
                      ? "project-item-selected"
                      : ""
                  }`}
                >
                  <button
                    type="button"
                    className="project-select"
                    disabled={
                      isSending ||
                      isUploadingImage ||
                      isLoadingMessages ||
                      isLoadingImages
                    }
                    onClick={() => {
                      setSelectedFile(null);
                      setEditingImage(null);
                      setSelectedProjectId(project.id);
                    }}
                  >
                    <span className="project-icon">▧</span>
                    <span className="project-name">{project.name}</span>
                  </button>

                  <button
                    type="button"
                    className="project-delete"
                    title={`Eliminar ${project.name}`}
                    aria-label={`Eliminar ${project.name}`}
                    disabled={
                      isSending ||
                      isUploadingImage ||
                      isLoadingMessages ||
                      isLoadingImages
                    }
                    onClick={() => void handleDeleteProject(project)}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>

        <section className="project-main">
          {error && (
            <div className="project-error" role="alert">
              {error}
              <button
                type="button"
                onClick={() => setError("")}
                aria-label="Cerrar aviso"
              >
                ×
              </button>
            </div>
          )}

          {selectedProject ? (
            <>
              <div className="panel-header">
                <div>
                  <h2>{selectedProject.name}</h2>
                  <p className="project-date">
                    Conversación de este proyecto
                  </p>
                </div>
              </div>

              <div className="workspace">
                <section className="chat-panel">
                  <div className="panel-header">
                    <h2>Conversación</h2>
                  </div>

                  <div className="messages">
                    {isLoadingMessages ? (
                      <p className="projects-empty">
                        Cargando conversación...
                      </p>
                    ) : messages.length === 0 ? (
                      <div className="welcome-message">
                        <h2>Empecemos a crear</h2>
                        <p>
                          Describe la imagen que quieres generar o editar.
                          Puedes adjuntar una imagen de referencia abajo o editar una existente desde la galería.
                        </p>
                      </div>
                    ) : (
                      messages.map((message) => (
                        <div
                          key={message.id}
                          className={`message message-${message.role}`}
                        >
                          <strong>
                            {message.role === "user" ? "Tú" : "Parsenia"}
                          </strong>

                          <p>{message.content}</p>

                          {generatedImages[String(message.id)] && (
                            <img
                              className="generated-image"
                              src={generatedImages[String(message.id)]}
                              alt="Imagen generada por Parsenia"
                              loading="lazy"
                            />
                          )}
                        </div>
                      ))
                    )}

                    {isSending && (
                      <div className="message message-assistant">
                        <strong>Parsenia</strong>
                        <p>{editingImage ? "Editando imagen..." : "Escribiendo..."}</p>
                      </div>
                    )}
                  </div>

                  {selectedFile && (
                    <div className="selected-image-preview">
                      {previewUrl && (
                        <img
                          src={previewUrl}
                          alt="Vista previa de la imagen seleccionada"
                        />
                      )}

                      <div className="selected-image-info">
                        <span>{selectedFile.name}</span>
                        <small>
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </small>
                      </div>

                      <button
                        type="button"
                        onClick={() => setSelectedFile(null)}
                        disabled={isUploadingImage}
                        aria-label="Cancelar imagen seleccionada"
                      >
                        ×
                      </button>
                    </div>
                  )}

                  {editingImage && (
                    <div className="selected-image-preview editing-banner">
                      <img
                        src={editingImage.url}
                        alt="Imagen seleccionada para editar"
                      />
                      <div className="selected-image-info">
                        <span>Editando: {editingImage.filename}</span>
                        <small>Escribe qué cambios quieres aplicar</small>
                      </div>
                      <button
                        type="button"
                        onClick={() => setEditingImage(null)}
                        disabled={isSending}
                        aria-label="Cancelar edición"
                      >
                        ×
                      </button>
                    </div>
                  )}

                  <div className="image-upload-controls">
                    <label
                      className="attach-image-button"
                      htmlFor="project-image-input"
                    >
                      {isUploadingImage ? "Subiendo..." : "＋ Adjuntar imagen"}
                    </label>

                    <input
                      id="project-image-input"
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      onChange={handleSelectImage}
                      disabled={
                        isUploadingImage ||
                        backendStatus !== "online"
                      }
                    />

                    {selectedFile && (
                      <button
                        type="button"
                        onClick={() => void handleUploadImage()}
                        disabled={
                          isUploadingImage ||
                          backendStatus !== "online"
                        }
                      >
                        {isUploadingImage ? "Subiendo..." : "Subir al proyecto"}
                      </button>
                    )}
                  </div>

                  <div className="composer">
                    <input
                      type="text"
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={
                        editingImage
                          ? "Describe los cambios para editar la imagen..."
                          : "Describe lo que quieres crear..."
                      }
                      disabled={
                        isSending ||
                        isLoadingMessages ||
                        isUploadingImage ||
                        backendStatus !== "online"
                      }
                    />

                    <button
                      className="send-button"
                      type="button"
                      onClick={() => void handleSendMessage()}
                      disabled={
                        isSending ||
                        isLoadingMessages ||
                        isUploadingImage ||
                        !input.trim() ||
                        backendStatus !== "online"
                      }
                    >
                      ↑
                    </button>
                  </div>
                </section>

                <section className="canvas-panel">
                  <div className="panel-header">
                    <h2>Imágenes del proyecto</h2>
                    <span>{images.length}</span>
                  </div>

                  <div className="project-image-gallery">
                    {isLoadingImages ? (
                      <p className="projects-empty">
                        Cargando imágenes...
                      </p>
                    ) : images.length === 0 ? (
                      <div className="image-placeholder">
                        <div>
                          <span className="placeholder-icon">✦</span>
                          <p>
                            Todavía no hay imágenes. Adjunta una imagen o genera una para comenzar.
                          </p>
                        </div>
                      </div>
                    ) : (
                      images.map((image) => (
                        <article
                          className="project-image-card"
                          key={image.id}
                        >
                          <a
                            href={image.url}
                            target="_blank"
                            rel="noreferrer"
                            title="Abrir imagen"
                          >
                            <img
                              src={image.url}
                              alt={image.filename}
                              loading="lazy"
                            />
                          </a>

                          <div className="image-card-footer">
                            <div className="image-card-meta">
                              <p title={image.filename}>{image.filename}</p>
                              <small>
                                {(image.size / (1024 * 1024)).toFixed(2)} MB
                              </small>
                            </div>
                            <button
                              type="button"
                              className="edit-image-action-btn"
                              onClick={() => setEditingImage(image)}
                              disabled={isSending}
                              title="Editar esta imagen"
                            >
                              Editar
                            </button>
                          </div>
                        </article>
                      ))
                    )}
                  </div>
                </section>
              </div>
            </>
          ) : (
            <div className="project-welcome">
              <span className="placeholder-icon">✦</span>
              <h2>Bienvenido a Parsenia</h2>
              <p>Crea o selecciona un proyecto para comenzar.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;