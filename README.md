# Histórias Bíblicas Studio

> **Versão Grok Build** — esta árvore substitui o MVP FastAPI inicial no `main`.
> Inclui formato 16:9 e Shorts 9:16, elenco por cena, pipeline com progresso,
> legendas SRT, thumbnail e **pacote YouTube (ZIP)**. Mídia gerada (`data/`,
> `*.mp4`, `*.mp3`) fica fora do repositório.

Estúdio web para produzir vídeos de **histórias bíblicas** para YouTube e Shorts:

1. Criar projeto (16:9 ou 9:16) e colar o roteiro em pt-BR
2. Cadastrar personagens (bíblia visual + foto de referência)
3. Segmentar cenas e editar título, texto, elenco e ordem
4. Narração TTS **por cena** (edge-tts → gTTS → espeak)
5. Imagens de IA (Grok Imagine / Pollinations / OpenAI) ou upload
6. Montar **MP4** com Ken Burns, legendas SRT, trilha e thumbnail
7. Baixar MP4, SRT, capa e **pacote YouTube (ZIP)**

Código original. Não usa assets, APIs ou branding de terceiros proprietários (exceto provedores de IA/TTS opcionais).

## Dependências do sistema

- **Python 3.10+**
- **FFmpeg** (obrigatório — vídeo, concat de áudio e duração)

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y ffmpeg

# macOS
brew install ffmpeg
```

## Instalação

```bash
cd historias-biblicas-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

TTS e imagens Pollinations **não exigem API key**. Grok Imagine (xAI) e OpenAI Images são opcionais.

**TTS (ordem de fallback):**

1. [edge-tts](https://github.com/rany2/edge-tts) ≥ 7.2.8 (vozes neurais pt-BR)
2. [gTTS](https://pypi.org/project/gTTS/)
3. `espeak-ng` / `espeak` — offline

## Rodar

```bash
source .venv/bin/activate
export PYTHONPATH=.
./scripts/run.sh
# ou: python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Abra a interface na porta **8080**.

### Demo Davi e Golias

1. Na home, escolha 16:9 ou Shorts 9:16 e clique em **Abrir demo Davi e Golias**
2. Ajuste formato, estilo visual, luz/câmera/atmosfera, áudio e série em **Formato e opções**
3. Clique em **Pipeline completo** e acompanhe a barra de progresso
4. Veja o preview, edite título/descrição/tags e baixe o ZIP

## Controles do projeto

Na aba **Formato**:

- **Estilo visual** (padrão: Cinemático bíblico). Também há pintura a óleo sacra, ilustração digital, semi-realista 3D, aquarela e alto contraste. O estilo entra em todo prompt de imagem.
- **Luz, câmera e atmosfera** — presets opcionais compostos no mesmo prompt (luz dourada, Rembrandt, close, deserto, templo, etc.).
- **Áudio do vídeo**: só narração, só trilha, narração e trilha, ou sem áudio. Sem narração, a duração de cada cena é estimada pelo texto.
- **Série e episódio** (opcionais). Aparecem na lista da home e no título/descrição padrão do YouTube.
- **Identidade visual** — nome da marca (padrão: Prosperidade e Fé), tom de voz, paleta, estilo de legenda, notas de consistência e nota de logo. Entram no prompt de imagem e no pacote do YouTube.
- **Notas extras de imagem** — texto livre (e blocos da biblioteca) acrescentado a cada geração.

Na seção **Biblioteca de prompts**:

- Blocos reutilizáveis por categoria (estilo de cena, personagem, ambiente, ação, voz narrativa).
- Aplicar acrescenta o texto às notas de imagem, ao roteiro ou às notas da marca.
- Há exemplos iniciais do estúdio; você pode salvar blocos do projeto ou da biblioteca do app.

No **Roteiro**, os modelos de arco (queda e graça, confronto e fé, chamado e libertação, julgamento e aliança, e o gancho bíblico) preenchem um esboço em português para editar.

### Gancho bíblico Prosperidade e Fé

Fórmula de narração do canal, em dez tempos:

1. **Gancho** — «Você sabia…?» com contraste
2. **Âncora bíblica** — livro e capítulo
3. **Cena** — o relato em ordem, com reverência
4. **Tensão** — o momento mais difícil
5. **Detalhe impressionante** — o fato que prende
6. **Por quê?** — a explicação breve da Escritura
7. **Legado** — o que a personagem deixou
8. **Ensinamento** — a moral explícita
9. **Aplicação** — «Talvez você também…»
10. **Fecho e convite** — pergunta de engajamento, inscrição e sino

O esboço médio mira **2 a 4 minutos** (cerca de 350 a 450 palavras). Há também **Gancho bíblico — Shorts**, cerca de 45 a 70 segundos. O exemplo preenchido é Moisés no monte Nebo (Deuteronômio 34), narração de referência do próprio canal. Troque personagem, lugar e passagem e conserve a ordem. Se for narrar direto, apague o rótulo do tempo no início de cada parágrafo.

No **Planejamento**, um breve que não cai num arco já catalogado também sai nessa voz. «Moisés no monte Nebo» devolve a narração de referência, já sem os rótulos. «shorts» no breve pede a versão curta. Os arcos conhecidos (Davi, Noé, o mar, Rute e os demais) continuam como estavam.

Na biblioteca de prompts, o bloco **Voz do gancho bíblico** (categoria voz narrativa) acrescenta um parágrafo nessa voz ao roteiro.

## Planejamento da equipe

Na home ou no projeto, escreva um breve (história, passagem ou tema) e clique em **Planejar com equipe**.

O estúdio monta o plano em três etapas, sem API externa:

1. **Roteirista** — cenas, narração e referências bíblicas
2. **Diretor de arte** — luz, câmera, atmosfera e notas por cena (entram no prompt da imagem; a câmera fica na cena)
3. **Editor YouTube** — gancho, título, descrição e tags, usando série, episódio e marca

O plano fica salvo no projeto. **Aplicar ao projeto** preenche só o que estiver marcado: roteiro e cenas, notas visuais (luz, atmosfera, biblioteca) e pacote do YouTube. Formato, áudio, marca, série e estilo visual não mudam. Se já houver roteiro ou metadados, a página pede confirmação. Imagens já geradas na mesma posição de cena são mantidas.

Caminho rápido: breve «Rute no campo de Boaz» → **Planejar com equipe** → revisar as três mesas → **Aplicar ao projeto** → roteiro, cenas e campos do YouTube preenchidos.

Outro caminho: breve «Moisés no monte Nebo, Deuteronômio 34» (ou uma história ainda sem arco) → o roteirista escreve o gancho, a âncora, o detalhe impressionante, a aplicação e o convite de inscrição.

Em **Publicar**, o botão **Preencher título e descrição padrão** monta os metadados (série, episódio e marca) sem precisar renderizar de novo.

## O que o pipeline gera

| Arquivo | Uso |
|---------|-----|
| `data/exports/<id>.mp4` | Vídeo final (Ken Burns + narração + legendas opcionais + música) |
| `data/projects/<id>/captions.srt` | Legendas sincronizadas com a duração de cada cena |
| `data/exports/<id>_thumb.jpg` | Thumbnail YouTube 1280×720 |
| `data/exports/<id>_youtube.zip` | MP4 + SRT + thumbnail + `youtube.txt` (título, descrição, tags) |

A narração é gerada **cena a cena** e concatenada; a duração de cada plano segue o áudio daquela cena.

## Imagens IA

| Prioridade | Provedor | Quando | Chave |
|------------|----------|--------|-------|
| 1 | xAI Grok Imagine | `XAI_API_KEY` ou `IMAGE_PROVIDER=grok` | Sim |
| 2 | OpenAI Images | `OPENAI_API_KEY` / `IMAGE_PROVIDER=openai` | Sim |
| 3 | Pollinations.ai | Padrão sem chave / fallback | Não |
| 4 | Pillow placeholder | Falha de rede/API | — |

16:9 gera 1920×1080; Shorts 9:16 gera 1080×1920. O thumbnail do YouTube permanece 1280×720 nos dois formatos.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | `8080` | Porta HTTP |
| `XAI_API_KEY` | — | Grok Imagine |
| `GROK_IMAGE_MODEL` | `grok-imagine-image-2.0` | Modelo Grok |
| `OPENAI_API_KEY` | — | OpenAI Images |
| `IMAGE_PROVIDER` | auto | `grok` \| `openai` \| `pollinations` \| `placeholder` |
| `IMAGE_TIMEOUT_SEC` | `120` | Timeout HTTP |
| `IMAGE_MAX_RETRIES` | `6` | Retries (útil p/ 429) |

## Personagens

No projeto, cadastre nome, papel e bíblia visual. O editor de cenas tem um campo **elenco** (ex.: `Davi, Saul`) que filtra quem entra no prompt. Sem elenco, o app detecta o nome no texto.

## Stack

- FastAPI + Jinja2 (UI pt-BR)
- Jobs em background (thread + SQLite) com barra de progresso
- edge-tts / gTTS / espeak
- Grok Imagine / Pollinations / OpenAI + Pillow
- FFmpeg (Ken Burns, legendas, mix de trilha)
- SQLite (`projects`, `characters`, `jobs`, `prompt_blocks`, `production_plans`)

## Limitações

- Pollinations anônimo tem fila curta (429) — retries ajudam, o pipeline fica mais lento.
- A trilha (com narração ou sozinha) é um leito sintético (senoides graves), não uma faixa licenciada.
- Sem upload direto para o YouTube / OAuth.

## Testes

```bash
PYTHONPATH=. python3 -m unittest tests.test_studio_controls tests.test_planning tests.test_gancho_biblico
```

## Licença

Código original deste repositório — use como quiser no seu fluxo de produção.
