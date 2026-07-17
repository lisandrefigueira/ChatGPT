# Skill de Estilo de Escrita Produtizada

> Classificação: 🟢 Quick win (esforço baixo/médio, impacto alto)

## Contexto (não precisa reler a conversa original)

Este projeto nasceu da análise de 4.492 mensagens de uma comunidade fechada de
juristas brasileiros usando IA generativa (dez/2025–jul/2026). O relatório completo
está em `../_docs/relatorio-mercado.html` — abra-o para ver todas as citações e dados
com data/hora exatas.

## Problema

Fluxo caseiro repetido dentro da comunidade: alimentar a IA com 300–1.000 peças
próprias do advogado para gerar um perfil de escrita/raciocínio jurídico, depois
convertido manualmente em "skill" do Claude ou "conhecimento"/custom GPT do ChatGPT.
Hoje esse processo é **100% manual** e depende de um tutorial informal do professor
da comunidade — não existe produto que empacote esse fluxo.

### Evidência (citações do chat)

- 18/03, 06/04, 10/06, 18/06/2026 — *"Ficou excelente [...] a qualidade do
  peticionamento é infinitamente melhor."*
- O relatório completo (Camada 1) também documenta que Claude é citado como
  "imbatível em qualidade de redação jurídica" e que o Cowork (repositórios de
  700–1.400 arquivos) é visto como divisor de águas — o produto aqui reduz a fricção
  de configurar esse ambiente.

## Público-alvo

Advogados/escritórios que já têm acervo digital de peças próprias — early adopters
naturais são a própria comunidade de origem (curso "IA na Prática Jurídica").

## Modelo de negócio

- SaaS self-service: cobrança única de "treinamento" do perfil + assinatura de
  manutenção/atualização.
- Alternativa/complemento: distribuição como marketplace via MCP/plugin dentro do
  Claude ou ChatGPT — aproveitando o canal de distribuição que já está emergindo
  organicamente na comunidade (JusRatio já roda via MCP dentro do Claude).

## MVP sugerido

Wizard de upload que:
1. Recebe lote de peças próprias do advogado (PDF/DOCX).
2. Extrai padrões de estilo, estrutura de argumentação, vocabulário recorrente.
3. Gera automaticamente um arquivo de skill/knowledge pronto para colar em Claude
   Project ou Custom GPT (ou, versão avançada, publica direto via API/MCP).
4. Permite refinamento incremental (adicionar novas peças, revisar perfil gerado).

## Próximos passos (para a sessão de desenvolvimento)

- [ ] Mapear formato exato de "skill" do Claude e "knowledge" do ChatGPT/Custom GPT
      para automação da geração
- [ ] Definir pipeline de extração de estilo (prompt engineering vs. fine-tuning leve)
- [ ] Validar com um pequeno grupo de beta testers da comunidade de origem
- [ ] Explorar integração via MCP como canal de distribuição nativo
