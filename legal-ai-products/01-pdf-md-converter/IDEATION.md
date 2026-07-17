# Conversor PDF→Markdown Jurídico Local

> Classificação: 🟢 Quick win — construir primeiro (esforço baixo, impacto alto)

## Contexto (não precisa reler a conversa original)

Este projeto nasceu da análise de 4.492 mensagens de uma comunidade fechada de
juristas brasileiros usando IA generativa (dez/2025–jul/2026). O relatório completo
está em `../_docs/relatorio-mercado.html` — abra-o para ver todas as citações e dados
com data/hora exatas.

## Problema

As duas maiores dores da comunidade (rankeadas por volume de reclamação/persistência):

1. **Janela de contexto e consumo imprevisível de tokens** (dor #1) — planos padrão de
   IA (ex.: Claude web) travam em ~200k tokens; cada novo PDF gigante consome cota
   rapidamente; usuários não sabem quanto de cota resta.
2. **Limites de arquivo e processos volumosos** (dor #4) — Claude limita a ~30–50MB/
   poucas dezenas de arquivos e sofre com PDFs de imagem; ChatGPT falha em arquivos de
   200–230 páginas mesmo fracionados; documentos manuscritos/escaneados exigem OCR
   prévio.

A comunidade já converge organicamente para ferramentas de terceiros (Docling,
pdf.ai, CloudConvert, iLovePDF) só para cortar tokens antes de subir processos — mas
sem garantia sobre planilhas, imagens ou trechos manuscritos, e com dúvida recorrente
sobre segurança de conversores online (upload de peças sigilosas para serviço
desconhecido).

### Evidência (citações do chat)

- 04/02/2026 13:57 — *"Claude suporta poucos arquivos. Junto algumas peças e peço para
  fazer uma petição e aparece mensagem com excesso de arquivos [...] Até cinquenta
  megas. Limita muito."*
- 07/04, 18/06, 19/05, 09/07/2026 — *"Uso o projeto do Docling [...] uma das melhores
  ferramentas para transformar em markdown."*
- 03/04/2026 12:23 — *"Surreal!!! O Claude acabou. Uma Ferrari na garagem que não
  conseguimos usar. Já voltei para Chatgpt."*

## Público-alvo

Advogado autônomo / pequeno escritório — dor mais aguda, ciclo de decisão de compra
rápido (não depende de aprovação institucional).

## Modelo de negócio

SaaS de assinatura baixa, ou freemium com limite de páginas/mês. Processamento
**local/desktop**, sem enviar conteúdo à nuvem — isso resolve simultaneamente a dor
de sigilo profissional/LGPD documentada na Camada 5 do relatório (vazamento de
metadados encontrado em auditoria do concorrente ConectaIA).

## Diferencial vs. concorrência (Docling, pdf.ai, CloudConvert)

- Preservar tabelas, carimbos de processo e anotações manuscritas — exatamente onde a
  comunidade relata perda de conteúdo hoje.
- Contador de "tokens economizados" como gancho de marketing/onboarding.
- Garantia de processamento 100% local (auditável) como diferencial de confiança
  jurídica.

## MVP sugerido

App desktop (ou extensão de navegador) que:
1. Recebe PDF de processo judicial (potencialmente centenas de páginas, com imagens
   escaneadas/anexos).
2. Converte para Markdown preservando estrutura de autos (numeração de páginas,
   seções, tabelas).
3. Mostra estimativa de tokens antes/depois da conversão.
4. Roda 100% local — nenhum dado sai da máquina do usuário.

## Próximos passos (para a sessão de desenvolvimento)

- [ ] Validar stack técnica (Docling como base open-source vs. build from scratch)
- [ ] Testar com PDFs reais de processo (incl. escaneados/manuscritos) — avaliar OCR
- [ ] Definir modelo de precificação (freemium por páginas/mês vs. assinatura fixa)
- [ ] Protótipo de UI mínima (drag-and-drop → markdown + relatório de tokens)
