"""Persistência SQLite de projetos, personagens e jobs."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config import DB_PATH
from app.services.audio_mode import normalize_audio_mode, uses_music
from app.services.visual import normalize_preset, normalize_style


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            kind TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            progress INTEGER DEFAULT 0,
            step TEXT DEFAULT '',
            error TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id)")
    _ensure_column(conn, "projects", "aspect", "TEXT DEFAULT '16:9'")
    _ensure_column(conn, "projects", "youtube_title", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "youtube_description", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "youtube_tags", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "thumbnail_path", "TEXT")
    _ensure_column(conn, "projects", "captions_path", "TEXT")
    _ensure_column(conn, "projects", "pack_path", "TEXT")
    _ensure_column(conn, "projects", "burn_captions", "INTEGER DEFAULT 1")
    _ensure_column(conn, "projects", "add_music", "INTEGER DEFAULT 1")
    _ensure_column(conn, "projects", "visual_style", "TEXT DEFAULT 'cinematic'")
    _ensure_column(conn, "projects", "light_preset", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "camera_preset", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "atmosphere_preset", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "audio_mode", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "series_name", "TEXT DEFAULT ''")
    _ensure_column(conn, "projects", "episode_number", "INTEGER")
    conn.execute(
        """
        UPDATE projects
        SET audio_mode = CASE WHEN COALESCE(add_music, 1) = 1 THEN 'both' ELSE 'narration' END
        WHERE audio_mode IS NULL OR TRIM(audio_mode) = ''
        """
    )
    conn.commit()
    conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, name: str, decl: str) -> None:
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if name not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def create_project(title: str, theme: str, aspect: str = "16:9") -> dict[str, Any]:
    pid = str(uuid4())
    now = _now()
    aspect = "9:16" if aspect in ("9:16", "shorts", "vertical") else "16:9"
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO projects (
            id, title, theme, script, status, scenes_json, aspect,
            visual_style, audio_mode, created_at, updated_at
        )
        VALUES (?, ?, ?, '', 'draft', '[]', ?, 'cinematic', 'both', ?, ?)
        """,
        (pid, title, theme, aspect, now, now),
    )
    conn.commit()
    conn.close()
    return get_project(pid)  # type: ignore[return-value]


def list_projects() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_project(project_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
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
        "aspect",
        "youtube_title",
        "youtube_description",
        "youtube_tags",
        "thumbnail_path",
        "captions_path",
        "pack_path",
        "burn_captions",
        "add_music",
        "visual_style",
        "light_preset",
        "camera_preset",
        "atmosphere_preset",
        "audio_mode",
        "series_name",
        "episode_number",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_project(project_id)
    if "visual_style" in updates:
        updates["visual_style"] = normalize_style(str(updates["visual_style"] or ""))
    if "light_preset" in updates:
        updates["light_preset"] = normalize_preset(str(updates["light_preset"] or ""), "light")
    if "camera_preset" in updates:
        updates["camera_preset"] = normalize_preset(str(updates["camera_preset"] or ""), "camera")
    if "atmosphere_preset" in updates:
        updates["atmosphere_preset"] = normalize_preset(
            str(updates["atmosphere_preset"] or ""), "atmosphere"
        )
    if "series_name" in updates:
        updates["series_name"] = str(updates["series_name"] or "").strip()[:80]
    if "episode_number" in updates:
        updates["episode_number"] = _parse_episode(updates["episode_number"])
    if "audio_mode" in updates:
        mode = normalize_audio_mode(str(updates["audio_mode"] or ""))
        updates["audio_mode"] = mode
        updates["add_music"] = 1 if uses_music(mode) else 0
    elif "add_music" in updates:
        on = updates["add_music"] in (1, True, "1", "on", "true")
        updates["add_music"] = 1 if on else 0
        updates["audio_mode"] = "both" if on else "narration"
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
    conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
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
    d["burn_captions"] = int(d.get("burn_captions") or 0) == 1
    legacy_music = int(d.get("add_music") if d.get("add_music") is not None else 1) == 1
    d["audio_mode"] = normalize_audio_mode(d.get("audio_mode"), music=legacy_music)
    d["add_music"] = uses_music(d["audio_mode"])
    d["aspect"] = d.get("aspect") or "16:9"
    d["visual_style"] = normalize_style(d.get("visual_style"))
    d["light_preset"] = normalize_preset(d.get("light_preset"), "light")
    d["camera_preset"] = normalize_preset(d.get("camera_preset"), "camera")
    d["atmosphere_preset"] = normalize_preset(d.get("atmosphere_preset"), "atmosphere")
    d["series_name"] = (d.get("series_name") or "").strip()
    d["episode_number"] = _parse_episode(d.get("episode_number"))
    return d


def _parse_episode(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 1 else None
    text = str(value).strip()
    if not text or not text.isdigit():
        return None
    number = int(text)
    return number if number >= 1 else None


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
    row = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    conn.close()
    return _char_row_to_dict(row) if row else None


def list_characters(project_id: str | None = None, *, include_global: bool = True) -> list[dict[str, Any]]:
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


# ---------- Jobs ----------


def create_job(project_id: str, kind: str) -> dict[str, Any]:
    jid = str(uuid4())
    now = _now()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO jobs (id, project_id, kind, status, progress, step, error, created_at, updated_at)
        VALUES (?, ?, ?, 'queued', 0, 'Na fila', '', ?, ?)
        """,
        (jid, project_id, kind, now, now),
    )
    conn.commit()
    conn.close()
    return get_job(jid)  # type: ignore[return-value]


def get_job(job_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def latest_job(project_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_job(job_id: str, **fields: Any) -> dict[str, Any] | None:
    allowed = {"status", "progress", "step", "error"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_job(job_id)
    updates["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [job_id]
    conn = get_conn()
    conn.execute(f"UPDATE jobs SET {cols} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_job(job_id)
