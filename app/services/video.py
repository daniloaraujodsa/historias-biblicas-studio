"""Montagem de MP4 com FFmpeg + efeito Ken Burns."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.config import VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH


def assemble_mp4(
    scenes: list[dict[str, Any]],
    audio_path: Path,
    output_path: Path,
    total_duration: float | None = None,
) -> Path:
    """
    Para cada cena: gera clipe Ken Burns (zoompan) com duração proporcional.
    Concatena clipes e muxa com o áudio de narração.
    """
    if not scenes:
        raise ValueError("Nenhuma cena para montar o vídeo")
    if not audio_path.exists():
        raise ValueError(f"Áudio não encontrado: {audio_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="hbs_video_"))
    try:
        clip_paths: list[Path] = []
        for i, scene in enumerate(scenes):
            img = scene.get("image_path")
            if not img or not Path(img).exists():
                raise ValueError(f"Imagem ausente na cena {i}")
            dur = float(scene.get("duration_sec") or 3.0)
            # Garantir mínimo para zoompan
            dur = max(dur, 1.0)
            clip = work / f"clip_{i:03d}.mp4"
            _ken_burns_clip(Path(img), clip, dur, i)
            clip_paths.append(clip)

        concat_list = work / "concat.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for c in clip_paths:
                # Caminhos absolutos escapados para demuxer concat
                p = str(c.resolve()).replace("'", "'\\''")
                f.write(f"file '{p}'\n")

        silent_video = work / "silent.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(silent_video),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Mux áudio; -shortest evita cauda sem áudio se vídeo for um pouco maior
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg falhou:\n{result.stderr[-2000:]}")
        return output_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _ken_burns_clip(
    image_path: Path, output_path: Path, duration: float, index: int
) -> None:
    """
    Aplica zoom/pan suave (Ken Burns) via filtro zoompan do FFmpeg.
    Alterna direção do zoom entre cenas.
    """
    frames = max(int(duration * VIDEO_FPS), VIDEO_FPS)
    # Zoom de ~1.0 para ~1.18 (ou inverso)
    zoom_in = index % 2 == 0
    if zoom_in:
        # z cresce; pan leve para o centro-direita
        z_expr = f"min(1.0+0.18*on/{frames},1.18)"
        x_expr = f"iw/2-(iw/zoom/2)+((iw*0.05)*on/{frames})"
        y_expr = f"ih/2-(ih/zoom/2)-((ih*0.03)*on/{frames})"
    else:
        z_expr = f"max(1.18-0.18*on/{frames},1.0)"
        x_expr = f"iw/2-(iw/zoom/2)-((iw*0.04)*on/{frames})"
        y_expr = f"ih/2-(ih/zoom/2)+((ih*0.02)*on/{frames})"

    # Escala a imagem maior que o frame para o zoompan ter margem
    scale_w = VIDEO_WIDTH * 2
    scale_h = VIDEO_HEIGHT * 2
    vf = (
        f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
        f"crop={scale_w}:{scale_h},"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-vf",
        vf,
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-tune",
        "stillimage",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Ken Burns falhou (cena {index}):\n{result.stderr[-1500:]}"
        )
