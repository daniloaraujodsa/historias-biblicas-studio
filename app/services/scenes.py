"""Segmentação e edição de cenas do roteiro."""
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
        sentences = _split_sentences(text)
        if len(sentences) >= min_scenes:
            paragraphs = _group_sentences(sentences, min_scenes, max_scenes)
        else:
            paragraphs = sentences or [text]

    if len(paragraphs) > max_scenes:
        paragraphs = _merge_to_max(paragraphs, max_scenes)

    scenes: list[dict[str, Any]] = []
    for i, para in enumerate(paragraphs):
        title = hints[i] if hints and i < len(hints) else _title_from_text(para, i + 1)
        scenes.append(_blank_scene(i, title, para))
    return scenes


def _blank_scene(index: int, title: str, text: str) -> dict[str, Any]:
    return {
        "index": index,
        "title": title,
        "text": text,
        "cast": "",
        "image_path": None,
        "duration_sec": None,
        "image_source": None,
        "image_prompt": None,
    }


def reindex(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for i, s in enumerate(scenes):
        s["index"] = i
    return scenes


def add_scene(scenes: list[dict[str, Any]], after: int | None = None) -> list[dict[str, Any]]:
    n = len(scenes)
    idx = n if after is None else min(after + 1, n)
    scenes.insert(idx, _blank_scene(idx, f"Cena {idx + 1}", ""))
    return reindex(scenes)


def delete_scene(scenes: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
    scenes = [s for s in scenes if int(s.get("index", -1)) != index]
    return reindex(scenes)


def move_scene(scenes: list[dict[str, Any]], index: int, direction: int) -> list[dict[str, Any]]:
    scenes = sorted(scenes, key=lambda s: int(s.get("index", 0)))
    i = next((k for k, s in enumerate(scenes) if int(s.get("index", -1)) == index), None)
    if i is None:
        return reindex(scenes)
    j = i + direction
    if j < 0 or j >= len(scenes):
        return reindex(scenes)
    scenes[i], scenes[j] = scenes[j], scenes[i]
    return reindex(scenes)


def apply_scene_edits(scenes: list[dict[str, Any]], edits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aplica title/text/cast/duration vindos do editor, preservando imagens."""
    by_index = {int(s.get("index", i)): s for i, s in enumerate(scenes)}
    out: list[dict[str, Any]] = []
    for i, ed in enumerate(edits):
        idx = int(ed.get("index", i))
        base = by_index.get(idx, _blank_scene(i, f"Cena {i + 1}", ""))
        title = (ed.get("title") or base.get("title") or f"Cena {i + 1}").strip()
        text = ed.get("text") if "text" in ed else (base.get("text") or "")
        cast = (ed.get("cast") if "cast" in ed else (base.get("cast") or "")).strip()
        dur = ed.get("duration_sec")
        merged = dict(base)
        merged.update(
            {
                "index": i,
                "title": title,
                "text": (text or "").strip(),
                "cast": cast,
            }
        )
        if dur not in (None, ""):
            try:
                merged["duration_sec"] = round(float(dur), 3)
            except (TypeError, ValueError):
                pass
        out.append(merged)
    return reindex(out)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _group_sentences(sentences: list[str], min_scenes: int, max_scenes: int) -> list[str]:
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
    first = re.sub(r'^[\"“]|[\"”]$', "", first)
    if len(first) > 60:
        first = first[:57] + "…"
    return first or f"Cena {index}"


def allocate_durations(
    scenes: list[dict[str, Any]], total_audio_sec: float
) -> list[dict[str, Any]]:
    """Distribui duração proporcional ao tamanho do texto (fallback se não houver TTS por cena)."""
    weights = [max(len(s.get("text") or ""), 1) for s in scenes]
    total_w = sum(weights) or 1
    min_d = 1.5
    raw = [total_audio_sec * (w / total_w) for w in weights]
    adjusted = [max(d, min_d) for d in raw]
    adj_sum = sum(adjusted)
    if adj_sum > 0 and total_audio_sec > 0:
        scale = total_audio_sec / adj_sum
        if adj_sum * scale < total_audio_sec * 0.5:
            adjusted = raw
            scale = 1.0
        else:
            adjusted = [d * scale for d in adjusted]
    for s, d in zip(scenes, adjusted):
        s["duration_sec"] = round(d, 3)
    return scenes
