"""Arco «Gancho bíblico Prosperidade e Fé».

Dez tempos em pt-BR, do gancho «Você sabia…?» ao convite de inscrição.
O espécime de Moisés no monte Nebo é a narração de referência do próprio canal.

A produção visual deste arco (stills semi-realistas, cortes curtos, legenda e
cena final de convite) fica aqui, junto da narração — o estúdio já faz Ken Burns.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Sequence

from app.services.demo_script import MOISES_NEBO_BEATS, MOISES_NEBO_SHORT_BEATS

# Rótulos estáveis na UI e nos marcadores do esboço.
BEATS: tuple[dict[str, str], ...] = (
    {"id": "gancho", "label": "Gancho"},
    {"id": "ancora", "label": "Âncora bíblica"},
    {"id": "cena", "label": "Cena"},
    {"id": "tensao", "label": "Tensão"},
    {"id": "detalhe", "label": "Detalhe impressionante"},
    {"id": "porque", "label": "Por quê?"},
    {"id": "legado", "label": "Legado"},
    {"id": "ensinamento", "label": "Ensinamento"},
    {"id": "aplicacao", "label": "Aplicação"},
    {"id": "fecho", "label": "Fecho e convite"},
)

MID_FORM_HINT = "cerca de 2 a 4 minutos (350 a 450 palavras)"
SHORTS_HINT = "cerca de 45 a 70 segundos"

# Frases que a narração falada precisa carregar, com ou sem rótulo de tempo.
VOICE_CUES: tuple[str, ...] = (
    "Você sabia",
    "A história está registrada",
    "momento mais difícil",
    "detalhe impressionante",
    "deixou um legado",
    "nos ensina",
    "Talvez você também",
    "Inscreva-se no canal",
    "ative o sino",
)


def beat_labels() -> list[str]:
    return [beat["label"] for beat in BEATS]


def marked_script(bodies: Sequence[str]) -> str:
    """Um parágrafo por tempo, com o rótulo no início para o esboço editável."""
    if len(bodies) != len(BEATS):
        raise ValueError("O gancho bíblico usa exatamente dez tempos.")
    parts = [
        f"{beat['label']} — {text.strip()}"
        for beat, text in zip(BEATS, bodies)
        if text and text.strip()
    ]
    if len(parts) != len(BEATS):
        raise ValueError("Cada tempo do gancho bíblico precisa de texto.")
    return "\n\n".join(parts)


def marked_reference_script() -> str:
    """Esboço médio preenchido com a narração de referência do canal."""
    return marked_script(MOISES_NEBO_BEATS)


def marked_shorts_script() -> str:
    """Esboço curto da mesma referência."""
    return marked_script(MOISES_NEBO_SHORT_BEATS)


def _clean_topic(text: str) -> str:
    cleaned = re.sub(r"(?i)\bshorts\b", " ", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:|-")
    return cleaned


def generic_narrations(
    brief: str,
    title: str,
    passage: str,
    *,
    shorts: bool = False,
) -> list[str]:
    """Narração nova, na voz do canal, quando o breve não cai num arco já catalogado."""
    topic = _clean_topic(brief) or _clean_topic(title) or "esta história"
    nome = _clean_topic(title) or topic
    livro = passage.strip()
    if livro:
        ancora = (
            f"A história está registrada em {livro} e marca um dos momentos "
            "mais emocionantes da Bíblia."
        )
        fonte = livro
    else:
        ancora = (
            "A história está registrada na Bíblia e marca um dos momentos "
            "mais emocionantes da Escritura."
        )
        fonte = "A Bíblia"

    if shorts:
        return [
            f"Você sabia que «{nome}» guarda um contraste que quase ninguém comenta?",
            ancora,
            f"A cena é esta: {topic}. O relato segue o que a Bíblia mostra, com reverência e sem pressa.",
            "Então, chegou o momento mais difícil. Havia um limite que a força humana não removia.",
            f"E existe um detalhe impressionante em «{nome}», um fato concreto que sustenta a cena.",
            f"Mas por que Deus permitiu esse caminho? {fonte} explica o motivo sem esconder a falha nem a misericórdia.",
            f"Quem viveu «{nome}» deixou um legado que atravessou gerações.",
            "Sua história nos ensina que servir a Deus não é receber tudo exatamente como imaginamos.",
            "Talvez você também esteja diante de algo que esperou durante muito tempo e ainda não conseguiu alcançar.",
            f"E você já tinha percebido esse detalhe sobre «{nome}»? Inscreva-se no canal e ative o sino para receber as notificações de novos vídeos.",
        ]

    return [
        (
            f"Você sabia que «{nome}» guarda um contraste que quase ninguém comenta de primeira? "
            "O que parece um fim fechado ainda deixa a promessa à vista."
        ),
        (
            f"{ancora} Antes de qualquer opinião, o relato aponta a passagem, "
            "para que a emoção não se solte da Escritura."
        ),
        (
            f"A cena começa assim: {topic}. "
            "Passo a passo, a narrativa acompanha quem viveu aquele dia, em terceira pessoa, "
            "com reverência e sem pressa. O lugar aparece, depois o gesto, depois a palavra de Deus, "
            f"na ordem em que a Bíblia conta. Quem ouve consegue ver o caminho de «{nome}» "
            "antes de saber como ele termina."
        ),
        (
            "Então, chegou o momento mais difícil. "
            "Havia um obstáculo que a força humana não removia, e a personagem precisou permanecer diante dele. "
            "Deus havia determinado um limite: a promessa continuava de pé, mas o passo seguinte "
            f"não era o que se imaginava. Em «{nome}», esse nó é o coração do episódio."
        ),
        (
            "E existe um detalhe impressionante. "
            "No meio da tensão, a Bíblia guarda um fato concreto — um número, um gesto ou uma frase "
            f"que não envelhece. Quem relê «{nome}» descobre que esse detalhe sustenta a cena "
            "e mostra que Deus não abandona quem o serviu até ali."
        ),
        (
            f"Mas por que Deus permitiu esse caminho em «{nome}»? "
            f"{fonte} explica o motivo com clareza, sem esconder a falha humana nem apagar a misericórdia. "
            "A consequência fica dita, e outra pessoa pode ser chamada a continuar a missão. "
            "A pergunta não acusa o Senhor: ela ajuda a entender o episódio."
        ),
        (
            "Mas a história não termina simplesmente no obstáculo. "
            f"{fonte} ainda guarda a memória do que ficou. "
            f"Quem viveu «{nome}» deixou um legado que atravessou gerações: uma obediência, "
            "uma palavra ou um caminho que outros puderam seguir. "
            "O nome permanece porque Deus usou aquela vida para além do desfecho visível."
        ),
        (
            "Sua história nos ensina que servir a Deus não significa que teremos todas as coisas "
            "exatamente como imaginamos. "
            f"Em «{nome}», a missão não foi esquecida mesmo quando o desejo pessoal ficou incompleto. "
            "A fidelidade vale mais do que o mapa que desenhamos para nós mesmos."
        ),
        (
            "Talvez você também esteja diante de algo que esperou durante muito tempo "
            "e ainda não conseguiu alcançar. "
            f"Lembre-se de «{nome}». Deus continua sendo Deus mesmo quando não entendemos todos os seus caminhos."
        ),
        (
            "Confie no Senhor, permaneça fiel e continue caminhando, porque a nossa história "
            "não termina simplesmente onde os nossos olhos conseguem enxergar. "
            f"E você já tinha percebido esse detalhe sobre «{nome}»? "
            "Inscreva-se no canal e ative o sino para receber as notificações de novos vídeos."
        ),
    ]


# --- Produção visual do mesmo vídeo de referência (sem renderer novo) ---

# 390 palavras em ~184 s no espécime do canal.
REFERENCE_WORDS_PER_SEC = 390 / 184
CUT_MIN_SEC = 3.0
CUT_MAX_SEC = 6.0
VISUAL_STYLE = "semi3d"
YOUTUBE_CTA = (
    "Inscreva-se no canal e ative o sino para receber as notificações de novos vídeos."
)
# O queimador de legendas ainda usa SRT em branco. O verde é a cor pedida
# para a palavra em destaque; fica anotado no estilo de legenda da marca.
CAPTION_STYLE = (
    "Legendas queimadas no quadro, no ritmo da fala (karaokê). "
    "Texto branco na base; a palavra em destaque deve aparecer em verde brilhante. "
    "O estúdio grava o SRT e queima a legenda em branco: o verde é a intenção "
    "de cor da palavra-chave neste arco."
)
_LOOK = (
    "Still premium em 3D semi-realista, quadro parado com espaço para um lento "
    "movimento de câmera. "
)

_CTA_SHOT: dict[str, str] = {
    "title": "Convite para se inscrever",
    "camera": "medium",
    "light": "natural",
    "atmosphere": "garden",
    "cast": "",
    "art_note": (
        _LOOK
        + "Cena de convite, separada das cenas bíblicas: pessoa de hoje, roupa "
        "contemporânea simples, interior ou varanda atual, olhando para a câmera "
        "e fazendo um gesto de inscrição, como quem pede para ativar o sino. "
        "Sem manto, sem deserto, sem monte, sem texto e sem logo."
    ),
}

_NEBO_BOARD: dict[str, dict[str, str]] = {
    "gancho": {
        "title": "A terra prometida à vista",
        "camera": "wide",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: plano aberto do monte Nebo, Moisés de costas, "
            "paisagem da terra prometida ao longe. Sem texto na imagem."
        ),
    },
    "ancora": {
        "title": "O rolo da Escritura",
        "camera": "close",
        "light": "firelight",
        "atmosphere": "camp",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: close de um rolo de pergaminho aberto, como quem "
            "cita a Escritura. Letras antigas só sugeridas, sem frase moderna legível."
        ),
    },
    "cena": {
        "title": "Nebo diante de Jericó",
        "camera": "wide",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: paisagem do vale, Jericó ao longe e o Jordão, "
            "Moisés no cume vendo Canaã. Sem texto na imagem."
        ),
    },
    "tensao": {
        "title": "O Jordão que não se atravessa",
        "camera": "medium",
        "light": "dramatic",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: Moisés parado diante do limite, o rio no vale, "
            "sem atravessar. Não mostrar morte nem corpo."
        ),
    },
    "detalhe": {
        "title": "Os olhos aos 120 anos",
        "camera": "close",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: close dos olhos de Moisés, claros, que nunca se "
            "escureceram, vigor no olhar de quem tem 120 anos. Sem número escrito."
        ),
    },
    "porque": {
        "title": "Meribá e o líder mais jovem",
        "camera": "medium",
        "light": "rembrandt",
        "atmosphere": "desert",
        "cast": "Moisés, Josué",
        "art_note": (
            _LOOK
            + "Storyboard literal: rocha e água de Meribá; Josué mais jovem, em pé, "
            "distinto do ancião, pronto para liderar. Sem violência."
        ),
    },
    "legado": {
        "title": "Egito, Sinai e o deserto",
        "camera": "wide",
        "light": "natural",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: o legado em quadro amplo — saída pelo deserto, "
            "o monte Sinai ao fundo e o povo em marcha. A sepultura não aparece."
        ),
    },
    "ensinamento": {
        "title": "A promessa contemplada",
        "camera": "medium",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "Moisés",
        "art_note": (
            _LOOK
            + "Storyboard literal: Moisés contempla a terra sem entrar, expressão "
            "de missão cumprida. Sem texto na imagem."
        ),
    },
    "aplicacao": {
        "title": "Quem ainda espera",
        "camera": "close",
        "light": "golden",
        "atmosphere": "camp",
        "cast": "",
        "art_note": (
            _LOOK
            + "Storyboard literal: close de um rosto em espera serena, olhando o "
            "horizonte. Ainda sem o convite moderno e sem texto."
        ),
    },
    "fecho": dict(_CTA_SHOT),
}

_GENERIC_BOARD: dict[str, dict[str, str]] = {
    "gancho": {
        "title": "O contraste",
        "camera": "wide",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal do gancho: o lugar da história em plano aberto, antes do desfecho. Sem texto na imagem.",
    },
    "ancora": {
        "title": "O rolo da Escritura",
        "camera": "close",
        "light": "firelight",
        "atmosphere": "camp",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal: close de um rolo de pergaminho aberto, citando a passagem. Letras antigas só sugeridas, sem frase moderna.",
    },
    "cena": {
        "title": "A cena narrada",
        "camera": "wide",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal da ação em ordem cronológica, no lugar que a frase descreve. Sem texto na imagem.",
    },
    "tensao": {
        "title": "O momento mais difícil",
        "camera": "medium",
        "light": "dramatic",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal do obstáculo: o limite visível no corpo e no cenário. Sem violência gráfica.",
    },
    "detalhe": {
        "title": "O detalhe que prende",
        "camera": "close",
        "light": "golden",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal do fato concreto da frase, em close. Sem letras na imagem.",
    },
    "porque": {
        "title": "A explicação",
        "camera": "medium",
        "light": "rembrandt",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal do motivo bíblico, sóbrio, sem tribunal caricato.",
    },
    "legado": {
        "title": "O legado",
        "camera": "wide",
        "light": "natural",
        "atmosphere": "desert",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal do que a personagem deixou: caminho, povo pequeno, horizonte.",
    },
    "ensinamento": {
        "title": "O ensinamento",
        "camera": "medium",
        "light": "golden",
        "atmosphere": "camp",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal da moral: um rosto e um gesto de fidelidade. Sem cartaz.",
    },
    "aplicacao": {
        "title": "Quem ainda espera",
        "camera": "close",
        "light": "golden",
        "atmosphere": "camp",
        "cast": "",
        "art_note": _LOOK + "Storyboard literal: close de quem espera, olhando o horizonte. Sem o convite moderno e sem texto.",
    },
    "fecho": dict(_CTA_SHOT),
}


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = raw.lower()
    raw = re.sub(r"[^a-z0-9]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _beat_id_for_label(label: str) -> str:
    for beat in BEATS:
        if beat["label"] == label:
            return beat["id"]
    return ""


def strip_beat_label(paragraph: str) -> tuple[str, str]:
    text = (paragraph or "").strip()
    for beat in BEATS:
        prefix = f"{beat['label']} — "
        if text.startswith(prefix):
            return text[len(prefix):].strip(), beat["id"]
    return text, ""


def is_gancho_outline(script: str) -> bool:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", script or "") if part.strip()]
    hits = 0
    for paragraph in paragraphs:
        _, beat_id = strip_beat_label(paragraph)
        if beat_id:
            hits += 1
    return hits >= 6


def split_cuts(text: str) -> list[str]:
    """Quebra a narração em falas de cerca de 3 a 6 segundos."""
    words = [word for word in (text or "").split() if word]
    if not words:
        return []
    min_w = max(1, int(CUT_MIN_SEC * REFERENCE_WORDS_PER_SEC + 0.999))
    max_w = max(min_w, int(CUT_MAX_SEC * REFERENCE_WORDS_PER_SEC))
    if len(words) <= max_w:
        return [" ".join(words)]
    cuts: list[str] = []
    index = 0
    total = len(words)
    while index < total:
        remaining = total - index
        if remaining <= max_w:
            if remaining < min_w and cuts:
                prev = cuts[-1].split()
                need = min_w - remaining
                if len(prev) - need >= min_w:
                    cuts[-1] = " ".join(prev[:-need])
                    cuts.append(" ".join(prev[-need:] + words[index:]))
                else:
                    cuts.append(" ".join(words[index:]))
            else:
                cuts.append(" ".join(words[index:]))
            break
        window = words[index : index + max_w]
        break_at = max_w
        for size in range(max_w, min_w - 1, -1):
            if window[size - 1][-1:] in ".!?":
                break_at = size
                break
        cuts.append(" ".join(words[index : index + break_at]))
        index += break_at
    return [cut for cut in cuts if cut.strip()]


def duration_for(text: str) -> float:
    words = max(1, len((text or "").split()))
    seconds = words * (1 / REFERENCE_WORDS_PER_SEC)
    return round(min(CUT_MAX_SEC, max(CUT_MIN_SEC, seconds)), 3)


def _keyword_board(text: str) -> dict[str, str] | None:
    folded = _fold(text)
    if "inscreva" in folded or "ative o sino" in folded or "ativar o sino" in folded:
        return dict(_CTA_SHOT)
    if "olhos" in folded or "escurec" in folded:
        return {
            "title": "Close dos olhos",
            "camera": "close",
            "light": "golden",
            "atmosphere": "desert",
            "cast": "",
            "art_note": (
                _LOOK
                + "Storyboard literal: close dos olhos, claros, que nunca se escureceram. "
                "Sem número escrito e sem texto."
            ),
        }
    if "josue" in folded:
        return {
            "title": "O líder mais jovem",
            "camera": "medium",
            "light": "golden",
            "atmosphere": "desert",
            "cast": "Josué",
            "art_note": (
                _LOOK
                + "Storyboard literal: Josué mais jovem que o ancião, em pé, assumindo "
                "a liderança. Sem violência e sem texto."
            ),
        }
    if any(token in folded for token in ("registrada", "capitulo", "escritura", "pergaminho", "rolo")):
        return {
            "title": "O rolo da Escritura",
            "camera": "close",
            "light": "firelight",
            "atmosphere": "camp",
            "cast": "",
            "art_note": (
                _LOOK
                + "Storyboard literal: close de um rolo de pergaminho aberto ao citar "
                "a passagem. Letras antigas só sugeridas, sem frase moderna."
            ),
        }
    if any(token in folded for token in ("terra prometida", "canaa", "nebo", "jerico", "jordao")):
        return {
            "title": "A paisagem prometida",
            "camera": "wide",
            "light": "golden",
            "atmosphere": "desert",
            "cast": "",
            "art_note": (
                _LOOK
                + "Storyboard literal: paisagem ampla da terra prometida, vale e horizonte. "
                "Sem texto na imagem."
            ),
        }
    return None


def storyboard_for(beat_id: str, text: str, *, nebo: bool) -> dict[str, str]:
    table = _NEBO_BOARD if nebo else _GENERIC_BOARD
    base = dict(table.get(beat_id) or table["cena"])
    override = _keyword_board(text)
    if override:
        cast = base.get("cast") or ""
        base.update(override)
        if cast and not base.get("cast"):
            base["cast"] = cast
    if beat_id == "fecho":
        base.update(_CTA_SHOT)
    snippet = " ".join((text or "").split())
    if len(snippet) > 180:
        snippet = snippet[:177].rstrip() + "…"
    note = base.get("art_note") or ""
    if snippet and snippet not in note:
        note = f"{note} Trecho: {snippet}"
    base["art_note"] = note.strip()
    return base


def expand_storyboard_cuts(scenes: Sequence[dict[str, Any]], *, nebo: bool) -> list[dict[str, Any]]:
    """Parte cada tempo em cortes de 3 a 6 s, com storyboard literal do trecho."""
    expanded: list[dict[str, Any]] = []
    for scene in scenes:
        beat_id = _beat_id_for_label(str(scene.get("beat") or "")) or "cena"
        parts = split_cuts(str(scene.get("narration") or ""))
        if not parts:
            continue
        for part_index, part in enumerate(parts):
            board = storyboard_for(beat_id, part, nebo=nebo)
            title = board["title"]
            if len(parts) > 1:
                title = f"{title} {part_index + 1}"
            item = dict(scene)
            item.update(
                {
                    "title": title,
                    "narration": part,
                    "camera": board["camera"],
                    "light": board["light"],
                    "atmosphere": board["atmosphere"],
                    "cast": board.get("cast") or "",
                    "art_note": board["art_note"],
                    "duration_sec": duration_for(part),
                    "reference": scene.get("reference") or "",
                }
            )
            expanded.append(item)
    if expanded:
        last = expanded[-1]
        cta = storyboard_for("fecho", str(last.get("narration") or ""), nebo=nebo)
        last["title"] = cta["title"]
        last["camera"] = cta["camera"]
        last["light"] = cta["light"]
        last["atmosphere"] = cta["atmosphere"]
        last["cast"] = cta.get("cast") or ""
        last["art_note"] = cta["art_note"]
        last["beat"] = "Fecho e convite"
    return expanded


def outline_to_scenes(script: str) -> list[dict[str, Any]]:
    """Cenas faláveis a partir do esboço com rótulos, já no ritmo de 3 a 6 s."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", script or "") if part.strip()]
    nebo = "nebo" in _fold(script)
    raw: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        body, beat_id = strip_beat_label(paragraph)
        label = next((beat["label"] for beat in BEATS if beat["id"] == beat_id), "Cena")
        raw.append(
            {
                "title": label,
                "beat": label if beat_id else "Cena",
                "narration": body,
                "reference": "Deuteronômio 34" if nebo else "",
                "cast": "",
                "camera": "wide",
                "light": "golden",
                "atmosphere": "desert",
                "art_note": "",
            }
        )
    paced = expand_storyboard_cuts(raw, nebo=nebo)
    scenes: list[dict[str, Any]] = []
    for index, item in enumerate(paced):
        scenes.append(
            {
                "index": index,
                "title": item["title"],
                "text": item["narration"],
                "cast": item.get("cast") or "",
                "image_path": None,
                "duration_sec": item.get("duration_sec"),
                "image_source": None,
                "image_prompt": None,
                "art_note": item.get("art_note") or "",
                "art_light": item.get("light") or "",
                "art_camera": item.get("camera") or "",
                "art_atmosphere": item.get("atmosphere") or "",
                "reference": item.get("reference") or "",
            }
        )
    return scenes


def project_production_fields() -> dict[str, Any]:
    """Sugestão de look deste arco: semi3d, legenda queimada e nota de karaokê."""
    return {
        "visual_style": VISUAL_STYLE,
        "burn_captions": 1,
        "brand_caption_style": CAPTION_STYLE,
    }


def template_uses_production(template_id: str) -> bool:
    return str(template_id or "").startswith("gancho_biblico")
