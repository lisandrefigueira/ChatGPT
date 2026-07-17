# Legal AI Products — Portfólio de Prospecção

Esta pasta reúne os produtos de LegalTech identificados a partir da mineração de dados
de uma comunidade fechada de juristas (advogados, defensores, promotores, procuradores
e magistrados) usando IA generativa na rotina forense brasileira — 4.492 mensagens,
7,5 meses (dez/2025–jul/2026), 173 autores.

Cada subpasta é um projeto independente, pensado para ser desenvolvido em uma
**conversa separada do Claude Code**. Todo projeto contém um `IDEATION.md`
autocontido — não é necessário reler esta conversa para começar: basta abrir
uma nova sessão na pasta do projeto e apontar para o `IDEATION.md`.

## Documentação compartilhada (`_docs/`)

- `relatorio-mercado.html` — relatório completo de inteligência de mercado (5 camadas:
  ferramentas, dores, subáreas do direito, product discovery, segurança/compliance).
  Abrir no navegador. É a fonte primária de evidência (citações, dados, datas) para
  todos os projetos abaixo.

## Projetos (ordenados por prioridade — esforço × impacto)

| Pasta | Produto | Esforço | Impacto |
|---|---|---|---|
| `01-pdf-md-converter/` | Conversor PDF→Markdown jurídico local | Baixo | Alto |
| `02-writing-style-skill/` | Skill de estilo de escrita produtizada | Baixo/Médio | Alto |
| `03-prompt-injection-firewall/` | Firewall de prompt injection (compliance-as-a-service) | Médio | Alto (institucional) |
| `04-jurisprudence-citation-engine/` | Motor de jurisprudência com citação verificável | Médio | Alto |
| `05-court-integration-layer/` | Camada de integração universal PJe/Eproc/SEI/SEEU | Alto | Muito alto |
| `06-sandboxed-automation-agent/` | Agente de automação com sandbox nativo | Alto | Médio/Alto |

## Sequenciamento recomendado

1. Começar por `01` (menor esforço, dor mais universal — funciona como cavalo de troia
   para base de usuários).
2. Em paralelo, `03` — a janela regulatória (Resolução CNJ 615/2025) está aberta agora;
   quem entrar cedo com produto de compliance pronto tem vantagem de posicionamento
   institucional.
3. Usar a base de usuários dos dois primeiros para validar apetite de pagamento antes
   de atacar `04`–`06`, que exigem mais capital/parcerias (dados oficiais de tribunal,
   infraestrutura de scraping, etc.).
