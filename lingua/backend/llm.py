"""Abstração mínima sobre o provider de LLM — sem framework de agentes.

Uma única função pública: chat(messages, system) -> str.
"""
from __future__ import annotations

import config
from schemas import Mensagem


def chat(messages: list[Mensagem], system: str) -> str:
    if config.LLM_PROVIDER == "anthropic":
        return _chat_anthropic(messages, system)
    return _chat_openai(messages, system)


def _chat_openai(messages: list[Mensagem], system: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "system", "content": system}]
        + [{"role": m.role, "content": m.content} for m in messages],
        max_tokens=300,
    )
    return resp.choices[0].message.content or ""


def _chat_anthropic(messages: list[Mensagem], system: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        system=system,
        messages=[{"role": m.role, "content": m.content} for m in messages],
        max_tokens=300,
    )
    return "".join(block.text for block in resp.content if block.type == "text")
