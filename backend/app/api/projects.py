
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])

DATABASE_PATH = Path(__file__).resolve().parents[2] / "parsenia.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_project
            ON messages(project_id, created_at)
        """)


initialize_database()


class ProjectCreate(BaseModel):
    name: str


class MessageCreate(BaseModel):
    role: str
    content: str


def project_exists(project_id: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

    return row is not None


@router.get("")
def get_projects():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, name, created_at
            FROM projects
            ORDER BY created_at ASC
        """).fetchall()

    return {
        "success": True,
        "projects": [dict(row) for row in rows],
    }


@router.post("")
def create_project(data: ProjectCreate):
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="El nombre del proyecto no puede estar vacío.",
        )

    project = {
        "id": str(uuid4()),
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (project["id"], project["name"], project["created_at"]),
        )

    return {
        "success": True,
        "project": project,
    }


@router.get("/{project_id}/messages")
def get_project_messages(project_id: str):
    if not project_exists(project_id):
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado.",
        )

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE project_id = ?
            ORDER BY rowid ASC
            """,
            (project_id,),
        ).fetchall()

    return {
        "success": True,
        "project_id": project_id,
        "messages": [dict(row) for row in rows],
    }


@router.post("/{project_id}/messages")
def add_project_message(project_id: str, data: MessageCreate):
    if not project_exists(project_id):
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado.",
        )

    if data.role not in ("user", "assistant"):
        raise HTTPException(
            status_code=400,
            detail="El rol debe ser user o assistant.",
        )

    content = data.content.strip()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío.",
        )

    message = {
        "id": str(uuid4()),
        "role": data.role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO messages
                (id, project_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message["id"],
                project_id,
                message["role"],
                message["content"],
                message["created_at"],
            ),
        )

    return {
        "success": True,
        "message": message,
    }


@router.delete("/{project_id}")
def delete_project(project_id: str):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Proyecto no encontrado.",
            )

    return {
        "success": True,
        "message": "Proyecto eliminado correctamente.",
    }