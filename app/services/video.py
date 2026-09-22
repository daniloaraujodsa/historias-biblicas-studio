"""Montagem de MP4 com FFmpeg + Ken Burns + legendas + música."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.config import VIDEO_FPS, frame_size



def assemble_mp4(
    scenes: list[dict[str, Any]],
    audio_path: Path,
    output_path: Path,
    total_duration: float | None = None,
    *,
    aspect: str = "16:9",
    captions_path: Path | None = None,
    music: bool = True,
) -> Path:
    if not scenes:
        raise ValueError("Nenhuma cena para montar o vídeo")
    if not audio_path.exists():
        raise ValueError(f"Áudio não encontrado: {audio_path}")

    width, height = frame_size(aspect)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="hbs_video_"))
    try:
        clip_paths: list[Path] = []
        for i, scene in enumerate(scenes):
            img = scene.get("image_path")
            if not img or not Path(img).exists():
                raise ValueError(f"Imagem ausente na cena {i}")
            dur = max(float(scene.get("duration_sec") or 3.0), 1.0)
            clip = work / f"clip_{i:03d}.mp4"
            _ken_burns_clip(Path(img), clip, dur, i, width, height)
            clip_paths.append(clip)

        concat_list = work / "concat.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for c in clip_paths:
                p = str(c.resolve()).replace("'", r"'\''")
                f.write(f"file '{p}'\n")

        silent_video = work / "silent.mp4"
        _run(
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
            "concat",
        )

        audio_mixed = Path(audio_path)
        if music:
            mixed = work / "narration_music.m4a"
            _mix_music(Path(audio_path), mixed, total_duration)
            audio_mixed = mixed

        vf = f"format=yuv420p"
        if captions_path and Path(captions_path).exists():
            srt = Path(captions_path)
            # Caminho escapado para o filtro subtitles
            srt_esc = str(srt.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'")
            size = 28 if width >= 1600 else 22
            if height > width:
                size = 32
            vf = (
                f"subtitles='{srt_esc}':force_style='"
                f"FontName=DejaVu Sans,FontSize={size},PrimaryColour=&H00FFFFFF,"
                f"OutlineColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,"
                f"Alignment=2,MarginV=48,Bold=0'"
                f",format=yuv420p"
            )



        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_mixed),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
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
        _run(cmd, "mux")
        return output_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _mix_music(narration: Path, output_path: Path, duration: float | None) -> None:
    dur = duration or 30.0
    bed = output_path.with_suffix(".bed.wav")
    fade_out_start = max(dur - 3.0, 0.5)
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=196:sample_rate=44100:duration={dur:.3f}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=294:sample_rate=44100:duration={dur:.3f}",
            "-filter_complex",
            (
                "amix=inputs=2:duration=longest,"
                "lowpass=f=650,volume=0.18,"
                "afade=t=in:st=0:d=1.5,"
                f"afade=t=out:st={fade_out_start:.3f}:d=2.5"
            ),
            str(bed),
        ],
        "music-bed",
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(narration),
            "-i",
            str(bed),
            "-filter_complex",
            "[0:a]volume=1.0[a0];[1:a]volume=0.22[a1];"
            "[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,"
            "alimiter=limit=0.95",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ],
        "music-mix",
    )


def _ken_burns_clip(
    image_path: Path,
    output_path: Path,
    duration: float,
    index: int,
    width: int,
    height: int,
) -> None:
    frames = max(int(duration * VIDEO_FPS), VIDEO_FPS)
    zoom_in = index % 2 == 0
    if zoom_in:
        z_expr = f"min(1.0+0.14*on/{frames},1.14)"
        x_expr = f"iw/2-(iw/zoom/2)+((iw*0.04)*on/{frames})"
        y_expr = f"ih/2-(ih/zoom/2)-((ih*0.025)*on/{frames})"
    else:
        z_expr = f"max(1.14-0.14*on/{frames},1.0)"
        x_expr = f"iw/2-(iw/zoom/2)-((iw*0.035)*on/{frames})"
        y_expr = f"ih/2-(ih/zoom/2)+((ih*0.02)*on/{frames})"

    scale_w = (width * 3 // 2) & ~1
    scale_h = (height * 3 // 2) & ~1
    vf = (
        f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
        f"crop={scale_w}:{scale_h},"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={frames}:s={width}x{height}:fps={VIDEO_FPS},"
        f"format=yuv420p"
    )
    _run(
        [
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
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-tune",
            "stillimage",
            str(output_path),
        ],
        f"kenburns-{index}",
    )


def _run(cmd: list[str], label: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg falhou ({label}):\n{result.stderr[-1800:]}")
