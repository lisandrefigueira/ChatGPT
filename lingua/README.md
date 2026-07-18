# Lingua

App pessoal de prática de inglês por conversação com IA (modo trilha
roteirizado + modo livre conversacional). Ver `ARCHITECTURE.md` para os
contratos técnicos entre módulos.

## Rodando localmente

```bash
cd lingua
cp .env.example .env   # preencha GROQ_API_KEY, OPENAI_API_KEY/ANTHROPIC_API_KEY,
                        # GOOGLE_APPLICATION_CREDENTIALS, APP_TOKEN
make install
make dev                # backend em :8000, frontend em :5173
```

Healthcheck: `curl http://localhost:8000/api/health` → `{"status":"ok"}`.

## Testes e validação

```bash
make test        # pytest do backend + validação das trilhas + build do frontend
make validar      # só as trilhas
```

## Deploy (DreamQuest / qualquer host com Docker)

```bash
cd lingua
cp .env.example .env   # preencha as credenciais
make deploy             # docker compose build && up -d
```

Acesso apenas via Tailscale; `deploy/lingua.service` mantém o container no
boot via systemd.

## Estrutura

Ver seção 3 da spec original / `ARCHITECTURE.md`.
