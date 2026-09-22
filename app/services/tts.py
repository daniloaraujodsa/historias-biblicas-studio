"""Narração TTS: edge-tts (preferido) → gTTS → espeak-ng (offline)."""
from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any


from app.config import DEFAULT_VOICE


async def _edge_tts_async(text: str, output_path: Path, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def _run_coro(coro) -> None:
    """Roda um coroutine numa thread com loop próprio (seguro no FastAPI)."""

    def _target() -> None:
        asyncio.run(coro)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()


def _gtts(text: str, output_path: Path) -> None:
    from gtts import gTTS

    tts = gTTS(text=text, lang="pt", tld="com.br")
    if output_path.suffix.lower() != ".mp3":
        tmp = output_path.with_suffix(".mp3")
        tts.save(str(tmp))
        if tmp != output_path:
            tmp.replace(output_path)
    else:
        tts.save(str(output_path))


def _espeak(text: str, output_path: Path) -> None:
    engine = None
    for cand in ("espeak-ng", "espeak"):
        if subprocess.run(["which", cand], capture_output=True).returncode == 0:
            engine = cand
            break
    if not engine:
        raise RuntimeError(
            "Nenhum motor TTS disponível (edge-tts, gTTS e espeak falharam)."
        )
    wav = Path(tempfile.mkstemp(suffix=".wav")[1])
    try:
        subprocess.run(
            [engine, "-v", "pt-br", "-s", "150", "-w", str(wav), text],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav),
                "-codec:a",
                "libmp3lame",
                "-qscale:a",
                "4",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        wav.unlink(missing_ok=True)


def synthesize(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
) -> Path:
    """Gera áudio de narração (MP3). Tenta edge-tts → gTTS → espeak."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = (text or "").strip()
    if not text:
        raise ValueError("Texto vazio para TTS")

    errors: list[str] = []

    try:
        _run_coro(_edge_tts_async(text, output_path, voice or DEFAULT_VOICE))
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except Exception as exc:  # noqa: BLE001
        errors.append(f"edge-tts: {exc}")

    try:
        _gtts(text, output_path)
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except Exception as exc:  # noqa: BLE001
        errors.append(f"gTTS: {exc}")

    try:
        _espeak(text, output_path)
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except Exception as exc:  # noqa: BLE001
        errors.append(f"espeak: {exc}")

    raise RuntimeError("Falha em todos os motores TTS:\n" + "\n".join(errors))


def synthesize_scenes(
    scenes: list[dict[str, Any]],
    audio_dir: Path,
    voice: str = DEFAULT_VOICE,
) -> tuple[Path, list[dict[str, Any]]]:
    """TTS por cena + concatena num único MP3. Atualiza duration_sec de cada cena."""
    audio_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for sc in scenes:
        idx = int(sc.get("index", 0))
        text = (sc.get("text") or sc.get("title") or "").strip()
        if not text:
            text = f"Cena {idx + 1}."
        part = audio_dir / f"narration_{idx:02d}.mp3"
        synthesize(text, part, voice=voice)
        dur = audio_duration_sec(part)
        sc["duration_sec"] = round(dur, 3)
        sc["audio_path"] = str(part)
        parts.append(part)

    out = audio_dir / "narration.mp3"
    _concat_mp3(parts, out)
    return out, scenes


def _concat_mp3(parts: list[Path], output_path: Path) -> Path:
    if not parts:
        raise ValueError("Nenhum trecho de áudio para concatenar")
    if len(parts) == 1:
        output_path.write_bytes(parts[0].read_bytes())
        return output_path
    lst = output_path.with_suffix(".concat.txt")
    with lst.open("w", encoding="utf-8") as f:
        for p in parts:
            esc = str(p.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    lst.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao concatenar áudio:\n{result.stderr[-1500:]}")
    return output_path


def audio_duration_sec(path: Path) -> float:
    """Duração em segundos via ffprobe, ou ffmpeg se ffprobe não existir."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())

    result = subprocess.run(
        ["ffmpeg", "-i", str(path)],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr or "")
    if not match:
        raise RuntimeError(f"Não foi possível ler a duração de {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)




def list_pt_br_voices() -> list[str]:
    return [
        "pt-BR-FranciscaNeural",
        "pt-BR-AntonioNeural",
        "pt-BR-ThalitaNeural",
    ]
