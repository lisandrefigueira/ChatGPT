"""Eleições sintéticas com verdade conhecida, para validar o código.

Nada aqui é dado real. Serve só para provar que cada método recupera o que
foi plantado (transições conhecidas, fraude injetada) antes de ser aplicado
aos boletins do TSE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

# Transição "verdadeira" de referência: linhas = 1º turno, colunas = 2º turno.
P_VERDADEIRA = np.array(
    [  # A     B    BN   ABS
        [0.93, 0.03, 0.02, 0.02],  # A
        [0.03, 0.92, 0.02, 0.03],  # B
        [0.40, 0.35, 0.15, 0.10],  # OUTROS
        [0.15, 0.15, 0.55, 0.15],  # BRANCO_NULO
        [0.05, 0.05, 0.02, 0.88],  # ABSTENCAO
    ]
)


def gerar(
    n_secoes: int = 40_000,
    semente: int = 1,
    heterogeneidade: float = 0.0,
    fraude_turno: int | None = None,
    fraude_cand: str = "V1",
    fi: float = 0.0,
    fe: float = 0.0,
) -> tuple[dict[int, pd.DataFrame], np.ndarray]:
    """Retorna ({1: df_1t, 2: df_2t}, P_media_verdadeira)."""
    rng = np.random.default_rng(semente)
    ufs = np.array([f"U{i:02d}" for i in range(27)])
    n_mun = max(n_secoes // 60, 30)
    mun_uf = rng.integers(0, 27, n_mun)
    mun = rng.integers(0, n_mun, n_secoes)
    uf = mun_uf[mun]
    aptos = np.clip(rng.normal(320, 70, n_secoes), 60, 600).astype(int)

    # Preferência regional (polarização como no Brasil) e comparecimento por UF.
    lean_uf = rng.normal(0, 0.8, 27)
    lean = lean_uf[uf] + rng.normal(0, 0.35, n_mun)[mun]
    comp = 1 / (1 + np.exp(-(rng.normal(1.4, 0.15, 27)[uf] + rng.normal(0, 0.2, n_secoes))))

    def multinom(n, p):
        """Multinomial vetorizada por binomiais condicionais sucessivas."""
        p = p / p.sum(1, keepdims=True)
        out = np.zeros(p.shape, int)
        resto = np.asarray(n, int).copy()
        massa = np.ones(len(p))
        for j in range(p.shape[1] - 1):
            q = np.clip(p[:, j] / np.maximum(massa, 1e-12), 0, 1)
            out[:, j] = rng.binomial(resto, q)
            resto -= out[:, j]
            massa -= p[:, j]
        out[:, -1] = resto
        return out

    votantes = rng.binomial(aptos, comp)
    pa = 1 / (1 + np.exp(-lean))
    pref = np.column_stack([0.85 * pa, 0.85 * (1 - pa), np.full(n_secoes, 0.10), np.full(n_secoes, 0.05)])
    r1 = multinom(votantes, pref)  # A, B, OUTROS, BN
    X = np.column_stack([r1, aptos - votantes])

    # Transição seção a seção (com heterogeneidade opcional por município).
    Y = np.zeros((n_secoes, 4), int)
    ruido = rng.normal(0, heterogeneidade, (n_mun, 5, 4)) if heterogeneidade else np.zeros((n_mun, 5, 4))
    for i in range(5):
        Pi = np.clip(P_VERDADEIRA[i][None, :] + ruido[mun, i, :], 1e-4, None)
        Y += multinom(X[:, i], Pi)
    P_media = np.zeros((5, 4))
    for i in range(5):
        Pi = np.clip(P_VERDADEIRA[i][None, :] + ruido[mun, i, :], 1e-4, None)
        Pi /= Pi.sum(1, keepdims=True)
        P_media[i] = (Pi * X[:, [i]]).sum(0) / X[:, i].sum()

    def tabela(cands: dict[str, np.ndarray], bn: np.ndarray, abst: np.ndarray) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "SG_UF": ufs[uf],
                "CD_MUNICIPIO": mun,
                "NR_ZONA": 1,
                "NR_SECAO": np.arange(n_secoes),
                "APTOS": aptos,
                "COMPARECIMENTO": aptos - abst,
                **cands,
                "BRANCOS": bn // 2,
                "NULOS": bn - bn // 2,
            }
        )
        return df

    t1 = tabela({"V1": X[:, 0], "V2": X[:, 1], "V3": X[:, 2]}, X[:, 3], X[:, 4])
    t2 = tabela({"V1": Y[:, 0], "V2": Y[:, 1]}, Y[:, 2], Y[:, 3])
    turnos = {1: t1, 2: t2}
    if fraude_turno:
        turnos[fraude_turno] = injetar_fraude(turnos[fraude_turno], fraude_cand, fi, fe, rng)
    return turnos, P_media


def injetar_fraude(df: pd.DataFrame, cand: str, fi: float, fe: float, rng) -> pd.DataFrame:
    """Enchimento de urna no estilo Klimek: abstenções e votos alheios viram votos de ``cand``."""
    df = df.copy()
    n = len(df)
    u = rng.random(n)
    x = np.zeros(n)
    inc, ext = u < fi, (u >= fi) & (u < fi + fe)
    x[inc] = np.clip(np.abs(rng.normal(0, 0.15, inc.sum())), 0, 1)
    x[ext] = np.clip(1 - np.abs(rng.normal(0, 0.03, ext.sum())), 0, 1)
    abst = df["APTOS"] - df["COMPARECIMENTO"]
    novos = np.floor(x * abst).astype(int)
    outros = [c for c in df.columns if c.startswith("V") and c != cand] + ["BRANCOS", "NULOS"]
    roubados = 0
    for c in outros:
        r = np.floor((x**2) * df[c]).astype(int)
        df[c] -= r
        roubados += r
    df[cand] += novos + roubados
    df["COMPARECIMENTO"] += novos
    return df
