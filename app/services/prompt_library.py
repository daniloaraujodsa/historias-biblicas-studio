"""Biblioteca de blocos de prompt reutilizáveis (pt-BR)."""
from __future__ import annotations

from typing import Any

# Categorias estáveis para a UI e a semente.
CATEGORIES: dict[str, str] = {
    "cena": "Estilo de cena",
    "personagem": "Personagem",
    "ambiente": "Ambiente",
    "acao": "Ação",
    "narrativa": "Voz narrativa",
}

# Destino ao aplicar o bloco (campos do projeto).
TARGETS: dict[str, dict[str, str]] = {
    "prompt_extra": {
        "label": "Notas de imagem",
        "hint": "Entra no prompt de cada cena gerada.",
        "field": "prompt_extra",
    },
    "script": {
        "label": "Roteiro",
        "hint": "Acrescenta um parágrafo ao roteiro.",
        "field": "script",
    },
    "brand_visual_notes": {
        "label": "Notas da marca",
        "hint": "Soma às notas de consistência visual.",
        "field": "brand_visual_notes",
    },
}

# Corpos em português. Nos blocos de imagem, o texto serve de orientação visual.
SEED_BLOCKS: tuple[dict[str, str], ...] = (
    {
        "title": "Luz de templo",
        "category": "cena",
        "target": "prompt_extra",
        "body": (
            "Interior de templo antigo com colunas de pedra, névoa de incenso e "
            "raios de luz dourada entrando por frestas altas."
        ),
    },
    {
        "title": "Close emocional",
        "category": "cena",
        "target": "prompt_extra",
        "body": (
            "Close no rosto, olhar intenso, profundidade de campo rasa e "
            "expressão de fé e tensão contida."
        ),
    },
    {
        "title": "Pastor jovem",
        "category": "personagem",
        "target": "prompt_extra",
        "body": (
            "Jovem pastor hebreu, cabelos castanhos ondulados, túnica simples "
            "de lã, postura segura e olhar sereno."
        ),
    },
    {
        "title": "Ancião sábio",
        "category": "personagem",
        "target": "prompt_extra",
        "body": (
            "Ancião de barba longa e branca, manto completo, mãos marcadas "
            "pelo trabalho, presença reverente."
        ),
    },
    {
        "title": "Deserto ao entardecer",
        "category": "ambiente",
        "target": "prompt_extra",
        "body": (
            "Deserto da Judeia ao entardecer, dunas de arenito, calor seco, "
            "céu em degradê ocre e violeta."
        ),
    },
    {
        "title": "Mar agitado",
        "category": "ambiente",
        "target": "prompt_extra",
        "body": (
            "Mar aberto com vento forte, ondas escuras, horizonte distante "
            "e spray salgado no ar."
        ),
    },
    {
        "title": "Travessia sob ameaça",
        "category": "acao",
        "target": "prompt_extra",
        "body": (
            "Personagens em movimento urgente atravessando o cenário, "
            "poeira no ar, tensão e direção clara do olhar."
        ),
    },
    {
        "title": "Joelho no chão",
        "category": "acao",
        "target": "prompt_extra",
        "body": (
            "Figura ajoelhada em oração ou súplica, mãos juntas, "
            "silêncio e humildade no centro do quadro."
        ),
    },
    {
        "title": "Narração acolhedora",
        "category": "narrativa",
        "target": "script",
        "body": (
            "Nesta história, caminhamos com quem ouviu o chamado de Deus "
            "e descobriu que a fé abre caminho mesmo quando o medo grita mais alto."
        ),
    },
    {
        "title": "Tom de esperança",
        "category": "narrativa",
        "target": "brand_visual_notes",
        "body": (
            "Manter clima de esperança e reverência: rostos humanos, "
            "sem violência gráfica, luz que convida à reflexão."
        ),
    },
)


def normalize_category(value: str | None) -> str:
    key = (value or "").strip().lower()
    return key if key in CATEGORIES else "cena"


def normalize_target(value: str | None) -> str:
    key = (value or "").strip().lower()
    return key if key in TARGETS else "prompt_extra"


def category_options() -> list[dict[str, str]]:
    return [{"id": key, "label": label} for key, label in CATEGORIES.items()]


def target_options() -> list[dict[str, str]]:
    return [
        {"id": key, "label": spec["label"], "hint": spec["hint"]}
        for key, spec in TARGETS.items()
    ]


def category_label(value: str | None) -> str:
    return CATEGORIES.get(normalize_category(value), CATEGORIES["cena"])


def target_label(value: str | None) -> str:
    return TARGETS[normalize_target(value)]["label"]


def target_field(value: str | None) -> str:
    return TARGETS[normalize_target(value)]["field"]


def append_block_text(current: str | None, block_body: str) -> str:
    """Concatena o corpo do bloco ao campo, sem duplicar se já estiver no fim."""
    base = (current or "").rstrip()
    addition = (block_body or "").strip()
    if not addition:
        return base
    if not base:
        return addition
    if addition in base:
        return base
    sep = "\n\n" if "\n" in base or "\n" in addition else " "
    return f"{base}{sep}{addition}".strip()


def apply_block_to_project(project: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    """Retorna o patch de campos a gravar ao aplicar um bloco."""
    field = target_field(block.get("target"))
    body = (block.get("body") or "").strip()
    if not body:
        return {}
    current = project.get(field) or ""
    return {field: append_block_text(str(current), body)}


def seed_specs() -> list[dict[str, str]]:
    return [dict(item) for item in SEED_BLOCKS]
