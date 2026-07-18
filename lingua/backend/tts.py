"""Text-to-speech via Google Cloud TTS (Neural2), com cache em disco por hash de conteúdo.

Falas fixas das trilhas (mesmo texto+voz+velocidade) nunca geram chamada repetida à API.
"""
from __future__ import annotations

import hashlib
import json
import logging

import config

logger = logging.getLogger("lingua.tts")

_voices_catalog: dict | None = None


def _catalogo() -> dict:
    global _voices_catalog
    if _voices_catalog is None:
        _voices_catalog = json.loads(config.VOICES_CATALOG_PATH.read_text())
    return _voices_catalog


def _taxa_fala(voice_id: str, slow: bool) -> float:
    for v in _catalogo()["voices"]:
        if v["id"] == voice_id:
            return v["speaking_rate_slow"] if slow else v["speaking_rate"]
    return 0.7 if slow else 0.9


def _idioma(voice_id: str) -> str:
    partes = voice_id.split("-")
    return "-".join(partes[:2]) if len(partes) >= 2 else "en-US"


def _cache_path(text: str, voice_id: str, rate: float):
    chave = hashlib.sha256(f"{text}|{voice_id}|{rate}".encode()).hexdigest()
    return config.TTS_CACHE_DIR / f"{chave}.mp3"


def sintetizar(text: str, voice_id: str, slow: bool = False) -> tuple[bytes, bool]:
    """Retorna (mp3_bytes, veio_do_cache)."""
    rate = _taxa_fala(voice_id, slow)
    config.TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    caminho = _cache_path(text, voice_id, rate)

    if caminho.exists():
        logger.info("tts cache hit: %s", caminho.name)
        return caminho.read_bytes(), True

    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code=_idioma(voice_id), name=voice_id),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=rate
        ),
    )
    caminho.write_bytes(resp.audio_content)
    logger.info("tts cache miss (sintetizado): %s chars", len(text))
    return resp.audio_content, False
