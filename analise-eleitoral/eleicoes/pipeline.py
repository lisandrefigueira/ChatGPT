"""Executa a análise completa para um conjunto de eleições e grava o relatório."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import comparar, config, forense, inferencia
from . import impressao_digital as fp
from .dados import checar_consistencia, finalistas


def _wilson(k: float, n: int) -> tuple[float, float]:
    """IC de Wilson para uma proporção k/n (vale também quando k = 0)."""
    if n == 0:
        return np.nan, np.nan
    z = 1.959963984540054
    ph = k / n
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    m = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(c - m, 0.0), min(c + m, 1.0)


def _media_uf_bootstrap(por_uf: pd.DataFrame, col: str, n_boot: int, rng) -> tuple[float, float, float]:
    """Média ponderada pelo nº de seções, com IC por reamostragem das UFs."""
    w = por_uf["secoes"].to_numpy(float)
    x = por_uf[col].to_numpy(float)
    val = float((w * x).sum() / w.sum())
    if not n_boot or len(x) < 2:
        return val, np.nan, np.nan
    idx = rng.integers(0, len(x), (n_boot, len(x)))
    b = (w[idx] * x[idx]).sum(1) / w[idx].sum(1)
    lo, hi = np.quantile(b, [(1 - config.NIVEL_IC) / 2, (1 + config.NIVEL_IC) / 2])
    return val, float(lo), float(hi)


def _linha(ano, turno, cand, metrica, valor, inf=np.nan, sup=np.nan):
    return {"ano": ano, "turno": turno, "candidato": cand, "metrica": metrica, "valor": valor, "inf": inf, "sup": sup}


def analisar_ano(ano: int, turnos: dict[int, pd.DataFrame], saida: Path, n_boot: int, usar_lphom: bool) -> tuple[list, dict]:
    rng = np.random.default_rng(config.SEMENTE + ano)
    fin = finalistas(turnos)
    rot = dict(zip(fin, ["A", "B"]))
    metr, extra = [], {"finalistas": {rot[c]: c for c in fin}, "consistencia": {}}
    for turno, df in turnos.items():
        extra["consistencia"][turno] = checar_consistencia(df)

    # 1. Inferência ecológica (só existe com 2º turno).
    if 2 in turnos:
        tab = inferencia.tabelas_transicao(turnos[1], turnos[2], fin)
        extra["secoes_pareadas"] = {"t1": len(turnos[1]), "t2": len(turnos[2]), "pareadas": len(tab)}
        g = inferencia.goodman_restrito(tab, n_boot=n_boot, rng=rng)
        loc = inferencia.goodman_local(tab, n_boot=n_boot, rng=rng)
        mun = inferencia.goodman_local(tab, grupo=("SG_UF", "CD_MUNICIPIO"))
        ei = {"goodman_global": g, "goodman_local": loc, "goodman_municipal": mun}
        if usar_lphom:
            fl = sum(inferencia.migracao(inferencia.lphom(gu), gu) for _, gu in tab.groupby("SG_UF"))
            ei["lphom_por_uf"] = {"P": fl.div(fl.sum(axis=1), axis=0)}
        for nome, r in ei.items():
            r["P"].to_csv(saida / f"{ano}_transicao_{nome}.csv", float_format="%.4f")
            inferencia.migracao(r["P"], tab).round(0).to_csv(saida / f"{ano}_eleitores_{nome}.csv")
            if "P_inf" in r:
                r["P_inf"].to_csv(saida / f"{ano}_transicao_{nome}_ic_inf.csv", float_format="%.4f")
                r["P_sup"].to_csv(saida / f"{ano}_transicao_{nome}_ic_sup.csv", float_format="%.4f")
        inferencia.limites_deterministicos(tab).to_csv(saida / f"{ano}_limites_sem_modelo.csv", float_format="%.0f")

        # Troca direta de lado (A->B e B->A) como fração dos eleitores dos finalistas.
        def troca(P):
            xa, xb = tab["X_A"].sum(), tab["X_B"].sum()
            return (P.loc["A", "B"] * xa + P.loc["B", "A"] * xb) / (xa + xb)

        pl = loc["P"]
        lo = hi = np.nan
        if "P_boot" in loc:
            tb = [troca(pd.DataFrame(b, index=pl.index, columns=pl.columns)) for b in loc["P_boot"]]
            lo, hi = np.quantile(tb, [(1 - config.NIVEL_IC) / 2, (1 + config.NIVEL_IC) / 2])
        metr.append(_linha(ano, 2, comparar.TODOS, "ei_taxa_troca_direta", troca(pl), lo, hi))

        # Resíduo extremo: seções cujo 2º turno é muito diferente do previsto pelo 1º.
        x, y, w, _ = inferencia._matrizes(tab)
        res = np.abs(y - x @ g["P"].to_numpy()).max(1)
        grandes = w >= config.MIN_APTOS_SECAO
        k, n = int((res[grandes] > 0.15).sum()), int(grandes.sum())
        metr.append(_linha(ano, 2, comparar.TODOS, "ei_frac_residuo_extremo", k / max(n, 1), *_wilson(k, n)))
        extra["ei"] = {k: v["P"].round(4).to_dict() for k, v in ei.items()}

    # 2 e 3. Impressão digital e forense, para os dois finalistas, em cada turno.
    for turno, df in turnos.items():
        for cand in fin:
            r = rot[cand]
            p = fp.pontos(df, cand)
            fp.figura(p, f"{ano} - {turno}º turno - candidato {r} (nº {cand[1:]})", saida / f"{ano}_t{turno}_{r}_impressao.png")
            for k, v in fp.metricas_descritivas(p).items():
                ic = _wilson(round(v * len(p)), len(p)) if k.startswith("frac") else (np.nan, np.nan)
                metr.append(_linha(ano, turno, r, f"fp_{k}", v, *ic))
            por_uf = fp.ajustar_por_uf(p, rng)
            por_uf.to_csv(saida / f"{ano}_t{turno}_{r}_fraude_klimek_por_uf.csv", index=False)
            if len(por_uf):
                for col in ("fi", "fe"):
                    metr.append(_linha(ano, turno, r, f"fp_{col}_ponderado", *_media_uf_bootstrap(por_uf, col, n_boot, rng)))
            bat = forense.bateria(df, cand, n_boot=n_boot, rng=rng)
            metr.append(_linha(ano, turno, r, "2bl_media_2bl", bat["2bl_media_2bl"], bat.get("2bl_media_2bl_inf", np.nan), bat.get("2bl_media_2bl_sup", np.nan)))
            for k in ("ult_frac_0_ou_5", "pint_comp_razao_obs_esp", "pint_voto_razao_obs_esp", "pint_voto_z", "pint_comp_z"):
                metr.append(_linha(ano, turno, r, k, bat[k]))
    return metr, extra


def rodar(conjunto: dict[int, dict[int, pd.DataFrame]], saida: Path, ano_alvo: int, n_boot: int = config.N_BOOTSTRAP, usar_lphom: bool = False) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    todas, extras = [], {}
    for ano, turnos in sorted(conjunto.items()):
        m, e = analisar_ano(ano, turnos, saida, n_boot, usar_lphom)
        todas += m
        extras[ano] = e
    tabela = pd.DataFrame(todas)
    tabela.to_csv(saida / "metricas.csv", index=False)
    av = comparar.avaliar(tabela, ano_alvo)
    av.to_csv(saida / "avaliacao_pre_registrada.csv", index=False)
    conc = comparar.conclusao(av) if len(av) else pd.DataFrame()
    conc.to_csv(saida / "conclusao.csv", index=False)
    (saida / "detalhes.json").write_text(json.dumps(extras, indent=2, default=float, ensure_ascii=False))
    from .relatorio import escrever

    escrever(saida, tabela, av, conc, extras, ano_alvo)
    return {"metricas": tabela, "avaliacao": av, "conclusao": conc, "extras": extras}
