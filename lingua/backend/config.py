"""Configuração central — nada de valores mágicos espalhados pelo código."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("LINGUA_DATA_DIR", BASE_DIR / "data"))
TTS_CACHE_DIR = DATA_DIR / "tts_cache"
CUSTOS_LOG = DATA_DIR / "custos.jsonl"
DB_PATH = DATA_DIR / "historico.sqlite"
TRILHAS_DIR = BASE_DIR / "trilhas"

APP_TOKEN = os.environ.get("APP_TOKEN", "")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_STT_MODEL = "whisper-large-v3"

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # "openai" | "anthropic"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Bandas de avaliação fonética (§ Agente 3 da spec)
BANDA_VERDE_MIN = 0.85
BANDA_AMARELO_MIN = 0.60

# Custos (estimativas usadas para o painel /api/custos, em BRL)
CUSTO_TTS_POR_1M_CHARS_BRL = 0.0  # dentro do free tier até o limite abaixo
TTS_FREE_TIER_CHARS_MES = 1_000_000
CUSTO_STT_POR_MINUTO_BRL = 0.0  # Groq free/baixo custo — ajustar se mudar de plano
CUSTO_LLM_POR_1K_TOKENS_BRL = 0.015  # aproximação gpt-4o-mini/haiku, ajustar manualmente

VOICES_CATALOG_PATH = BASE_DIR / "backend" / "voices.json"

NIVEIS = ("A2", "B1", "B2")
