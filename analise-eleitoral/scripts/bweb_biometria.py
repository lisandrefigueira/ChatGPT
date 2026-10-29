"""Lê os boletins de urna (BU na Web) e resume biometria e horário de encerramento.

Uso: python -I scripts/bweb_biometria.py <pasta_bweb> <turno> <saida.parquet|.pkl>
Gera uma linha por urna (seção), só com o cargo Presidente.
"""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

COLS = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO_PERGUNTA", "QT_APTOS",
        "QT_COMPARECIMENTO", "CD_TIPO_URNA", "DS_TIPO_URNA", "NR_VOTAVEL", "QT_VOTOS", "DT_ABERTURA",
        "DT_ENCERRAMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO", "QT_ELEITORES_BIOMETRIA_NH", "DT_EMISSAO_BU"]


def ler(z: Path) -> pd.DataFrame:
    with zipfile.ZipFile(z) as f:
        nome = [n for n in f.namelist() if n.lower().endswith(".csv")][0]
        with f.open(nome) as fh:
            # Em blocos: o 1º turno tem todos os cargos e não cabe na memória de uma vez.
            blocos = pd.read_csv(io.TextIOWrapper(fh, encoding="latin-1"), sep=";", usecols=lambda c: c in COLS,
                                 low_memory=False, chunksize=1_000_000)
            df = pd.concat(b[b["CD_CARGO_PERGUNTA"] == 1] for b in blocos)
    bio = "QT_ELEI_BIOM_SEM_HABILITACAO" if "QT_ELEI_BIOM_SEM_HABILITACAO" in df else "QT_ELEITORES_BIOMETRIA_NH"
    df["SEM_BIOM"] = pd.to_numeric(df[bio], errors="coerce")
    chave = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
    votos = df.pivot_table(index=chave, columns="NR_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    votos.columns = [f"V{c}" for c in votos.columns]
    meta = df.groupby(chave).agg(NM_MUNICIPIO=("NM_MUNICIPIO", "first"), APTOS=("QT_APTOS", "first"),
                                 COMPARECIMENTO=("QT_COMPARECIMENTO", "first"), TIPO_URNA=("DS_TIPO_URNA", "first"),
                                 ABERTURA=("DT_ABERTURA", "first"), ENCERRAMENTO=("DT_ENCERRAMENTO", "first"),
                                 SEM_BIOM=("SEM_BIOM", "first"))
    return meta.join(votos).reset_index()


if __name__ == "__main__":
    pasta, turno, saida = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    partes = [ler(z) for z in sorted(pasta.glob(f"bweb_{turno}t_*.zip"))]
    out = pd.concat(partes, ignore_index=True)
    out.to_pickle(saida)
    print(len(out), "urnas;", out["SEM_BIOM"].sum(), "sem biometria")
