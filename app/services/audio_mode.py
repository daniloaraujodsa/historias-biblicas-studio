"""Modos de áudio do MP4: narração, trilha, os dois ou mudo."""
from __future__ import annotations

AUDIO_MODES: tuple[tuple[str, str, str], ...] = (
    ("narration", "Só narração", "Voz do roteiro, sem trilha."),
    ("music", "Só trilha", "Leito musical, sem voz."),
    ("both", "Narração e trilha", "Voz com leito por baixo."),
    ("none", "Sem áudio", "MP4 mudo. A duração segue o texto ou o valor de cada cena."),
)

_VALID = {item[0] for item in AUDIO_MODES}


def mode_options() -> list[dict[str, str]]:
    return [{"id": mid, "label": label, "hint": hint} for mid, label, hint in AUDIO_MODES]


def normalize_audio_mode(value: str | None, *, music: bool | None = None) -> str:
    key = (value or "").strip().lower()
    if key in _VALID:
        return key
    if music is False:
        return "narration"
    return "both"


def resolve_mode(audio_mode: str | None, *, music: bool = True) -> str:
    if audio_mode is not None and str(audio_mode).strip():
        return normalize_audio_mode(audio_mode, music=music)
    return "both" if music else "narration"


def uses_narration(mode: str) -> bool:
    return normalize_audio_mode(mode) in ("narration", "both")


def uses_music(mode: str) -> bool:
    return normalize_audio_mode(mode) in ("music", "both")
