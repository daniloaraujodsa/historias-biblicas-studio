"""Segmentação de roteiro em cenas."""
from __future__ import annotations

import re
from typing import Any


def segment_script(
    script: str,
    min_scenes: int = 4,
    max_scenes: int = 16,
    hints: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Divide o roteiro em cenas por parágrafo / sentença."""
    text = (script or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) < min_scenes:
        # Quebra por sentenças
        sentences = _split_sentences(text)
        if len(sentences) >= min_scenes:
            paragraphs = _group_sentences(sentences, min_scenes, max_scenes)
        else:
            paragraphs = sentences or [text]

    if len(paragraphs) > max_scenes:
        paragraphs = _merge_to_max(paragraphs, max_scenes)

    scenes: list[dict[str, Any]] = []
    for i, para in enumerate(paragraphs):
        title = ""
        if hints and i < len(hints):
            title = hints[i]
        else:
            title = _title_from_text(para, i + 1)
        scenes.append(
            {
                "index": i,
                "title": title,
                "text": para,
                "image_path": None,
                "duration_sec": None,
            }
        )
    return scenes


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _group_sentences(
    sentences: list[str], min_scenes: int, max_scenes: int
) -> list[str]:
    n = min(max(min_scenes, len(sentences) // 2 or 1), max_scenes, len(sentences))
    if n <= 0:
        return sentences
    groups: list[str] = []
    size = max(1, len(sentences) // n)
    for i in range(0, len(sentences), size):
        chunk = " ".join(sentences[i : i + size])
        if chunk:
            groups.append(chunk)
        if len(groups) >= max_scenes:
            rest = " ".join(sentences[i + size :])
            if rest and groups:
                groups[-1] = groups[-1] + " " + rest
            break
    return groups


def _merge_to_max(paragraphs: list[str], max_scenes: int) -> list[str]:
    while len(paragraphs) > max_scenes:
        # Une os dois menores consecutivos
        best_i = 0
        best_len = len(paragraphs[0]) + len(paragraphs[1])
        for i in range(len(paragraphs) - 1):
            s = len(paragraphs[i]) + len(paragraphs[i + 1])
            if s < best_len:
                best_len = s
                best_i = i
        merged = paragraphs[best_i] + "\n\n" + paragraphs[best_i + 1]
        paragraphs = paragraphs[:best_i] + [merged] + paragraphs[best_i + 2 :]
    return paragraphs


def _title_from_text(text: str, index: int) -> str:
    first = text.split("\n")[0].strip()
    first = re.sub(r'^["“]|["”]$', "", first)
    if len(first) > 60:
        first = first[:57] + "…"
    return first or f"Cena {index}"


def allocate_durations(
    scenes: list[dict[str, Any]], total_audio_sec: float
) -> list[dict[str, Any]]:
    """Distribui duração proporcional ao tamanho do texto."""
    weights = [max(len(s.get("text") or ""), 1) for s in scenes]
    total_w = sum(weights) or 1
    # Mínimo 1.5s por cena
    min_d = 1.5
    raw = [total_audio_sec * (w / total_w) for w in weights]
    # Garantir mínimos e renormalizar
    adjusted = [max(d, min_d) for d in raw]
    adj_sum = sum(adjusted)
    if adj_sum > 0 and total_audio_sec > 0:
        scale = total_audio_sec / adj_sum
        # Se o áudio for curto demais para os mínimos, usa raw
        if adj_sum * scale < total_audio_sec * 0.5:
            adjusted = raw
            scale = 1.0
        else:
            adjusted = [d * scale for d in adjusted]
    for s, d in zip(scenes, adjusted):
        s["duration_sec"] = round(d, 3)
    return scenes
