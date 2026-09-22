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
2. Ajuste formato, legendas e trilha em **Formato e opções**
3. Clique em **Pipeline completo** e acompanhe a barra de progresso
4. Veja o preview, edite título/descrição/tags e baixe o ZIP

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
- SQLite (`projects`, `characters`, `jobs`)

## Limitações

- Pollinations anônimo tem fila curta (429) — retries ajudam, o pipeline fica mais lento.
- A trilha é um leito sintético (senoides graves), não uma faixa licenciada.
- Sem upload direto para o YouTube / OAuth.

## Licença

Código original deste repositório — use como quiser no seu fluxo de produção.
