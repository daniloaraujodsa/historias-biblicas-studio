#!/usr/bin/env python3
"""Gera um MP4 16:9 de ~120s e um Short 9:16 do mesmo roteiro."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["IMAGE_PROVIDER"] = "placeholder"

from app import db  # noqa: E402
from app.config import DEFAULT_VOICE, EXPORTS_DIR, PROJECTS_DIR  # noqa: E402
from app.services import demo_script, pipeline, scenes as scenes_svc, tts  # noqa: E402

TARGET_SEC = 120.0


def _report(progress: int, step: str) -> None:
    print(f"  {progress:3d}% {step}", flush=True)


def _fit_audio(src: Path, dst: Path, target: float) -> float:
    current = tts.audio_duration_sec(src)
    print(f"  TTS natural: {current:.1f}s (alvo {target:.0f}s)", flush=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if abs(current - target) <= 3.5:
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        return tts.audio_duration_sec(dst)

    rate = max(0.5, min(2.0, current / target))
    tmp = dst.with_name(dst.stem + ".tempo.mp3")
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-filter:a",
            f"atempo={rate:.5f}",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(tmp),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"atempo falhou:\n{result.stderr[-1200:]}")
    tmp.replace(dst)
    fitted = tts.audio_duration_sec(dst)
    print(f"  Áudio ajustado: {fitted:.1f}s (atempo={rate:.3f})", flush=True)
    return fitted


def _scale_durations(scene_list: list, factor: float) -> None:
    for sc in scene_list:
        dur = float(sc.get("duration_sec") or 0) or 1.5
        sc["duration_sec"] = round(max(dur * factor, 1.0), 3)


def _duration_ffmpeg(path: Path) -> float:
    return tts.audio_duration_sec(path)


def build_project(title: str, aspect: str) -> dict:
    project = db.create_project(title, demo_script.DAVI_GOLIAS_THEME, aspect=aspect)
    pid = project["id"]
    pipeline._pdir(pid)
    db.update_project(
        pid,
        script=demo_script.DAVI_GOLIAS_LONG_SCRIPT,
        status="script_ready",
        burn_captions=1,
        add_music=1,
    )
    db.seed_demo_characters(pid)
    return db.get_project(pid)


def main() -> int:
    db.init_db()
    script = demo_script.DAVI_GOLIAS_LONG_SCRIPT
    words = len(script.split())
    print(f"Roteiro: {words} palavras / {len(script)} chars", flush=True)

    land_id = os.environ.get("TEST_LAND_ID", "").strip()
    short_id = os.environ.get("TEST_SHORT_ID", "").strip()
    if land_id and short_id and db.get_project(land_id) and db.get_project(short_id):
        land = db.get_project(land_id)
        short = db.get_project(short_id)
        print("Retomando projetos existentes", flush=True)
    else:
        land = build_project("Davi e Golias — 2 min (16:9)", "16:9")
        short = build_project("Davi e Golias — Short (9:16)", "9:16")
    land_id, short_id = land["id"], short["id"]
    print(f"16:9  {land_id}", flush=True)
    print(f"9:16  {short_id}", flush=True)

    print("\n== Segmentar ==", flush=True)
    if not (db.get_project(land_id) or {}).get("scenes"):
        pipeline.run_segment(land_id)
    else:
        print("  16:9 já tem cenas", flush=True)
    db.update_project(short_id, script=script)
    if not (db.get_project(short_id) or {}).get("scenes"):
        pipeline.run_segment(short_id)
    else:
        print("  9:16 já tem cenas", flush=True)
    print(
        f"  cenas: {len((db.get_project(land_id) or {}).get('scenes') or [])} / "
        f"{len((db.get_project(short_id) or {}).get('scenes') or [])}",
        flush=True,
    )

    print("\n== TTS (compartilhado) ==", flush=True)
    land = db.get_project(land_id)
    existing_audio = Path(land.get("audio_path") or "")
    if existing_audio.exists() and existing_audio.stat().st_size > 1000:
        print("  reusando narração já gerada", flush=True)
    else:
        pipeline.run_tts(land_id, DEFAULT_VOICE, _report)
        land = db.get_project(land_id)
    audio_src = Path(land["audio_path"])
    scene_list = land.get("scenes") or []
    scene_sum = sum(float(s.get("duration_sec") or 0) for s in scene_list)
    fitted = _fit_audio(audio_src, audio_src, TARGET_SEC)
    if scene_sum < 10:
        scene_list = scenes_svc.allocate_durations(scene_list, fitted)
    else:
        _scale_durations(scene_list, fitted / scene_sum)
    db.update_project(
        land_id,
        audio_path=str(audio_src),
        scenes_json=db.scenes_to_json(scene_list),
        status="audio_ready",
    )

    # copia áudio + durações para o short
    short_audio = pipeline._pdir(short_id) / "audio" / "narration.mp3"
    short_audio.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_src, short_audio)
    short_scenes = db.get_project(short_id).get("scenes") or []
    by_idx = {int(s.get("index", i)): s for i, s in enumerate(scene_list)}
    for i, sc in enumerate(short_scenes):
        src = by_idx.get(int(sc.get("index", i)))
        if src and src.get("duration_sec"):
            sc["duration_sec"] = src["duration_sec"]
            sc["audio_path"] = src.get("audio_path")
    db.update_project(
        short_id,
        audio_path=str(short_audio),
        scenes_json=db.scenes_to_json(short_scenes),
        status="audio_ready",
    )
    print(f"  duração compartilhada: {fitted:.2f}s", flush=True)

    print("\n== Imagens 16:9 ==", flush=True)
    pipeline.run_images(land_id, _report)
    print("\n== Imagens 9:16 ==", flush=True)
    pipeline.run_images(short_id, _report)

    print("\n== Render 16:9 ==", flush=True)
    pipeline.run_render(land_id, _report)
    print("\n== Render 9:16 ==", flush=True)
    pipeline.run_render(short_id, _report)

    land = db.get_project(land_id)
    short = db.get_project(short_id)
    for label, proj in (("16:9", land), ("9:16", short)):
        v = Path(proj["video_path"])
        dur = _duration_ffmpeg(v)
        size = v.stat().st_size
        print(
            f"\n{label}  {dur:.2f}s  {size/1e6:.1f} MB  {v.name}",
            flush=True,
        )
        print(f"  projeto: /projects/{proj['id']}", flush=True)
        print(f"  download: /api/projects/{proj['id']}/download", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
