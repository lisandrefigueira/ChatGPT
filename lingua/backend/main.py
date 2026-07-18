"""Lingua — backend FastAPI. Serviço único: API + estáticos do build do frontend."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from string import Template

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

import config
import custos
import llm
import pronuncia
import stt
import tts
from schemas import (
    AvaliarPronunciaRequest,
    AvaliarPronunciaResponse,
    ConversaRequest,
    ConversaResponse,
    CorrigirRequest,
    CorrigirResponse,
    CustosResponse,
    Health,
    Mensagem,
    STTResponse,
    TTSRequest,
    Trilha,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lingua.main")

app = FastAPI(title="Lingua API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPTS_DIR = Path(__file__).parent / "prompts"


@app.middleware("http")
async def autenticar(request: Request, call_next):
    caminho = request.url.path
    protegido = caminho.startswith("/api") and caminho != "/api/health"
    if protegido and config.APP_TOKEN:
        if request.headers.get("x-app-token") != config.APP_TOKEN:
            return JSONResponse(status_code=401, content={"detail": "token inválido ou ausente"})
    return await call_next(request)


@app.get("/api/health", response_model=Health)
def health():
    return Health()


# ---------------------------------------------------------------------------
# STT
# ---------------------------------------------------------------------------
@app.post("/api/stt", response_model=STTResponse)
async def api_stt(audio: UploadFile):
    conteudo = await audio.read()
    resultado = stt.transcrever(conteudo, audio.content_type or "audio/webm")
    custos.registrar("stt_segundos", resultado.duration)
    return resultado


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
@app.post("/api/tts")
def api_tts(req: TTSRequest):
    mp3_bytes, veio_do_cache = tts.sintetizar(req.text, req.voice_id, req.slow)
    if not veio_do_cache:
        custos.registrar("tts_chars", len(req.text))
    return Response(content=mp3_bytes, media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# Conversa (modo livre) + correção assíncrona
# ---------------------------------------------------------------------------
def _aproximar_tokens(*textos: str) -> float:
    return sum(len(t) for t in textos) / 4.0


@app.post("/api/conversa", response_model=ConversaResponse)
def api_conversa(req: ConversaRequest):
    template = Template((PROMPTS_DIR / "persona_base.md").read_text())
    system = template.substitute(
        nome=req.persona.nome,
        papel=req.persona.papel,
        estilo=req.persona.estilo,
        nivel=req.nivel,
        contexto="",
    )
    resposta = llm.chat(req.mensagens, system)
    entrada = "\n".join(m.content for m in req.mensagens)
    custos.registrar("llm_tokens", _aproximar_tokens(system, entrada, resposta))
    return ConversaResponse(resposta=resposta)


@app.post("/api/corrigir", response_model=CorrigirResponse)
def api_corrigir(req: CorrigirRequest):
    template = Template((PROMPTS_DIR / "corretor.md").read_text())
    contexto_txt = "\n".join(f"{m.role}: {m.content}" for m in req.contexto)
    system = template.substitute(nivel="B1", contexto=contexto_txt)
    bruto = llm.chat([Mensagem(role="user", content=req.fala)], system)
    custos.registrar("llm_tokens", _aproximar_tokens(system, req.fala, bruto))

    try:
        dados = json.loads(bruto.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        return CorrigirResponse(**dados)
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning("corretor: resposta não-JSON do LLM, assumindo sem erro: %r", bruto[:200])
        return CorrigirResponse(tem_erro=False, original=req.fala)


# ---------------------------------------------------------------------------
# Pronúncia (avaliação local, sem chamada externa)
# ---------------------------------------------------------------------------
@app.post("/api/avaliar-pronuncia", response_model=AvaliarPronunciaResponse)
def api_avaliar_pronuncia(req: AvaliarPronunciaRequest):
    palavras = pronuncia.avaliar(req.esperado, req.transcrito)
    return AvaliarPronunciaResponse(palavras=palavras)


# ---------------------------------------------------------------------------
# Trilhas
# ---------------------------------------------------------------------------
def _carregar_trilhas() -> list[Trilha]:
    trilhas = []
    for caminho in sorted(config.TRILHAS_DIR.glob("*.json")):
        if caminho.name == "schema.json":
            continue
        trilhas.append(Trilha(**json.loads(caminho.read_text())))
    return trilhas


@app.get("/api/trilhas", response_model=list[Trilha])
def api_trilhas():
    return _carregar_trilhas()


@app.get("/api/trilhas/{trilha_id}", response_model=Trilha)
def api_trilha(trilha_id: str):
    for t in _carregar_trilhas():
        if t.id == trilha_id:
            return t
    raise HTTPException(status_code=404, detail="trilha não encontrada")


# ---------------------------------------------------------------------------
# Custos
# ---------------------------------------------------------------------------
@app.get("/api/custos", response_model=CustosResponse)
def api_custos():
    return custos.resumo_mensal()


# ---------------------------------------------------------------------------
# Estáticos do frontend (build de produção) — montado por último para não
# sombrear as rotas /api/*.
# ---------------------------------------------------------------------------
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
