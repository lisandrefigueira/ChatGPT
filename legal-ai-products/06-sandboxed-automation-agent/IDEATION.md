# Agente de Automação com Sandbox Nativo

> Classificação: 🔴 Bet grande, nicho técnico (esforço alto, impacto médio/alto)

## Contexto (não precisa reler a conversa original)

Este projeto nasceu da análise de 4.492 mensagens de uma comunidade fechada de
juristas brasileiros usando IA generativa (dez/2025–jul/2026). O relatório completo
está em `../_docs/relatorio-mercado.html` — abra-o para ver todas as citações e dados
com data/hora exatas.

## Problema

O **OpenClaw** (ex-Clawbot/Moltbot) provou apetite real por um agente pessoal
autônomo 24h via WhatsApp/Telegram: baixa processos do Eproc/PJe, monitora redes
sociais, e-mail, agenda, notícias jurídicas, publica conteúdo. Descrito pelo próprio
professor da comunidade como algo que "mudou a minha rotina". Mas a comunidade teve
que **improvisar isolamento por conta própria** (alugar uma VM dedicada, ~R$45–50/mês)
diante do risco real de o agente apagar arquivos se rodado localmente.

### Evidência (citações do chat)

- 29/01, 18/02/2026 — *"não é recomendado instalá-la no computador de uso pessoal
  [...] pode acabar apagando arquivos."*
- Renomeado 3× por notificação de marca da Anthropic — sinal de que o produto opera em
  zona cinzenta de compliance com provedores de IA.
- Roda sobre a assinatura já existente de Claude/GPT/Gemini (sem token extra — até
  mudança de cobrança em abr/2026), o que barateou a adoção inicial mas depois
  encareceu.

## Público-alvo

Advogados/escritórios tech-forward — nicho menor que os demais produtos deste
portfólio, mas com apetite de uso já comprovado dentro da própria comunidade.

## Modelo de negócio

SaaS com infraestrutura gerenciada: sandbox incluso no preço, eliminando a fricção
(e o custo variável) da VM própria que os usuários hoje pagam à parte. Ticket mais
alto que os demais produtos do portfólio, porque embute custo real de infraestrutura.

## Diferencial vs. OpenClaw

- Sandbox e permissões granulares **nativas** desde o design (não uma VM alugada por
  fora) — mitigando o risco de exclusão acidental de arquivos que motivou o alerta da
  própria comunidade.
- Clareza de compliance com os termos dos provedores de IA (evitar o problema de
  renomeações forçadas por notificação de marca que o OpenClaw sofreu).
- Modelo de cobrança transparente desde o início (não sujeito a mudanças abruptas como
  a que tornou o OpenClaw inviável no plano de R$100).

## MVP sugerido

1. Agente com escopo restrito inicial (ex.: apenas baixa de processos + notificação de
   movimentação — sem acesso de escrita/exclusão no filesystem do usuário).
2. Execução em sandbox gerenciado pelo próprio produto (containers isolados por
   usuário), não na máquina pessoal do cliente.
3. Sistema de permissões explícito e auditável (o usuário aprova cada categoria de
   ação: leitura de processo, envio de notificação, publicação de conteúdo, etc.).

## Próximos passos (para a sessão de desenvolvimento)

- [ ] Definir escopo mínimo de automações do MVP (priorizar monitoramento de processos
      sobre publicação de conteúdo, que é mais arriscado)
- [ ] Desenhar modelo de permissões granulares e sandbox por usuário
- [ ] Avaliar termos de uso dos provedores de IA (Anthropic/OpenAI/Google) para evitar
      o problema de marca que afetou o OpenClaw
- [ ] Modelar custo de infraestrutura gerenciada no pricing (ticket mais alto que os
      demais produtos do portfólio)
