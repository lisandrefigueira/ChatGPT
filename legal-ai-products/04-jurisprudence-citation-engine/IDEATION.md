# Motor de Jurisprudência com Citação Verificável (Anti-Alucinação)

> Classificação: 🟡 Aposta de médio prazo (esforço médio, impacto alto)

## Contexto (não precisa reler a conversa original)

Este projeto nasceu da análise de 4.492 mensagens de uma comunidade fechada de
juristas brasileiros usando IA generativa (dez/2025–jul/2026). O relatório completo
está em `../_docs/relatorio-mercado.html` — abra-o para ver todas as citações e dados
com data/hora exatas.

## Problema

Dor #2 do ranking geral (por volume/persistência): **alucinação de jurisprudência e
fatos processuais**. Modelos "cientes" sem acesso a base real de jurisprudência
inventam ementas plausíveis; agregadores herdam a alucinação do modelo-base; até o
JusBrasil sinaliza internamente decisões sem procedência confirmada. Risco disciplinar
direto — citar jurisprudência falsa em petição.

### Evidência (citações do chat)

- 06/03/2026 08:54 — *"6 jurisprudências fornecidas, todas 6 falsas."*
- 16/07/2026 — *"Não se sabe mais o q é verdade e o q não é."*
- 16/07/2026 — sobre um robô interno do professor: *"Não Alucina porque cai direito no
  site do STF e STJ."*

## Ferramentas já validando a demanda no mercado

- **JusRatio** — citado como "extremamente superior" ao JusBrasil; acesso via **MCP**
  dentro do Claude; cobra ~R$19/mês (plano anual). Ainda sem cobertura de todos os
  tribunais (só STF/STJ).
- **JusIA (Jusbrasil)** — gratuito para assinantes Jusbrasil, mas admite internamente
  não confirmar procedência de algumas decisões citadas.

## Público-alvo

Ambos (privado e público), mas monetiza melhor em advogados/escritórios — JusRatio já
prova disposição de pagamento (~R$19/mês) com boa avaliação.

## Modelo de negócio

SaaS + distribuição via **MCP** — canal já validado pelo mercado (JusRatio roda dentro
do Claude Code/Desktop). Expansão natural: cobrir tribunais estaduais além de
STF/STJ, que é exatamente o gap que o JusRatio ainda tem hoje.

## Por que esforço médio (não baixo)

A parte difícil não é a camada de IA — é o pipeline de obtenção de dados oficiais
(scraping ou parceria com fonte de jurisprudência por tribunal), o mesmo obstáculo
técnico do projeto `05-court-integration-layer`. Ver seção "Datajud" no relatório
completo: uma tentativa da própria comunidade de usar a API pública do CNJ foi
abandonada por estar "muito desatualizada e dependente da boa vontade dos tribunais".

## MVP sugerido

1. Motor de busca de jurisprudência que **só retorna decisões com link direto e
   verificável** à fonte oficial (STF/STJ como ponto de partida, replicando a lógica
   do "robô que não alucina" do professor).
2. Distribuição inicial via MCP server (integração direta com Claude).
3. Expansão incremental por tribunal, priorizando os TJs/TRFs mais citados pela
   comunidade-alvo.

## Próximos passos (para a sessão de desenvolvimento)

- [ ] Avaliar parceria/licenciamento de dados vs. scraping direto por tribunal
- [ ] Prototipar MCP server mínimo com STF/STJ apenas
- [ ] Definir critério de "verificabilidade" (link direto + hash/checagem de
      procedência)
- [ ] Estudar posicionamento vs. JusRatio (concorrência direta ou complementar)
