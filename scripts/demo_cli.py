#!/usr/bin/env python3
"""CLI: gera MP4 demo Davi e Golias sem abrir o browser."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from app.config import DEFAULT_VOICE, EXPORTS_DIR, PROJECTS_DIR  # noqa: E402
from app.services import demo_script, images, scenes, tts, video  # noqa: E402


def main() -> int:
    db.init_db()
    project = db.create_project(
        demo_script.DAVI_GOLIAS_TITLE, demo_script.DAVI_GOLIAS_THEME
    )
    pid = project["id"]
    print(f"Projeto: {pid}")

    script = demo_script.DAVI_GOLIAS_SCRIPT
    scene_list = scenes.segment_script(
        script, hints=demo_script.DAVI_GOLIAS_SCENE_HINTS
    )
    print(f"Cenas: {len(scene_list)}")

    pdir = PROJECTS_DIR / pid
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "images").mkdir(exist_ok=True)
    (pdir / "characters").mkdir(exist_ok=True)
    chars = db.seed_demo_characters(pid)
    print(f"Personagens: {', '.join(c['name'] for c in chars)}")

    audio_path = pdir / "narration.mp3"
    print("Gerando TTS (edge-tts)…")
    tts.synthesize(script, audio_path, voice=DEFAULT_VOICE)
    duration = tts.audio_duration_sec(audio_path)
    print(f"Áudio: {duration:.1f}s → {audio_path}")

    scene_list = scenes.allocate_durations(scene_list, duration)
    print(f"Gerando imagens IA ({images.active_provider_label()})…")
    for s in scene_list:
        idx = int(s["index"])
        out_img = pdir / "images" / f"cena-{idx:02d}.jpg"
        _path, source = images.generate_scene_image(
            s["title"], s["text"], out_img, scene_index=idx, characters=chars
        )
        s["image_path"] = str(out_img)
        s["image_source"] = source
        s["image_prompt"] = images.build_image_prompt(
            s["title"], s["text"], idx, characters=chars
        )
        print(f"  cena-{idx:02d}: {source}")
        if idx < len(scene_list) - 1 and source == "pollinations":
            time.sleep(12)
    print("Imagens geradas.")

    out = EXPORTS_DIR / f"{pid}.mp4"
    print("Montando MP4 (FFmpeg Ken Burns)…")
    video.assemble_mp4(scene_list, audio_path, out, total_duration=duration)

    db.update_project(
        pid,
        script=script,
        audio_path=str(audio_path),
        video_path=str(out),
        scenes_json=db.scenes_to_json(scene_list),
        status="video_ready",
    )
    print(f"\n✓ MP4 pronto: {out}")
    print(f"  Abrir projeto: http://127.0.0.1:8080/projects/{pid}")
    print(f"  Download:     http://127.0.0.1:8080/api/projects/{pid}/download")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
