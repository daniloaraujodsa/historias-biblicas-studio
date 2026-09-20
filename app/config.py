"""Configuração do Histórias Bíblicas Studio."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

DATA_DIR = ROOT / "data"
PROJECTS_DIR = DATA_DIR / "projects"
EXPORTS_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "studio.db"
REFERENCES_DIR = ROOT / "references"

# Resolução de vídeo (YouTube 16:9)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

# Voz TTS padrão (pt-BR feminina narrativa)
DEFAULT_VOICE = "pt-BR-FranciscaNeural"
# Alternativa masculina: pt-BR-AntonioNeural

DEFAULT_THEME = "histórias bíblicas"

# --- Geração de imagens (IA) ---
# Auto: grok (se XAI_API_KEY) > openai (se OPENAI_API_KEY) > pollinations.
# Em falha → próximo provedor → placeholder Pillow.
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


def _default_image_provider() -> str:
    raw = os.getenv("IMAGE_PROVIDER", "").strip().lower()
    if raw and raw not in ("auto",):
        return raw
    if XAI_API_KEY:
        return "grok"
    if OPENAI_API_KEY:
        return "openai"
    return "pollinations"


IMAGE_PROVIDER = _default_image_provider()
GROK_IMAGE_MODEL = os.getenv("GROK_IMAGE_MODEL", "grok-imagine-image-2.0").strip()
POLLINATIONS_BASE = os.getenv(
    "POLLINATIONS_BASE",
    "https://image.pollinations.ai/prompt",
).rstrip("/")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
IMAGE_TIMEOUT_SEC = int(os.getenv("IMAGE_TIMEOUT_SEC", "120"))
IMAGE_MAX_RETRIES = int(os.getenv("IMAGE_MAX_RETRIES", "6"))

for d in (DATA_DIR, PROJECTS_DIR, EXPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
