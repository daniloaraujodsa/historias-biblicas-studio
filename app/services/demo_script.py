"""Roteiros demo: Davi e Golias (curto e ~2 min), pt-BR."""

DAVI_GOLIAS_TITLE = "Davi e Golias"
DAVI_GOLIAS_THEME = "histórias bíblicas"

DAVI_GOLIAS_SCRIPT = """\
Há milhares de anos, no vale de Elá, dois exércitos se enfrentavam: Israel e os filisteus.

Do lado dos filisteus surgiu um gigante chamado Golias. Ele media quase três metros e desafiava Israel todos os dias.

Ninguém ousava enfrentá-lo. O medo dominava o acampamento de Saul.

Então chegou um jovem pastor chamado Davi. Ele veio apenas trazer comida aos seus irmãos.

Mas ao ouvir o desafio de Golias, Davi se indignou. “Quem é esse filisteu para desafiar o exército do Deus vivo?”

Saul tentou vestir Davi com sua armadura, mas ela era pesada demais. Davi preferiu sua funda e cinco pedras lisas do riacho.

Diante do gigante, Davi proclamou: “Tu vens contra mim com espada e lança, mas eu vou contra ti em nome do Senhor!”

Davi girou a funda, a pedra voou e atingiu Golias na testa. O gigante caiu. A vitória era do Senhor.

Assim o jovem pastor derrotou o gigante — não pela força, mas pela fé.
"""

# Cenas sugeridas (o segmentador também funciona a partir do roteiro)
DAVI_GOLIAS_SCENE_HINTS = [
    "Dois exércitos no vale de Elá",
    "O gigante Golias desafia Israel",
    "O medo no acampamento de Saul",
    "O jovem pastor Davi chega",
    "Davi se indigna com o desafio",
    "Davi escolhe a funda e as pedras",
    "Davi confronta Golias em nome do Senhor",
    "A pedra atinge Golias; a fé vence",
]

DAVI_GOLIAS_LONG_TITLE = "Davi e Golias — 2 minutos"
DAVI_GOLIAS_LONG_SCRIPT = """\
No vale de Elá, entre as montanhas de Judá, o sol caía sobre dois acampamentos. De um lado, os homens de Israel. Do outro, os filisteus, armados até os dentes.

Durante quarenta dias, manhã e tarde, um gigante chamado Golias saía das fileiras. Media quase três metros. A armadura de bronze brilhava. A lança parecia o mastro de um navio.

Golias gritava: “Escolhei um homem para lutar comigo! Se ele me vencer, seremos vossos servos. Se eu o vencer, sereis nossos servos.”

O silêncio era a única resposta. Até o rei Saul, o mais alto de Israel, temia. O medo se espalhava como fumaça no acampamento.

Naqueles dias, um jovem pastor chamado Davi veio do campo. Seu pai, Jessé, o enviara apenas para levar pão e queijo aos irmãos soldados.

Davi ouviu o desafio. Viu os homens recuarem. E o coração se inflamou. “Quem é esse filisteu para desafiar os exércitos do Deus vivo?”

Os irmãos o repreenderam, achando que falava por orgulho. Davi não recuou. Levaram-no até Saul.

Saul olhou o rapaz e disse: “Tu não podes ir contra esse filisteu. És um jovem, e ele é guerreiro desde a mocidade.”

Davi respondeu: “Teu servo pastoreava as ovelhas. Quando vinha um leão ou um urso, eu o perseguia. O Senhor me livrou das garras do leão e do urso; ele me livrará da mão deste filisteu.”

Saul tentou vestir Davi com sua própria armadura: capacete, couraça e espada. Davi deu alguns passos e parou. “Não posso andar com isto. Não estou acostumado.”

Tirou tudo. Pegou o cajado, escolheu cinco pedras lisas no riacho e colocou-as na bolsa de pastor. Na mão, só a funda.

Golias viu o menino se aproximar e o desprezou. “Sou eu algum cão, para vires a mim com paus? Vem, e darei tua carne às aves do céu.”

Davi não tremeu. “Tu vens contra mim com espada, lança e escudo. Eu vou contra ti em nome do Senhor dos Exércitos, o Deus das fileiras de Israel, a quem desafiaste.”

“Hoje o Senhor te entregará na minha mão. Toda a terra saberá que há Deus em Israel. E esta assembleia saberá que o Senhor não salva com espada nem com lança.”

Davi correu para a linha de combate. Girou a funda. A pedra cortou o ar e cravou-se na testa de Golias. O gigante caiu com o rosto em terra.

Davi tomou a espada do próprio Golias e venceu. Os filisteus fugiram. Israel gritou. A vitória não veio da força, nem do bronze — veio da fé.

Assim um pastor derrotou um gigante. E o nome do Senhor foi exaltado no vale de Elá.
"""

DAVI_GOLIAS_LONG_HINTS = [
    "Dois acampamentos no vale de Elá",
    "Golias desafia Israel quarenta dias",
    "O grito do gigante e o silêncio",
    "O medo no acampamento de Saul",
    "Davi chega com pão para os irmãos",
    "Davi se indigna com o desafio",
    "Saul duvida do jovem pastor",
    "O Senhor livrou Davi do leão e do urso",
    "Davi recusa a armadura do rei",
    "Cinco pedras lisas e a funda",
    "Golias despreza o menino",
    "Davi enfrenta Golias em nome do Senhor",
    "A pedra atinge a testa do gigante",
    "A vitória da fé no vale de Elá",
]


# Referência do próprio canal Prosperidade e Fé (YouTube t3xB18IwbFk, ~184 s).
# Espécime da fórmula de narração do canal, para testes e para o arco do roteirista.
# Não é material de terceiro.
MOISES_NEBO_TITLE = "Moisés no Monte Nebo"
MOISES_NEBO_THEME = "histórias bíblicas"
MOISES_NEBO_PASSAGE = "Deuteronômio 34"
MOISES_NEBO_CHANNEL = "Prosperidade e Fé"
MOISES_NEBO_YOUTUBE_ID = "t3xB18IwbFk"
MOISES_NEBO_DURATION_SEC = 184

# Dez tempos, na ordem do arco. Juntar com espaço único reproduz a narração contínua.
MOISES_NEBO_BEATS: tuple[str, ...] = (
    "Você sabia que Moisés chegou a contemplar a terra prometida com os próprios olhos, mas nunca entrou nela?",
    "A história está registrada em Deuteronômio, capítulo 34, e marca um dos momentos mais emocionantes da Bíblia.",
    "Depois de muitos anos conduzindo o povo de Israel pelo deserto, Moisés subiu ao monte Nebo, diante de Jericó. Ali Deus mostrou a ele a terra prometida. Moisés conseguiu enxergar Canaã, as terras que Deus havia prometido a Abraão, Isaque e Jacó.",
    "Mas havia algo que Moisés não sabia fazer. Ele não poderia atravessar o Jordão e entrar naquela terra. Deus havia determinado que Moisés apenas contemplaria a promessa. Então, chegou o momento mais difícil. A Bíblia diz que Moisés, servo do Senhor, morreu ali na terra de Moabe, conforme a palavra do próprio Deus.",
    "E existe um detalhe impressionante. Os seus olhos nunca se escureceram, nem se lhe abateu o vigor. Moisés tinha 120 anos. Mesmo depois de uma vida inteira de desafios, sua força permanecia.",
    "Mas por que Deus permitiu que Moisés morresse antes de entrar na terra prometida? A Bíblia explica que em determinado momento Moisés e Arão não santificaram o nome de Deus diante do povo nas águas de Meribá. Por isso, Deus declarou que Moisés contemplaria a terra, mas não entraria nela. E então Josué assumiria a liderança de Israel.",
    "Mas a história não termina simplesmente com a morte de Moisés. Deuteronômio diz que ninguém conheceu o lugar da sua sepultura. E Moisés deixou um legado que atravessou gerações. Ele foi o homem que Deus usou para conduzir Israel para fora do Egito. Recebeu a lei no monte Sinai e guiou o povo durante décadas.",
    "Sua história nos ensina que servir a Deus não significa que teremos todas as coisas exatamente como imaginamos. Moisés não entrou em Canaã, mas contemplou a promessa e sua missão não foi esquecida.",
    "Talvez você também esteja diante de algo que esperou durante muito tempo e ainda não conseguiu alcançar. Lembre-se de Moisés. Deus continua sendo Deus mesmo quando não entendemos todos os seus caminhos.",
    "Confie no Senhor, permaneça fiel e continue caminhando, porque a nossa história não termina simplesmente onde os nossos olhos conseguem enxergar. E você já tinha percebido esse detalhe sobre a morte de Moisés no Monte Nebo? Inscreva-se no canal e ative o sino para receber as notificações de novos vídeos.",
)

MOISES_NEBO_SCRIPT = " ".join(MOISES_NEBO_BEATS)

MOISES_NEBO_SCENE_HINTS = [
    "Gancho: a terra vista e não entrada",
    "Âncora: Deuteronômio 34",
    "Cena: o monte Nebo diante de Jericó",
    "Tensão: o Jordão que não se atravessa",
    "Detalhe: vigor aos 120 anos",
    "Por quê: as águas de Meribá",
    "Legado: Egito, Sinai e o deserto",
    "Ensinamento: a missão não foi esquecida",
    "Aplicação: a espera de quem assiste",
    "Fecho: confiança e convite ao canal",
]

# Variante curta (~45–70 s) da mesma referência, ainda nos dez tempos.
MOISES_NEBO_SHORT_BEATS: tuple[str, ...] = (
    "Você sabia que Moisés contemplou a terra prometida e nunca entrou nela?",
    "A história está registrada em Deuteronômio, capítulo 34.",
    "No monte Nebo, diante de Jericó, Deus mostrou Canaã a Moisés.",
    "Então, chegou o momento mais difícil. Ele não atravessou o Jordão e morreu em Moabe.",
    "E existe um detalhe impressionante. Aos 120 anos, os olhos não se escureceram nem se lhe abateu o vigor.",
    "Mas por que Deus permitiu isso? Em Meribá, Moisés e Arão não santificaram o nome do Senhor.",
    "Moisés deixou um legado: a saída do Egito, a lei no Sinai e décadas guiando o povo.",
    "Sua história nos ensina que servir a Deus não é receber tudo como imaginamos.",
    "Talvez você também espere algo que ainda não alcançou. Deus continua sendo Deus.",
    "E você já tinha percebido esse detalhe? Inscreva-se no canal e ative o sino para receber as notificações de novos vídeos.",
)

MOISES_NEBO_SHORT_SCRIPT = " ".join(MOISES_NEBO_SHORT_BEATS)
