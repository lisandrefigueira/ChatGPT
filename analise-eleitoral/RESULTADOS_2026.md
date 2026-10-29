# Resultados — eleição presidencial de 2026, por seção

Execução em 29/10/2026 com os arquivos abertos do TSE (`votacao_secao` e
`detalhe_votacao_secao`, publicados em 26/10/2026), seguindo as regras de
`PREREGISTRO.md`. Para reproduzir: `python rodar_analise.py --saida resultados`.
As tabelas completas estão em `resultados/`.

Finalistas, rotulados pela ordem do número de urna: **A = 13** e **B = 22**.

## 1. Conferência dos dados

| | 1º turno | 2º turno |
|---|---:|---:|
| Seções | 499.206 | 499.205 |
| Aptos | 158.745.007 | 158.744.977 |
| Comparecimento | 125.275.835 | 128.236.074 |
| Brancos + nulos | 5.969.801 | 4.153.801 |
| A (13) | 53.879.538 (45,16% dos válidos) | 64.256.232 (51,79%) |
| B (22) | 56.104.503 (47,03%) | 59.826.041 (48,21%) |
| Demais candidatos | 9.321.993 | — |

* Em todas as seções, os votos apurados somam exatamente o comparecimento.
* Nenhuma seção tem comparecimento maior que o número de aptos.
* 499.205 seções foram pareadas entre os turnos.
* Os mesmos procedimentos reproduzem exatamente os totais oficiais de 2022:
  13 com 57.259.504 e 60.345.999; 22 com 51.072.345 e 58.206.354.

## 2. Veredito pela regra pré-registrada

| Turno | Candidato | Famílias que destoam do histórico (2014–2022) | Veredito |
|---|---|---|---|
| 1º | A (13) | percentuais inteiros | sinal isolado; insuficiente pela regra |
| 1º | B (22) | nenhuma | sem anomalia em relação ao histórico |
| 2º | A (13) | nenhuma | sem anomalia em relação ao histórico |
| 2º | B (22) | nenhuma | sem anomalia em relação ao histórico |

Nenhum candidato, em nenhum turno, chega às duas famílias convergentes que a
regra exige para pedir auditoria localizada.

**O sinal isolado.** No 1º turno, a votação de A cai em percentuais inteiros
2,2% mais vezes do que o esperado (razão de 1,022; z ≈ 3,1). O teto
histórico dessa razão é 1,016. Esse valor entrou na regra sem intervalo de
confiança. Por UF, o excesso é difuso: o maior z é 2,6, no Paraná, e nenhuma UF
concentra o efeito. Isso é compatível com flutuação estatística entre 28 UFs
e não com números fabricados num lugar específico.

## 3. Comparação com o histórico, métrica a métrica

| Métrica | 2014 | 2018 | 2022 | **2026** |
|---|---|---|---|---|
| Seções com comparecimento e votação > 95%, 2º turno, A | 0,0042% | 0,0042% | 0,0038% | **0,0082%** (41 seções) |
| Idem, 2º turno, B | 0 | 0 | 0 | **0,0004%** (2 seções) |
| f_e de Klimek (fraude extrema), 2º turno, A / B | 0,05% / 0,06% | 0,13% / 0,09% | 0,07% / 0,03% | **0,05% / 0,07%** |
| Média do 2º dígito (Benford = 4,187), 2º turno, A / B | 3,97 / 4,03 | 4,04 / 4,18 | 3,85 / 4,07 | **3,86 / 3,97** |
| Últimos dígitos 0 ou 5 (esperado = 20%), 2º turno, A / B | 20,4% / 20,4% | 20,6% / 20,3% | 20,5% / 20,4% | **20,4% / 20,3%** |
| Seções com resíduo extremo na transição 1º→2º | 0,48% | 0,59% | 0,14% | **0,25%** |

* As 41 seções "extremas" de A no 2º turno são, em geral, seções pequenas da
  zona rural do Norte e do Nordeste: 10 no MA, 6 na BA, 6 no PA, 5 no CE, 4 no
  AM. É o perfil que já aparecia nos anos anteriores, com 18 a 19 seções. O
  número dobrou, mas segue dentro do envelope pela margem pré-registrada: o
  limite inferior do IC de 2026 é 0,0061%, contra o teto histórico de
  0,0066%. Essa é a métrica mais perto do limite e a primeira a examinar em
  campo.
* As impressões digitais do 2º turno (`resultados/painel_impressoes_2turno.png`)
  têm o mesmo formato das de 2014 a 2022. Não há cauda puxada para
  (100%, 100%), que é a assinatura de enchimento de urna no trabalho de Klimek
  et al.

## 4. Quem migrou do 1º para o 2º turno (inferência ecológica)

Estimador principal: Goodman restrito por UF, com IC de 95% por bootstrap de
200 réplicas. Os números estão em milhões de eleitores.

| 1º turno ↓ / 2º turno → | A (13) | B (22) | Branco/nulo | Abstenção |
|---|---:|---:|---:|---:|
| A (13) — 53,9 | **53,27** | 0,00 | 0,09 | 0,52 |
| B (22) — 56,1 | 0,09 | **55,45** | 0,17 | 0,40 |
| Demais candidatos — 9,3 | 3,95 | 3,56 | 1,36 | 0,45 |
| Branco/nulo — 6,0 | 3,75 | 0,08 | 2,11 | 0,03 |
| Abstenção — 33,5 | 3,19 | 0,80 | 0,39 | 29,09 |

**Troca direta de lado** (A→B mais B→A): 0,08% dos eleitores dos dois
finalistas, cerca de 93 mil pessoas, com IC de 0,08% a 0,10%. É da mesma
ordem de 2014 (0,21%), 2018 (0,02%) e 2022 (0,002%). Na prática, quase
ninguém trocou de lado.

**A virada (B liderou o 1º turno, A venceu o 2º) não exige troca de lado.**
O ganho de A entre os turnos, de 10,4 milhões, veio de três fontes:
* eleitores dos demais candidatos: cerca de 3,9 milhões;
* quem votou branco ou nulo no 1º turno: cerca de 3,8 milhões;
* quem se absteve no 1º turno e votou no 2º: cerca de 3,2 milhões.

B ganhou 3,7 milhões, quase só dos demais candidatos. Isso também fecha com a
conta simples, sem modelo nenhum:
* o comparecimento subiu 2,96 milhões;
* brancos e nulos caíram 1,82 milhão;
* os demais candidatos somavam 9,32 milhões;
* juntos, esses grupos formam 14,1 milhões, que é exatamente a soma dos ganhos
  de A e B.

**Robustez.** Três estimadores diferentes concordam no essencial:
* Goodman global e Goodman municipal: troca direta inferior a 1%;
* LPHOM por município: troca direta igual a zero;
* nos três, os demais candidatos se dividem de forma parecida entre A e B, e
  brancos/nulos e novos votantes pendem para A.

**O ponto mais atípico, para leitura cuidadosa.** A estima que 57% a 70% de
quem anulou ou votou branco no 1º turno votou em A no 2º. Em 2022, essa
proporção foi de 16%; em 2014, de 44%. A seção a seção, a fatia de
brancos/nulos no 1º turno se correlaciona com o ganho de A (r = 0,46), mas
não com o de B (r = 0,03). O padrão aparece em todas as UFs, não numa só. É
uma inferência ecológica: ela mostra que A ganhou mais onde havia mais
brancos e nulos, mas não prova que foram os mesmos eleitores. Esse dado é
descritivo e, pela regra fixada, não é indicador de fraude.

**Fatos sem modelo (limites de Duncan-Davis).**
* Pelo menos 383 mil eleitores de B no 1º turno não repetiram o voto em B, ou
  foram substituídos por outros eleitores na mesma seção.
* Para A, esse piso é de 59 mil.

## 5. Conclusão

* Pelos métodos e regras fixados antes de ver os dados, os números por seção de
  2026 **não destoam do padrão brasileiro de 2014, 2018 e 2022** em nenhum
  candidato e em nenhum turno.
* Houve um único sinal isolado: percentuais inteiros no 1º turno de A. Ele é
  difuso entre as UFs e está abaixo do critério de convergência.
* A mudança de liderança entre os turnos se explica pela redistribuição dos
  votos dos demais candidatos, dos brancos/nulos e de quem não votou no 1º
  turno, e não por migração direta entre os finalistas.

Como em toda análise estatística, isso **não prova lisura**. Mostra que os
números são compatíveis com os processos observados nas eleições anteriores e
que nenhuma assinatura conhecida de fraude aparece. A verificação da
integridade cabe à auditoria:
* teste de integridade das urnas;
* conferência dos boletins impressos com os publicados;
* inspeção do código-fonte e dos logs.

Um bom ponto de partida para essa conferência são as 43 seções extremas do
2º turno (41 de A e 2 de B), listadas em
`resultados/2026_t2_secoes_extremas.csv`.
