"""Pydantic models — fonte de verdade dos contratos de API.

`frontend/src/types.ts` espelha estes tipos manualmente (projeto pequeno,
sem geração de código — simplicidade primeiro).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Banda = Literal["verde", "amarelo", "vermelho", "cinza"]
Nivel = Literal["A2", "B1", "B2"]
Role = Literal["user", "assistant"]


class Health(BaseModel):
    status: str = "ok"


# ---------------------------------------------------------------------------
# STT
# ---------------------------------------------------------------------------
class WordTiming(BaseModel):
    word: str
    start: float
    end: float
    confidence: float | None = None


class STTResponse(BaseModel):
    text: str
    words: list[WordTiming]
    duration: float


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    voice_id: str
    slow: bool = False


# ---------------------------------------------------------------------------
# Conversa (modo livre)
# ---------------------------------------------------------------------------
class Mensagem(BaseModel):
    role: Role
    content: str


class PersonaConfig(BaseModel):
    nome: str
    papel: str
    voz: str
    estilo: str


class ConversaRequest(BaseModel):
    mensagens: list[Mensagem]
    persona: PersonaConfig
    nivel: Nivel = "B1"


class ConversaResponse(BaseModel):
    resposta: str


class CorrigirRequest(BaseModel):
    fala: str
    contexto: list[Mensagem] = []


class CorrigirResponse(BaseModel):
    tem_erro: bool
    original: str
    sugestao: str | None = None
    explicacao_pt: str | None = None


# ---------------------------------------------------------------------------
# Pronúncia
# ---------------------------------------------------------------------------
class PalavraAvaliada(BaseModel):
    palavra: str
    esperada: str
    banda: Banda
    score: float | None = None


class AvaliarPronunciaRequest(BaseModel):
    esperado: str
    transcrito: str


class AvaliarPronunciaResponse(BaseModel):
    palavras: list[PalavraAvaliada]


# ---------------------------------------------------------------------------
# Custos
# ---------------------------------------------------------------------------
class CustosResponse(BaseModel):
    tts_chars_mes: int
    stt_segundos_mes: float
    llm_tokens_mes: int
    estimativa_mensal_brl: float
    alerta_tts: bool


# ---------------------------------------------------------------------------
# Trilhas
# ---------------------------------------------------------------------------
class Persona(BaseModel):
    nome: str
    papel: str
    voz: str
    estilo: str


class No(BaseModel):
    id: str
    fala_ia: str
    resposta_alvo: str
    alternativas_aceitas: list[str] = []
    dica_pt: str
    proximo: dict[str, str]


class Trilha(BaseModel):
    id: str
    titulo: str
    nivel: Nivel
    persona: Persona
    vocabulario_alvo: list[str]
    nos: list[No]
    modo_livre_seed: str
