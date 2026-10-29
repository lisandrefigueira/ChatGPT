# Análise eleitoral com dados abertos do TSE (por seção)

Roteiro científico e replicável para duas perguntas sobre a eleição
presidencial de 2026:

1. **Quantos eleitores trocaram de lado entre o 1º e o 2º turno?** Isso se
   estima por inferência ecológica, seção a seção.
2. **Os números de 2026 destoam do padrão histórico brasileiro?** Isso se testa
   com a impressão digital eleitoral (Klimek et al., PNAS 2012), a forense de
   dígitos (linha de Mebane) e o teste de percentuais inteiros (Kobak et al.,
   2016). Os mesmos métodos são aplicados a 2014, 2018 e 2022 como referência.

As regras de decisão estão em [`PREREGISTRO.md`](PREREGISTRO.md) e foram
fixadas antes da leitura dos dados de 2026. A imparcialidade não depende de
escolher a fonte "certa". Ela vem de três coisas: dados públicos, regras
definidas antes de ver o resultado e um cálculo que qualquer pessoa pode
refazer. Nenhuma regra usa nome ou partido: os finalistas viram "A" e "B" pela
ordem do número de urna, e todo teste é aplicado aos dois.

## Como rodar

```bash
pip install -r requirements.txt
python -m pytest -q tests                     # valida os métodos com verdade conhecida
python rodar_analise.py --saida resultados    # baixa os dados do TSE e roda tudo
python rodar_analise.py --lphom ...           # inclui o estimador por programação linear (mais lento)
```

O script baixa do CDN do TSE, para a pasta `dados_tse/`, os arquivos abaixo
(um par por ano: 2014, 2018, 2022 e 2026):

* `votacao_secao_{ano}_BR.zip`
* `detalhe_votacao_secao_{ano}.zip`

Se o download automático falhar porque o TSE mudou a URL ou bloqueou a rede,
baixe os arquivos à mão em <https://dadosabertos.tse.jus.br>, nos conjuntos
"Resultados" de cada ano, coloque-os em `dados_tse/` e rode com
`--sem-download`. Os arquivos de 2026 só existem depois que o TSE os publica.

`python rodar_analise.py --sintetico --saida demo` roda o pipeline inteiro
sobre eleições **fictícias**, com fraude plantada no "2026" fictício. Serve só
para conferir que os testes detectam o que foi plantado. Não é resultado real.

## O que sai em `resultados/`

| Arquivo | Conteúdo |
|---|---|
| `RELATORIO.md` | veredito pela regra pré-registrada, conferência com os totais oficiais, matrizes de transição, comparação com o histórico e figuras |
| `{ano}_transicao_*.csv` | matriz 1º → 2º turno (proporções), com IC 95% quando há bootstrap |
| `{ano}_eleitores_*.csv` | a mesma matriz em número de eleitores |
| `{ano}_limites_sem_modelo.csv` | pisos e tetos que valem sem modelo nenhum (Duncan-Davis, perda líquida mínima) |
| `{ano}_t{turno}_{A,B}_impressao.png` | impressão digital (comparecimento × votação por seção) |
| `{ano}_t{turno}_{A,B}_fraude_klimek_por_uf.csv` | f_i e f_e estimados em cada UF |
| `metricas.csv`, `avaliacao_pre_registrada.csv`, `conclusao.csv` | todas as métricas, a comparação com o envelope histórico e o veredito |

## Métodos em uma linha cada

* **Goodman restrito** (`inferencia.goodman_restrito`): regressão de
  Goodman ponderada pelo eleitorado, com probabilidades em [0, 1] e linhas
  somando 1. É resolvida exatamente por gradiente projetado. O IC vem de
  bootstrap de Poisson sobre as seções.
* **Goodman local** (`goodman_local`): o mesmo ajuste dentro de cada UF,
  agregado depois. Reduz o viés de agregação causado pela polarização
  regional. É a estimativa principal da taxa de troca. A versão por
  município (`goodman_municipal`) é só sensibilidade: na validação
  sintética, ela superestimou fluxos pequenos.
* **LPHOM** (`lphom`): programação linear que minimiza desvios absolutos
  (Romero, Pavía, Martín & Romero, 2020), com os municípios como unidade.
  Serve de checagem de robustez.
* **Limites determinísticos** (`limites_deterministicos`): pisos e tetos que
  valem sem modelo nenhum.
* **Impressão digital** (`impressao_digital`): histograma 2D e o modelo de
  fraude incremental e extrema de Klimek et al., ajustado por UF.
* **Dígitos** (`forense`): 2º dígito de Benford (média esperada de 4,187) e
  último dígito.
* **Percentuais inteiros** (`forense.percentuais_inteiros`): excesso de
  seções em percentuais exatos, contra um nulo binomial que preserva o
  denominador de cada seção.

## Limites que precisam constar em qualquer conclusão

* A inferência ecológica estima fluxos médios. Ela não identifica indivíduos e
  depende de os padrões de transição serem parecidos dentro de cada
  município. Por isso o relatório mostra três estimadores e os limites sem
  modelo.
* Com cerca de 470 mil seções, qualquer teste de aderência "rejeita". A
  leitura é sempre comparativa (2026 contra 2014, 2018 e 2022), nunca pelo
  p-valor isolado.
* Desvios no 2º dígito aparecem também com comportamento estratégico normal
  (Mebane). Um sinal isolado não basta: a regra exige duas famílias
  independentes, e mesmo assim o resultado só indica **onde auditar**.
* Voto obrigatório, polarização regional e seções atípicas (aldeias, presídios,
  exterior) mudam a forma da "nuvem" sem fraude nenhuma. É por isso que a
  comparação com o próprio histórico brasileiro é a referência.

## Validação com verdade conhecida (dados sintéticos)

Antes de tocar em dado real, o pipeline foi rodado sobre eleições fictícias
com 40 mil seções, polarização regional e transições conhecidas:

| Cenário | Resultado da regra pré-registrada |
|---|---|
| "2026" fictício **com** enchimento de urna plantado no 2º turno para A (f_i = 10%, f_e = 2%) | 2º turno, A: "padrão atípico convergente" (impressão digital + inferência ecológica). Nos demais casos não houve sinal, exceto a inferência ecológica, que vale para o turno inteiro e por isso aparece também em B |
| "2026" fictício **sem** fraude (controle negativo) | nenhuma família destoa, nos dois turnos e para os dois candidatos |

Na inferência ecológica, a taxa de troca direta verdadeira era de cerca de
3,0%. O estimador local por UF deu entre 2,8% e 3,6% nos quatro cenários
fictícios, e o LPHOM ficou perto de 2,9%. O intervalo de confiança cobre só o
erro amostral, não o viés de agregação, e em alguns cenários não incluiu o
valor verdadeiro. Por isso os três estimadores são apresentados lado a lado.
