"""Identidade visual do canal/projeto — marca, tom e consistência."""
from __future__ import annotations

from typing import Any

# Padrão editável, alinhado a histórias bíblicas em pt-BR (Prosperidade e Fé).
DEFAULT_BRAND: dict[str, str] = {
    "brand_name": "Prosperidade e Fé",
    "brand_voice": (
        "Reverente, claro e acolhedor em português do Brasil. "
        "Narrativa firme, sem sensacionalismo nem linguagem de autoajuda vazia."
    ),
    "brand_palette": (
        "Dourado suave, areia, terracota e azul noite; contraste legível, "
        "sem neon e sem róseo artificial."
    ),
    "brand_caption_style": (
        "Legenda limpa, sans-serif, branco com sombra escura, "
        "centralizada na base do quadro, texto curto."
    ),
    "brand_visual_notes": (
        "Ambiente bíblico histórico do Oriente Próximo; rostos e figurinos "
        "consistentes entre cenas; sem anacronismos modernos, logos ou texto na imagem."
    ),
    "brand_logo_note": "",
}

BRAND_FIELDS = tuple(DEFAULT_BRAND.keys())


def default_brand_values() -> dict[str, str]:
    return dict(DEFAULT_BRAND)


def project_brand(project: dict[str, Any] | None) -> dict[str, str]:
    """Campos de marca do projeto, com fallback nos padrões."""
    project = project or {}
    out: dict[str, str] = {}
    for key, default in DEFAULT_BRAND.items():
        raw = project.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            out[key] = default if key != "brand_logo_note" else ""
        else:
            out[key] = str(raw).strip()
    return out


def compose_brand_prompt_fragment(project: dict[str, Any] | None) -> str:
    """Trecho em inglês/pt leve acrescentado ao prompt de imagem."""
    brand = project_brand(project)
    parts: list[str] = []
    name = brand.get("brand_name") or ""
    if name:
        parts.append(f"channel look inspired by {name} biblical storytelling")
    palette = brand.get("brand_palette") or ""
    if palette:
        parts.append(f"preferred colors: {palette}")
    notes = brand.get("brand_visual_notes") or ""
    if notes:
        parts.append(f"visual consistency: {notes}")
    logo = brand.get("brand_logo_note") or ""
    if logo:
        parts.append(f"brand reference note: {logo}")
    return "; ".join(parts)


def brand_fields_from_form(**fields: Any) -> dict[str, str]:
    """Normaliza strings vindas do formulário (vazios viram padrão, exceto logo)."""
    out: dict[str, str] = {}
    for key in BRAND_FIELDS:
        raw = fields.get(key, "")
        text = str(raw or "").strip()
        if not text and key != "brand_logo_note":
            text = DEFAULT_BRAND[key]
        if key == "brand_name":
            text = text[:80]
        elif key == "brand_logo_note":
            text = text[:240]
        else:
            text = text[:500]
        out[key] = text
    return out
