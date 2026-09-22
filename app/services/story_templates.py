"""Arcos reutilizáveis de história bíblica — esboços em pt-BR, editáveis."""
from __future__ import annotations

from typing import Any

# Cada roteiro usa parágrafos separados para a segmentação em cenas.
_TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "id": "queda_graca",
        "label": "Queda, graça e esperança",
        "summary": "Como o encontro no templo ou a restauração de Pedro: falha pública, graça e um caminho novo.",
        "script": """No pátio do templo, a manhã já está quente quando a multidão empurra uma mulher até o centro. Há pedras nas mãos e um julgamento pronto na boca de todos. Ela não levanta os olhos.

Os mestres da Lei cercam Jesus. Querem uma sentença que o encurrale: Moisés mandou apedrejar. Se ele perdoar, desobedece. Se condenar, deixa de ser o que dizem que é.

Jesus se inclina e escreve no chão de terra. O silêncio cresce. Depois ele se ergue e diz que atire a primeira pedra quem não tiver pecado. Os mais velhos soltam as pedras primeiro. Um a um, os acusadores vão embora.

Quando o pátio esvazia, ela continua ali. Jesus pergunta onde estão os que a acusavam. Ninguém ficou para condenar. Ele também não condena. Manda que ela vá e não volte ao mesmo caminho.

A história não termina na vergonha. A graça abre uma porta onde só havia sentença. Quem ouve é chamado a largar a pedra, reconhecer a própria queda e caminhar de novo com esperança.""",
    },
    {
        "id": "confronto_fe",
        "label": "Confronto, fé e vitória",
        "summary": "Como Davi diante do gigante: o medo do povo, a recusa da armadura alheia e a vitória que começa na fé.",
        "script": """No vale de Elá, o exército de Israel está parado. Do outro lado, um guerreiro gigante repete o desafio toda manhã. Ninguém aceita descer. O medo virou rotina.

Um jovem pastor chega com pão para os irmãos e ouve o insulto. Não é só uma ameaça de guerra: é um desprezo contra o nome do Deus de Israel. Davi pergunta o que será dado a quem enfrentar o filisteu.

Saul oferece a própria armadura. Davi experimenta e recusa. O bronze não é a sua medida. Ele pega o cajado, escolhe cinco pedras lisas no riacho e desce ao vale com a funda que já conhece.

Golias ri quando vê o rapaz. Davi responde que não vem com espada nem lança, mas com o nome do Senhor. A pedra encontra a testa do gigante. O vale, que parecia impossível, muda de dono num só instante.

A vitória não começa no golpe. Começa quando alguém pequeno se recusa a medir o desafio só pelo tamanho do inimigo. A fé atravessa o medo e o povo volta a respirar.""",
    },
    {
        "id": "chamado_obediencia",
        "label": "Chamado, obediência e libertação",
        "summary": "Como Moisés: um chamado no deserto, a obediência antes do milagre e a saída da escravidão.",
        "script": """No deserto de Midiã, Moisés apascenta o rebanho quando um arbusto queima sem se consumir. Ele se aproxima. Uma voz chama o seu nome e pede que tire as sandálias: aquele chão é santo.

Deus vê a opressão do povo no Egito e chama Moisés para tirar Israel de lá. O pastor recua. Diz que não sabe falar, que ninguém vai ouvir, que já fugiu daquele palácio. O chamado parece maior do que a sua história.

A resposta não é um discurso brilhante. É uma ordem simples e uma promessa: eu estarei com você. O cajado na mão de Moisés se torna sinal. A obediência começa antes da libertação, no passo de voltar para o lugar do qual ele tinha medo.

Diante de Faraó, a recusa se repete. Pragas, noites e o mar ainda estão pela frente. Moisés não controla o coração do rei. Ele apenas volta ao povo e faz o que foi dito, mesmo quando o caminho parece fechar.

Na margem do mar, com o exército atrás e a água na frente, a libertação chega como passagem no impossível. O chamado, a obediência e a saída formam um só arco: Deus tira um povo da escravidão e Moisés aprende a andar na frente.""",
    },
    {
        "id": "julgamento_alianca",
        "label": "Julgamento, salvação e aliança",
        "summary": "Como Noé: o aviso, a arca construída a seco, o dilúvio e o arco de uma aliança nova.",
        "script": """No mundo de Noé, a violência virou paisagem. Deus olha para a terra e anuncia um julgamento: as águas vão cobrir o que o coração humano corrompeu. No meio do aviso, há um homem que ainda anda com Deus.

Noé recebe medidas, madeiras e um prazo. A arca não é uma ideia abstrata. É trabalho de anos, porta, compartimentos e um teto que precisa aguentar o dilúvio. Os vizinhos veem um navio onde não há mar.

Ele obedece antes de ver a chuva. Entram a família e os animais, dois a dois, como foi ordenado. A porta se fecha por fora. Então as fontes do abismo e as janelas do céu se abrem, e o mundo conhecido desaparece debaixo d'água.

Quando as águas baixam, a arca repousa. Noé solta a ave, espera, e pisa de novo em terra firme. O primeiro gesto não é reconstruir uma cidade: é um altar. A salvação pede gratidão antes de qualquer plano novo.

No céu fica o arco. Deus estabelece uma aliança com Noé e com toda a vida: as águas não voltarão a destruir a terra desse modo. Julgamento, salvação e aliança fecham a história. O recomeço é um compromisso, não só um sobrevivente.""",
    },
)


def list_templates() -> list[dict[str, str]]:
    return [dict(item) for item in _TEMPLATES]


def get_template(template_id: str) -> dict[str, Any] | None:
    key = (template_id or "").strip()
    for item in _TEMPLATES:
        if item["id"] == key:
            return dict(item)
    return None
