"""Validação dos métodos com verdade conhecida (dados sintéticos)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eleicoes import comparar, forense, inferencia, sintetico  # noqa: E402
from eleicoes import impressao_digital as fp  # noqa: E402


def test_goodman_recupera_transicao_homogenea():
    turnos, P = sintetico.gerar(n_secoes=20_000, semente=3)
    tab = inferencia.tabelas_transicao(turnos[1], turnos[2], ["V1", "V2"])
    est = inferencia.goodman_restrito(tab)["P"].to_numpy()
    assert np.abs(est - P)[:2].max() < 0.02  # fluxos dos finalistas
    assert np.allclose(est.sum(1), 1)


def test_local_e_lphom_com_heterogeneidade():
    turnos, P = sintetico.gerar(n_secoes=12_000, semente=4, heterogeneidade=0.03)
    tab = inferencia.tabelas_transicao(turnos[1], turnos[2], ["V1", "V2"])
    loc = inferencia.goodman_local(tab)["P"].to_numpy()
    assert np.abs(loc - P)[:2].max() < 0.03
    mun = inferencia.goodman_local(tab, grupo=("SG_UF", "CD_MUNICIPIO"))["P"].to_numpy()
    assert np.allclose(mun.sum(axis=1), 1)
    sub = tab[tab["SG_UF"] == "U00"]
    lp = inferencia.lphom(sub).to_numpy()
    assert np.allclose(lp.sum(1), 1, atol=1e-6) and (lp >= -1e-9).all()


def test_limites_sem_modelo_sao_coerentes():
    turnos, _ = sintetico.gerar(n_secoes=5_000, semente=5)
    tab = inferencia.tabelas_transicao(turnos[1], turnos[2], ["V1", "V2"])
    lim = inferencia.limites_deterministicos(tab)
    assert (lim["fluxo_A_para_B_min"].dropna() <= lim["fluxo_A_para_B_max"].dropna()).all()
    assert (lim["perda_liquida_minima"] <= lim["votos_1t"]).all()


def test_simplex():
    V = np.random.default_rng(0).normal(size=(100, 5))
    P = inferencia._projetar_simplex(V)
    assert np.allclose(P.sum(1), 1) and (P >= 0).all()


def test_benford_segundo_digito():
    assert abs(forense.MEDIA_BENFORD_2 - 4.187) < 1e-3
    assert np.isclose(forense.BENFORD_2.sum(), 1)
    assert list(forense.segundo_digito(np.array([10, 123, 4567, 99]))) == [0, 2, 5, 9]


def test_impressao_digital_detecta_fraude_plantada():
    limpo, _ = sintetico.gerar(n_secoes=15_000, semente=6)
    sujo, _ = sintetico.gerar(n_secoes=15_000, semente=6, fraude_turno=2, fraude_cand="V1", fi=0.0, fe=0.03)
    pl, ps = fp.pontos(limpo[2], "V1"), fp.pontos(sujo[2], "V1")
    assert fp.metricas_descritivas(ps)["frac_secoes_extremas"] > 10 * max(fp.metricas_descritivas(pl)["frac_secoes_extremas"], 1e-4)
    g = pl[pl["SG_UF"] == "U01"]
    h = ps[ps["SG_UF"] == "U01"]
    assert fp.ajustar_fraude(h)["fe"] > fp.ajustar_fraude(g)["fe"]


def test_percentuais_inteiros_detecta_numeros_fabricados():
    rng = np.random.default_rng(0)
    den = rng.integers(100, 500, 20_000)
    num = rng.binomial(den, 0.6)
    limpo = forense.percentuais_inteiros(num, den, n_sim=30)
    fab = num.copy()
    k = 2_000
    fab[:k] = (den[:k] * 0.6).astype(int)
    fab[:k] = np.where((den[:k] * 60) % 100 == 0, den[:k] * 60 // 100, fab[:k])
    den2 = den.copy()
    den2[:k] = 200  # 120/200 = 60% exato
    fab[:k] = 120
    sujo = forense.percentuais_inteiros(fab, den2, n_sim=30)
    assert abs(limpo["z"]) < 4
    assert sujo["z"] > 10


def test_regra_pre_registrada():
    linhas = []
    for ano in (2014, 2018, 2022):
        for c in ("A", "B"):
            linhas.append({"ano": ano, "turno": 2, "candidato": c, "metrica": "fp_frac_secoes_extremas", "valor": 0.001 * ano / 2000, "inf": np.nan, "sup": np.nan})
            linhas.append({"ano": ano, "turno": 2, "candidato": c, "metrica": "pint_voto_razao_obs_esp", "valor": 1.0, "inf": np.nan, "sup": np.nan})
    linhas.append({"ano": 2026, "turno": 2, "candidato": "A", "metrica": "fp_frac_secoes_extremas", "valor": 0.05, "inf": np.nan, "sup": np.nan})
    linhas.append({"ano": 2026, "turno": 2, "candidato": "A", "metrica": "pint_voto_razao_obs_esp", "valor": 1.5, "inf": np.nan, "sup": np.nan})
    linhas.append({"ano": 2026, "turno": 2, "candidato": "B", "metrica": "fp_frac_secoes_extremas", "valor": 0.0005, "inf": np.nan, "sup": np.nan})
    av = comparar.avaliar(pd.DataFrame(linhas), 2026)
    c = comparar.conclusao(av).set_index("candidato")
    assert c.loc["A", "n"] == 2 and "convergente" in c.loc["A", "veredito"]
    assert c.loc["B", "n"] == 0  # abaixo do histórico não é suspeito
