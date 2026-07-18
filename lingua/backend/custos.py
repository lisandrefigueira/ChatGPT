"""Registro e estimativa de custos — append-only JSONL, sem banco de dados.

NOTA: a contagem de tokens de LLM é aproximada (chars/4), pois llm.chat() por
design (spec Agente 4) só retorna a string de resposta, não os campos de uso
específicos de cada provider. Suficiente para o alerta de orçamento pessoal.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import config


def registrar(tipo: str, quantidade: float) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    linha = {
        "data": datetime.now(timezone.utc).isoformat(),
        "tipo": tipo,
        "quantidade": quantidade,
    }
    with open(config.CUSTOS_LOG, "a") as f:
        f.write(json.dumps(linha) + "\n")


def resumo_mensal() -> dict:
    agora = datetime.now(timezone.utc)
    tts_chars = stt_seg = llm_tokens = 0.0

    if config.CUSTOS_LOG.exists():
        with open(config.CUSTOS_LOG) as f:
            for linha in f:
                try:
                    reg = json.loads(linha)
                    data = datetime.fromisoformat(reg["data"])
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
                if data.year != agora.year or data.month != agora.month:
                    continue
                if reg["tipo"] == "tts_chars":
                    tts_chars += reg["quantidade"]
                elif reg["tipo"] == "stt_segundos":
                    stt_seg += reg["quantidade"]
                elif reg["tipo"] == "llm_tokens":
                    llm_tokens += reg["quantidade"]

    estimativa = (
        (stt_seg / 60.0) * config.CUSTO_STT_POR_MINUTO_BRL
        + (llm_tokens / 1000.0) * config.CUSTO_LLM_POR_1K_TOKENS_BRL
        + (tts_chars / 1_000_000.0) * config.CUSTO_TTS_POR_1M_CHARS_BRL
    )
    return {
        "tts_chars_mes": int(tts_chars),
        "stt_segundos_mes": stt_seg,
        "llm_tokens_mes": int(llm_tokens),
        "estimativa_mensal_brl": round(estimativa, 2),
        "alerta_tts": tts_chars > 0.7 * config.TTS_FREE_TIER_CHARS_MES,
    }
