"""Orquestra o pipeline de produção com callback de progresso."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from app import db
from app.config import EXPORTS_DIR, PROJECTS_DIR
from app.services import captions, demo_script, images, publish, scenes, tts, video
from app.services.audio_mode import resolve_mode, uses_narration
from app.services.visual import project_visual_kwargs

ProgressFn = Callable[[int, str], None]


def _pdir(project_id: str) -> Path:
    p = PROJECTS_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    (p / "images").mkdir(exist_ok=True)
    (p / "audio").mkdir(exist_ok=True)
    (p / "characters").mkdir(exist_ok=True)
    return p


def _gen_image(project_id: str, scene: dict, out: Path, seed_salt: int = 0) -> tuple[Path, str, str]:
    project = db.get_project(project_id) or {}
    chars = db.list_characters(project_id, include_global=False)
    aspect = project.get("aspect") or "16:9"
    idx = int(scene.get("index", 0))
    title = scene.get("title") or f"Cena {idx + 1}"
    scene_text = scene.get("text") or ""
    cast = scene.get("cast") or ""
    look = project_visual_kwargs(project)
    path, source = images.generate_scene_image(
        title,
        scene_text,
        out,
        scene_index=idx,
        seed_salt=seed_salt,
        characters=chars,
        aspect=aspect,
        cast=cast,
        **look,
    )
    prompt = images.build_image_prompt(
        title,
        scene_text,
        idx,
        characters=chars,
        aspect=aspect,
        cast=cast,
        **look,
    )
    return path, source, prompt


def run_segment(project_id: str) -> list[dict]:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("Projeto não encontrado")
    script = (project.get("script") or "").strip()
    if not script:
        raise ValueError("Roteiro vazio")
    hints = None
    title_l = (project.get("title") or "").lower()
    if "davi" in title_l:
        if any(k in title_l for k in ("2 min", "2 minutos", "short", "120")):
            hints = demo_script.DAVI_GOLIAS_LONG_HINTS
        else:
            hints = demo_script.DAVI_GOLIAS_SCENE_HINTS
    scene_list = scenes.segment_script(script, hints=hints)
    db.update_project(
        project_id,
        scenes_json=db.scenes_to_json(scene_list),
        status="scenes_ready",
    )
    return scene_list


def run_tts(project_id: str, voice: str, report: ProgressFn | None = None) -> None:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("Projeto não encontrado")
    script = (project.get("script") or "").strip()
    if not script:
        raise ValueError("Roteiro vazio")
    scene_list = project.get("scenes") or []
    if not scene_list:
        scene_list = run_segment(project_id)
    pdir = _pdir(project_id)
    if report:
        report(12, "Gerando narração por cena…")
    audio_path, scene_list = tts.synthesize_scenes(scene_list, pdir / "audio", voice=voice)
    db.update_project(
        project_id,
        audio_path=str(audio_path),
        scenes_json=db.scenes_to_json(scene_list),
        status="audio_ready",
    )


def run_images(project_id: str, report: ProgressFn | None = None) -> None:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("Projeto não encontrado")
    scene_list = project.get("scenes") or []
    if not scene_list:
        raise ValueError("Segmente as cenas primeiro")
    img_dir = _pdir(project_id) / "images"
    n = len(scene_list)
    for i, s in enumerate(scene_list):
        if report:
            report(28 + int(50 * i / max(n, 1)), f"Imagem da cena {i + 1}/{n}…")
        idx = int(s.get("index", 0))
        out = img_dir / f"cena-{idx:02d}.jpg"
        _path, source, prompt = _gen_image(project_id, s, out)
        s["image_path"] = str(out)
        s["image_source"] = source
        s["image_prompt"] = prompt
        if i < n - 1 and source == "pollinations":
            time.sleep(8)
    db.update_project(
        project_id,
        scenes_json=db.scenes_to_json(scene_list),
        status="images_ready",
    )


def _prepare_timing(project: dict, scene_list: list[dict]) -> tuple[list[dict], float, Path | None]:
    """Duração das cenas e arquivo de narração, conforme o modo de áudio."""
    mode = resolve_mode(project.get("audio_mode"), music=bool(project.get("add_music", True)))
    audio_raw = project.get("audio_path")
    narration = Path(audio_raw) if audio_raw and Path(audio_raw).exists() else None
    if uses_narration(mode):
        if narration is None:
            raise ValueError("Gere a narração TTS primeiro")
        duration = tts.audio_duration_sec(narration)
        if not all(s.get("duration_sec") for s in scene_list):
            scene_list = scenes.allocate_durations(scene_list, duration)
        return scene_list, duration, narration
    scene_list = scenes.ensure_durations(scene_list)
    duration = sum(max(float(s.get("duration_sec") or 3.0), 1.0) for s in scene_list)
    return scene_list, duration, None


def run_render(project_id: str, report: ProgressFn | None = None) -> None:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("Projeto não encontrado")
    scene_list = project.get("scenes") or []
    if not scene_list or not all(s.get("image_path") for s in scene_list):
        raise ValueError("Gere as imagens das cenas primeiro")
    mode = resolve_mode(project.get("audio_mode"), music=bool(project.get("add_music", True)))
    scene_list, duration, narration = _prepare_timing(project, scene_list)

    pdir = _pdir(project_id)
    if report:
        report(82, "Gerando legendas e thumbnail…")
    srt = captions.write_srt(scene_list, pdir / "captions.srt")
    first_img = next(
        (Path(s["image_path"]) for s in scene_list if s.get("image_path")), None
    )
    thumb = None
    if first_img:
        thumb = publish.write_thumbnail(
            first_img,
            project.get("title") or "História",
            EXPORTS_DIR / f"{project_id}_thumb.jpg",
            aspect=project.get("aspect") or "16:9",
        )
    meta = publish.generate_metadata(
        project.get("title") or "",
        project.get("theme") or "",
        project.get("script") or "",
        series_name=project.get("series_name") or "",
        episode_number=project.get("episode_number"),
    )
    if (project.get("youtube_title") or "").strip():
        meta["youtube_title"] = project["youtube_title"].strip()
    if (project.get("youtube_description") or "").strip():
        meta["youtube_description"] = project["youtube_description"].strip()
    if (project.get("youtube_tags") or "").strip():
        meta["youtube_tags"] = project["youtube_tags"].strip()


    if report:
        step = {
            "none": "Montando MP4 sem áudio…",
            "music": "Montando MP4 com trilha…",
            "narration": "Montando MP4 com narração…",
        }.get(mode, "Montando MP4 (Ken Burns + áudio)…")
        report(88, step)
    out = EXPORTS_DIR / f"{project_id}.mp4"
    video.assemble_mp4(
        scene_list,
        narration,
        out,
        total_duration=duration,
        aspect=project.get("aspect") or "16:9",
        captions_path=srt if project.get("burn_captions", True) else None,
        music=bool(project.get("add_music", True)),
        audio_mode=mode,
    )
    pack = publish.write_pack(
        output_path=EXPORTS_DIR / f"{project_id}_youtube.zip",
        video_path=out,
        captions_path=srt,
        thumbnail_path=thumb,
        meta=meta,
    )
    db.update_project(
        project_id,
        video_path=str(out),
        captions_path=str(srt),
        thumbnail_path=str(thumb) if thumb else None,
        pack_path=str(pack),
        youtube_title=meta["youtube_title"],
        youtube_description=meta["youtube_description"],
        youtube_tags=meta["youtube_tags"],
        scenes_json=db.scenes_to_json(scene_list),
        status="video_ready",
    )


def run_full(project_id: str, voice: str, report: ProgressFn) -> None:
    report(4, "Segmentando o roteiro em cenas…")
    run_segment(project_id)
    project = db.get_project(project_id) or {}
    mode = resolve_mode(project.get("audio_mode"), music=bool(project.get("add_music", True)))
    if uses_narration(mode):
        report(10, "Narração TTS por cena…")
        run_tts(project_id, voice, report)
    else:
        report(10, "Modo sem narração — duração estimada pelo texto…")
        fresh = db.get_project(project_id) or {}
        timed = scenes.ensure_durations(list(fresh.get("scenes") or []))
        db.update_project(project_id, scenes_json=db.scenes_to_json(timed))
    report(28, "Gerando imagens das cenas…")
    run_images(project_id, report)
    report(80, "Legendas, áudio e montagem…")
    run_render(project_id, report)
    report(100, "Vídeo pronto")
