"""Planejamento da equipe do estúdio — três etapas, sem API externa.

O roteirista esboça cenas e referências. O diretor de arte marca luz, câmera,
atmosfera e blocos da biblioteca. O editor de YouTube redige gancho e metadados.
Tudo é determinístico: o mesmo breve gera o mesmo plano.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.services.prompt_library import append_block_text, seed_specs
from app.services.publish import generate_metadata
from app.services.visual import (
    ATMOSPHERES,
    CAMERAS,
    LIGHTS,
    label_for_style,
    normalize_preset,
    normalize_style,
)

AGENT_ORDER = ("roteirista", "diretor_arte", "editor_youtube")

_STEP_LABELS = {
    "roteirista": "Leu o breve e fechou cenas, narração e referências.",
    "diretor_arte": "Marcou luz, câmera, atmosfera e blocos da biblioteca.",
    "editor_youtube": "Redigiu gancho, título, descrição e tags.",
}

_AGENT_META = {
    "roteirista": (
        "Roteirista",
        "Esboça as cenas, a narração e as referências bíblicas.",
    ),
    "diretor_arte": (
        "Diretor de arte",
        "Define luz, câmera, atmosfera e notas visuais por cena.",
    ),
    "editor_youtube": (
        "Editor YouTube",
        "Prepara gancho, título, descrição e tags.",
    ),
}

_SHARED_TAIL = "Sem violência gráfica, sem anacronismo moderno e sem texto na imagem."

_GENERIC_TITLES = {
    "novo",
    "novo projeto",
    "nova historia",
    "nova historia biblica",
}

_BOOKS = (
    "Gênesis",
    "Êxodo",
    "Levítico",
    "Números",
    "Deuteronômio",
    "Josué",
    "Juízes",
    "Rute",
    "Samuel",
    "Reis",
    "Crônicas",
    "Esdras",
    "Neemias",
    "Ester",
    "Jó",
    "Salmos",
    "Provérbios",
    "Eclesiastes",
    "Cantares",
    "Isaías",
    "Jeremias",
    "Lamentações",
    "Ezequiel",
    "Daniel",
    "Oseias",
    "Joel",
    "Amós",
    "Obadias",
    "Jonas",
    "Miquéias",
    "Naum",
    "Habacuque",
    "Sofonias",
    "Ageu",
    "Zacarias",
    "Malaquias",
    "Mateus",
    "Marcos",
    "Lucas",
    "João",
    "Atos",
    "Romanos",
    "Coríntios",
    "Gálatas",
    "Efésios",
    "Filipenses",
    "Colossenses",
    "Tessalonicenses",
    "Timóteo",
    "Tito",
    "Filemom",
    "Hebreus",
    "Tiago",
    "Pedro",
    "Judas",
    "Apocalipse",
)


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = raw.lower()
    raw = re.sub(r"[^a-z0-9]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


_BOOK_DISPLAY = {_fold(name): name for name in _BOOKS}
_BOOK_ALT = "|".join(sorted(_BOOK_DISPLAY, key=len, reverse=True))
_PASSAGE_RE = re.compile(
    rf"(?:(?<=\s)|^)(?:(\d)\s+)?({_BOOK_ALT})\s+(\d+)(?:\s+(\d+))?"
)


def _cena(
    title: str,
    beat: str,
    narration: str,
    reference: str,
    cast: str,
    camera: str,
    light: str,
    atmosphere: str,
    art_note: str,
) -> dict[str, str]:
    return {
        "title": title,
        "beat": beat,
        "narration": narration.strip(),
        "reference": reference,
        "cast": cast,
        "camera": camera,
        "light": light,
        "atmosphere": atmosphere,
        "art_note": art_note.strip(),
    }


# Arcos conhecidos. Chaves são (termo, peso): nome próprio pesa mais que lugar.
_STORIES: tuple[dict[str, Any], ...] = (
    {
        "id": "davi_golias",
        "title": "Davi e Golias",
        "passage": "1 Samuel 17",
        "hook": "No vale de Elá, o medo tinha tamanho de gigante — e a fé cabia numa funda.",
        "light": "golden",
        "atmosphere": "battle",
        "keys": (
            ("golias", 40),
            ("davi e golias", 40),
            ("vale de ela", 28),
            ("1 samuel 17", 40),
        ),
        "scenes": (
            _cena(
                "O vale em silêncio",
                "O desafio",
                "No vale de Elá, Israel e os filisteus se encaram sem avançar. Toda manhã um guerreiro gigante repete o insulto, e ninguém desce. O medo já parece parte da paisagem.",
                "1 Samuel 17:4-11",
                "Saul",
                "wide",
                "natural",
                "battle",
                "Plano aberto do vale, dois acampamentos e poeira baixa. O gigante aparece ao longe, dominante, sem sangue nem luta explícita.",
            ),
            _cena(
                "O pastor que ouve",
                "A chegada",
                "Davi chega com pão para os irmãos e ouve o desafio. Não é só uma ameaça de guerra: é um desprezo ao Deus de Israel. Ele pergunta o que será de quem enfrentar o filisteu.",
                "1 Samuel 17:20-26",
                "Davi",
                "medium",
                "golden",
                "battle",
                "Plano médio de um jovem pastor entre soldados, cesta de pão e olhar firme para o outro lado do vale.",
            ),
            _cena(
                "Cinco pedras",
                "A escolha",
                "Saul oferece a armadura real. Davi experimenta e recusa: aquele bronze não é a sua medida. No riacho, escolhe cinco pedras lisas e segura a funda que já conhece.",
                "1 Samuel 17:38-40",
                "Davi",
                "close",
                "natural",
                "battle",
                "Close nas mãos dentro do riacho, cinco pedras lisas e a funda de couro. Água rasa, sem arma em destaque.",
            ),
            _cena(
                "Em nome do Senhor",
                "O confronto",
                "Golias ri quando vê o rapaz. Davi responde que não vem com espada, mas com o nome do Senhor dos exércitos. A pedra parte, o vale muda de dono, e a fé atravessa o medo antes do golpe.",
                "1 Samuel 17:45-50",
                "Davi, Golias",
                "low",
                "dramatic",
                "battle",
                "Ângulo baixo: o gigante em contraluz e o pastor pequeno, porém firme, com a funda em movimento. Sem violência gráfica.",
            ),
        ),
    },
    {
        "id": "noe_arca",
        "title": "Noé e a arca",
        "passage": "Gênesis 6–9",
        "hook": "A arca foi construída em terra seca, antes de cair a primeira chuva.",
        "light": "dramatic",
        "atmosphere": "storm",
        "keys": (
            ("noe", 40),
            ("diluvio", 36),
            ("genesis 6", 34),
            ("genesis 7", 28),
            ("genesis 8", 24),
            ("genesis 9", 24),
        ),
        "scenes": (
            _cena(
                "O aviso",
                "O anúncio",
                "No mundo de Noé, a violência virou paisagem. Deus anuncia o julgamento e, no meio do aviso, chama um homem que ainda anda com ele. Há medidas, madeira e um prazo.",
                "Gênesis 6:13-22",
                "Noé",
                "medium",
                "dramatic",
                "storm",
                "Noé diante de um céu que escurece, plantas de madeira na mão, expressão sóbria. Sem multidão em pânico.",
            ),
            _cena(
                "Navio em terra seca",
                "A obra",
                "A arca sobe onde não há mar. Porta, compartimentos e um teto que precisa aguentar o dilúvio. Os vizinhos veem um navio no chão seco, e Noé continua a obra.",
                "Gênesis 6:14-16",
                "Noé",
                "wide",
                "natural",
                "desert",
                "Plano aberto de uma arca de madeira em terra seca, ferramentas simples e céu ainda sem chuva.",
            ),
            _cena(
                "A porta fechada",
                "O dilúvio",
                "Entram a família e os animais, como foi ordenado. A porta se fecha. Então as fontes do abismo e as janelas do céu se abrem, e o mundo conhecido some debaixo d'água.",
                "Gênesis 7:11-16",
                "Noé",
                "medium",
                "dramatic",
                "storm",
                "Chuva densa sobre a arca, porta já fechada, luz fraca nas frestas. Animais só como silhueta, sem caos.",
            ),
            _cena(
                "O arco",
                "A aliança",
                "Quando as águas baixam, Noé pisa de novo em terra firme. O primeiro gesto é um altar. No céu fica o arco: uma aliança de que a vida pode recomeçar.",
                "Gênesis 8:20; 9:12-17",
                "Noé",
                "wide",
                "golden",
                "garden",
                "Altar simples, família pequena ao fundo e um arco suave no céu depois da chuva. Clima de gratidão, não de espetáculo.",
            ),
        ),
    },
    {
        "id": "moises_mar",
        "title": "Moisés e o mar",
        "passage": "Êxodo 14",
        "hook": "Com o mar na frente e o exército atrás, a ordem foi seguir adiante.",
        "light": "dramatic",
        "atmosphere": "sea",
        "keys": (
            ("mar vermelho", 40),
            ("exodo 14", 40),
            ("moises e o mar", 36),
            ("travessia do mar", 32),
        ),
        "scenes": (
            _cena(
                "Sem saída",
                "O impasse",
                "O povo chega à beira do mar com o exército do Egito ao longe. Há água na frente e medo atrás. Moisés ouve o clamor e ainda não há caminho.",
                "Êxodo 14:9-12",
                "Moisés",
                "wide",
                "dramatic",
                "sea",
                "Multidão de costas para um mar escuro, poeira do exército no horizonte. Figuras pequenas, céu pesado.",
            ),
            _cena(
                "O cajado erguido",
                "A ordem",
                "A ordem não é voltar. Moisés estende a mão sobre as águas. A obediência começa antes de o chão aparecer, com o cajado que já veio do deserto.",
                "Êxodo 14:15-16",
                "Moisés",
                "low",
                "golden",
                "sea",
                "Ângulo baixo de Moisés com o cajado sobre o mar, manto ao vento, luz rasante. Sem texto na imagem.",
            ),
            _cena(
                "Muro de água",
                "A passagem",
                "O vento sopra a noite inteira. As águas se abrem e o povo pisa em chão seco no meio do mar. Cada passo é pequeno; o caminho é impossível e, ainda assim, está ali.",
                "Êxodo 14:21-22",
                "Moisés",
                "wide",
                "dramatic",
                "sea",
                "Corredor entre duas paredes de água, famílias caminhando com trouxas. Clima solene, sem afogamento visível.",
            ),
            _cena(
                "A outra margem",
                "O canto",
                "De manhã, Israel está do outro lado. O mar volta ao lugar. O cântico não celebra a força do povo: celebra quem abriu caminho quando não havia saída.",
                "Êxodo 14:30-31; 15:1-2",
                "Moisés",
                "medium",
                "golden",
                "sea",
                "Grupo na margem ao amanhecer, rostos cansados e aliviados, mar calmo atrás. Luz dourada, sem troféu de guerra.",
            ),
        ),
    },
    {
        "id": "rute",
        "title": "Rute no campo",
        "passage": "Rute 2",
        "hook": "Uma estrangeira pediu para respigar, e a bondade abriu lugar à mesa.",
        "light": "golden",
        "atmosphere": "garden",
        "keys": (
            ("rute", 40),
            ("boaz", 34),
            ("respigar", 30),
            ("rute 2", 28),
        ),
        "scenes": (
            _cena(
                "O campo de cevada",
                "A chegada",
                "Rute, moabita, chega aos campos de Belém na época da ceifa. Ela pede licença para respigar atrás dos ceifeiros. É estrangeira, viúva, e o trabalho é o que cabe nas mãos.",
                "Rute 2:2-3",
                "Rute",
                "wide",
                "golden",
                "garden",
                "Campo de cevada ao sol baixo, uma mulher com véu simples respigando espigas caídas. Sem glamour.",
            ),
            _cena(
                "Quem é esta?",
                "O encontro",
                "Boaz vê a jovem entre os trabalhadores e pergunta de quem ela é. O capataz conta a história: veio com Noemi e pede para recolher o que sobra, do amanhecer até agora.",
                "Rute 2:5-7",
                "Rute, Boaz",
                "over_shoulder",
                "golden",
                "garden",
                "Por cima do ombro de Boaz, Rute ao longe entre os feixes. Poeira dourada e ceifeiros ao fundo.",
            ),
            _cena(
                "À sombra dos feixes",
                "A mesa",
                "Boaz manda que ninguém a maltrate e que deixem espigas de propósito. Na hora da refeição, oferece pão e vinagre. Rute come com os ceifeiros e ainda separa o que sobra.",
                "Rute 2:8-14",
                "Rute, Boaz",
                "medium",
                "natural",
                "garden",
                "Refeição simples à sombra: pão, cântaro e espigas. Rosto de Rute em dignidade, não em pose.",
            ),
            _cena(
                "O colo de Noemi",
                "A esperança",
                "De volta à cidade, Rute mostra a Noemi o que recolheu. A sogra reconhece a bondade de Boaz, parente que pode proteger. O dia de trabalho vira uma porta de cuidado.",
                "Rute 2:17-20",
                "Rute, Noemi",
                "close",
                "firelight",
                "camp",
                "Close de duas mulheres numa casa simples, grãos no manto, luz de lamparina. Clima de alívio.",
            ),
        ),
    },
    {
        "id": "daniel_leoes",
        "title": "Daniel na cova",
        "passage": "Daniel 6",
        "hook": "A janela continuou aberta para Jerusalém, mesmo com o decreto do rei.",
        "light": "rembrandt",
        "atmosphere": "court",
        "keys": (
            ("cova dos leoes", 42),
            ("daniel 6", 40),
            ("daniel", 26),
        ),
        "scenes": (
            _cena(
                "O decreto",
                "A armadilha",
                "Os administradores convencem o rei a assinar um decreto: durante trinta dias, só a ele se pode orar. Daniel ouve a lei e não muda o hábito. A armadilha já está armada.",
                "Daniel 6:6-10",
                "Daniel",
                "medium",
                "rembrandt",
                "court",
                "Sala do trono com o rei sentado e o decreto nas mãos. Luz lateral, cortesãos em silhueta, sem caricatura.",
            ),
            _cena(
                "A janela aberta",
                "A oração",
                "Daniel sobe ao quarto, abre as janelas para Jerusalém e se ajoelha, como sempre, três vezes ao dia. Ele sabe o preço. A oração continua mesmo assim.",
                "Daniel 6:10",
                "Daniel",
                "close",
                "golden",
                "temple",
                "Close de Daniel ajoelhado diante de uma janela aberta, cidade ao longe, luz de fim de tarde no rosto.",
            ),
            _cena(
                "A cova",
                "A noite",
                "O rei, preso à própria lei, manda lançar Daniel na cova dos leões. Passa a noite em jejum. Na pedra que fecha a cova não há garantia humana — só a fidelidade de Deus.",
                "Daniel 6:16-18",
                "Daniel",
                "low",
                "moonlight",
                "court",
                "Boca de uma cova em pedra, luar, leões apenas como vultos quietos. Daniel sentado, ileso, sem ataque.",
            ),
            _cena(
                "De manhã",
                "O livramento",
                "Ao alvorecer o rei corre até a cova e chama pelo nome. Daniel responde: Deus enviou o seu anjo e fechou a boca dos leões. A fidelidade quieta atravessou a noite.",
                "Daniel 6:19-22",
                "Daniel",
                "medium",
                "golden",
                "court",
                "Manhã na boca da cova, o rei inclinado e Daniel de pé, ileso. Luz nova, alívio no rosto, sem feras em ataque.",
            ),
        ),
    },
    {
        "id": "jonas",
        "title": "Jonas",
        "passage": "Jonas 1–2",
        "hook": "A fuga pelo mar terminou numa oração no fundo das águas.",
        "light": "dramatic",
        "atmosphere": "sea",
        "keys": (
            ("jonas", 40),
            ("grande peixe", 30),
            ("jonas 1", 24),
            ("jonas 2", 24),
        ),
        "scenes": (
            _cena(
                "O navio para Társis",
                "A fuga",
                "Jonas recebe o chamado para Nínive e desce ao porto na direção contrária. Paga a passagem e desce ao porão. A fuga parece um plano até o vento mudar.",
                "Jonas 1:1-5",
                "Jonas",
                "medium",
                "natural",
                "sea",
                "Porto antigo e um homem embarcando num navio de madeira, olhar desviado. Céu ainda claro.",
            ),
            _cena(
                "A sorte lançada",
                "A tempestade",
                "A tempestade quase desfaz o navio. Os marinheiros oram e lançam sortes. A sorte cai sobre Jonas. Ele conta quem é e pede que o lancem ao mar.",
                "Jonas 1:7-15",
                "Jonas",
                "wide",
                "dramatic",
                "storm",
                "Convés inclinado, ondas altas e marinheiros segurando cordas. Jonas no centro, sem afogamento explícito.",
            ),
            _cena(
                "No profundo",
                "A oração",
                "Nas profundezas, Jonas ora. Ele lembra o templo e admite a fuga. A oração não é um discurso bonito: é o fim da fuga, dito de dentro das águas.",
                "Jonas 2:1-7",
                "Jonas",
                "close",
                "moonlight",
                "sea",
                "Close do rosto de Jonas em penumbra azul, água e luz fraca. Clima de oração, não de horror.",
            ),
            _cena(
                "A praia",
                "A segunda chance",
                "O grande peixe o devolve à terra seca. Jonas pisa na areia com a mesma missão de antes. A misericórdia o alcançou na fuga e o coloca de novo no caminho.",
                "Jonas 2:10",
                "Jonas",
                "wide",
                "golden",
                "sea",
                "Praia ao amanhecer, Jonas ajoelhado na areia, horizonte calmo. O peixe só sugerido ao longe, sem gore.",
            ),
        ),
    },
    {
        "id": "belem",
        "title": "O nascimento em Belém",
        "passage": "Lucas 2",
        "hook": "Não havia quarto na hospedaria. Havia uma manjedoura e uma promessa.",
        "light": "firelight",
        "atmosphere": "camp",
        "keys": (
            ("manjedoura", 42),
            ("lucas 2", 36),
            ("nascimento de jesus", 36),
            ("pastores de belem", 32),
            ("belem", 12),
        ),
        "scenes": (
            _cena(
                "O caminho",
                "A viagem",
                "José e Maria sobem para Belém por causa do recenseamento. Maria está para dar à luz. A estrada é longa e a noite chega antes da cidade.",
                "Lucas 2:1-5",
                "José, Maria",
                "wide",
                "moonlight",
                "desert",
                "Casal numa estrada de pedra sob a lua, Maria no jumento, José a pé. Clima simples e digno.",
            ),
            _cena(
                "Sem lugar",
                "A hospedaria",
                "Na cidade não há quarto para eles. O menino nasce num espaço de animais. Maria o envolve em panos e o deita na manjedoura.",
                "Lucas 2:6-7",
                "Maria, José",
                "medium",
                "firelight",
                "camp",
                "Manjedoura de madeira, panos claros e luz de lamparina. Sem brilho de cartão postal nem texto.",
            ),
            _cena(
                "Os pastores",
                "O anúncio",
                "No campo, pastores vigiam o rebanho de noite. O anjo anuncia uma boa notícia para todo o povo: nasceu o Salvador. O medo vira pressa de ir ver.",
                "Lucas 2:8-14",
                "Pastores",
                "wide",
                "moonlight",
                "camp",
                "Pastores e ovelhas num campo noturno, luz suave no céu, rostos de espanto contido. Sem efeitos neon.",
            ),
            _cena(
                "Eles foram ver",
                "A visita",
                "Os pastores acham Maria, José e o menino na manjedoura, como foi dito. Contam o que ouviram. Maria guarda tudo no coração. A noite de Belém cabe numa família pequena.",
                "Lucas 2:15-19",
                "Maria, José, Pastores",
                "close",
                "firelight",
                "camp",
                "Close da manjedoura com pastores ao redor, em reverência. Luz quente, rostos humanos, sem multidão.",
            ),
        ),
    },
    {
        "id": "pedro_aguas",
        "title": "Pedro sobre as águas",
        "passage": "Mateus 14",
        "hook": "Na noite do lago, um pescador saiu do barco antes de saber andar.",
        "light": "moonlight",
        "atmosphere": "sea",
        "keys": (
            ("sobre as aguas", 42),
            ("mateus 14", 36),
            ("pedro saiu do barco", 34),
        ),
        "scenes": (
            _cena(
                "O barco de noite",
                "A travessia",
                "Os discípulos estão no meio do lago, de noite, com o vento contra. Jesus ainda não está no barco. As ondas batem e a margem some.",
                "Mateus 14:22-24",
                "Pedro",
                "wide",
                "moonlight",
                "sea",
                "Barco de pesca pequeno no lago escuro, luar nas ondas, homens segurando o remo.",
            ),
            _cena(
                "Quem vem andando",
                "O susto",
                "De madrugada eles veem Jesus andando sobre o mar e pensam que é um fantasma. Ele fala: tenham coragem, sou eu. O medo ainda está no barco, mas a voz é conhecida.",
                "Mateus 14:25-27",
                "Pedro",
                "medium",
                "moonlight",
                "sea",
                "Figura serena sobre a água ao luar, vista do barco. Clima de assombro, sem terror gráfico.",
            ),
            _cena(
                "Se és tu",
                "O passo",
                "Pedro pede: manda-me ir até ti. Jesus diz: vem. Pedro desce do barco e caminha sobre as águas enquanto olha para quem o chamou.",
                "Mateus 14:28-29",
                "Pedro",
                "low",
                "dramatic",
                "sea",
                "Pedro com um pé fora do barco, água escura, olhar para frente. Ângulo baixo, tensão contida.",
            ),
            _cena(
                "A mão",
                "O socorro",
                "Quando Pedro olha o vento, começa a afundar e grita. Jesus estende a mão e o segura. No barco, o vento cessa. A fé aprende a pedir socorro sem vergonha.",
                "Mateus 14:30-33",
                "Pedro",
                "close",
                "golden",
                "sea",
                "Close de duas mãos se encontrando sobre a água, uma firme e outra cansada. Sem afogamento explícito.",
            ),
        ),
    },
    {
        "id": "elias_carmelo",
        "title": "Elias no Carmelo",
        "passage": "1 Reis 18",
        "hook": "No Carmelo, o altar foi molhado de propósito — e o fogo desceu mesmo assim.",
        "light": "dramatic",
        "atmosphere": "storm",
        "keys": (
            ("carmelo", 40),
            ("1 reis 18", 40),
            ("elias", 30),
        ),
        "scenes": (
            _cena(
                "O monte",
                "O desafio",
                "Elias chama o povo ao Carmelo. De um lado, os profetas de Baal. Do outro, um profeta e um altar por fazer. A pergunta é simples: quem responde de verdade?",
                "1 Reis 18:20-21",
                "Elias",
                "wide",
                "natural",
                "storm",
                "Monte com dois altares distantes e o povo no meio. Céu carregado, sem ídolo em close grotesco.",
            ),
            _cena(
                "O altar molhado",
                "A preparação",
                "Elias levanta doze pedras, arruma a lenha e manda molhar o holocausto três vezes. A vala enche de água. Ele não facilita o sinal: pede que Deus responda para que o povo saiba.",
                "1 Reis 18:30-35",
                "Elias",
                "medium",
                "firelight",
                "temple",
                "Altar de pedras molhadas, água escorrendo na vala, Elias em pé. Lenha escura, ainda sem chama.",
            ),
            _cena(
                "O fogo desce",
                "A resposta",
                "Elias ora. O fogo do Senhor desce, consome o holocausto, a lenha e a água da vala. O povo se curva. Não é um truque de palco: é resposta a uma oração pública.",
                "1 Reis 18:36-39",
                "Elias",
                "low",
                "dramatic",
                "storm",
                "Chama descendo sobre o altar molhado, povo a distância, Elias de joelhos. Luz forte, sem queimadura humana.",
            ),
            _cena(
                "A nuvem pequena",
                "A chuva",
                "Depois do fogo, Elias sobe para orar pela chuva. O servo olha o mar sete vezes. Na sétima, uma nuvem pequena sobe. O céu que estava fechado volta a chover.",
                "1 Reis 18:41-45",
                "Elias",
                "wide",
                "golden",
                "storm",
                "Horizonte do mar com uma nuvem pequena e Elias em oração no alto do monte. Vento na roupa, chuva chegando.",
            ),
        ),
    },
    {
        "id": "ester",
        "title": "Ester diante do rei",
        "passage": "Ester 4–5",
        "hook": "Ela entrou no pátio do rei sem garantia de voltar, pelo povo que jejuava.",
        "light": "rembrandt",
        "atmosphere": "court",
        "keys": (
            ("ester", 40),
            ("ester 4", 28),
            ("ester 5", 28),
        ),
        "scenes": (
            _cena(
                "O jejum",
                "A decisão",
                "Mardoqueu avisa Ester: o povo está sentenciado. Ela pede jejum de três dias. Entrar diante do rei sem ser chamada pode custar a vida, e ela decide entrar mesmo assim.",
                "Ester 4:15-16",
                "Ester, Mardoqueu",
                "close",
                "rembrandt",
                "court",
                "Close de Ester em traje simples de jejum, luz lateral, expressão resoluta. Sem sensualidade.",
            ),
            _cena(
                "O pátio",
                "O passo",
                "No terceiro dia, Ester veste os trajes reais e fica no pátio interior, à vista do trono. Cada passo é uma escolha pelo povo que jejua do lado de fora.",
                "Ester 5:1",
                "Ester",
                "wide",
                "dramatic",
                "court",
                "Pátio longo de palácio persa, Ester pequena diante da porta do trono. Colunas, luz dura, solidão.",
            ),
            _cena(
                "O cetro",
                "O favor",
                "O rei estende o cetro de ouro. Ester se aproxima e toca a ponta. O favor não apaga o risco: só abre a boca para ela falar.",
                "Ester 5:2",
                "Ester",
                "medium",
                "golden",
                "court",
                "Cetro estendido e a mão de Ester o tocando. Rei ao fundo, ouro sóbrio, sem luxo exagerado.",
            ),
            _cena(
                "O pedido",
                "O banquete",
                "Ester não conta tudo de uma vez. Convida o rei e Hamã para um banquete. A coragem aqui é paciência: a vida do povo será pedida na hora certa, com clareza.",
                "Ester 5:3-8",
                "Ester",
                "over_shoulder",
                "firelight",
                "court",
                "Mesa baixa com pão e taças, Ester falando com calma. Hamã e o rei apenas de perfil, sem caricatura.",
            ),
        ),
    },
    {
        "id": "jose_irmaos",
        "title": "José e os irmãos",
        "passage": "Gênesis 45",
        "hook": "Os irmãos que o venderam ouviram o nome que não esperavam: eu sou José.",
        "light": "golden",
        "atmosphere": "court",
        "keys": (
            ("genesis 45", 42),
            ("eu sou jose", 42),
            ("jose e os irmaos", 36),
        ),
        "scenes": (
            _cena(
                "A sala no Egito",
                "O reconhecimento",
                "Os irmãos estão diante do governador do Egito e ainda não sabem quem ele é. José vê a fome, o medo e Benjamim. A sala é de poder, mas o choro já não cabe no cargo.",
                "Gênesis 45:1-2",
                "José",
                "wide",
                "golden",
                "court",
                "Sala egípcia sóbria, irmãos inclinados e José de pé, prestes a chorar. Sem ostentação vazia.",
            ),
            _cena(
                "Eu sou José",
                "O nome",
                "José manda sair os servos e diz: eu sou José. Os irmãos não conseguem responder. Ele chega mais perto e repete o nome do pai. O segredo de anos cai numa frase.",
                "Gênesis 45:3-4",
                "José",
                "close",
                "rembrandt",
                "court",
                "Close do rosto de José, barba e colar simples de governador, lágrimas contidas. Irmãos desfocados.",
            ),
            _cena(
                "Não foram vocês",
                "O sentido",
                "José pede que não se culpem pelo caminho. Deus o enviou adiante para preservar vida. O mal que fizeram não é apagado, mas não é a última palavra sobre a família.",
                "Gênesis 45:5-8",
                "José",
                "medium",
                "golden",
                "court",
                "José com as mãos abertas diante dos irmãos, luz quente, corpos ainda tensos começando a ceder.",
            ),
            _cena(
                "O abraço",
                "A volta",
                "Ele beija os irmãos e chora. Depois manda buscar o pai. A história que começou com uma cova termina com carroças a caminho de Canaã, para que a família viva.",
                "Gênesis 45:14-15, 27-28",
                "José",
                "medium",
                "golden",
                "desert",
                "Abraço entre irmãos numa sala clara e, ao fundo, a ideia de uma estrada para casa. Sem violência da venda antiga.",
            ),
        ),
    },
    {
        "id": "bom_samaritano",
        "title": "O bom samaritano",
        "passage": "Lucas 10",
        "hook": "Na estrada para Jericó, quem parou foi o que ninguém esperava.",
        "light": "natural",
        "atmosphere": "desert",
        "keys": (
            ("samaritano", 42),
            ("lucas 10", 30),
        ),
        "scenes": (
            _cena(
                "A descida",
                "A estrada",
                "Jesus conta de um homem que descia de Jerusalém para Jericó. No caminho, é assaltado e deixado ferido. A estrada segue vazia, e ele não consegue se levantar.",
                "Lucas 10:30",
                "",
                "wide",
                "natural",
                "desert",
                "Estrada de pedra entre colinas secas, um homem caído à beira, sem feridas gráficas. Luz dura de meio-dia.",
            ),
            _cena(
                "Quem passou",
                "A pressa",
                "Um sacerdote e um levita veem o homem e seguem. A parábola não explica o motivo. Mostra o passo que desvia e o corpo que continua no chão.",
                "Lucas 10:31-32",
                "",
                "high",
                "natural",
                "desert",
                "Ângulo alto: duas figuras passando longe de um corpo na beira da estrada. Distância fria, sem caricatura.",
            ),
            _cena(
                "Quem parou",
                "A misericórdia",
                "Um samaritano, de quem não se esperava cuidado, vê e se compadece. Limpa as feridas, coloca o homem no próprio animal e caminha ao lado.",
                "Lucas 10:33-34",
                "",
                "medium",
                "golden",
                "desert",
                "Homem ajoelhado cuidando de outro, óleo e pano, jumento ao lado. Gesto de cuidado, sangue só sugerido.",
            ),
            _cena(
                "A hospedaria",
                "O custo",
                "Ele leva o ferido a uma hospedaria, paga o estalajadeiro e promete voltar. Jesus pergunta quem foi o próximo. A resposta não é um título: é quem praticou misericórdia.",
                "Lucas 10:34-37",
                "",
                "close",
                "firelight",
                "camp",
                "Porta de hospedaria à noite, moedas na mão e um ferido recolhido lá dentro. Luz de lamparina.",
            ),
        ),
    },
    {
        "id": "criacao",
        "title": "A criação",
        "passage": "Gênesis 1",
        "hook": "No princípio, a luz veio antes de qualquer cidade — e o mundo ganhou ordem.",
        "light": "golden",
        "atmosphere": "garden",
        "keys": (
            ("genesis 1", 42),
            ("no principio", 36),
            ("criacao do mundo", 34),
            ("haja luz", 28),
        ),
        "scenes": (
            _cena(
                "Haja luz",
                "A luz",
                "No princípio, a terra está sem forma e há treva sobre o abismo. Deus diz: haja luz. A luz aparece, e ele separa a luz das trevas. O primeiro dia tem nome.",
                "Gênesis 1:1-5",
                "",
                "wide",
                "golden",
                "sea",
                "Águas escuras e um horizonte que se abre em luz dourada. Sem pessoas, sem texto, sem sol ainda como disco moderno.",
            ),
            _cena(
                "Céu e terra",
                "A ordem",
                "Deus separa as águas, faz aparecer o seco e chama a terra e o mar. A vegetação nasce por espécie. O mundo deixa de ser um vazio e ganha lugar para viver.",
                "Gênesis 1:9-12",
                "",
                "wide",
                "natural",
                "garden",
                "Costa antiga, mar de um lado e verde novo do outro. Luz clara, escala vasta, sem cidade.",
            ),
            _cena(
                "Os luzeiros",
                "O tempo",
                "Sol, lua e estrelas marcam dias e estações. Aves cruzam o céu e os mares se enchem de vida. Tudo é chamado bom, antes de haver pressa humana.",
                "Gênesis 1:14-21",
                "",
                "wide",
                "golden",
                "sea",
                "Céu com aves e um mar calmo ao entardecer. Lua discreta, estrelas suaves, sem diagrama.",
            ),
            _cena(
                "À imagem",
                "O descanso",
                "O ser humano é feito à imagem de Deus e recebe o cuidado da terra. No sétimo dia, Deus descansa. A criação termina não em barulho, mas em um mundo abençoado.",
                "Gênesis 1:26-31; 2:1-3",
                "",
                "medium",
                "golden",
                "garden",
                "Jardim amplo com duas figuras humanas distantes, dignas, sem nudez explícita. Luz de descanso, oliveiras e rio.",
            ),
        ),
    },
    {
        "id": "ovelha_perdida",
        "title": "A ovelha perdida",
        "passage": "Lucas 15",
        "hook": "Noventa e nove ficaram no aprisco. O pastor saiu por causa de uma.",
        "light": "firelight",
        "atmosphere": "camp",
        "keys": (
            ("ovelha perdida", 42),
            ("lucas 15", 36),
        ),
        "scenes": (
            _cena(
                "O aprisco",
                "As noventa e nove",
                "Jesus fala de um pastor que tem cem ovelhas. Noventa e nove estão seguras. Uma falta. A história inteira cabe nessa conta que não fecha.",
                "Lucas 15:3-4",
                "",
                "wide",
                "firelight",
                "camp",
                "Aprisco de pedra ao anoitecer, ovelhas juntas e um vão vazio na cerca. Fogueira baixa.",
            ),
            _cena(
                "A busca",
                "A colina",
                "O pastor deixa as noventa e nove e vai atrás da perdida. A colina está escura. Ele chama, escuta e não volta de mãos vazias só porque o rebanho maior está bem.",
                "Lucas 15:4",
                "",
                "wide",
                "moonlight",
                "desert",
                "Pastor com cajado numa encosta à noite, luar, arbustos secos. Uma ovelha ainda não visível.",
            ),
            _cena(
                "Nos ombros",
                "O encontro",
                "Quando acha a ovelha, ele a põe nos ombros, alegre. O peso é real. A alegria também. O caminho de volta é o mesmo, agora com a que faltava.",
                "Lucas 15:5",
                "",
                "medium",
                "moonlight",
                "desert",
                "Pastor carregando uma ovelha nos ombros, manto simples, noite clara. Ternura, sem doçura artificial.",
            ),
            _cena(
                "A festa",
                "A alegria",
                "Em casa, ele chama os amigos: alegrem-se comigo. Jesus diz que há alegria no céu por um pecador que se arrepende. A festa é por uma só vida recuperada.",
                "Lucas 15:6-7",
                "",
                "close",
                "firelight",
                "camp",
                "Rosto do pastor à luz do fogo, ovelha ao lado, vizinhos chegando. Clima de alegria contida.",
            ),
        ),
    },
    {
        "id": "jerico",
        "title": "Josué e Jericó",
        "passage": "Josué 6",
        "hook": "Sete dias de marcha em silêncio, e as muralhas caíram sem um aríete.",
        "light": "dramatic",
        "atmosphere": "desert",
        "keys": (
            ("jerico", 42),
            ("josue 6", 40),
        ),
        "scenes": (
            _cena(
                "A muralha fechada",
                "A cidade",
                "Jericó está fechada. Ninguém entra nem sai. Josué recebe um modo estranho de avançar: marchar, tocar trombetas e, por seis dias, não gritar.",
                "Josué 6:1-10",
                "Josué",
                "wide",
                "natural",
                "desert",
                "Muralha alta de tijolo e pedra, cidade fechada, o povo pequeno ao redor. Luz de dia seco.",
            ),
            _cena(
                "A marcha calada",
                "A obediência",
                "Os sacerdotes levam a arca e as trombetas. O povo contorna a cidade em silêncio. A obediência, nesses dias, é não antecipar o grito.",
                "Josué 6:8-14",
                "Josué",
                "medium",
                "golden",
                "desert",
                "Procissão sóbria em volta da muralha, arca coberta ao centro, trombetas sem som ainda. Poeira dourada.",
            ),
            _cena(
                "O sétimo dia",
                "As trombetas",
                "No sétimo dia eles dão sete voltas. Na última, as trombetas soam e Josué manda gritar. O silêncio guardado vira um só brado.",
                "Josué 6:15-16",
                "Josué",
                "low",
                "dramatic",
                "battle",
                "Ângulo baixo das trombetas contra o céu e a muralha. Bocas abertas no grito, sem combate corpo a corpo.",
            ),
            _cena(
                "O muro cai",
                "A passagem",
                "A muralha cai. O povo entra, como foi dito. A história não ensina pressa: ensina um povo que andou em silêncio até a hora marcada.",
                "Josué 6:20",
                "Josué",
                "wide",
                "dramatic",
                "desert",
                "Muralha rachada vista de longe, poeira subindo, povo entrando em ordem. Sem massacre visível.",
            ),
        ),
    },
)


def example_briefs() -> list[tuple[str, str]]:
    """Pares (breve, id do arco) para testes."""
    return [
        ("Davi e Golias no vale", "davi_golias"),
        ("a arca de Noé", "noe_arca"),
        ("Moisés no mar Vermelho", "moises_mar"),
        ("Rute no campo de Boaz", "rute"),
        ("Daniel na cova dos leões", "daniel_leoes"),
        ("Jonas e o grande peixe", "jonas"),
        ("o nascimento em Belém", "belem"),
        ("Pedro sobre as águas", "pedro_aguas"),
        ("Elias no Carmelo", "elias_carmelo"),
        ("Ester diante do rei", "ester"),
        ("Gênesis 45, eu sou José", "jose_irmaos"),
        ("o bom samaritano", "bom_samaritano"),
        ("No princípio, Gênesis 1", "criacao"),
        ("a ovelha perdida", "ovelha_perdida"),
        ("as muralhas de Jericó", "jerico"),
    ]


def _contains_key(folded: str, key: str) -> bool:
    needle = _fold(key)
    if not needle or needle not in folded:
        return False
    for match in re.finditer(re.escape(needle), folded):
        start, end = match.start(), match.end()
        before = folded[start - 1] if start else " "
        after = folded[end] if end < len(folded) else " "
        if before.isalnum() or after.isalnum():
            continue
        return True
    return False


def match_story(brief: str) -> dict[str, Any] | None:
    folded = _fold(brief)
    best: dict[str, Any] | None = None
    best_score = 0
    for story in _STORIES:
        score = 0
        for key, weight in story["keys"]:
            if _contains_key(folded, key):
                score += int(weight)
        if score > best_score:
            best = story
            best_score = score
    if best is None or best_score < 12:
        return None
    return best


def extract_passage(brief: str) -> str:
    folded = _fold(brief)
    match = _PASSAGE_RE.search(folded)
    if not match:
        return ""
    number, book, chapter, verse = match.groups()
    label = _BOOK_DISPLAY.get(book, book.title())
    prefix = f"{number} " if number else ""
    base = f"{prefix}{label} {chapter}"
    if verse:
        base += f":{verse}"
    return base


def suggest_title(brief: str) -> str:
    text = re.sub(r"\s+", " ", (brief or "")).strip()
    story = match_story(text)
    if story:
        return str(story["title"])
    line = re.split(r"[.!?…]", text)[0].strip()
    if len(line) > 72:
        line = line[:69].rstrip() + "…"
    return line or "Nova história bíblica"


def _clean_brief(brief: str) -> str:
    text = re.sub(r"\s+", " ", (brief or "").replace("\n", " ")).strip()
    if not text:
        raise ValueError("Escreva um breve com a história, a passagem ou o tema.")
    if len(text) > 800:
        text = text[:799].rstrip() + "…"
    return text


def _preset(kind: str, key: str, fallback: str) -> str:
    found = normalize_preset(key, kind) or normalize_preset(fallback, kind)
    if not found:
        raise ValueError(f"Preset inválido ({kind}): {key}")
    return found


def _label(kind: str, key: str) -> str:
    catalog = {"light": LIGHTS, "camera": CAMERAS, "atmosphere": ATMOSPHERES}[kind]
    return catalog[key]["label"]


def _guess_atmosphere(text: str) -> str:
    folded = _fold(text)
    rules = (
        (("tempestade", "diluvio", "chuva forte"), "storm"),
        (("mar", "barco", "peixe", "aguas", "praia", "onda", "lago"), "sea"),
        (("templo", "altar", "incenso"), "temple"),
        (("batalha", "exercito", "muralha", "trombeta", "gigante"), "battle"),
        (("rei", "trono", "palacio", "cetro"), "court"),
        (("jardim", "eden", "oliveira", "seara", "cevada", "campo"), "garden"),
        (("noite", "tenda", "acampamento"), "camp"),
        (("deserto", "areia", "estrada"), "desert"),
    )
    for words, key in rules:
        if any(_soft_has(folded, word) for word in words):
            return key
    return "desert"


def _soft_has(folded: str, word: str) -> bool:
    """Palavra curta exige fronteira; termo longo pode aparecer no meio da frase."""
    if len(word) <= 4:
        return _contains_key(folded, word)
    return word in folded


def _guess_light(atmosphere: str, text: str) -> str:
    folded = _fold(text)
    if any(word in folded for word in ("noite", "lua", "madrugada")):
        return "moonlight"
    if atmosphere == "storm":
        return "dramatic"
    if atmosphere in ("camp", "court"):
        return "firelight" if atmosphere == "camp" else "rembrandt"
    if atmosphere == "temple":
        return "firelight"
    return "golden"


def _short_brief(brief: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", brief).strip().strip("«»\"'")
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _generic_scenes(brief: str, title: str, passage: str) -> list[dict[str, str]]:
    short = _short_brief(brief)
    passage_bit = f" ({passage})" if passage else ""
    reference = passage or "Conferir a passagem antes de publicar"
    atmosphere = _guess_atmosphere(f"{brief} {title}")
    light = _guess_light(atmosphere, brief)
    cameras = ("wide", "medium", "close", "over_shoulder", "wide")
    lights = (light, "dramatic", "firelight", "golden", "golden")
    outlines = (
        (
            "Onde a história começa",
            "Abertura",
            f"Esta história bíblica começa assim: {short}. Antes de qualquer sinal, a cena mostra o lugar e quem está ali.",
            "Mostre o lugar antes de as pessoas ocuparem o quadro.",
        ),
        (
            "O peso do conflito",
            "Conflito",
            f"O conflito de «{title}» ganha peso: há algo a perder e alguém que ainda não sabe como atravessar. A narração não apressa a resposta.",
            "O problema precisa ser legível no corpo e no cenário.",
        ),
        (
            "A escolha",
            "Decisão",
            "Chega o instante da escolha. Obediência, fé ou misericórdia aparecem num gesto pequeno, antes de qualquer sinal grandioso.",
            "Um gesto pequeno no centro: mãos, olhar, um objeto.",
        ),
        (
            "A virada",
            "Virada",
            f"A virada não apaga o caminho já andado. Em «{title}», Deus age no meio da fraqueza humana, e a cena guarda um rosto — não só o prodígio.",
            "A ação entra na luz, sem efeito vazio e sem texto na imagem.",
        ),
        (
            "O que permanece",
            "Desfecho",
            f"A última cena deixa uma frase de esperança e aponta de volta para a Escritura{passage_bit}. Quem assiste é convidado a reler com calma.",
            "Rostos em paz e espaço para a última frase da narração.",
        ),
    )
    scenes: list[dict[str, str]] = []
    for index, (scene_title, beat, narration, hint) in enumerate(outlines):
        camera = cameras[index]
        scene_light = lights[index]
        scenes.append(
            _cena(
                scene_title,
                beat,
                narration,
                reference,
                "",
                camera,
                scene_light,
                atmosphere,
                (
                    f"{_label('camera', camera)} com luz {_label('light', scene_light).lower()} "
                    f"e clima de {_label('atmosphere', atmosphere).lower()}. {hint}"
                ),
            )
        )
    return scenes


def _script_from_scenes(scenes: list[dict[str, Any]]) -> str:
    parts = [str(scene.get("narration") or "").strip() for scene in scenes]
    return "\n\n".join(part for part in parts if part)


def _library_blocks(notes: list[dict[str, Any]], narration: str, cast: str) -> list[dict[str, str]]:
    specs = {
        item["title"]: item
        for item in seed_specs()
        if item.get("target") == "prompt_extra"
    }
    atmospheres = {note.get("atmosphere") for note in notes}
    blob = _fold(f"{narration} {cast}")
    wanted: list[str] = []
    for atmosphere, title in (
        ("temple", "Luz de templo"),
        ("desert", "Deserto ao entardecer"),
        ("sea", "Mar agitado"),
    ):
        if atmosphere in atmospheres:
            wanted.append(title)
    if any(note.get("camera") == "close" for note in notes):
        wanted.append("Close emocional")
    if "davi" in blob or "pastor" in blob:
        wanted.append("Pastor jovem")
    if any(stem in blob for stem in ("anciao", "noe", "sacerdote")):
        wanted.append("Ancião sábio")
    if any(stem in blob for stem in ("oracao", "suplica", "jejum", "ajoelh")):
        wanted.append("Joelho no chão")
    if any(stem in blob for stem in ("travess", "fuga", "marcha")):
        wanted.append("Travessia sob ameaça")
    picked: list[dict[str, str]] = []
    seen: set[str] = set()
    for title in wanted:
        if title in seen or title not in specs:
            continue
        seen.add(title)
        picked.append({"title": title, "body": specs[title]["body"]})
        if len(picked) >= 3:
            break
    return picked


def _split_scenes(
    raw_scenes: list[dict[str, str]],
    *,
    fallback_light: str,
    fallback_atmosphere: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    narrative: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    for index, scene in enumerate(raw_scenes):
        light = _preset("light", scene.get("light", ""), fallback_light)
        camera = _preset("camera", scene.get("camera", ""), "wide")
        atmosphere = _preset("atmosphere", scene.get("atmosphere", ""), fallback_atmosphere)
        narrative.append(
            {
                "index": index,
                "title": scene["title"],
                "beat": scene["beat"],
                "narration": scene["narration"],
                "reference": scene.get("reference") or "",
                "cast": scene.get("cast") or "",
            }
        )
        notes.append(
            {
                "index": index,
                "title": scene["title"],
                "light": light,
                "light_label": _label("light", light),
                "camera": camera,
                "camera_label": _label("camera", camera),
                "atmosphere": atmosphere,
                "atmosphere_label": _label("atmosphere", atmosphere),
                "art_note": scene.get("art_note") or "",
            }
        )
    return narrative, notes


def _majority_key(notes: list[dict[str, Any]], field: str, fallback: str) -> str:
    counts: dict[str, int] = {}
    for note in notes:
        key = str(note.get(field) or "")
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return fallback
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _meaningful_title(title: str, suggested: str) -> str:
    cleaned = re.sub(r"\s+", " ", (title or "")).strip()
    if not cleaned or _fold(cleaned) in _GENERIC_TITLES:
        return suggested
    return cleaned


def compose_plan(
    brief: str,
    *,
    title: str = "",
    theme: str = "",
    series_name: str = "",
    episode_number: int | None = None,
    brand_name: str = "",
    brand_voice: str = "",
    brand_caption_style: str = "",
    visual_style: str = "",
) -> dict[str, Any]:
    """Roda as três etapas e devolve um plano serializável."""
    cleaned = _clean_brief(brief)
    story = match_story(cleaned)
    suggested = str(story["title"]) if story else suggest_title(cleaned)
    passage = str(story["passage"]) if story else extract_passage(cleaned)
    if story:
        raw_scenes = [dict(scene) for scene in story["scenes"]]
        fallback_light = _preset("light", str(story.get("light") or ""), "golden")
        fallback_atmosphere = _preset(
            "atmosphere", str(story.get("atmosphere") or ""), "desert"
        )
    else:
        fallback_atmosphere = _guess_atmosphere(cleaned)
        fallback_light = _guess_light(fallback_atmosphere, cleaned)
        raw_scenes = _generic_scenes(cleaned, suggested, passage)

    narrative, notes = _split_scenes(
        raw_scenes,
        fallback_light=fallback_light,
        fallback_atmosphere=fallback_atmosphere,
    )
    script = _script_from_scenes(narrative)
    style_key = normalize_style(visual_style)
    style_label = label_for_style(style_key)
    project_light = _preset("light", str(story.get("light") if story else fallback_light), "golden")
    project_atmosphere = _preset(
        "atmosphere",
        str(story.get("atmosphere") if story else fallback_atmosphere),
        "desert",
    )
    # Se o arco não fixou um clima único, usa o que mais aparece nas cenas.
    if not story:
        project_light = _majority_key(notes, "light", project_light)
        project_atmosphere = _majority_key(notes, "atmosphere", project_atmosphere)

    cast_blob = " ".join(str(scene.get("cast") or "") for scene in narrative)
    blocks = _library_blocks(notes, script, cast_blob)
    block_titles = [block["title"] for block in blocks]
    light_label = _label("light", project_light)
    atmosphere_label = _label("atmosphere", project_atmosphere)
    prompt_extra = (
        f"Direção de arte para {suggested}: luz {light_label}, "
        f"atmosfera {atmosphere_label}. { _SHARED_TAIL }"
    )
    beats = ", ".join(str(scene["beat"]) for scene in narrative)
    if story:
        roteiro_summary = (
            f"Arco de «{story['title']}» ({passage}): {len(narrative)} cenas — {beats}."
        )
    else:
        roteiro_summary = (
            f"Arco livre a partir do breve, em {len(narrative)} cenas — {beats}. "
            "Vale conferir a passagem antes de gravar."
        )
    library_bit = ", ".join(block_titles) if block_titles else "nenhum bloco extra"
    arte_summary = (
        f"Mantive o estilo já escolhido ({style_label}) e marquei {light_label} "
        f"com atmosfera de {atmosphere_label}. A câmera muda em cada cena; "
        f"o preset global de câmera do projeto fica como está. "
        f"Blocos da biblioteca: {library_bit}."
    )

    yt_title_base = _meaningful_title(title, suggested)
    theme_line = (theme or "histórias bíblicas").strip()
    meta = generate_metadata(
        yt_title_base,
        theme_line,
        script,
        series_name=series_name or "",
        episode_number=episode_number,
        brand_name=brand_name or "",
        brand_voice=brand_voice or "",
        brand_caption_style=brand_caption_style or "",
    )
    hook = str(story["hook"]) if story else (
        f"Antes do desfecho, há uma escolha. Acompanhe {suggested} em poucos minutos."
    )
    description = (meta.get("youtube_description") or "").strip()
    if hook and not description.startswith(hook):
        description = f"{hook}\n\n{description}"
    if passage and passage.lower() not in description.lower():
        needle = "\n\n#HistoriasBiblicas"
        line = f"\n\nPassagem: {passage}"
        if needle in description:
            description = description.replace(needle, f"{line}{needle}", 1)
        else:
            description = f"{description}{line}"
    series = (series_name or "").strip()
    editor_bits = [f"título com {len(meta['youtube_title'])} caracteres"]
    if series:
        editor_bits.append(f"série «{series}»")
    if episode_number not in (None, ""):
        try:
            episode_int = int(episode_number)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            episode_int = 0
        if episode_int >= 1:
            editor_bits.append(f"episódio {episode_int}")
    brand = (brand_name or "").strip()
    if brand:
        editor_bits.append(f"tom de {brand}")
    editor_summary = (
        "Pacote pronto: " + ", ".join(editor_bits) + ". O gancho abre a descrição."
    )

    roteirista = {
        "id": "roteirista",
        "name": _AGENT_META["roteirista"][0],
        "mandate": _AGENT_META["roteirista"][1],
        "summary": roteiro_summary,
        "passage": passage,
        "scenes": narrative,
        "script": script,
    }
    diretor = {
        "id": "diretor_arte",
        "name": _AGENT_META["diretor_arte"][0],
        "mandate": _AGENT_META["diretor_arte"][1],
        "summary": arte_summary,
        "style_label": style_label,
        "light_preset": project_light,
        "light_label": light_label,
        "atmosphere_preset": project_atmosphere,
        "atmosphere_label": atmosphere_label,
        "prompt_extra": prompt_extra,
        "library_blocks": blocks,
        "scene_notes": notes,
    }
    editor = {
        "id": "editor_youtube",
        "name": _AGENT_META["editor_youtube"][0],
        "mandate": _AGENT_META["editor_youtube"][1],
        "summary": editor_summary,
        "hook": hook,
        "youtube_title": meta["youtube_title"],
        "youtube_description": description,
        "youtube_tags": meta["youtube_tags"],
    }
    return {
        "source": "template",
        "source_label": "Gerado no estúdio, sem API externa.",
        "brief": cleaned,
        "story_id": story["id"] if story else None,
        "passage": passage,
        "suggested_title": suggested,
        "agent_order": list(AGENT_ORDER),
        "steps": [
            {
                "id": agent_id,
                "name": _AGENT_META[agent_id][0],
                "label": _STEP_LABELS[agent_id],
            }
            for agent_id in AGENT_ORDER
        ],
        "agents": {
            "roteirista": roteirista,
            "diretor_arte": diretor,
            "editor_youtube": editor,
        },
    }


def compose_plan_for_project(project: dict[str, Any], brief: str) -> dict[str, Any]:
    project = project or {}
    return compose_plan(
        brief,
        title=str(project.get("title") or ""),
        theme=str(project.get("theme") or ""),
        series_name=str(project.get("series_name") or ""),
        episode_number=project.get("episode_number"),
        brand_name=str(project.get("brand_name") or ""),
        brand_voice=str(project.get("brand_voice") or ""),
        brand_caption_style=str(project.get("brand_caption_style") or ""),
        visual_style=str(project.get("visual_style") or ""),
    )


def scene_prompt_kwargs(project_look: dict[str, Any], scene: dict[str, Any] | None) -> dict[str, Any]:
    """Aplica a nota de arte da cena por cima do visual do projeto."""
    look = dict(project_look or {})
    scene = scene or {}
    for source, dest in (
        ("art_light", "light"),
        ("art_camera", "camera"),
        ("art_atmosphere", "atmosphere"),
    ):
        value = str(scene.get(source) or "").strip()
        if value:
            look[dest] = value
    note = str(scene.get("art_note") or "").strip()
    if note:
        look["scene_direction"] = note
    return look


def apply_plan_fields(
    project: dict[str, Any],
    plan: dict[str, Any],
    *,
    script: bool = True,
    visual: bool = True,
    youtube: bool = True,
) -> dict[str, Any]:
    """Monta o patch do projeto. Não mexe em formato, áudio, marca, série nem estilo."""
    project = project or {}
    agents = (plan or {}).get("agents") or {}
    patch: dict[str, Any] = {}
    if script:
        roteiro = agents.get("roteirista") or {}
        arte = agents.get("diretor_arte") or {}
        scenes_in = list(roteiro.get("scenes") or [])
        if not scenes_in:
            raise ValueError("Plano sem cenas para aplicar.")
        notes = {
            int(note.get("index", index)): note
            for index, note in enumerate(arte.get("scene_notes") or [])
        }
        existing = list(project.get("scenes") or [])
        merged: list[dict[str, Any]] = []
        for index, scene in enumerate(scenes_in):
            prev = existing[index] if index < len(existing) and isinstance(existing[index], dict) else {}
            note = notes.get(index, {})
            item: dict[str, Any] = {
                "index": index,
                "title": str(scene.get("title") or f"Cena {index + 1}"),
                "text": str(scene.get("narration") or "").strip(),
                "cast": str(scene.get("cast") or "").strip(),
                "image_path": prev.get("image_path"),
                "image_source": prev.get("image_source"),
                "image_prompt": prev.get("image_prompt"),
                "duration_sec": prev.get("duration_sec") if prev.get("duration_sec") not in ("",) else None,
                "art_note": str(note.get("art_note") or ""),
                "art_light": str(note.get("light") or ""),
                "art_camera": str(note.get("camera") or ""),
                "art_atmosphere": str(note.get("atmosphere") or ""),
                "reference": str(scene.get("reference") or ""),
            }
            merged.append(item)
        patch["script"] = str(roteiro.get("script") or _script_from_scenes(scenes_in))
        patch["scenes"] = merged
        patch["status"] = "scenes_ready"
    if visual:
        arte = agents.get("diretor_arte") or {}
        extra = str(project.get("prompt_extra") or "")
        extra = append_block_text(extra, str(arte.get("prompt_extra") or ""))
        for block in arte.get("library_blocks") or []:
            extra = append_block_text(extra, str(block.get("body") or ""))
        patch["prompt_extra"] = extra
        if arte.get("light_preset"):
            patch["light_preset"] = arte["light_preset"]
        if arte.get("atmosphere_preset"):
            patch["atmosphere_preset"] = arte["atmosphere_preset"]
    if youtube:
        editor = agents.get("editor_youtube") or {}
        if not (editor.get("youtube_title") or editor.get("youtube_description")):
            raise ValueError("Plano sem pacote do YouTube.")
        patch["youtube_title"] = str(editor.get("youtube_title") or "")
        patch["youtube_description"] = str(editor.get("youtube_description") or "")
        patch["youtube_tags"] = str(editor.get("youtube_tags") or "")
    return patch
