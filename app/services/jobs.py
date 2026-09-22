"""Fila simples de jobs em background (thread + SQLite)."""
from __future__ import annotations

import logging
import threading
import traceback
from typing import Any, Callable
from uuid import uuid4

from app import db

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None]
JobFn = Callable[[ProgressFn], None]


def start_job(project_id: str, kind: str, fn: JobFn) -> dict[str, Any]:
    """Cria um job e executa `fn` numa thread daemon."""
    job = db.create_job(project_id, kind)
    job_id = job["id"]

    def _run() -> None:
        def report(progress: int, step: str) -> None:
            db.update_job(
                job_id,
                status="running",
                progress=max(0, min(100, int(progress))),
                step=step,
            )

        db.update_job(job_id, status="running", progress=1, step="Iniciando…")
        try:
            fn(report)
            db.update_job(job_id, status="done", progress=100, step="Concluído")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %s falhou", job_id)
            db.update_job(
                job_id,
                status="error",
                step="Erro",
                error=f"{exc}\n{traceback.format_exc()[-1500:]}",
            )

    threading.Thread(target=_run, name=f"job-{kind}-{job_id[:8]}", daemon=True).start()
    return job


def new_id() -> str:
    return str(uuid4())
