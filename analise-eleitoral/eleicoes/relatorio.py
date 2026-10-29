"""Relatório em Markdown, gerado só a partir dos arquivos de saída."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def _md(df: pd.DataFrame, fmt: str = "{:.4f}") -> str:
    if df is None or df.empty:
        return "_(vazio)_\n"
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join([""] + cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, row in df.iterrows():
        cel = [fmt.format(v) if isinstance(v, float) else str(v) for v in row]
        out.append("| " + " | ".join([str(idx)] + cel) + " |")
    return "\n".join(out) + "\n"


def escrever(saida: Path, metr, av, conc, extras, ano_alvo) -> Path:
    L = [f"# Análise eleitoral por seção — alvo {ano_alvo}\n"]
    L.append(
        "Gerado automaticamente por `rodar_analise.py`. As regras de decisão estão em "
        "`PREREGISTRO.md` e foram fixadas antes da leitura dos dados do ano-alvo.\n"
    )
    L.append("## Veredito pela regra pré-registrada\n")
    L.append(_md(conc.set_index(["turno", "candidato"]) if len(conc) else conc))
    L.append("\n## Conferência dos dados (comparar com os totais oficiais do TSE)\n")
    for ano, e in sorted(extras.items()):
        L.append(f"### {ano} — finalistas {e['finalistas']}\n")
        L.append(_md(pd.DataFrame(e["consistencia"]), "{:,.0f}"))
        if "secoes_pareadas" in e:
            L.append(f"Seções pareadas entre turnos: {e['secoes_pareadas']}\n")
    L.append("\n## Inferência ecológica: para onde foi cada grupo do 1º turno\n")
    L.append("Linhas = escolha no 1º turno; colunas = escolha no 2º turno (proporções).\n")
    for ano, e in sorted(extras.items()):
        for nome, P in e.get("ei", {}).items():
            L.append(f"### {ano} — {nome}\n")
            L.append(_md(pd.DataFrame(P)))
            f = saida / f"{ano}_eleitores_{nome}.csv"
            if f.exists():
                L.append("Em número de eleitores:\n")
                L.append(_md(pd.read_csv(f, index_col=0), "{:,.0f}"))
        lim = saida / f"{ano}_limites_sem_modelo.csv"
        if lim.exists():
            L.append(f"**{ano} — fatos sem modelo (limites determinísticos):**\n")
            L.append(_md(pd.read_csv(lim, index_col=0), "{:,.0f}"))
    L.append("\n## Comparação de cada métrica do ano-alvo com o histórico\n")
    if len(av):
        cols = ["turno", "candidato", "familia", "metrica", "valor", "inf", "sup", "ref_min", "ref_max", "status"]
        L.append(_md(av[cols].reset_index(drop=True)))
    L.append("\n## Todas as métricas, todas as eleições\n")
    piv = metr.pivot_table(index=["metrica", "turno", "candidato"], columns="ano", values="valor")
    L.append(_md(piv))
    L.append("\n## Impressões digitais (Klimek et al., 2012)\n")
    for png in sorted(saida.glob("*_impressao.png")):
        L.append(f"![{png.stem}]({png.name})\n")
    p = saida / "RELATORIO.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p
