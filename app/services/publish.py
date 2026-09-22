"""Thumbnail, metadados de YouTube e pacote ZIP de publicação."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.config import SUBTITLE_FONT



STOP = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "um", "uma",
    "para", "com", "em", "no", "na", "por", "que", "se", "ao", "à",
}


def generate_metadata(
    title: str,
    theme: str,
    script: str,
    *,
    series_name: str = "",
    episode_number: int | None = None,
) -> dict[str, str]:
    clean_title = (title or "História bíblica").strip()
    series = (series_name or "").strip()
    episode: int | None = None
    if episode_number not in (None, ""):
        try:
            parsed = int(episode_number)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            parsed = 0
        if parsed >= 1:
            episode = parsed

    if series and episode:
        yt_title = f"{series} — Ep. {episode} · {clean_title}"
    elif series:
        yt_title = f"{series} — {clean_title}"
    else:
        yt_title = clean_title
    biblical = "bíblic" in yt_title.lower() or "biblic" in yt_title.lower()
    if not biblical:
        with_tag = f"{yt_title} | História Bíblica"
        yt_title = with_tag if len(with_tag) <= 95 else yt_title
    if len(yt_title) > 95:
        yt_title = yt_title[:92] + "…"

    body = (script or "").strip()
    lead = re.split(r"\n\s*\n", body)[0].strip() if body else ""
    if len(lead) > 400:
        lead = lead[:397] + "…"
    desc_parts = [lead, ""]
    if series:
        series_line = f"Série: {series}"
        if episode:
            series_line += f" · Episódio {episode}"
        desc_parts.extend([series_line, ""])
    desc_parts.extend(
        [
            f"📖 {theme.strip().capitalize() or 'Histórias bíblicas'}",
            "",
            "Vídeo narrado automaticamente pelo Histórias Bíblicas Studio.",
            "Inscreva-se para mais histórias da Bíblia.",
            "",
            "#HistoriasBiblicas #Biblia #Fe",
        ]
    )
    description = "\n".join(desc_parts).strip()

    words = re.findall(r"[A-Za-zÀ-ÿ0-9]+", f"{clean_title} {theme} {series}")
    tags = ["histórias bíblicas", "bíblia", "história bíblica", "youtube", "fé"]
    if series and series.lower() not in {t.lower() for t in tags}:
        tags.append(series)
    for w in words:
        lw = w.lower()
        if len(lw) < 3 or lw in STOP:
            continue
        if lw not in {t.lower() for t in tags}:
            tags.append(w)
        if len(tags) >= 12:
            break
    return {
        "youtube_title": yt_title,
        "youtube_description": description,
        "youtube_tags": ", ".join(tags),
    }


def write_thumbnail(
    scene_image: Path,
    title: str,
    output_path: Path,
    aspect: str = "16:9",
) -> Path:
    """Capa 1280×720 (YouTube) a partir da primeira cena + título."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # YouTube thumbnail sempre 16:9 1280x720, mesmo para Shorts
    W, H = 1280, 720
    canvas = Image.new("RGB", (W, H), (18, 12, 8))
    if scene_image and Path(scene_image).exists():
        src = Image.open(scene_image).convert("RGB")
        src = _cover(src, W, H)
        canvas.paste(src, (0, 0))
    # vinheta inferior
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(H // 2, H):
        alpha = int(210 * ((y - H / 2) / (H / 2)))
        draw.line([(0, y), (W, y)], fill=(12, 8, 4, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    font = _font(54)
    small = _font(22)
    wrapped = _fit_title(title or "História Bíblica", 22)
    y = H - 88 - 58 * (wrapped.count("\n"))
    # borda do texto
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (0, 0)):
        color = (40, 24, 8) if (dx, dy) != (0, 0) else (243, 224, 176)
        draw.multiline_text((48 + dx, y + dy), wrapped, font=font, fill=color, spacing=6)
    draw.text((48, H - 42), "HISTÓRIAS BÍBLICAS", font=small, fill=(212, 168, 75))
    canvas.save(output_path, "JPEG", quality=92)
    return output_path


def write_pack(
    *,
    output_path: Path,
    video_path: Path | None,
    captions_path: Path | None,
    thumbnail_path: Path | None,
    meta: dict[str, str],
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if video_path and Path(video_path).exists():
            zf.write(video_path, "video.mp4")
        if captions_path and Path(captions_path).exists():
            zf.write(captions_path, "legendas.srt")
        if thumbnail_path and Path(thumbnail_path).exists():
            zf.write(thumbnail_path, "thumbnail.jpg")
        txt = (
            f"Título: {meta.get('youtube_title', '')}\n\n"
            f"Descrição:\n{meta.get('youtube_description', '')}\n\n"
            f"Tags: {meta.get('youtube_tags', '')}\n"
        )
        zf.writestr("youtube.txt", txt)
    return output_path


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path(SUBTITLE_FONT)
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _fit_title(title: str, max_chars: int) -> str:
    words = title.strip().split()
    lines: list[str] = []
    cur: list[str] = []
    n = 0
    remaining = list(words)
    while remaining:
        w = remaining[0]
        extra = len(w) + (1 if cur else 0)
        if n + extra > max_chars and cur:
            lines.append(" ".join(cur))
            cur = []
            n = 0
            if len(lines) >= 2:
                rest = " ".join(remaining)
                if rest:
                    lines.append(rest)
                break
            continue
        cur.append(w)
        remaining = remaining[1:]
        n += extra
    if cur and len(lines) < 3:
        lines.append(" ".join(cur))
    return "\n".join(lines[:3])

