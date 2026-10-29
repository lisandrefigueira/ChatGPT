"""Regras de decisão pré-registradas (ver PREREGISTRO.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

TODOS = "(ambos)"  # métricas que valem para o turno inteiro, não por candidato

# f_i (fraude incremental) fica só descritivo: ele é sensível à forma suposta
# para a distribuição "limpa" (normal), que o voto obrigatório e a
# polarização regional violam mesmo sem fraude.
# Família de cada métrica e a direção que seria suspeita.
#   "maior": só valores acima do histórico contam; "ambos": qualquer lado.
METRICAS = {
    "ei_frac_residuo_extremo": ("inferencia_ecologica", "maior"),
    "fp_frac_secoes_extremas": ("impressao_digital", "maior"),
    "fp_fe_ponderado": ("impressao_digital", "maior"),
    "2bl_media_2bl": ("digitos", "ambos"),
    "ult_frac_0_ou_5": ("digitos", "maior"),
    "pint_comp_razao_obs_esp": ("percentuais_inteiros", "maior"),
    "pint_voto_razao_obs_esp": ("percentuais_inteiros", "maior"),
}


def avaliar(tabela: pd.DataFrame, ano_alvo: int = config.ANO_ALVO) -> pd.DataFrame:
    """``tabela``: colunas ano, turno, candidato, metrica, valor, inf, sup.

    Para cada métrica do ano-alvo, monta o envelope das referências do mesmo
    turno (todos os finalistas, sem distinguir vencedor) e marca "destoa".
    """
    t = tabela.copy()
    t["inf"] = t["inf"].fillna(t["valor"])
    t["sup"] = t["sup"].fillna(t["valor"])
    alvo = t[t["ano"] == ano_alvo]
    ref = t[t["ano"] != ano_alvo]
    linhas = []
    for _, r in alvo.iterrows():
        if r["metrica"] not in METRICAS:
            continue
        familia, direcao = METRICAS[r["metrica"]]
        R = ref[(ref["metrica"] == r["metrica"]) & (ref["turno"] == r["turno"])]
        if R.empty or not np.isfinite(r["valor"]):
            status, lo, hi = "sem_referencia", np.nan, np.nan
        else:
            lo, hi = R["inf"].min(), R["sup"].max()
            m = config.MARGEM_ENVELOPE * max(hi - lo, 1e-12)
            acima, abaixo = r["inf"] > hi + m, r["sup"] < lo - m
            if acima or (abaixo and direcao == "ambos"):
                status = "destoa"
            elif abaixo:
                status = "abaixo_do_historico"  # não suspeito nesta direção
            else:
                status = "dentro_do_historico"
        linhas.append({**r.to_dict(), "familia": familia, "ref_min": lo, "ref_max": hi, "status": status})
    return pd.DataFrame(linhas)


def conclusao(av: pd.DataFrame) -> pd.DataFrame:
    """Aplica a regra de convergência entre famílias, por candidato e turno."""
    out = []
    for (turno, cand), g in av.groupby(["turno", "candidato"]):
        if cand == TODOS:
            continue
        fams = sorted(g.loc[g["status"] == "destoa", "familia"].unique())
        # A inferência ecológica é por turno, não por candidato: entra em ambos.
        ei = av[(av["turno"] == turno) & (av["familia"] == "inferencia_ecologica") & (av["status"] == "destoa")]
        if len(ei) and "inferencia_ecologica" not in fams:
            fams.append("inferencia_ecologica")
        n = len(fams)
        if n >= config.MIN_FAMILIAS_CONVERGENTES:
            veredito = "padrao atipico convergente: exige auditoria localizada (nao e prova de fraude)"
        elif n == 1:
            veredito = "sinal isolado: insuficiente pela regra pre-registrada; investigar causa local"
        else:
            veredito = "sem anomalia em relacao ao historico brasileiro"
        out.append({"turno": turno, "candidato": cand, "familias_destoantes": ", ".join(fams), "n": n, "veredito": veredito})
    return pd.DataFrame(out)
