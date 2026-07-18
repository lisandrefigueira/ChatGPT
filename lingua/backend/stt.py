"""Speech-to-text via Groq Whisper (whisper-large-v3)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import httpx

import config
from schemas import STTResponse, WordTiming

GROQ_TRANSCRIPTIONS_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def _para_wav_16k_mono(audio_bytes: bytes, sufixo_origem: str) -> bytes:
    """Normaliza o áudio recebido do MediaRecorder (webm/opus) para WAV 16kHz mono via ffmpeg.

    Whisper aceita webm diretamente, mas normalizar melhora a robustez da transcrição
    e evita surpresas com variações de container/codec entre navegadores.
    """
    with tempfile.TemporaryDirectory() as tmp:
        entrada = Path(tmp) / f"in{sufixo_origem}"
        saida = Path(tmp) / "out.wav"
        entrada.write_bytes(audio_bytes)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(entrada),
                "-ac", "1", "-ar", "16000", str(saida),
            ],
            check=True,
            capture_output=True,
        )
        return saida.read_bytes()


def transcrever(audio_bytes: bytes, content_type: str) -> STTResponse:
    sufixo = ".webm" if "webm" in content_type else ".ogg" if "ogg" in content_type else ".wav"
    try:
        wav_bytes = _para_wav_16k_mono(audio_bytes, sufixo)
        nome_arquivo, corpo = "audio.wav", wav_bytes
    except (subprocess.CalledProcessError, FileNotFoundError):
        # ffmpeg indisponível ou falhou: envia o blob original (Whisper aceita webm/ogg).
        nome_arquivo, corpo = f"audio{sufixo}", audio_bytes

    resp = httpx.post(
        GROQ_TRANSCRIPTIONS_URL,
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        files={"file": (nome_arquivo, corpo)},
        data={
            "model": config.GROQ_STT_MODEL,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    dados = resp.json()

    segmentos = dados.get("segments", [])

    def confianca_no_tempo(t: float) -> float | None:
        for seg in segmentos:
            if seg["start"] <= t <= seg["end"] and "avg_logprob" in seg:
                # avg_logprob é log-probabilidade média (negativa); normaliza para [0,1] aproximado.
                return max(0.0, min(1.0, 1.0 + seg["avg_logprob"]))
        return None

    palavras = [
        WordTiming(
            word=w["word"].strip(),
            start=w["start"],
            end=w["end"],
            confidence=confianca_no_tempo(w["start"]),
        )
        for w in dados.get("words", [])
    ]

    return STTResponse(text=dados.get("text", "").strip(), words=palavras, duration=dados.get("duration", 0.0))
