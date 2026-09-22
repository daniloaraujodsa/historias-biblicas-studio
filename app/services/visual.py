"""Presets de estilo, luz, câmera e atmosfera para o prompt de imagem.

Textos de prompt em inglês (modelos de imagem). Rótulos da UI ficam em pt-BR.
"""
from __future__ import annotations

from typing import Any

# Ordem estável da UI. O primeiro item é o padrão.
STYLES: dict[str, dict[str, str]] = {
    "cinematic": {
        "label": "Cinemático bíblico",
        "hint": "Filme épico, fotográfico, luz quente.",
        "prompt": (
            "biblical epic cinematic still, ancient Near East, film still, "
            "photorealistic, rich color grade"
        ),
        "default_light": "warm cinematic light with gentle golden highlights",
    },
    "oil": {
        "label": "Pintura a óleo sacra",
        "hint": "Tela, pincelada e claro-escuro de pintura religiosa.",
        "prompt": (
            "sacred oil painting, visible brushstrokes, old-master religious art, "
            "canvas texture, umber and gold pigments"
        ),
        "default_light": "chiaroscuro oil-paint light, warm varnish glow",
    },
    "illustration": {
        "label": "Ilustração digital clean",
        "hint": "Formas nítidas, paleta contida, sem fotorrealismo.",
        "prompt": (
            "clean digital illustration, crisp shapes, readable silhouettes, "
            "limited palette, polished concept art, not a photograph"
        ),
        "default_light": "even illustrative light, clear color separation",
    },
    "semi3d": {
        "label": "Semi-realista 3D",
        "hint": "Render estilizado, materiais suaves, profundidade de campo.",
        "prompt": (
            "semi-realistic 3D render, stylized proportions, soft skin shading, "
            "cinematic materials, gentle depth of field"
        ),
        "default_light": "soft studio key light with a warm rim",
    },
    "watercolor": {
        "label": "Aquarela storybook",
        "hint": "Papel, aguada e traço leve de livro ilustrado.",
        "prompt": (
            "watercolor storybook illustration, paper grain, soft pigment washes, "
            "delicate ink outlines, gentle biblical picture-book mood"
        ),
        "default_light": "soft diffused daylight, pale washes",
    },
    "contrast": {
        "label": "Alto contraste dramático",
        "hint": "Sombras duras, recorte gráfico, clima tenso.",
        "prompt": (
            "high-contrast dramatic biblical still, deep shadows, hard rim light, "
            "stark silhouettes, graphic chiaroscuro"
        ),
        "default_light": "single hard key light, crushed blacks",
    },
}

LIGHTS: dict[str, dict[str, str]] = {
    "golden": {
        "label": "Dourada bíblica",
        "prompt": "lighting: warm biblical golden hour, honey highlights, soft god rays",
    },
    "rembrandt": {
        "label": "Rembrandt",
        "prompt": "lighting: Rembrandt lighting, small triangle of light on the cheek, deep shadow side",
    },
    "natural": {
        "label": "Natural",
        "prompt": "lighting: natural daylight, open shade, true colors, no theatrical beams",
    },
    "dramatic": {
        "label": "Dramática",
        "prompt": "lighting: dramatic key light, strong contrast, theatrical beam through dust",
    },
    "moonlight": {
        "label": "Luar",
        "prompt": "lighting: cool moonlight, silver rim light, deep blue shadows",
    },
    "firelight": {
        "label": "Luz de fogo",
        "prompt": "lighting: oil lamps and firelight, flickering warm glow, smoky highlights",
    },
}

CAMERAS: dict[str, dict[str, str]] = {
    "close": {
        "label": "Close",
        "prompt": "camera: intimate close-up, shallow depth of field, face and hands in focus",
    },
    "medium": {
        "label": "Plano médio",
        "prompt": "camera: medium shot, waist-up framing, clear gesture and costume",
    },
    "wide": {
        "label": "Plano aberto",
        "prompt": "camera: wide establishing shot, vast landscape, figures small in the frame",
    },
    "low": {
        "label": "Ângulo baixo",
        "prompt": "camera: low angle looking up, monumental scale",
    },
    "high": {
        "label": "Ângulo alto",
        "prompt": "camera: high angle looking down, overview and vulnerability",
    },
    "over_shoulder": {
        "label": "Por cima do ombro",
        "prompt": "camera: over-the-shoulder composition, tension between two figures",
    },
}

ATMOSPHERES: dict[str, dict[str, str]] = {
    "storm": {
        "label": "Tempestade",
        "prompt": "atmosphere: gathering storm, wind, heavy clouds, dust and rain",
    },
    "temple": {
        "label": "Templo",
        "prompt": "atmosphere: ancient temple interior, stone columns, incense haze, oil lamps",
    },
    "desert": {
        "label": "Deserto",
        "prompt": "atmosphere: Judean desert, dry heat, sandstone, sparse scrub, harsh sun",
    },
    "camp": {
        "label": "Acampamento",
        "prompt": "atmosphere: night encampment, tents, campfires, stars",
    },
    "sea": {
        "label": "Mar",
        "prompt": "atmosphere: open water and wind, distant horizon, spray in the air",
    },
    "garden": {
        "label": "Jardim",
        "prompt": "atmosphere: quiet garden, olive trees, soft shade, still air",
    },
    "court": {
        "label": "Tribunal",
        "prompt": "atmosphere: crowded ancient courtyard and judgment seat, tense onlookers",
    },
    "battle": {
        "label": "Campo de batalha",
        "prompt": "atmosphere: valley battlefield, dust, banners, distant army",
    },
}

_CATALOGS = {
    "light": LIGHTS,
    "camera": CAMERAS,
    "atmosphere": ATMOSPHERES,
}

CONSTRAINTS = "no text, no watermark, no logos, no subtitles, no modern objects"


def normalize_style(value: str | None) -> str:
    key = (value or "").strip().lower()
    return key if key in STYLES else "cinematic"


def normalize_preset(value: str | None, kind: str) -> str:
    catalog = _CATALOGS.get(kind) or {}
    key = (value or "").strip().lower()
    return key if key in catalog else ""


def label_for_style(value: str | None) -> str:
    return STYLES[normalize_style(value)]["label"]


def _options(catalog: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    return [{"id": key, "label": spec["label"]} for key, spec in catalog.items()]


def style_options() -> list[dict[str, str]]:
    return [
        {"id": key, "label": spec["label"], "hint": spec["hint"]}
        for key, spec in STYLES.items()
    ]


def light_options() -> list[dict[str, str]]:
    return _options(LIGHTS)


def camera_options() -> list[dict[str, str]]:
    return _options(CAMERAS)


def atmosphere_options() -> list[dict[str, str]]:
    return _options(ATMOSPHERES)


def compose_visual_block(
    visual_style: str | None = "",
    light: str | None = "",
    camera: str | None = "",
    atmosphere: str | None = "",
) -> str:
    """Bloco único acrescentado a todo prompt de cena."""
    style_key = normalize_style(visual_style)
    spec = STYLES[style_key]
    parts = [spec["prompt"]]
    light_key = normalize_preset(light, "light")
    if light_key:
        parts.append(LIGHTS[light_key]["prompt"])
    elif spec.get("default_light"):
        parts.append(spec["default_light"])
    camera_key = normalize_preset(camera, "camera")
    if camera_key:
        parts.append(CAMERAS[camera_key]["prompt"])
    atmosphere_key = normalize_preset(atmosphere, "atmosphere")
    if atmosphere_key:
        parts.append(ATMOSPHERES[atmosphere_key]["prompt"])
    parts.append(CONSTRAINTS)
    return ", ".join(parts)


def project_visual_kwargs(project: dict[str, Any] | None) -> dict[str, str]:
    project = project or {}
    from app.services.brand import compose_brand_prompt_fragment

    return {
        "visual_style": normalize_style(project.get("visual_style")),
        "light": normalize_preset(project.get("light_preset"), "light"),
        "camera": normalize_preset(project.get("camera_preset"), "camera"),
        "atmosphere": normalize_preset(project.get("atmosphere_preset"), "atmosphere"),
        "prompt_extra": (project.get("prompt_extra") or "").strip(),
        "brand_fragment": compose_brand_prompt_fragment(project),
    }


def compose_full_visual_preview(project: dict[str, Any] | None) -> str:
    """Pré-visualização do bloco visual + marca + notas de imagem."""
    kwargs = project_visual_kwargs(project)
    parts = [
        compose_visual_block(
            kwargs["visual_style"],
            light=kwargs["light"],
            camera=kwargs["camera"],
            atmosphere=kwargs["atmosphere"],
        )
    ]
    if kwargs.get("brand_fragment"):
        parts.append(kwargs["brand_fragment"])
    if kwargs.get("prompt_extra"):
        parts.append(kwargs["prompt_extra"])
    return "\n".join(parts)
