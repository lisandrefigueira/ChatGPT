"""Impressão digital eleitoral (Klimek, Yegorov, Hanel & Thurner, PNAS 2012).

Para cada seção: comparecimento t = comparecimento/aptos e votação
v = votos do candidato/comparecimento. Eleições limpas geram uma "nuvem"
aproximadamente unimodal; enchimento de urna gera uma cauda puxada para
(t, v) -> (1, 1). O modelo do artigo estima duas frações:

* f_i (fraude incremental): seções onde uma fração x de abstenções e de votos
  dos adversários foi convertida em votos do candidato;
* f_e (fraude extrema): seções onde quase tudo foi convertido.

O ajuste é feito por busca em grade, comparando o histograma 2D observado com
o simulado. Tudo é aplicado aos DOIS finalistas, simetricamente.

Ressalva importante para o Brasil: o voto é obrigatório e há forte
polarização regional, então a nuvem nacional pode ser bimodal sem fraude. Por
isso o ajuste é feito por UF (onde a hipótese de unimodalidade é mais
plausível) e, sobretudo, comparado com eleições anteriores.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

BINS = 50


def pontos(df: pd.DataFrame, cand: str) -> pd.DataFrame:
    d = df[df["APTOS"] >= config.MIN_APTOS_SECAO]
    d = d[d["COMPARECIMENTO"] > 0]
    return pd.DataFrame(
        {
            "SG_UF": d["SG_UF"].to_numpy(),
            "aptos": d["APTOS"].to_numpy(float),
            "t": (d["COMPARECIMENTO"] / d["APTOS"]).clip(0, 1).to_numpy(),
            "v": (d[cand] / d["COMPARECIMENTO"]).clip(0, 1).to_numpy(),
        }
    )


def metricas_descritivas(p: pd.DataFrame) -> dict[str, float]:
    ext = (p["t"] > config.LIMIAR_EXTREMO) & (p["v"] > config.LIMIAR_EXTREMO)
    return {
        "frac_secoes_extremas": float(ext.mean()),
        "corr_t_v": float(np.corrcoef(p["t"], p["v"])[0, 1]) if len(p) > 2 else np.nan,
        "frac_comparecimento_100": float((p["t"] >= 0.999).mean()),
    }


def _hist(t, v, w=None):
    """Histograma 2D normalizado (bincount: bem mais rápido que histogram2d)."""
    t = np.asarray(t)
    v = np.asarray(v)
    i = np.minimum((t * BINS).astype(int), BINS - 1)
    j = np.minimum((v * BINS).astype(int), BINS - 1)
    h = np.bincount(i * BINS + j, weights=w, minlength=BINS * BINS).reshape(BINS, BINS)
    return h / max(h.sum(), 1)


def _robusto(z):
    med = np.median(z)
    return med, 1.4826 * np.median(np.abs(z - med)) + 1e-6


def _sorteios(n, rng):
    return {k: rng.standard_normal(n) for k in ("t", "v", "x")} | {"u": rng.random(n)}


def _base_limpa(p: pd.DataFrame, s: dict) -> tuple:
    mt, st = _robusto(p["t"].to_numpy())
    mv, sv = _robusto(p["v"].to_numpy())
    return np.clip(mt + st * s["t"], 0, 1), np.clip(mv + sv * s["v"], 0, 1)


def simular(p: pd.DataFrame, fi: float, fe: float, rng=None, alpha: float = 2.0, sx: float = 0.075, sorteios=None, base=None) -> tuple:
    """Modelo do artigo: parte de uma distribuição 'limpa' e injeta fraude.

    Os parâmetros limpos (centro e dispersão) são estimados de forma robusta
    (mediana e MAD) no próprio dado. ``sorteios`` permite reutilizar os mesmos
    números aleatórios em toda a grade (números aleatórios comuns).
    """
    s = sorteios or _sorteios(len(p), rng)
    t, v = base if base is not None else _base_limpa(p, s)
    inc = s["u"] < fi
    ext = (s["u"] >= fi) & (s["u"] < fi + fe)
    ax = np.abs(sx * s["x"])
    x = np.where(inc, np.clip(ax, 0, 1), np.where(ext, np.clip(1 - ax, 0, 1), 0.0))
    votos = v * t
    novos_t = t + x * (1 - t)
    novos_votos = votos + x * (1 - t) + (x**alpha) * (t - votos)
    v2 = np.where(novos_t > 0, novos_votos / np.where(novos_t > 0, novos_t, 1), 0)
    return novos_t, np.clip(v2, 0, 1)


def ajustar_fraude(p: pd.DataFrame, rng=None, grade_fi=None, grade_fe=None) -> dict[str, float]:
    """Busca em grade de (f_i, f_e) minimizando a distância L2 entre histogramas."""
    rng = rng or np.random.default_rng(config.SEMENTE)
    grade_fi = np.linspace(0, 0.4, 21) if grade_fi is None else grade_fi
    grade_fe = np.linspace(0, 0.04, 21) if grade_fe is None else grade_fe
    obs = _hist(p["t"], p["v"])
    s = _sorteios(len(p), rng)
    base = _base_limpa(p, s)
    melhor = (np.inf, 0.0, 0.0)
    for fi in grade_fi:
        for fe in grade_fe:
            ts, vs = simular(p, fi, fe, sorteios=s, base=base)
            d = float(((obs - _hist(ts, vs)) ** 2).sum())
            if d < melhor[0]:
                melhor = (d, float(fi), float(fe))
    return {"fi": melhor[1], "fe": melhor[2], "dist": melhor[0]}


def ajustar_por_uf(p: pd.DataFrame, rng=None) -> pd.DataFrame:
    rng = rng or np.random.default_rng(config.SEMENTE)
    linhas = []
    for uf, g in p.groupby("SG_UF"):
        if len(g) < 200:
            continue
        r = ajustar_fraude(g, rng)
        linhas.append({"SG_UF": uf, "secoes": len(g), **r})
    return pd.DataFrame(linhas)


def figura(p: pd.DataFrame, titulo: str, caminho) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4.5))
    h = _hist(p["t"], p["v"])
    ax.imshow(
        np.log10(h.T + 1e-7), origin="lower", extent=[0, 1, 0, 1], aspect="auto", cmap="viridis", vmin=-6
    )
    ax.set_xlabel("comparecimento na seção")
    ax.set_ylabel("votação do candidato na seção")
    ax.set_title(titulo, fontsize=9)
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)
