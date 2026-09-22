"""Legendas SRT a partir das cenas (duração da narração)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _ts(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def scene_windows(scenes: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    """(start, end, text) por cena, em sequência."""
    t = 0.0
    windows: list[tuple[float, float, str]] = []
    for sc in scenes:
        dur = float(sc.get("duration_sec") or 0) or 1.5
        text = (sc.get("text") or sc.get("title") or "").strip()
        windows.append((t, t + dur, text))
        t += dur
    return windows


def write_srt(scenes: list[dict[str, Any]], output_path: Path) -> Path:
    """Gera um arquivo .srt com o texto de cada cena."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    for i, (start, end, text) in enumerate(scene_windows(scenes), start=1):
        if not text:
            continue
        line = _wrap(text, 42)
        blocks.append(f"{i}\n{_ts(start)} --> {_ts(end)}\n{line}\n")
    output_path.write_text("\n".join(blocks).strip() + "\n", encoding="utf-8")
    return output_path


def _wrap(text: str, width: int) -> str:
    words = text.replace("\n", " ").split()
    lines: list[str] = []
    cur: list[str] = []
    n = 0
    for i, w in enumerate(words):
        extra = len(w) + (1 if cur else 0)
        if n + extra > width and cur:
            lines.append(" ".join(cur))
            cur = [w]
            n = len(w)
            if len(lines) >= 2:
                lines.append(" ".join(words[i:]))
                return "\n".join(lines[:3])
        else:
            cur.append(w)
            n += extra
    if cur:
        lines.append(" ".join(cur))
    return "\n".join(lines[:3])
