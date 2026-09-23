"""Arco «Gancho bíblico Prosperidade e Fé».

Dez tempos em pt-BR, do gancho «Você sabia…?» ao convite de inscrição.
O espécime de Moisés no monte Nebo é a narração de referência do próprio canal.
"""
from __future__ import annotations

import re
from typing import Sequence

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
