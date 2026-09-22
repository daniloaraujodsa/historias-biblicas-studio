"""Histórias Bíblicas Studio — API + UI pt-BR."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.config import DEFAULT_THEME, DEFAULT_VOICE, EXPORTS_DIR, PORT, PROJECTS_DIR
from app.services import images, jobs, pipeline, scenes, tts

app = FastAPI(title="Histórias Bíblicas Studio", version="1.1.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["basename"] = lambda p: Path(p or "").name
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

STATUS_LABELS = {
    "draft": "Rascunho",
    "script_ready": "Roteiro",
    "scenes_ready": "Cenas",
    "audio_ready": "Narração",
    "images_ready": "Imagens",
    "video_ready": "Vídeo pronto",
}


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


def _project_dir(project_id: str) -> Path:
    p = PROJECTS_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    (p / "images").mkdir(exist_ok=True)
    (p / "audio").mkdir(exist_ok=True)
    (p / "characters").mkdir(exist_ok=True)
    return p


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "application/json" in accept and "text/html" not in accept.split(",")[0]


def _job_redirect(request: Request, project_id: str, job: dict[str, Any]) -> Any:
    if _wants_json(request):
        return JSONResponse({"ok": True, "job_id": job["id"], "project_id": project_id})
    return RedirectResponse(f"/projects/{project_id}?job={job['id']}", status_code=303)


def _save_character_upload(project_id: str, character_id: str, upload: UploadFile) -> str:
    pdir = _project_dir(project_id) / "characters"
    suffix = Path(upload.filename or "ref.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".jpg"
    dest = pdir / f"{character_id}{suffix}"
    data = upload.file.read()
    if not data:
        raise HTTPException(400, "Arquivo de imagem vazio")
    dest.write_bytes(data)
    return str(dest)


def _page_ctx(request: Request, **extra: Any) -> dict[str, Any]:
    ctx = {
        "request": request,
        "status_labels": STATUS_LABELS,
        "default_theme": DEFAULT_THEME,
        "default_voice": DEFAULT_VOICE,
    }
    ctx.update(extra)
    return ctx


# ---------- Páginas ----------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> Any:
    projects = db.list_projects()
    return templates.TemplateResponse(
        "index.html",
        _page_ctx(request, projects=projects),
    )


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_page(request: Request, project_id: str) -> Any:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projeto não encontrado")
    characters = db.list_characters(project_id, include_global=False)
    job = db.latest_job(project_id)
    return templates.TemplateResponse(
        "project.html",
        _page_ctx(
            request,
            project=project,
            characters=characters,
            voices=tts.list_pt_br_voices(),
            image_provider_label=images.active_provider_label(),
            job=job,
            status_label=STATUS_LABELS.get(project.get("status") or "", project.get("status") or ""),
        ),
    )


# ---------- Projetos ----------


@app.post("/api/projects")
async def api_create_project(
    title: str = Form(...),
    theme: str = Form(DEFAULT_THEME),
    aspect: str = Form("16:9"),
) -> RedirectResponse:
    title = title.strip() or "Novo projeto"
    theme = theme.strip() or DEFAULT_THEME
    project = db.create_project(title, theme, aspect=aspect)
    _project_dir(project["id"])
    return RedirectResponse(f"/projects/{project['id']}", status_code=303)


@app.post("/api/projects/demo-davi-golias")
async def api_demo_davi_golias(aspect: str = Form("16:9")) -> RedirectResponse:
    from app.services import demo_script

    project = db.create_project(
        demo_script.DAVI_GOLIAS_TITLE, demo_script.DAVI_GOLIAS_THEME, aspect=aspect
    )
    pid = project["id"]
    _project_dir(pid)
    scene_list = scenes.segment_script(
        demo_script.DAVI_GOLIAS_SCRIPT,
        hints=demo_script.DAVI_GOLIAS_SCENE_HINTS,
    )
    db.update_project(
        pid,
        script=demo_script.DAVI_GOLIAS_SCRIPT,
        scenes_json=db.scenes_to_json(scene_list),
        status="script_ready",
    )
    db.seed_demo_characters(pid)
    return RedirectResponse(f"/projects/{pid}", status_code=303)


@app.post("/api/projects/{project_id}/script")
async def api_save_script(project_id: str, script: str = Form("")) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    db.update_project(project_id, script=script.strip(), status="script_ready")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/settings")
async def api_settings(
    project_id: str,
    aspect: str = Form("16:9"),
    burn_captions: str = Form("off"),
    add_music: str = Form("off"),
) -> RedirectResponse:
    if not db.get_project(project_id):
        raise HTTPException(404)
    db.update_project(
        project_id,
        aspect="9:16" if aspect == "9:16" else "16:9",
        burn_captions=1 if burn_captions in ("on", "1", "true") else 0,
        add_music=1 if add_music in ("on", "1", "true") else 0,
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/youtube")
async def api_youtube_meta(
    project_id: str,
    youtube_title: str = Form(""),
    youtube_description: str = Form(""),
    youtube_tags: str = Form(""),
) -> RedirectResponse:
    if not db.get_project(project_id):
        raise HTTPException(404)
    db.update_project(
        project_id,
        youtube_title=youtube_title.strip(),
        youtube_description=youtube_description.strip(),
        youtube_tags=youtube_tags.strip(),
    )
    return RedirectResponse(f"/projects/{project_id}#publicar", status_code=303)


# ---------- Jobs / pipeline ----------


@app.get("/api/jobs/{job_id}")
async def api_get_job(job_id: str) -> JSONResponse:
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    return JSONResponse(job)


@app.get("/api/projects/{project_id}/job")
async def api_latest_job(project_id: str) -> JSONResponse:
    job = db.latest_job(project_id)
    if not job:
        return JSONResponse({"status": "idle"})
    return JSONResponse(job)


@app.post("/api/projects/{project_id}/segment")
async def api_segment(request: Request, project_id: str) -> Any:
    if not db.get_project(project_id):
        raise HTTPException(404)

    def fn(report):
        report(20, "Segmentando roteiro…")
        pipeline.run_segment(project_id)
        report(100, "Cenas prontas")

    job = jobs.start_job(project_id, "segment", fn)
    return _job_redirect(request, project_id, job)


@app.post("/api/projects/{project_id}/tts")
async def api_tts(
    request: Request,
    project_id: str,
    voice: str = Form(DEFAULT_VOICE),
) -> Any:
    if not db.get_project(project_id):
        raise HTTPException(404)

    def fn(report):
        pipeline.run_tts(project_id, voice or DEFAULT_VOICE, report)

    job = jobs.start_job(project_id, "tts", fn)
    return _job_redirect(request, project_id, job)


@app.post("/api/projects/{project_id}/images")
async def api_images(request: Request, project_id: str) -> Any:
    if not db.get_project(project_id):
        raise HTTPException(404)

    def fn(report):
        pipeline.run_images(project_id, report)

    job = jobs.start_job(project_id, "images", fn)
    return _job_redirect(request, project_id, job)


@app.post("/api/projects/{project_id}/render")
async def api_render(request: Request, project_id: str) -> Any:
    if not db.get_project(project_id):
        raise HTTPException(404)

    def fn(report):
        pipeline.run_render(project_id, report)

    job = jobs.start_job(project_id, "render", fn)
    return _job_redirect(request, project_id, job)


@app.post("/api/projects/{project_id}/pipeline")
async def api_full_pipeline(
    request: Request,
    project_id: str,
    voice: str = Form(DEFAULT_VOICE),
) -> Any:
    if not db.get_project(project_id):
        raise HTTPException(404)

    def fn(report):
        pipeline.run_full(project_id, voice or DEFAULT_VOICE, report)

    job = jobs.start_job(project_id, "pipeline", fn)
    return _job_redirect(request, project_id, job)


@app.post("/api/projects/{project_id}/images/{scene_index}/regenerate")
async def api_regenerate_scene_image(
    request: Request, project_id: str, scene_index: int
) -> Any:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)

    def fn(report):
        report(10, f"Regenerando cena {scene_index + 1}…")
        proj = db.get_project(project_id)
        scene_list = proj.get("scenes") or []
        target = next(
            (s for s in scene_list if int(s.get("index", -1)) == scene_index), None
        )
        if target is None:
            raise ValueError("Cena não encontrada")
        img_dir = _project_dir(project_id) / "images"
        out = img_dir / f"cena-{scene_index:02d}-{uuid4().hex[:6]}.jpg"
        import time as _t

        _path, source, prompt = pipeline._gen_image(
            project_id, target, out, seed_salt=int(_t.time()) % 1_000_000
        )
        target["image_path"] = str(out)
        target["image_source"] = source
        target["image_prompt"] = prompt
        db.update_project(
            project_id,
            scenes_json=db.scenes_to_json(scene_list),
            status="images_ready",
        )
        report(100, "Imagem atualizada")

    job = jobs.start_job(project_id, "regen", fn)
    return _job_redirect(request, project_id, job)


# ---------- Editor de cenas ----------


@app.post("/api/projects/{project_id}/scenes/save")
async def api_save_scenes(request: Request, project_id: str) -> Any:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    payload = await request.json()
    edits = payload.get("scenes") or []
    updated = scenes.apply_scene_edits(project.get("scenes") or [], edits)
    db.update_project(project_id, scenes_json=db.scenes_to_json(updated), status="scenes_ready")
    return JSONResponse({"ok": True, "count": len(updated)})


@app.post("/api/projects/{project_id}/scenes/add")
async def api_add_scene(project_id: str) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    updated = scenes.add_scene(list(project.get("scenes") or []))
    db.update_project(project_id, scenes_json=db.scenes_to_json(updated), status="scenes_ready")
    return RedirectResponse(f"/projects/{project_id}#cenas", status_code=303)


@app.post("/api/projects/{project_id}/scenes/{scene_index}/delete")
async def api_delete_scene(project_id: str, scene_index: int) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    updated = scenes.delete_scene(list(project.get("scenes") or []), scene_index)
    db.update_project(project_id, scenes_json=db.scenes_to_json(updated), status="scenes_ready")
    return RedirectResponse(f"/projects/{project_id}#cenas", status_code=303)


@app.post("/api/projects/{project_id}/scenes/{scene_index}/move")
async def api_move_scene(
    project_id: str, scene_index: int, direction: int = Form(...)
) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    updated = scenes.move_scene(list(project.get("scenes") or []), scene_index, int(direction))
    db.update_project(project_id, scenes_json=db.scenes_to_json(updated), status="scenes_ready")
    return RedirectResponse(f"/projects/{project_id}#cena-{scene_index}", status_code=303)


@app.post("/api/projects/{project_id}/scenes/{scene_index}/upload")
async def api_upload_scene_image(
    project_id: str,
    scene_index: int,
    image: UploadFile = File(...),
) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    scene_list = project.get("scenes") or []
    target = next((s for s in scene_list if int(s.get("index", -1)) == scene_index), None)
    if target is None:
        raise HTTPException(404, "Cena não encontrada")
    suffix = Path(image.filename or "cena.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    dest = _project_dir(project_id) / "images" / f"cena-{scene_index:02d}-upload{suffix}"
    data = image.file.read()
    if not data:
        raise HTTPException(400, "Arquivo vazio")
    dest.write_bytes(data)
    try:
        from PIL import Image as PILImage

        from app.config import frame_size

        w, h = frame_size(project.get("aspect"))
        img = PILImage.open(dest).convert("RGB")
        img = images._fit_cover(img, w, h)
        jpeg = dest.with_suffix(".jpg")
        img.save(jpeg, "JPEG", quality=92)
        dest = jpeg
    except Exception:  # noqa: BLE001
        pass
    target["image_path"] = str(dest)
    target["image_source"] = "upload"
    db.update_project(
        project_id, scenes_json=db.scenes_to_json(scene_list), status="images_ready"
    )
    return RedirectResponse(f"/projects/{project_id}#cena-{scene_index}", status_code=303)


# ---------- Downloads / mídia ----------


@app.get("/api/projects/{project_id}/download")
async def api_download(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    path = project.get("video_path")
    if not path or not Path(path).exists():
        raise HTTPException(404, "MP4 ainda não gerado")
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "_"
        for c in (project.get("title") or "video")
    ).strip() or "video"
    return FileResponse(path, media_type="video/mp4", filename=f"{safe_title}.mp4")


@app.get("/api/projects/{project_id}/download-srt")
async def api_download_srt(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("captions_path"):
        raise HTTPException(404)
    path = Path(project["captions_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="application/x-subrip", filename="legendas.srt")


@app.get("/api/projects/{project_id}/download-thumb")
async def api_download_thumb(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("thumbnail_path"):
        raise HTTPException(404)
    path = Path(project["thumbnail_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg", filename="thumbnail.jpg")


@app.get("/api/projects/{project_id}/download-pack")
async def api_download_pack(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    path = project.get("pack_path")
    if not path or not Path(path).exists():
        raise HTTPException(404, "Pacote ainda não gerado — rode o pipeline")
    safe = "".join(
        c if c.isalnum() or c in " -_" else "_"
        for c in (project.get("title") or "youtube")
    ).strip() or "youtube"
    return FileResponse(path, media_type="application/zip", filename=f"{safe}-youtube.zip")


@app.get("/media/projects/{project_id}/images/{filename}")
async def media_image(project_id: str, filename: str) -> FileResponse:
    path = PROJECTS_DIR / project_id / "images" / filename
    if not path.exists() or ".." in filename:
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/media/projects/{project_id}/characters/{filename}")
async def media_character_image(project_id: str, filename: str) -> FileResponse:
    path = PROJECTS_DIR / project_id / "characters" / filename
    if not path.exists() or ".." in filename:
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/media/projects/{project_id}/audio")
async def media_audio(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("audio_path"):
        raise HTTPException(404)
    path = Path(project["audio_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/mpeg")


@app.get("/media/projects/{project_id}/video")
async def media_video(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("video_path"):
        raise HTTPException(404)
    path = Path(project["video_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4")


@app.get("/media/projects/{project_id}/thumb")
async def media_thumb(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("thumbnail_path"):
        raise HTTPException(404)
    path = Path(project["thumbnail_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg")


# ---------- Personagens ----------


@app.post("/api/projects/{project_id}/characters")
async def api_create_character(
    project_id: str,
    name: str = Form(...),
    role: str = Form(""),
    visual_bible: str = Form(""),
    reference_image: UploadFile | None = File(None),
) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projeto não encontrado")
    name = name.strip()
    if not name:
        raise HTTPException(400, "Nome obrigatório")
    ch = db.create_character(
        project_id=project_id, name=name, role=role, visual_bible=visual_bible
    )
    if reference_image and reference_image.filename:
        path = _save_character_upload(project_id, ch["id"], reference_image)
        db.update_character(ch["id"], reference_images=[path])
    return RedirectResponse(f"/projects/{project_id}#personagens", status_code=303)


@app.post("/api/projects/{project_id}/characters/{character_id}")
async def api_update_character(
    project_id: str,
    character_id: str,
    name: str = Form(...),
    role: str = Form(""),
    visual_bible: str = Form(""),
    reference_image: UploadFile | None = File(None),
) -> RedirectResponse:
    project = db.get_project(project_id)
    ch = db.get_character(character_id)
    if not project or not ch or ch.get("project_id") != project_id:
        raise HTTPException(404)
    name = name.strip()
    if not name:
        raise HTTPException(400, "Nome obrigatório")
    updates: dict[str, Any] = {"name": name, "role": role, "visual_bible": visual_bible}
    if reference_image and reference_image.filename:
        path = _save_character_upload(project_id, character_id, reference_image)
        refs = list(ch.get("reference_images") or [])
        refs = [path] + [r for r in refs if r != path]
        updates["reference_images"] = refs
    db.update_character(character_id, **updates)
    return RedirectResponse(f"/projects/{project_id}#personagens", status_code=303)


@app.post("/api/projects/{project_id}/characters/{character_id}/delete")
async def api_delete_character(project_id: str, character_id: str) -> RedirectResponse:
    ch = db.get_character(character_id)
    if not ch or ch.get("project_id") != project_id:
        raise HTTPException(404)
    for p in ch.get("reference_images") or []:
        try:
            Path(p).unlink(missing_ok=True)
        except OSError:
            pass
    db.delete_character(character_id)
    return RedirectResponse(f"/projects/{project_id}#personagens", status_code=303)


@app.post("/api/projects/{project_id}/characters/seed-demo")
async def api_seed_demo_characters(project_id: str) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    db.seed_demo_characters(project_id)
    return RedirectResponse(f"/projects/{project_id}#personagens", status_code=303)


@app.post("/api/projects/{project_id}/delete")
async def api_delete(project_id: str) -> RedirectResponse:
    pdir = PROJECTS_DIR / project_id
    if pdir.exists():
        shutil.rmtree(pdir, ignore_errors=True)
    for extra in (
        EXPORTS_DIR / f"{project_id}.mp4",
        EXPORTS_DIR / f"{project_id}_thumb.jpg",
        EXPORTS_DIR / f"{project_id}_youtube.zip",
    ):
        if extra.exists():
            extra.unlink()
    db.delete_project(project_id)
    return RedirectResponse("/", status_code=303)


@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "app": "Histórias Bíblicas Studio",
            "version": "1.1.0",
            "port": PORT,
            "image_provider": images.active_provider_label(),
        }
    )
