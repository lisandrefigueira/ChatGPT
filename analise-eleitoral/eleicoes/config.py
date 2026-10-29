"""Parâmetros fixados ANTES de olhar os dados de 2026 (ver PREREGISTRO.md).

Alterar qualquer valor deste arquivo depois de ver os resultados invalida o
pré-registro: registre a mudança e o motivo no histórico do git.
"""

# Eleição sob análise e eleições de referência (mesmo cargo: Presidente).
ANO_ALVO = 2026
ANOS_REFERENCIA = (2014, 2018, 2022)
CD_CARGO_PRESIDENTE = 1

# Fontes abertas do TSE (Portal de Dados Abertos / CDN). Os modelos de URL
# podem mudar; os arquivos também podem ser baixados à mão e colocados em
# --dados (ver README).
URL_VOTACAO_SECAO = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/"
    "votacao_secao_{ano}_BR.zip"
)
URL_DETALHE_SECAO = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/"
    "detalhe_votacao_secao_{ano}.zip"
)

# Códigos de "votável" especiais no TSE.
NR_BRANCO = 95
NR_NULO = 96
NR_ANULADO = 97  # voto anulado e apurado em separado: tratado como nulo

# Chave de seção.
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]

# --- Regras de decisão pré-registradas -----------------------------------
SEMENTE = 20261025
N_BOOTSTRAP = 200
NIVEL_IC = 0.95
# Uma métrica de 2026 só "destoa" se o seu IC não tocar o envelope formado
# pelos ICs das eleições de referência (mesmo turno), alargado por esta
# margem relativa à amplitude do envelope.
MARGEM_ENVELOPE = 0.10
# Conclusão "padrão compatível com fraude" exige destoar em pelo menos este
# número de famílias de testes independentes (EI, impressão digital, dígitos,
# percentuais inteiros).
MIN_FAMILIAS_CONVERGENTES = 2

# Seções pequenas geram proporções extremas por puro acaso.
MIN_APTOS_SECAO = 50
# Teste do 2º dígito (2BL) só em contagens >= 10; último dígito em >= 100.
MIN_VOTOS_2BL = 10
MIN_VOTOS_ULTIMO_DIGITO = 100
# Inferência ecológica local: municípios com ao menos este número de seções.
MIN_SECOES_MUNICIPIO = 10
# Impressão digital: limiar de "comparecimento e votação quase totais".
LIMIAR_EXTREMO = 0.95
