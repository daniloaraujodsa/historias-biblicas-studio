# Histórias Bíblicas Studio

MVP web local para produzir vídeos de **histórias bíblicas** para YouTube:

1. Criar projeto + tema  
2. Colar/gerar roteiro (pt-BR)  
3. Narração TTS (edge-tts, sem API key)  
4. Segmentar cenas + **imagens geradas por IA** (Grok Imagine / Pollinations / OpenAI)  
5. Montar **MP4** com FFmpeg (Ken Burns + áudio)  
6. **Baixar MP4**  

Código 100% original. Não usa assets, APIs ou branding de terceiros proprietários (exceto provedores de IA/TTS opcionais/documentados).

## Dependências do sistema

- **Python 3.10+**
- **FFmpeg** (obrigatório — vídeo e duração do áudio)

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y ffmpeg

# macOS
brew install ffmpeg
```

Confirme:

```bash
ffmpeg -version
ffprobe -version
```

## Instalação

```bash
cd /workspace/historias-biblicas-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**TTS e imagens Pollinations não exigem API key.** Grok Imagine (xAI) e OpenAI Images são opcionais (veja abaixo).

**TTS (ordem de fallback):**
1. [edge-tts](https://github.com/rany2/edge-tts) ≥ 7.2.8 (vozes neurais pt-BR) — requer rede  
2. [gTTS](https://pypi.org/project/gTTS/) — requer rede  
3. `espeak-ng` / `espeak` — offline (opcional: `sudo apt install espeak-ng`)

Se edge-tts retornar 403, atualize: `pip install -U edge-tts` (versões antigas quebram com mudanças do serviço Microsoft).

Copie `.env.example` → `.env` se quiser configurar provedores.

## Imagens IA (provedores)

Cada cena recebe um prompt cinematográfico bíblico derivado do título + texto do roteiro (pt-BR → prompt em inglês para o modelo).

| Prioridade | Provedor | Quando | Chave |
|------------|----------|--------|-------|
| 1 | **xAI Grok Imagine** | `XAI_API_KEY` definida (ou `IMAGE_PROVIDER=grok`) | Sim |
| 2 | **OpenAI Images** | `OPENAI_API_KEY` definida (sem XAI) ou `IMAGE_PROVIDER=openai` | Sim |
| 3 | **Pollinations.ai** | Padrão sem chave / fallback | Não |
| 4 | **Pillow placeholder** | Qualquer falha de rede/API | — |

Fallback: Grok → Pollinations → Pillow; OpenAI → Pollinations → Pillow.

### xAI Grok Imagine (recomendado)

No `.env`:

```bash
XAI_API_KEY=xai-...
# opcional:
GROK_IMAGE_MODEL=grok-imagine-image-2.0
# IMAGE_PROVIDER=grok   # força Grok (padrão automático se XAI_API_KEY existir)
```

- Endpoint: `POST https://api.x.ai/v1/images/generations`
- Modelo padrão: `grok-imagine-image-2.0` (alternativa: `grok-imagine-image-quality`)
- Body: `aspect_ratio=16:9`, `resolution=2k`; a URL temporária é baixada na hora e salva como JPEG 1920×1080.
- Docs: [Image Generation](https://docs.x.ai/developers/model-capabilities/images/generation)

### Pollinations.ai (padrão sem chave)

- Endpoint: `GET https://image.pollinations.ai/prompt/{urlencoded_prompt}?width=1920&height=1080&nologo=true&model=flux&seed=…`
- Sem API key na fila anônima.
- **Quirk:** pode retornar **HTTP 429** (“queue full”). O app faz retry com backoff (15s, 30s…). Contas/API key em [enter.pollinations.ai](https://enter.pollinations.ai) evitam a fila limitada.
- O endpoint novo `gen.pollinations.ai` exige API key — **não** é o padrão deste MVP.

### OpenAI Images (opcional)

No `.env`:

```bash
OPENAI_API_KEY=sk-...
# opcional:
OPENAI_IMAGE_MODEL=dall-e-3
# IMAGE_PROVIDER=openai   # força OpenAI mesmo se quiser sobrescrever o auto-detect
```

Usa `POST https://api.openai.com/v1/images/generations` (tamanho 1792×1024) e redimensiona para 1920×1080.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `XAI_API_KEY` | — | Habilita xAI Grok Imagine |
| `GROK_IMAGE_MODEL` | `grok-imagine-image-2.0` | Modelo Grok Imagine |
| `OPENAI_API_KEY` | — | Habilita OpenAI Images |
| `OPENAI_IMAGE_MODEL` | `dall-e-3` | Modelo OpenAI |
| `IMAGE_PROVIDER` | auto: `grok` / `openai` / `pollinations` | `grok` \| `openai` \| `pollinations` \| `placeholder` \| `auto` |
| `POLLINATIONS_BASE` | `https://image.pollinations.ai/prompt` | Base URL |
| `IMAGE_TIMEOUT_SEC` | `120` | Timeout HTTP |
| `IMAGE_MAX_RETRIES` | `6` | Retries (útil p/ 429) |

Na UI (pt-BR): aviso de que as imagens são geradas por IA + botão **↻ Regenerar imagem** por cena.

## Rodar a interface

```bash
source .venv/bin/activate
export PYTHONPATH=.
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765
# ou: ./scripts/run.sh
```

Abra: **http://127.0.0.1:8765**

### Demo Davi e Golias (UI)

1. Na home, clique em **▶ Demo Davi e Golias**  
2. No projeto, clique em **⚡ Pipeline completo**  
3. Aguarde TTS + imagens IA + FFmpeg (pode passar de 3 min por causa da fila Pollinations)  
4. Clique em **⬇ Baixar MP4**

### Demo via CLI (sem browser)

```bash
source .venv/bin/activate
export PYTHONPATH=.
python3 scripts/demo_cli.py
```

O script imprime o caminho do MP4 e URLs de download.

## Onde os arquivos ficam

| Tipo | Caminho |
|------|---------|
| Banco SQLite | `data/studio.db` |
| Áudio / imagens por projeto | `data/projects/<id>/` |
| Refs de personagens | `data/projects/<id>/characters/` |
| **MP4 exportado** | `data/exports/<id>.mp4` |
| Referências de mood (amostras) | `references/` (não usadas como assets de produção) |

Download HTTP: `GET /api/projects/<id>/download`

## Stack

- **FastAPI** + Jinja2 (UI pt-BR)
- **edge-tts** (voz `pt-BR-FranciscaNeural` por padrão)
- **Grok Imagine** / **Pollinations.ai** / **OpenAI Images** (cenas) + **Pillow** (fallback)
- **FFmpeg** (Ken Burns `zoompan` + AAC/H.264)
- **SQLite** (persistência de projetos + personagens)


## Fidelidade de personagens (character bible)

Para manter **Davi, Golias, Saul** (ou outros) visualmente consistentes entre cenas:

1. No projeto, abra a seção **Personagens**.
2. Cadastre nome, papel e **bíblia visual** (pt-BR): idade, rosto, cabelo, roupas, porte, traços.
3. (Opcional) Faça upload de uma **imagem de referência**.
4. Ao gerar imagens, o app:
   - Detecta quem aparece na cena pelo **nome** no título/texto;
   - Se ninguém bater, anexa a bible de **todos** os personagens do projeto;
   - Sempre injeta um bloco forte de consistência no prompt;
   - Se `XAI_API_KEY` existir **e** houver imagem de referência, tenta
     `POST https://api.x.ai/v1/images/edits` com data URI(s) da(s) ref(s)
     (até 3 — multi-image editing). Em falha, cai para `/v1/images/generations`
     com a bible no texto, depois Pollinations (só texto).

### Persistência

| Dado | Onde |
|------|------|
| Metadados (nome, papel, bible) | SQLite `characters` (`data/studio.db`) |
| Imagens de referência | `data/projects/<id>/characters/<character_id>.jpg|png|…` |

`project_id` pode ser `NULL` para uma biblioteca global (API pronta; UI do MVP foca no elenco do projeto).

### Demo Davi e Golias

O botão **▶ Demo Davi e Golias** (e `scripts/demo_cli.py`) semeia automaticamente:

- **Davi** — jovem pastor  
- **Golias** — gigante filisteu  
- **Saul** — rei de Israel  

Cada um com bible visual em pt-BR. Sem refs de imagem no seed (faça upload na UI se quiser Grok edit).

### TODO / notas

- Lip-sync e animação facial estão **fora de escopo** deste MVP.
- Se a forma exata do campo multi-image da API xAI mudar, o fallback gera com bible no prompt.
- Pollinations não recebe imagens de referência — só o texto da bible (prompt compacto).

## Limitações do MVP

- Pollinations anônimo tem fila curta (429) — retries ajudam, mas o pipeline fica mais lento.
- TTS depende de rede (Microsoft Edge neural voices via edge-tts).
- Upload de imagem de cena customizada ainda não existe (só refs de personagem).
- Sem publicação no YouTube / OAuth.
- Ken Burns é zoom/pan suave fixo; não há animação avançada por cena.

## Aceite

- [x] README com install/run + FFmpeg  
- [x] Fluxo demo Davi e Golias → MP4 baixável  
- [x] Botão/script de demo  
- [x] UI em pt-BR, nome original  
- [x] Imagens IA (Grok Imagine / Pollinations / OpenAI) + fallback Pillow  

## Licença

Código original deste repositório — use como quiser no seu fluxo de produção.
