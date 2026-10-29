# Pré-registro da análise — eleição presidencial de 2026

**Data de registro:** 29/10/2026. A data e o conteúdo ficam fixados pelo commit
no git. Este documento foi escrito **antes** de qualquer leitura dos boletins
por seção de 2026, e o código que o implementa (`eleicoes/config.py` e
`eleicoes/comparar.py`) está no mesmo commit.

## 1. Pergunta

Os resultados por seção da eleição presidencial de 2026 (1º e 2º turnos)
apresentam padrões estatísticos que **destoam do histórico brasileiro**
(2014, 2018 e 2022), medidos pelos mesmos métodos? E, em separado: quantos
eleitores de cada grupo do 1º turno foram para cada opção no 2º turno?

## 2. O que esta análise não faz

* Não "prova" fraude nem lisura. Um teste estatístico só mostra se os números
  são compatíveis com processos conhecidos. A integridade de uma eleição se
  verifica por auditoria: teste de integridade das urnas, conferência dos
  boletins impressos com os publicados, código-fonte e logs.
* Não usa totais nacionais para inferir migração de votos. Totais não
  identificam quem migrou.
* Não usa nome, partido nem resultado dos candidatos nas regras. Os finalistas
  são rotulados A e B pela ordem do número de urna, e todo teste é aplicado
  aos dois.

## 3. Dados

* `votacao_secao_{ano}_BR.zip` e `detalhe_votacao_secao_{ano}.zip`, do Portal
  de Dados Abertos do TSE. Cargo: Presidente (código 1). Inclui o exterior
  (UF "ZZ").
* Unidade de análise: a seção eleitoral, identificada por UF, município, zona e
  seção. Entre os turnos, as seções são pareadas por essa chave.
* Conferência obrigatória antes de qualquer teste: os totais somados por seção
  precisam bater com os totais oficiais divulgados pelo TSE. O relatório traz
  essa tabela. Divergência acima de 0,1% suspende a análise daquele ano.
* Exclusões fixadas: seções com menos de 50 aptos ficam fora dos testes de
  proporção, porque proporções extremas nelas surgem por acaso; o 2º dígito
  só se calcula em contagens a partir de 10; o último dígito, a partir de 100.

## 4. Métodos (fixados)

| Família | Método | Referência | Métrica usada na regra | Direção suspeita |
|---|---|---|---|---|
| Inferência ecológica | Goodman com restrições lógicas (global e por município), LP de Romero et al. e limites de Duncan-Davis | Goodman (1953); Romero et al. (2020, *Sociol. Methods Res.*); Duncan & Davis (1953) | fração de seções com resíduo absoluto acima de 0,15 (1º turno → 2º turno; IC de Wilson) | maior |
| Impressão digital | histograma 2D comparecimento × votação; modelo de fraude incremental (f_i) e extrema (f_e) ajustado por UF | Klimek et al. (2012, *PNAS* 109:16469) | fração de seções com comparecimento > 95% e votação > 95% (IC de Wilson); f_e médio ponderado por seções (IC por reamostragem das UFs). O f_i é só descritivo, porque depende da forma suposta para a distribuição "limpa" | maior |
| Dígitos | 2º dígito de Benford (2BL) e último dígito | Mebane (2006, 2011); Beber & Scacco (2012, *Polit. Anal.*) | média do 2º dígito; fração de últimos dígitos 0 ou 5 | ambos / maior |
| Percentuais inteiros | excesso de seções em percentuais exatos, contra um nulo binomial simulado | Kobak, Shpilkin & Pshenichnikov (2016, *Ann. Appl. Stat.*) | razão observado/esperado (comparecimento e votação) | maior |

A taxa de troca direta de lado (A→B mais B→A) e a matriz de transição
completa são **descritivas**: respondem quantos eleitores trocaram de lado, mas
não entram na regra de anomalia, porque mudar de voto entre turnos é
comportamento legítimo.

## 5. Regra de decisão (fixada)

1. Para cada métrica, turno e finalista de 2026, calcula-se o valor e, quando
   houver, o intervalo de confiança de 95% por bootstrap (200 réplicas,
   semente 20261025).
2. O envelope de referência é o intervalo entre o menor limite inferior e o
   maior limite superior da mesma métrica no mesmo turno, considerando os dois
   finalistas de 2014, 2018 e 2022. Ele é alargado em 10% da própria amplitude.
3. A métrica **destoa** quando o intervalo de 2026 fica inteiramente fora do
   envelope, na direção suspeita.
4. Veredito por finalista e turno:
   * nenhuma família destoa: "sem anomalia em relação ao histórico brasileiro";
   * uma família destoa: "sinal isolado, insuficiente; investigar a causa local";
   * duas ou mais famílias independentes destoam: "padrão atípico convergente;
     exige auditoria localizada". Mesmo esse resultado **não é prova de
     fraude**: ele aponta onde auditar.
   A família de inferência ecológica mede o turno inteiro (a passagem do 1º
   para o 2º turno), então conta para os dois finalistas do 2º turno.
5. Qualquer sinal leva a uma análise por UF (as tabelas `*_por_uf.csv`), para
   localizar a origem e checar explicações conhecidas: aldeias indígenas,
   seções em presídios, seções agregadas e mudanças de zoneamento.

## 6. Desvios do plano

Qualquer mudança neste arquivo ou em `config.py` depois da leitura dos dados
de 2026 deve ser feita em commit próprio, com a justificativa. O relatório
apresenta o resultado pela regra original e, se for o caso, também pela regra
alterada.
