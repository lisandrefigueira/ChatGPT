"""Forense eleitoral por dígitos e proporções.

* 2BL — teste do segundo dígito de Benford sobre a contagem de votos por seção
  (Mebane, 2006; 2011). Referência: média do 2º dígito = 4,187.
* Último dígito — deve ser aproximadamente uniforme em contagens grandes
  (Beber & Scacco, 2012, *Political Analysis*).
* Percentuais inteiros — excesso de seções com comparecimento ou votação
  exatamente em percentuais redondos, sinal de números "fabricados"
  (Kobak, Shpilkin & Pshenichnikov, 2016, *Annals of Applied Statistics*).

Com centenas de milhares de seções, qualquer qui-quadrado "rejeita". Por isso
a leitura é sempre comparativa: o mesmo número calculado em eleições
anteriores do próprio Brasil é a referência (ver PREREGISTRO.md). Mebane
também alerta que desvios no 2BL surgem de comportamento estratégico normal,
não só de fraude.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

_K = np.arange(1, 10)
BENFORD_2 = np.array([np.log10(1 + 1 / (10 * _K + d)).sum() for d in range(10)])
MEDIA_BENFORD_2 = float((np.arange(10) * BENFORD_2).sum())  # 4,187


def segundo_digito(n: np.ndarray) -> np.ndarray:
    n = n[n >= config.MIN_VOTOS_2BL].astype(np.int64)
    ordem = np.floor(np.log10(n)).astype(int)
    return (n // 10 ** (ordem - 1)) % 10


def teste_2bl(votos: np.ndarray, n_boot: int = 0, rng=None) -> dict[str, float]:
    d = segundo_digito(np.asarray(votos))
    if len(d) == 0:
        return {"n": 0, "media_2bl": np.nan, "desvio_media": np.nan, "chi2_por_obs": np.nan}
    obs = np.bincount(d, minlength=10)
    esp = BENFORD_2 * len(d)
    res = {
        "n": int(len(d)),
        "media_2bl": float(d.mean()),
        "desvio_media": float(d.mean() - MEDIA_BENFORD_2),
        "chi2_por_obs": float(((obs - esp) ** 2 / esp).sum() / len(d)),
    }
    if n_boot:
        rng = rng or np.random.default_rng(config.SEMENTE)
        medias = [rng.choice(d, len(d)).mean() for _ in range(n_boot)]
        res["media_2bl_inf"], res["media_2bl_sup"] = map(float, _quantis(medias))
    return res


def teste_ultimo_digito(votos: np.ndarray) -> dict[str, float]:
    v = np.asarray(votos)
    v = v[v >= config.MIN_VOTOS_ULTIMO_DIGITO].astype(np.int64)
    if len(v) == 0:
        return {"n": 0, "chi2_por_obs": np.nan, "frac_0_ou_5": np.nan}
    obs = np.bincount(v % 10, minlength=10)
    esp = len(v) / 10
    return {
        "n": int(len(v)),
        "chi2_por_obs": float(((obs - esp) ** 2 / esp).sum() / len(v)),
        "frac_0_ou_5": float((obs[0] + obs[5]) / len(v)),  # esperado 0,20
    }


def percentuais_inteiros(num: np.ndarray, den: np.ndarray, n_sim: int = 100, rng=None) -> dict[str, float]:
    """Excesso de razões que caem exatamente em percentual inteiro (1% a 99%).

    O valor esperado depende só dos denominadores; ele é obtido por simulação
    binomial que preserva o denominador e a proporção de cada seção.
    """
    rng = rng or np.random.default_rng(config.SEMENTE)
    num = np.asarray(num, np.int64)
    den = np.asarray(den, np.int64)
    ok = den >= config.MIN_APTOS_SECAO
    num, den = num[ok], den[ok]

    def conta(nm):
        inteiro = (nm * 100) % den == 0
        borda = (nm == 0) | (nm == den)
        return int((inteiro & ~borda).sum())

    obs = conta(num)
    p = np.clip(num / den, 0, 1)
    sims = np.array([conta(rng.binomial(den, p)) for _ in range(n_sim)])
    dp = sims.std(ddof=1) or 1.0
    return {
        "n": int(len(den)),
        "observado": obs,
        "esperado": float(sims.mean()),
        "razao_obs_esp": float(obs / sims.mean()) if sims.mean() else np.nan,
        "z": float((obs - sims.mean()) / dp),
    }


def bateria(df: pd.DataFrame, cand: str, n_boot: int = 0, rng=None) -> dict[str, float]:
    """Todos os testes de dígitos/proporções para um candidato num turno."""
    rng = rng or np.random.default_rng(config.SEMENTE)
    v = df[cand].to_numpy()
    out = {}
    out.update({f"2bl_{k}": x for k, x in teste_2bl(v, n_boot, rng).items()})
    out.update({f"ult_{k}": x for k, x in teste_ultimo_digito(v).items()})
    pc = percentuais_inteiros(df["COMPARECIMENTO"], df["APTOS"], rng=rng)
    pv = percentuais_inteiros(df[cand], df["COMPARECIMENTO"], rng=rng)
    out.update({f"pint_comp_{k}": x for k, x in pc.items()})
    out.update({f"pint_voto_{k}": x for k, x in pv.items()})
    return out


def _quantis(x):
    a = (1 - config.NIVEL_IC) / 2
    return np.quantile(x, [a, 1 - a])
