"""Narração TTS: edge-tts (preferido) → gTTS → espeak-ng (offline)."""
from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

from app.config import DEFAULT_VOICE


async def _edge_tts_async(text: str, output_path: Path, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def _gtts(text: str, output_path: Path) -> None:
    from gtts import gTTS

    tts = gTTS(text=text, lang="pt", tld="com.br")
    # gTTS grava mp3
    if output_path.suffix.lower() != ".mp3":
        tmp = output_path.with_suffix(".mp3")
        tts.save(str(tmp))
        if tmp != output_path:
            tmp.replace(output_path)
    else:
        tts.save(str(output_path))


def _espeak(text: str, output_path: Path) -> None:
    """Fallback offline com espeak-ng + ffmpeg."""
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
        asyncio.run(_edge_tts_async(text, output_path, voice or DEFAULT_VOICE))
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


def audio_duration_sec(path: Path) -> float:
    """Duração em segundos via ffprobe."""
    cmd = [
        "ffprobe",
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


def list_pt_br_voices() -> list[str]:
    return [
        "pt-BR-FranciscaNeural",
        "pt-BR-AntonioNeural",
        "pt-BR-ThalitaNeural",
    ]
