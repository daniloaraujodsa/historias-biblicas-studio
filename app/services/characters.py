"""Personagens: bible visual, matching em cenas, seed demo."""
from __future__ import annotations

from typing import Any

# Seeds pt-BR para Demo Davi e Golias
DEMO_CHARACTERS: list[dict[str, str]] = [
    {
        "name": "Davi",
        "role": "jovem pastor",
        "visual_bible": (
            "Idade: adolescente / jovem adulto (~15–17 anos). "
            "Rosto: oval, pele bronzeada do sol, olhos castanhos expressivos, "
            "expressão corajosa e serena. "
            "Cabelo: castanho-escuro ondulado até a nuca, sem barba. "
            "Corpo: magro-atlético de pastor, ombros estreitos, mãos calejadas. "
            "Roupas: túnica curta de lã bege/creme, cinto de couro, sandálias simples; "
            "às vezes funda de couro e pedras lisas. "
            "Traços distintivos: sempre o mesmo rosto jovem, sem armadura pesada; "
            "mantém identidade visual consistente em todas as cenas."
        ),
    },
    {
        "name": "Golias",
        "role": "gigante filisteu",
        "visual_bible": (
            "Idade: adulto maduro. "
            "Rosto: largo, mandíbula forte, barba escura espessa, olhar intimidador. "
            "Cabelo: preto/castanho-escuro curto sob o capacete. "
            "Corpo: gigante (~quase 3 m), musculatura massiva, ombros enormes. "
            "Roupas: armadura de bronze completa, capacete com crista, escudo grande, "
            "lança e espada; sandálias de guerreiro. "
            "Traços distintivos: escala muito maior que humanos ao redor; "
            "mesmo rosto e armadura em todas as cenas."
        ),
    },
    {
        "name": "Saul",
        "role": "rei de Israel",
        "visual_bible": (
            "Idade: homem maduro (~40–50 anos). "
            "Rosto: anguloso, barba castanha com fios grisalhos, expressão preocupada. "
            "Cabelo: castanho médio com grisalhos, sob capacete ou coroa simples. "
            "Corpo: alto e forte de guerreiro, porém menos imponente que Golias. "
            "Roupas: manto real púrpura/vermelho escuro sobre armadura de bronze, "
            "cinturão e capa. "
            "Traços distintivos: presença régia; mesmo rosto/manto em todas as cenas."
        ),
    },
]


def match_characters_in_scene(
    characters: list[dict[str, Any]],
    scene_title: str,
    scene_text: str,
    cast: str = "",
) -> list[dict[str, Any]]:
    """Detecta personagens pelo elenco da cena ou pelo nome no texto.

    `cast` é uma lista separada por vírgula (ex.: "Davi, Saul").
    Se ninguém bater, devolve todos (consistência do elenco).
    """
    if not characters:
        return []
    if cast.strip():
        wanted = {n.strip().lower() for n in cast.split(",") if n.strip()}
        matched = [
            ch
            for ch in characters
            if (ch.get("name") or "").strip().lower() in wanted
        ]
        if matched:
            return matched
    hay = f"{scene_title or ''}\n{scene_text or ''}".lower()
    matched = []
    for ch in characters:
        name = (ch.get("name") or "").strip()
        if name and name.lower() in hay:
            matched.append(ch)
    return matched if matched else list(characters)


def build_consistency_block(characters: list[dict[str, Any]]) -> str:
    """Bloco forte de consistência visual (EN, para o modelo de imagem)."""
    if not characters:
        return ""
    lines = [
        "CHARACTER CONSISTENCY (CRITICAL — keep identical appearance across scenes):",
    ]
    names = []
    for ch in characters:
        name = (ch.get("name") or "Character").strip()
        role = (ch.get("role") or "").strip()
        bible = (ch.get("visual_bible") or "").strip()
        names.append(name)
        header = f"- {name}"
        if role:
            header += f" ({role})"
        header += ":"
        lines.append(header)
        if bible:
            # visual_bible is pt-BR; models handle mixed language well
            lines.append(f"  Visual bible: {bible}")
        lines.append(
            f"  MUST depict the SAME face, hair, clothes, body build and distinctive "
            f"traits for {name} every time. Do not reinvent the character."
        )
    who = ", ".join(names)
    lines.append(
        f"Characters present in this scene: {who}. "
        "Do not change ethnicity, age bracket, costume colors, or facial features."
    )
    return " ".join(lines) if len("\n".join(lines)) > 3500 else "\n".join(lines)


def reference_image_paths(character: dict[str, Any]) -> list[str]:
    """Lista caminhos de imagens de referência do personagem."""
    refs = character.get("reference_images") or []
    if isinstance(refs, str):
        refs = [refs] if refs else []
    paths: list[str] = []
    for r in refs:
        if isinstance(r, str) and r.strip():
            paths.append(r.strip())
        elif isinstance(r, dict) and r.get("path"):
            paths.append(str(r["path"]))
    # legado: um único path
    single = character.get("reference_image_path")
    if single and single not in paths:
        paths.append(str(single))
    return paths


def collect_reference_paths(characters: list[dict[str, Any]], limit: int = 3) -> list[str]:
    """Até `limit` imagens de referência (xAI multi-image ≈ 3)."""
    out: list[str] = []
    for ch in characters:
        for p in reference_image_paths(ch):
            if p not in out:
                out.append(p)
            if len(out) >= limit:
                return out
    return out
