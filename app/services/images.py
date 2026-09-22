"""Geração de imagens de cena: Grok Imagine / OpenAI / Pollinations + fallback Pillow."""
from __future__ import annotations

import hashlib
import re
import io
import json
import logging
import math
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.config import (
    GROK_IMAGE_MODEL,
    IMAGE_MAX_RETRIES,
    IMAGE_PROVIDER,
    IMAGE_TIMEOUT_SEC,
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    POLLINATIONS_BASE,
    XAI_API_KEY,
    frame_size,
    grok_aspect,
)

logger = logging.getLogger(__name__)

# Paletas “cinematográficas” bíblicas (fallback Pillow)
PALETTES = [
    ((28, 18, 12), (120, 72, 32), (212, 168, 88)),
    ((12, 20, 36), (48, 72, 110), (200, 160, 90)),
    ((20, 28, 18), (60, 90, 50), (180, 150, 70)),
    ((36, 16, 20), (100, 40, 40), (220, 140, 80)),
    ((14, 14, 28), (40, 40, 80), (160, 140, 200)),
    ((24, 22, 16), (80, 70, 40), (230, 200, 120)),
]

STYLE_SUFFIX = (
    "biblical epic cinematic still, ancient Near East landscape, "
    "golden hour dramatic lighting, film still, photorealistic, "
    "no text, no watermark, no logos, no subtitles"
)
STYLE_LANDSCAPE = "wide 16:9 cinematic composition"
STYLE_PORTRAIT = "vertical 9:16 cinematic composition, full-body or close portrait framed for mobile"

def _sanitize_prompt(text: str) -> str:
    """Normaliza pontuação problemática p/ URL/API Pollinations."""
    text = text.replace("—", "-").replace("–", "-").replace("…", "...")
    text = text.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text




def build_image_prompt(
    scene_title: str,
    scene_text: str,
    scene_index: int = 0,
    *,
    characters: list | None = None,
    compact: bool = False,
    aspect: str = "16:9",
    cast: str = "",
) -> str:
    """Monta prompt em inglês a partir do roteiro/título + bible dos personagens.

    Args:
        characters: lista de dicts (name, role, visual_bible) já filtrados p/ a cena.
        compact: se True, encurta o texto narrativo (útil p/ Pollinations).
    """
    from app.services.characters import build_consistency_block, match_characters_in_scene

    title = _sanitize_prompt(scene_title or f"Scene {scene_index + 1}")
    text = _sanitize_prompt((scene_text or "").replace("\n", " "))
    limit = 120 if compact else 220
    if len(text) > limit:
        text = text[: limit - 3] + "..."

    matched = characters
    if matched is None:
        matched = []
    # Se passaram a lista completa do projeto, filtrar por cena
    # (caller pode já ter filtrado; match_characters_in_scene é idempotente)
    if matched:
        matched = match_characters_in_scene(
            matched, scene_title, scene_text, cast=cast
        )

    names = [((c.get("name") or "").strip()) for c in matched if (c.get("name") or "").strip()]
    who = f" Featuring: {', '.join(names)}." if names else ""
    core = f"Biblical story scene: {title}.{who} Narration cue: {text}".strip()
    consistency = build_consistency_block(matched) if matched else ""
    framing = STYLE_PORTRAIT if grok_aspect(aspect) == "9:16" else STYLE_LANDSCAPE
    parts = [core]
    if consistency:
        parts.append(consistency)
    parts.append(framing)
    parts.append(STYLE_SUFFIX)
    prompt = "\n".join(parts)
    if compact:
        prompt = " ".join(prompt.split())
    # Pollinations URL length / Grok prompt caps
    max_len = 1800 if compact else 3900
    if len(prompt) > max_len:
        prompt = prompt[: max_len - 3] + "..."
    return prompt


def generate_scene_image(
    scene_title: str,
    scene_text: str,
    output_path: Path,
    scene_index: int = 0,
    *,
    provider: str | None = None,
    force_placeholder: bool = False,
    seed_salt: int = 0,
    characters: list | None = None,
    aspect: str = "16:9",
    cast: str = "",
) -> tuple[Path, str]:
    """Gera imagem no formato do projeto (16:9 ou 9:16).

    Returns:
        (path, source) onde source é 'grok' | 'grok_edit' | 'openai' | 'pollinations' | 'placeholder'.
    """
    from app.services.characters import collect_reference_paths, match_characters_in_scene

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = frame_size(aspect)

    chars = list(characters or [])
    scene_chars = (
        match_characters_in_scene(chars, scene_title, scene_text, cast=cast)
        if chars
        else []
    )
    ref_paths = [p for p in collect_reference_paths(scene_chars, limit=3) if Path(p).is_file()]

    chosen = (provider or IMAGE_PROVIDER or "pollinations").lower()
    if chosen == "auto":
        if XAI_API_KEY:
            chosen = "grok"
        elif OPENAI_API_KEY:
            chosen = "openai"
        else:
            chosen = "pollinations"
    seed_key = scene_index + int(seed_salt)

    prompt_full = build_image_prompt(
        scene_title,
        scene_text,
        scene_index,
        characters=chars,
        compact=False,
        aspect=aspect,
        cast=cast,
    )
    prompt_compact = build_image_prompt(
        scene_title,
        scene_text,
        scene_index,
        characters=chars,
        compact=True,
        aspect=aspect,
        cast=cast,
    )

    if not force_placeholder:
        chain: list[str] = []
        if chosen == "grok":
            chain = ["grok", "pollinations"]
        elif chosen == "openai":
            chain = ["openai", "pollinations"]
        elif chosen == "pollinations":
            chain = ["pollinations"]
        elif chosen == "placeholder":
            chain = []
        else:
            chain = ["pollinations"]

        for name in chain:
            try:
                if name == "grok":
                    if not XAI_API_KEY:
                        raise RuntimeError("XAI_API_KEY não definida")
                    if ref_paths:
                        try:
                            _generate_grok_edit(
                                prompt_full, output_path, ref_paths, aspect=aspect
                            )
                            return output_path, "grok_edit"
                        except Exception as edit_exc:  # noqa: BLE001
                            logger.warning(
                                "Grok edit/ref failed, falling back to generations: %s",
                                edit_exc,
                            )
                    _generate_grok(prompt_full, output_path, seed_key, aspect=aspect)
                    return output_path, "grok"
                if name == "openai":
                    if not OPENAI_API_KEY:
                        raise RuntimeError("OPENAI_API_KEY não definida")
                    _generate_openai(
                        prompt_full, output_path, seed_key, aspect=aspect
                    )
                    return output_path, "openai"
                if name == "pollinations":
                    _generate_pollinations(
                        prompt_compact, output_path, seed_key, aspect=aspect
                    )
                    return output_path, "pollinations"
            except Exception as exc:  # noqa: BLE001
                nxt = "Pollinations" if name != "pollinations" else "placeholder"
                logger.warning("%s image failed, trying %s: %s", name, nxt, exc)

    _generate_placeholder(
        scene_title, scene_text, output_path, scene_index, width=width, height=height
    )
    return output_path, "placeholder"


def active_provider_label() -> str:
    """Rótulo amigável do provedor ativo (para UI)."""
    if IMAGE_PROVIDER == "grok" and XAI_API_KEY:
        return f"xAI Grok Imagine ({GROK_IMAGE_MODEL})"
    if IMAGE_PROVIDER == "grok":
        return "xAI Grok Imagine (sem XAI_API_KEY → fallback)"
    if IMAGE_PROVIDER == "openai" and OPENAI_API_KEY:
        return "OpenAI Images"
    if IMAGE_PROVIDER == "placeholder":
        return "Placeholder (Pillow)"
    if IMAGE_PROVIDER == "openai":
        return "OpenAI Images (sem chave → Pollinations)"
    return "Pollinations.ai"


# ---------- Providers ----------





def _file_to_data_uri(path: Path) -> str:
    """Converte arquivo local em data URI base64 p/ xAI edits."""
    import base64
    import mimetypes

    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    if not mime or not mime.startswith("image/"):
        # JPEG default se extensão desconhecida
        if raw[:2] == b"\xff\xd8":
            mime = "image/jpeg"
        elif raw[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        elif raw[:6] in (b"GIF87a", b"GIF89a"):
            mime = "image/gif"
        elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            mime = "image/jpeg"
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _generate_grok_edit(
    prompt: str,
    output_path: Path,
    reference_paths: list[str],
    *,
    aspect: str = "16:9",
) -> None:
    """xAI Grok Imagine edit com imagens de referência (POST /v1/images/edits).

    Usa data URIs locais. Até 3 refs (multi-image editing).
    Docs: https://docs.x.ai/developers/model-capabilities/images/editing
    """
    import base64

    refs = [Path(p) for p in reference_paths if Path(p).is_file()][:3]
    if not refs:
        raise RuntimeError("Nenhuma imagem de referência válida")

    # Prompt de edição: manter identidade dos refs + nova cena
    edit_prompt = (
        "Using the reference image(s) as the exact character appearance guide, "
        "compose this NEW biblical cinematic scene while preserving the same faces, "
        "hair, clothing colors and body builds from the references. "
        f"{prompt}"
    )[:3900]

    images_payload = [{"url": _file_to_data_uri(p), "type": "image_url"} for p in refs]
    body: dict = {
        "model": GROK_IMAGE_MODEL,
        "prompt": edit_prompt,
        "n": 1,
        "aspect_ratio": grok_aspect(aspect),
        "resolution": "2k",
        "response_format": "url",
    }
    if "2.0" in GROK_IMAGE_MODEL:
        body["quality"] = "medium"

    if len(images_payload) == 1:
        body["image"] = images_payload[0]
    else:
        # Multi-image editing: campo `images` (até 3)
        body["images"] = images_payload

    req = urllib.request.Request(
        "https://api.x.ai/v1/images/edits",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "HistoriasBiblicasStudio/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=IMAGE_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = b""
        try:
            err_body = exc.read()
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(
            f"Grok Imagine edit HTTP {exc.code}: "
            f"{err_body[:400].decode('utf-8', errors='replace')}"
        ) from exc

    items = payload.get("data") or []
    if not items:
        raise RuntimeError(f"Grok Imagine edit: resposta sem data: {payload!r}"[:300])
    item = items[0]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        _save_image_bytes(raw, output_path, aspect=aspect)
        return
    image_url = item.get("url")
    if not image_url:
        raise RuntimeError("Grok Imagine edit: sem url nem b64_json")
    data = _http_get_bytes(image_url, retries=2)
    _save_image_bytes(data, output_path, aspect=aspect)


def _generate_grok(
    prompt: str, output_path: Path, scene_index: int, *, aspect: str = "16:9"
) -> None:
    """xAI Grok Imagine — POST /v1/images/generations (requer XAI_API_KEY)."""
    import base64

    body = {
        "model": GROK_IMAGE_MODEL,
        "prompt": prompt[:3900],
        "n": 1,
        "aspect_ratio": grok_aspect(aspect),
        "resolution": "2k",
        "response_format": "url",
    }
    # quality só é suportado em grok-imagine-image-2.0
    if "2.0" in GROK_IMAGE_MODEL:
        body["quality"] = "medium"

    req = urllib.request.Request(
        "https://api.x.ai/v1/images/generations",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "HistoriasBiblicasStudio/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=IMAGE_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = b""
        try:
            err_body = exc.read()
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(
            f"Grok Imagine HTTP {exc.code}: "
            f"{err_body[:400].decode('utf-8', errors='replace')}"
        ) from exc

    items = payload.get("data") or []
    if not items:
        raise RuntimeError(f"Grok Imagine: resposta sem data: {payload!r}"[:300])
    item = items[0]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        _save_image_bytes(raw, output_path, aspect=aspect)
        return
    image_url = item.get("url")
    if not image_url:
        raise RuntimeError("Grok Imagine: sem url nem b64_json")
    data = _http_get_bytes(image_url, retries=2)
    _save_image_bytes(data, output_path, aspect=aspect)


def _generate_pollinations(
    prompt: str, output_path: Path, scene_index: int, *, aspect: str = "16:9"
) -> None:
    """GET image.pollinations.ai/prompt/{urlencoded}?width&height&nologo&seed."""
    encoded = urllib.parse.quote(prompt, safe="")
    seed = int(hashlib.md5(f"{scene_index}:{prompt[:80]}".encode()).hexdigest()[:8], 16)
    shorts = grok_aspect(aspect) == "9:16"
    params = urllib.parse.urlencode(
        {
            "width": 768 if shorts else 1280,
            "height": 1280 if shorts else 720,
            "nologo": "true",
            "seed": seed,
            "model": "flux",
        }
    )
    url = f"{POLLINATIONS_BASE}/{encoded}?{params}"
    data = _http_get_bytes(url, retries=IMAGE_MAX_RETRIES)
    _save_image_bytes(data, output_path, aspect=aspect)


def _generate_openai(
    prompt: str, output_path: Path, scene_index: int, *, aspect: str = "16:9"
) -> None:
    """OpenAI Images API (DALL·E 3 / gpt-image) via REST — requer OPENAI_API_KEY."""
    # dall-e-3 sizes: 1024x1024, 1792x1024, 1024x1792
    size = "1024x1792" if grok_aspect(aspect) == "9:16" else "1792x1024"
    body = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt[:3900],
        "n": 1,
        "size": size,
        "response_format": "url",
    }
    # gpt-image models may not support response_format=url the same way
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "HistoriasBiblicasStudio/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=IMAGE_TIMEOUT_SEC) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    items = payload.get("data") or []
    if not items:
        raise RuntimeError("OpenAI Images: resposta sem data")
    item = items[0]
    if item.get("b64_json"):
        import base64

        raw = base64.b64decode(item["b64_json"])
        _save_image_bytes(raw, output_path, aspect=aspect)
        return
    image_url = item.get("url")
    if not image_url:
        raise RuntimeError("OpenAI Images: sem url nem b64_json")
    data = _http_get_bytes(image_url, retries=2)
    _save_image_bytes(data, output_path, aspect=aspect)


def _http_get_bytes(url: str, retries: int = 4) -> bytes:
    """GET com retry em 429/5xx. Valida que o corpo parece imagem."""
    last_err: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "HistoriasBiblicasStudio/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=IMAGE_TIMEOUT_SEC) as resp:
                data = resp.read()
                ctype = (resp.headers.get("Content-Type") or "").lower()
            if data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n":
                return data
            if "json" in ctype or data[:1] == b"{":
                raise RuntimeError(f"API retornou JSON: {data[:200]!r}")
            # Aceitar outros binários e deixar o Pillow validar
            if len(data) > 5000:
                return data
            raise RuntimeError(f"Resposta pequena/inválida ({len(data)} bytes)")
        except urllib.error.HTTPError as exc:
            last_err = exc
            body = b""
            try:
                body = exc.read()
            except Exception:  # noqa: BLE001
                pass
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                # Fila anônima Pollinations: backoff longo em 429
                wait = (45 if exc.code == 429 else 15) * (attempt + 1)
                logger.info(
                    "HTTP %s na geração de imagem; retry em %ss (%s)",
                    exc.code,
                    wait,
                    body[:120],
                )
                time.sleep(wait)
                continue
            raise RuntimeError(
                f"HTTP {exc.code}: {body[:300].decode('utf-8', errors='replace')}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Falha HTTP após retries: {last_err}")


def _save_image_bytes(data: bytes, output_path: Path, *, aspect: str = "16:9") -> None:
    """Abre bytes, redimensiona para o frame do projeto e salva JPEG."""
    width, height = frame_size(aspect)
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    if img.size != (width, height):
        img = _fit_cover(img, width, height)
    img.save(output_path, "JPEG", quality=92)


def _fit_cover(img: Image.Image, width: int, height: int) -> Image.Image:
    """Crop central cobrindo o frame (cover)."""
    src_w, src_h = img.size
    scale = max(width / src_w, height / src_h)
    new_w, new_h = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return img.crop((left, top, left + width, top + height))


# ---------- Placeholder Pillow (fallback) ----------


def _generate_placeholder(
    scene_title: str,
    scene_text: str,
    output_path: Path,
    scene_index: int = 0,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Cria imagem estilizada com gradiente + título da cena."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seed = int(hashlib.md5(f"{scene_index}:{scene_title}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    top, mid, accent = PALETTES[scene_index % len(PALETTES)]

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height, 1)
        if t < 0.55:
            c = _lerp(top, mid, t / 0.55)
        else:
            u = (t - 0.55) / 0.45
            c = _lerp(mid, accent, u * 0.6)
        draw.line([(0, y), (width, y)], fill=c)

    cx = int(width * rng.uniform(0.3, 0.7))
    cy = int(height * rng.uniform(0.15, 0.45))
    light = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    for r in range(420, 0, -20):
        alpha = int(40 * (r / 420))
        color = (*accent, alpha)
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    img = Image.alpha_composite(img.convert("RGBA"), light).convert("RGB")
    draw = ImageDraw.Draw(img)

    _draw_hills(draw, rng, mid, accent, width, height)
    if scene_index % 3 != 2:
        _draw_silhouette(draw, rng, top, width, height)

    img = img.filter(ImageFilter.SMOOTH_MORE)
    img = _apply_vignette(img)

    draw = ImageDraw.Draw(img)
    font_title = _load_font(64 if width >= 1600 else 48)
    font_sub = _load_font(32 if width >= 1600 else 26)
    font_badge = _load_font(26)

    badge = f"CENA {scene_index + 1:02d}"
    title = (scene_title or f"Cena {scene_index + 1}")[:80]

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle(
        [0, height - 280, width, height],
        fill=(8, 6, 4, 170),
    )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.text((80, height - 240), badge, fill=(212, 175, 100), font=font_badge)
    draw.text((80, height - 190), title, fill=(245, 235, 210), font=font_title)

    preview = (scene_text or "").replace("\n", " ")[:110]
    if len((scene_text or "")) > 110:
        preview += "…"
    draw.text((80, height - 100), preview, fill=(200, 190, 170), font=font_sub)

    draw.text(
        (max(24, width - 420), 40),
        "Histórias Bíblicas Studio",
        fill=(180, 160, 120),
        font=_load_font(24),
    )

    img.save(output_path, "JPEG", quality=92)
    return output_path


def _lerp(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _draw_hills(
    draw: ImageDraw.ImageDraw,
    rng: random.Random,
    mid: tuple[int, int, int],
    accent: tuple[int, int, int],
    width: int = 1920,
    height: int = 1080,
) -> None:
    base_y = int(height * 0.62)
    for layer in range(3):
        points = [(0, height)]
        y = base_y + layer * 40
        color = _lerp(mid, (10, 8, 6), 0.3 + layer * 0.2)
        x = 0
        while x <= width:
            h = int(30 + 80 * abs(math.sin(x / 180 + layer)) + rng.randint(-10, 10))
            points.append((x, y - h))
            x += 80
        points.append((width, height))
        draw.polygon(points, fill=color)


def _draw_silhouette(
    draw: ImageDraw.ImageDraw,
    rng: random.Random,
    top: tuple[int, int, int],
    width: int = 1920,
    height: int = 1080,
) -> None:
    x = int(width * rng.uniform(0.35, 0.65))
    base = int(height * 0.72)
    fill = (max(0, top[0] - 8), max(0, top[1] - 8), max(0, top[2] - 8))
    draw.ellipse([x - 22, base - 200, x + 22, base - 156], fill=fill)
    draw.polygon(
        [(x - 35, base - 150), (x + 35, base - 150), (x + 50, base - 20), (x - 50, base - 20)],
        fill=fill,
    )
    if rng.random() > 0.4:
        draw.line([(x + 40, base - 220), (x + 55, base)], fill=fill, width=6)


def _apply_vignette(img: Image.Image) -> Image.Image:
    vignette = Image.new("L", img.size, 0)
    vd = ImageDraw.Draw(vignette)
    cx, cy = img.size[0] // 2, img.size[1] // 2
    max_r = int(math.hypot(cx, cy))
    for r in range(max_r, 0, -8):
        brightness = int(255 * (1 - (r / max_r) ** 1.8) * 0.85 + 40)
        vd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=brightness)
    return Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)), vignette)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()
