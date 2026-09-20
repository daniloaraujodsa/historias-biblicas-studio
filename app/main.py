"""Histórias Bíblicas Studio — API + UI pt-BR."""
from __future__ import annotations

import json
import time
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.config import DEFAULT_THEME, DEFAULT_VOICE, EXPORTS_DIR, PROJECTS_DIR, ROOT
from app.services import demo_script, images, scenes, tts, video

app = FastAPI(title="Histórias Bíblicas Studio", version="1.0.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


def _project_dir(project_id: str) -> Path:
    p = PROJECTS_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    (p / "images").mkdir(exist_ok=True)
    (p / "characters").mkdir(exist_ok=True)
    return p


def _save_character_upload(project_id: str, character_id: str, upload: UploadFile) -> str:
    """Salva imagem de referência em data/projects/<id>/characters/."""
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



def _gen_scene_with_chars(
    project_id: str,
    scene: dict[str, Any],
    out: Path,
    *,
    seed_salt: int = 0,
) -> tuple[Path, str, str]:
    """Gera imagem da cena injetando bible + refs dos personagens do projeto."""
    chars = db.list_characters(project_id, include_global=False)
    idx = int(scene.get("index", 0))
    title = scene.get("title") or f"Cena {idx + 1}"
    scene_text = scene.get("text") or ""
    path, source = images.generate_scene_image(
        title,
        scene_text,
        out,
        scene_index=idx,
        seed_salt=seed_salt,
        characters=chars,
    )
    prompt = images.build_image_prompt(title, scene_text, idx, characters=chars)
    return path, source, prompt


# ---------- Páginas ----------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> Any:
    projects = db.list_projects()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "projects": projects,
            "default_theme": DEFAULT_THEME,
        },
    )


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_page(request: Request, project_id: str) -> Any:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projeto não encontrado")
    characters = db.list_characters(project_id, include_global=False)
    return templates.TemplateResponse(
        "project.html",
        {
            "request": request,
            "project": project,
            "characters": characters,
            "voices": tts.list_pt_br_voices(),
            "default_voice": DEFAULT_VOICE,
            "image_provider_label": images.active_provider_label(),
        },
    )


# ---------- API / ações ----------


@app.post("/api/projects")
async def api_create_project(
    title: str = Form(...),
    theme: str = Form(DEFAULT_THEME),
) -> RedirectResponse:
    title = title.strip() or "Novo projeto"
    theme = theme.strip() or DEFAULT_THEME
    project = db.create_project(title, theme)
    _project_dir(project["id"])
    return RedirectResponse(f"/projects/{project['id']}", status_code=303)


@app.post("/api/projects/demo-davi-golias")
async def api_demo_davi_golias() -> RedirectResponse:
    """Cria projeto demo com roteiro Davi e Golias."""
    project = db.create_project(
        demo_script.DAVI_GOLIAS_TITLE, demo_script.DAVI_GOLIAS_THEME
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
async def api_save_script(
    project_id: str,
    script: str = Form(""),
) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    db.update_project(project_id, script=script.strip(), status="script_ready")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/segment")
async def api_segment(project_id: str) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    script = project.get("script") or ""
    if not script.strip():
        raise HTTPException(400, "Roteiro vazio")
    hints = None
    if "davi" in (project.get("title") or "").lower():
        hints = demo_script.DAVI_GOLIAS_SCENE_HINTS
    scene_list = scenes.segment_script(script, hints=hints)
    db.update_project(
        project_id,
        scenes_json=db.scenes_to_json(scene_list),
        status="scenes_ready",
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/tts")
async def api_tts(
    project_id: str,
    voice: str = Form(DEFAULT_VOICE),
) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    script = (project.get("script") or "").strip()
    if not script:
        raise HTTPException(400, "Roteiro vazio")
    pdir = _project_dir(project_id)
    audio_path = pdir / "narration.mp3"
    try:
        tts.synthesize(script, audio_path, voice=voice or DEFAULT_VOICE)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha no TTS: {exc}") from exc

    scene_list = project.get("scenes") or []
    if not scene_list:
        scene_list = scenes.segment_script(script)
    duration = tts.audio_duration_sec(audio_path)
    scene_list = scenes.allocate_durations(scene_list, duration)
    db.update_project(
        project_id,
        audio_path=str(audio_path),
        scenes_json=db.scenes_to_json(scene_list),
        status="audio_ready",
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/images")
async def api_images(project_id: str) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    scene_list = project.get("scenes") or []
    if not scene_list:
        raise HTTPException(400, "Segmente as cenas primeiro")
    img_dir = _project_dir(project_id) / "images"
    for i, s in enumerate(scene_list):
        idx = int(s.get("index", 0))
        out = img_dir / f"cena-{idx:02d}.jpg"
        _path, source, prompt = _gen_scene_with_chars(project_id, s, out)
        s["image_path"] = str(out)
        s["image_source"] = source
        s["image_prompt"] = prompt
        # Espaço entre requests (fila anônima Pollinations)
        if i < len(scene_list) - 1 and source == "pollinations":
            time.sleep(12)
    db.update_project(
        project_id,
        scenes_json=db.scenes_to_json(scene_list),
        status="images_ready",
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/images/{scene_index}/regenerate")
async def api_regenerate_scene_image(project_id: str, scene_index: int) -> RedirectResponse:
    """Regenera a imagem de uma cena com IA (ou placeholder em falha)."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    scene_list = project.get("scenes") or []
    target = None
    for s in scene_list:
        if int(s.get("index", -1)) == scene_index:
            target = s
            break
    if target is None:
        raise HTTPException(404, "Cena não encontrada")
    img_dir = _project_dir(project_id) / "images"
    out = img_dir / f"cena-{scene_index:02d}.jpg"
    salt = int(time.time()) % 1_000_000
    _path, source, prompt = _gen_scene_with_chars(
        project_id, target, out, seed_salt=salt
    )
    target["image_path"] = str(out)
    target["image_source"] = source
    target["image_prompt"] = prompt
    db.update_project(
        project_id,
        scenes_json=db.scenes_to_json(scene_list),
        status="images_ready",
    )
    return RedirectResponse(f"/projects/{project_id}#cena-{scene_index}", status_code=303)


@app.post("/api/projects/{project_id}/render")
async def api_render(project_id: str) -> RedirectResponse:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    audio = project.get("audio_path")
    scene_list = project.get("scenes") or []
    if not audio or not Path(audio).exists():
        raise HTTPException(400, "Gere a narração TTS primeiro")
    if not scene_list or not all(s.get("image_path") for s in scene_list):
        raise HTTPException(400, "Gere as imagens das cenas primeiro")
    # Realocar durações se necessário
    duration = tts.audio_duration_sec(Path(audio))
    scene_list = scenes.allocate_durations(scene_list, duration)

    out = EXPORTS_DIR / f"{project_id}.mp4"
    try:
        video.assemble_mp4(scene_list, Path(audio), out, total_duration=duration)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha ao montar MP4: {exc}") from exc

    db.update_project(
        project_id,
        video_path=str(out),
        scenes_json=db.scenes_to_json(scene_list),
        status="video_ready",
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/pipeline")
async def api_full_pipeline(
    project_id: str,
    voice: str = Form(DEFAULT_VOICE),
) -> RedirectResponse:
    """Pipeline completo: segmentar → TTS → imagens → MP4."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404)
    script = (project.get("script") or "").strip()
    if not script:
        raise HTTPException(400, "Roteiro vazio")

    hints = None
    if "davi" in (project.get("title") or "").lower():
        hints = demo_script.DAVI_GOLIAS_SCENE_HINTS
    scene_list = scenes.segment_script(script, hints=hints)

    pdir = _project_dir(project_id)
    audio_path = pdir / "narration.mp3"
    try:
        tts.synthesize(script, audio_path, voice=voice or DEFAULT_VOICE)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha no TTS: {exc}") from exc

    duration = tts.audio_duration_sec(audio_path)
    scene_list = scenes.allocate_durations(scene_list, duration)

    img_dir = pdir / "images"
    for i, s in enumerate(scene_list):
        idx = int(s.get("index", 0))
        out_img = img_dir / f"cena-{idx:02d}.jpg"
        _path, source, prompt = _gen_scene_with_chars(project_id, s, out_img)
        s["image_path"] = str(out_img)
        s["image_source"] = source
        s["image_prompt"] = prompt
        if i < len(scene_list) - 1 and source == "pollinations":
            time.sleep(12)

    out = EXPORTS_DIR / f"{project_id}.mp4"
    try:
        video.assemble_mp4(scene_list, audio_path, out, total_duration=duration)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Falha ao montar MP4: {exc}") from exc

    db.update_project(
        project_id,
        audio_path=str(audio_path),
        video_path=str(out),
        scenes_json=db.scenes_to_json(scene_list),
        status="video_ready",
    )
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


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
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{safe_title}.mp4",
    )


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
        project_id=project_id,
        name=name,
        role=role,
        visual_bible=visual_bible,
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
    updates: dict[str, Any] = {
        "name": name,
        "role": role,
        "visual_bible": visual_bible,
    }
    if reference_image and reference_image.filename:
        path = _save_character_upload(project_id, character_id, reference_image)
        refs = list(ch.get("reference_images") or [])
        # nova ref vira a principal
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


@app.get("/media/projects/{project_id}/audio")
async def media_audio(project_id: str) -> FileResponse:
    project = db.get_project(project_id)
    if not project or not project.get("audio_path"):
        raise HTTPException(404)
    path = Path(project["audio_path"])
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/mpeg")


@app.post("/api/projects/{project_id}/delete")
async def api_delete(project_id: str) -> RedirectResponse:
    pdir = PROJECTS_DIR / project_id
    if pdir.exists():
        shutil.rmtree(pdir, ignore_errors=True)
    vp = EXPORTS_DIR / f"{project_id}.mp4"
    if vp.exists():
        vp.unlink()
    db.delete_project(project_id)
    return RedirectResponse("/", status_code=303)


@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "app": "Histórias Bíblicas Studio",
            "root": str(ROOT),
            "image_provider": images.active_provider_label(),
        }
    )
