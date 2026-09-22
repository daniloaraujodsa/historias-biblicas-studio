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
MUSIC_DIR = DATA_DIR / "music"
DB_PATH = DATA_DIR / "studio.db"
REFERENCES_DIR = ROOT / "references"

# Resolução de vídeo
VIDEO_FPS = 30
ASPECT_LANDSCAPE = "16:9"
ASPECT_SHORTS = "9:16"
DEFAULT_ASPECT = ASPECT_LANDSCAPE

SUBTITLE_FONT = os.getenv(
    "SUBTITLE_FONT",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

# Voz TTS padrão (pt-BR feminina narrativa)
DEFAULT_VOICE = "pt-BR-FranciscaNeural"

DEFAULT_THEME = "histórias bíblicas"

# Preview / server
PORT = int(os.getenv("PORT", "8080"))

# --- Geração de imagens (IA) ---
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


def frame_size(aspect: str | None) -> tuple[int, int]:
    """Retorna (width, height) para o formato do projeto."""
    a = (aspect or DEFAULT_ASPECT).strip()
    if a in ("9:16", "shorts", "vertical", "portrait"):
        return 1080, 1920
    return 1920, 1080


def grok_aspect(aspect: str | None) -> str:
    a = (aspect or DEFAULT_ASPECT).strip()
    return "9:16" if a in ("9:16", "shorts", "vertical", "portrait") else "16:9"


for d in (DATA_DIR, PROJECTS_DIR, EXPORTS_DIR, MUSIC_DIR):
    d.mkdir(parents=True, exist_ok=True)
