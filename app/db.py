"""Persistência SQLite de projetos e personagens."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config import DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            theme TEXT NOT NULL,
            script TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            scenes_json TEXT DEFAULT '[]',
            audio_path TEXT,
            video_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            name TEXT NOT NULL,
            role TEXT DEFAULT '',
            visual_bible TEXT DEFAULT '',
            reference_images_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id)"
    )
    conn.commit()
    conn.close()


def create_project(title: str, theme: str) -> dict[str, Any]:
    pid = str(uuid4())
    now = _now()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO projects (id, title, theme, script, status, scenes_json, created_at, updated_at)
        VALUES (?, ?, ?, '', 'draft', '[]', ?, ?)
        """,
        (pid, title, theme, now, now),
    )
    conn.commit()
    conn.close()
    return get_project(pid)  # type: ignore[return-value]


def list_projects() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_project(project_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_project(project_id: str, **fields: Any) -> dict[str, Any] | None:
    allowed = {
        "title",
        "theme",
        "script",
        "status",
        "scenes_json",
        "audio_path",
        "video_path",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_project(project_id)
    updates["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [project_id]
    conn = get_conn()
    conn.execute(f"UPDATE projects SET {cols} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_project(project_id)


def delete_project(project_id: str) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM characters WHERE project_id = ?", (project_id,))
    cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    try:
        d["scenes"] = json.loads(d.pop("scenes_json") or "[]")
    except json.JSONDecodeError:
        d["scenes"] = []
    return d


def scenes_to_json(scenes: list[dict[str, Any]]) -> str:
    return json.dumps(scenes, ensure_ascii=False)


# ---------- Characters ----------


def _char_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    try:
        refs = json.loads(d.pop("reference_images_json") or "[]")
    except json.JSONDecodeError:
        refs = []
    if not isinstance(refs, list):
        refs = []
    d["reference_images"] = refs
    d["reference_image_path"] = refs[0] if refs else None
    return d


def create_character(
    *,
    name: str,
    role: str = "",
    visual_bible: str = "",
    project_id: str | None = None,
    reference_images: list[str] | None = None,
) -> dict[str, Any]:
    cid = str(uuid4())
    now = _now()
    refs = reference_images or []
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO characters
          (id, project_id, name, role, visual_bible, reference_images_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cid,
            project_id,
            name.strip(),
            (role or "").strip(),
            (visual_bible or "").strip(),
            json.dumps(refs, ensure_ascii=False),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return get_character(cid)  # type: ignore[return-value]


def get_character(character_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM characters WHERE id = ?", (character_id,)
    ).fetchone()
    conn.close()
    return _char_row_to_dict(row) if row else None


def list_characters(project_id: str | None = None, *, include_global: bool = True) -> list[dict[str, Any]]:
    """Lista personagens do projeto; opcionalmente inclui biblioteca global (project_id NULL)."""
    conn = get_conn()
    if project_id is None:
        rows = conn.execute(
            "SELECT * FROM characters WHERE project_id IS NULL ORDER BY name COLLATE NOCASE"
        ).fetchall()
    elif include_global:
        rows = conn.execute(
            """
            SELECT * FROM characters
            WHERE project_id = ? OR project_id IS NULL
            ORDER BY CASE WHEN project_id IS NULL THEN 1 ELSE 0 END, name COLLATE NOCASE
            """,
            (project_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM characters WHERE project_id = ? ORDER BY name COLLATE NOCASE",
            (project_id,),
        ).fetchall()
    conn.close()
    return [_char_row_to_dict(r) for r in rows]


def update_character(character_id: str, **fields: Any) -> dict[str, Any] | None:
    allowed = {"name", "role", "visual_bible", "reference_images", "project_id"}
    updates: dict[str, Any] = {}
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "reference_images":
            updates["reference_images_json"] = json.dumps(v or [], ensure_ascii=False)
        else:
            updates[k] = v.strip() if isinstance(v, str) else v
    if not updates:
        return get_character(character_id)
    updates["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [character_id]
    conn = get_conn()
    conn.execute(f"UPDATE characters SET {cols} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_character(character_id)


def delete_character(character_id: str) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def seed_demo_characters(project_id: str) -> list[dict[str, Any]]:
    """Insere Davi / Golias / Saul se o projeto ainda não tiver personagens."""
    from app.services.characters import DEMO_CHARACTERS

    existing = list_characters(project_id, include_global=False)
    if existing:
        return existing
    created = []
    for spec in DEMO_CHARACTERS:
        created.append(
            create_character(
                project_id=project_id,
                name=spec["name"],
                role=spec["role"],
                visual_bible=spec["visual_bible"],
            )
        )
    return created
