# Lingua — arquitetura

App pessoal (usuária única) de prática oral de inglês. Backend FastAPI +
frontend React PWA, servidos por um único processo/container. Ver a spec
completa na issue original para requisitos de produto; este documento cobre
apenas os contratos técnicos entre módulos.

## Visão geral

```
┌─────────────┐  MediaRecorder   ┌──────────────────────────┐
│  Frontend   │ ───────────────► │  POST /api/stt (Groq)    │
│  (PWA React)│                  └──────────────┬────────────┘
│             │                                 │ {text, words[]}
│             │   paralelo A (caminho crítico, ≤4s)
│             │ ─► POST /api/conversa (LLM) ─► POST /api/tts (Google) ─► toca áudio
│             │   paralelo B (assíncrono, ≤10s)
│             │ ─► POST /api/corrigir (LLM) ─► card de correção
│             │   paralelo C (modo trilha, local/instantâneo)
│             │ ─► POST /api/avaliar-pronuncia (g2p_en + rapidfuzz) ─► palavras coloridas
└─────────────┘
```

## Módulos do backend (`backend/`)

| Arquivo | Responsabilidade | I/O externo |
|---|---|---|
| `main.py` | rotas FastAPI, middleware de auth (`X-App-Token`), monta estáticos do frontend | — |
| `config.py` | única fonte de valores configuráveis (thresholds, paths, provider) | — |
| `schemas.py` | contratos Pydantic — espelhados manualmente em `frontend/src/types.ts` | — |
| `llm.py` | `chat(messages, system) -> str`, plugável openai/anthropic via `LLM_PROVIDER` | OpenAI ou Anthropic |
| `stt.py` | normaliza áudio (ffmpeg) e transcreve via Groq Whisper | Groq |
| `tts.py` | sintetiza voz via Google Cloud TTS, cache em disco por hash de conteúdo | Google Cloud |
| `pronuncia.py` | avaliação fonética pura (sem I/O), alinhamento simples + g2p_en + rapidfuzz | — |
| `custos.py` | log append-only (`data/custos.jsonl`) e estimativa mensal em BRL | — |

Prompts vivem em `backend/prompts/*.md` (nunca inline no código), com
placeholders `$variavel` (interpolados via `string.Template`).

## Trilhas (`trilhas/`)

Cada trilha é um JSON validado contra `schema.json` (ver `validar_trilhas.py`).
O backend carrega todos os arquivos do diretório em `/api/trilhas`. Não há
banco de dados para o conteúdo das trilhas — são arquivos versionados no repo.

## Frontend (`frontend/`)

Vite + React + TypeScript + Tailwind. Três telas (Home, Diálogo), estado
local/Context, sem Redux/router pesado. `src/api.ts` é o único ponto de
contato com o backend, tipado por `src/types.ts`.

## Persistência

- Conteúdo de trilhas: arquivos JSON no repo (não runtime).
- Cache de TTS: `data/tts_cache/*.mp3` (chave = hash de `text|voice_id|rate`).
- Custos: `data/custos.jsonl` (append-only, uma linha por evento cobrável).
- Histórico de sessões: `data/historico.sqlite` (reservado — não usado na v1;
  ver backlog).

Nada em `data/` é versionado (`.gitignore`).

## Auth

Token estático (`APP_TOKEN`) verificado em middleware para todo `/api/*`
exceto `/api/health`. Camada extra sobre o Tailscale — não é autenticação de
usuário (app de usuária única, sem contas).

## Deploy

Container único (`Dockerfile` multi-stage: build do frontend → cópia dos
estáticos para a imagem Python) exposto na porta 8000, orquestrado por
`docker-compose.yml` e mantido no boot via `deploy/lingua.service` (systemd).
Acesso externo apenas via Tailscale.

## Decisões que não devem ser revisitadas sem discussão explícita

Ver seção 6 da spec original (STT=Groq, TTS=Google Neural2, LLM plugável,
fonética local, SQLite, auth via Tailscale+token, 4 vozes fixas, correção em
canal separado).
