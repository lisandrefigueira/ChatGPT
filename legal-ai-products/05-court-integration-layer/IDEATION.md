# Camada de Integração Universal PJe/Eproc/SEI/SEEU

> Classificação: 🔴 Bet grande — mas é o "santo graal" (esforço alto, impacto muito
> alto)

## Contexto (não precisa reler a conversa original)

Este projeto nasceu da análise de 4.492 mensagens de uma comunidade fechada de
juristas brasileiros usando IA generativa (dez/2025–jul/2026). O relatório completo
está em `../_docs/relatorio-mercado.html` — abra-o para ver todas as citações e dados
com data/hora exatas.

## Problema

Dor #3 do ranking geral, de natureza **estrutural**: fragmentação dos sistemas
processuais. Cada tribunal roda uma versão diferente do mesmo sistema (PJe, Eproc,
Projudi, SEEU), quebrando extensões de integração de forma inconsistente; proteção
Cloudflare bloqueia scraping automatizado tribunal a tribunal; o Projudi (Goiás)
sequer é suportado pelas ferramentas atuais.

### Evidência (citações do chat)

- 15/02/2026 19:25 — *"Aqui no TJGO tem proteção via cloudfire então a IA não
  consegue passar... a infraestrutura para conseguir isso fica bem cara."*
- 16/07/2026 20:01 — *"Alguma dica de site ou programa que acessa o PJE para leitura
  diária de processos? [...] média de 1500 processos por Defensor."*

## Sinal de mercado já validado (e seus limites)

O **ConectaIA** ("Direito Hub") já validou a demanda — extensão que conecta
Eproc/PJe/SEI/SEEU direto a Claude/Gemini/ChatGPT/Adapta/Perplexity/JusIA, eliminando
baixa/upload manual, com adoção rápida e plano anual "vendido sozinho". Mas expôs os
problemas reais de um produto assim:
- Instabilidade por versão de tribunal.
- Falso positivo de antivírus (trojan).
- Bugs de envio.
- **Vazamento de metadados em log** — auditoria técnica independente encontrou, em
  `error-log.js/sendReport()`, número CNJ do processo, URL, tribunal, fingerprint do
  navegador e até **nome do arquivo** (ex.: "laudo psicossocial.pdf") sendo enviados a
  um Supabase de telemetria — suficiente para reconstruir a categoria do processo em
  varas de família, infância/juventude ou violência doméstica (29/04/2026).

## Público-alvo

Recomendação: focar primeiro em **servidores públicos/defensores** — a dor mais
dramática documentada é o defensor com 1.500 processos/gabinete sem forma viável de
monitorar movimentações diárias, o que sugere venda institucional para
Defensorias/Procuradorias.

## Modelo de negócio

- Enterprise/institucional: contrato com o tribunal/órgão, não com o usuário final —
  ideal a longo prazo dado o tamanho do problema.
- Alternativa de entrada mais realista: replicar o modelo do ConectaIA (freemium +
  plano anual acessível), mas com **telemetria auditável desde o dia 1** — resolvendo
  de cara o problema de vazamento de metadados que o concorrente teve.

## MVP sugerido

1. Começar por **um único tribunal/sistema** (ex.: Eproc, citado como "mais estável"
   pela comunidade) para provar o conceito antes de generalizar.
2. Camada de extração 100% local/client-side (processamento no dispositivo do
   usuário, nada de conteúdo saindo para servidor de terceiros).
3. Log de telemetria mínimo, auditável e documentado publicamente (diferencial de
   confiança vs. ConectaIA).

## Próximos passos (para a sessão de desenvolvimento)

- [ ] Escolher tribunal/sistema piloto (Eproc parece o ponto de entrada mais estável
      segundo os relatos da comunidade)
- [ ] Estudar tecnicamente o bloqueio Cloudflare por tribunal e alternativas legítimas
      de acesso (ex.: API oficial vs. automação de navegador)
- [ ] Desenhar arquitetura 100% local desde o início (aprender com a falha de
      auditoria do ConectaIA)
- [ ] Mapear Defensorias/Procuradorias como primeiros prospects institucionais
