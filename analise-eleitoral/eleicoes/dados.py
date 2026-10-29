"""Download e leitura dos arquivos abertos do TSE, por seção eleitoral.

Saída padronizada: um DataFrame por (ano, turno) com uma linha por seção e as
colunas CHAVE + APTOS, COMPARECIMENTO, BRANCOS, NULOS e uma coluna
``V<numero>`` por candidato. Nenhum nome de candidato é usado na análise:
os finalistas são identificados só pelo número, para que as regras não
dependam de quem ganhou.
"""
from __future__ import annotations

import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from . import config

_COLS_VOTACAO = config.CHAVE + ["ANO_ELEICAO", "NR_TURNO", "CD_CARGO", "NR_VOTAVEL", "QT_VOTOS"]
_COLS_DETALHE = config.CHAVE + ["ANO_ELEICAO", "NR_TURNO", "CD_CARGO", "QT_APTOS", "QT_COMPARECIMENTO"]


def baixar(url: str, destino: Path) -> Path:
    """Baixa ``url`` para ``destino`` se ainda não estiver em cache."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    tmp = destino.with_suffix(destino.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.rename(destino)
    return destino


def arquivos_do_ano(ano: int, pasta: Path, baixar_se_faltar: bool = True) -> tuple[Path, Path]:
    vot = pasta / f"votacao_secao_{ano}_BR.zip"
    det = pasta / f"detalhe_votacao_secao_{ano}.zip"
    if baixar_se_faltar:
        baixar(config.URL_VOTACAO_SECAO.format(ano=ano), vot)
        baixar(config.URL_DETALHE_SECAO.format(ano=ano), det)
    for p in (vot, det):
        if not p.exists():
            raise FileNotFoundError(f"{p} não encontrado; baixe do Portal de Dados Abertos do TSE")
    return vot, det


def _ler_csvs_do_zip(caminho: Path, colunas: list[str]) -> pd.DataFrame:
    """Lê todos os CSVs do zip (formato TSE: ';', latin-1), só o cargo Presidente."""
    partes = []
    with zipfile.ZipFile(caminho) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        # Se houver arquivo nacional (_BR), ele já contém tudo; evita duplicar.
        br = [n for n in nomes if n.upper().endswith("_BR.CSV")]
        for nome in br or nomes:
            with z.open(nome) as fh:
                leitor = pd.read_csv(
                    io.TextIOWrapper(fh, encoding="latin-1"),
                    sep=";",
                    usecols=lambda c: c in colunas,
                    dtype={"SG_UF": "string"},
                    chunksize=2_000_000,
                    low_memory=False,
                )
                for bloco in leitor:
                    bloco = bloco[bloco["CD_CARGO"] == config.CD_CARGO_PRESIDENTE]
                    if len(bloco):
                        partes.append(bloco)
    if not partes:
        raise ValueError(f"nenhuma linha de Presidente em {caminho}")
    return pd.concat(partes, ignore_index=True)


def montar_secoes(votacao: pd.DataFrame, detalhe: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """Converte as tabelas longas do TSE em uma tabela larga por turno."""
    resultado = {}
    for turno in sorted(votacao["NR_TURNO"].unique()):
        v = votacao[votacao["NR_TURNO"] == turno].copy()
        v.loc[v["NR_VOTAVEL"] == config.NR_ANULADO, "NR_VOTAVEL"] = config.NR_NULO
        larga = v.pivot_table(
            index=config.CHAVE, columns="NR_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0
        )
        ren = {}
        for c in larga.columns:
            if c == config.NR_BRANCO:
                ren[c] = "BRANCOS"
            elif c == config.NR_NULO:
                ren[c] = "NULOS"
            else:
                ren[c] = f"V{int(c)}"
        larga = larga.rename(columns=ren)
        for c in ("BRANCOS", "NULOS"):
            if c not in larga:
                larga[c] = 0
        d = detalhe[detalhe["NR_TURNO"] == turno]
        d = d.groupby(config.CHAVE)[["QT_APTOS", "QT_COMPARECIMENTO"]].sum()
        d.columns = ["APTOS", "COMPARECIMENTO"]
        t = d.join(larga, how="inner").reset_index()
        resultado[int(turno)] = t
    return resultado


def carregar_ano(ano: int, pasta: Path, baixar_se_faltar: bool = True) -> dict[int, pd.DataFrame]:
    vot, det = arquivos_do_ano(ano, pasta, baixar_se_faltar)
    return montar_secoes(_ler_csvs_do_zip(vot, _COLS_VOTACAO), _ler_csvs_do_zip(det, _COLS_DETALHE))


def candidatos(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("V")]


def finalistas(turnos: dict[int, pd.DataFrame]) -> list[str]:
    """Os dois candidatos do 2º turno; sem 2º turno, os dois mais votados no 1º.

    Ordenados pelo número do candidato, nunca pelo resultado.
    """
    base = turnos.get(2, turnos[1])
    cands = candidatos(base)
    top2 = base[cands].sum().sort_values(ascending=False).index[:2]
    return sorted(top2, key=lambda c: int(c[1:]))


def checar_consistencia(df: pd.DataFrame) -> dict[str, float]:
    """Conferências que precisam bater com os totais oficiais divulgados pelo TSE."""
    votos = df[candidatos(df)].sum(axis=1) + df["BRANCOS"] + df["NULOS"]
    return {
        "secoes": float(len(df)),
        "aptos": float(df["APTOS"].sum()),
        "comparecimento": float(df["COMPARECIMENTO"].sum()),
        "votos_apurados": float(votos.sum()),
        "secoes_votos_diferente_comparecimento": float((votos != df["COMPARECIMENTO"]).sum()),
        "secoes_comparecimento_maior_aptos": float((df["COMPARECIMENTO"] > df["APTOS"]).sum()),
        **{f"total_{c}": float(df[c].sum()) for c in candidatos(df)},
    }
