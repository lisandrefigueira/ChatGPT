#!/usr/bin/env python3
"""Linha de comando da análise. Exemplos:

    python rodar_analise.py --dados dados_tse --saida resultados
    python rodar_analise.py --sintetico --saida demo_sintetica
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eleicoes import config, dados, pipeline, sintetico


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dados", type=Path, default=Path("dados_tse"), help="pasta com os .zip do TSE (cache)")
    ap.add_argument("--saida", type=Path, default=Path("resultados"))
    ap.add_argument("--alvo", type=int, default=config.ANO_ALVO)
    ap.add_argument("--referencias", type=int, nargs="*", default=list(config.ANOS_REFERENCIA))
    ap.add_argument("--sem-download", action="store_true", help="usar só arquivos já presentes em --dados")
    ap.add_argument("--bootstrap", type=int, default=config.N_BOOTSTRAP)
    ap.add_argument("--lphom", action="store_true", help="roda também o estimador LP de Romero et al. (lento)")
    ap.add_argument("--sintetico", action="store_true", help="demonstração com dados fictícios de verdade conhecida")
    ap.add_argument("--sem-fraude", action="store_true", help="com --sintetico: alvo fictício limpo (controle negativo)")
    a = ap.parse_args(argv)

    if a.sintetico:
        conjunto = {}
        for i, ano in enumerate(a.referencias):
            conjunto[ano], _ = sintetico.gerar(semente=ano, heterogeneidade=0.02)
        # Alvo fictício com enchimento de urna plantado no 2º turno para o candidato V1.
        conjunto[a.alvo], _ = sintetico.gerar(
            semente=a.alvo, heterogeneidade=0.02, fraude_turno=None if a.sem_fraude else 2,
            fraude_cand="V1", fi=0.10, fe=0.02,
        )
    else:
        conjunto = {}
        for ano in [*a.referencias, a.alvo]:
            try:
                conjunto[ano] = dados.carregar_ano(ano, a.dados, baixar_se_faltar=not a.sem_download)
            except Exception as e:  # noqa: BLE001
                print(f"[erro] {ano}: {e}", file=sys.stderr)
                if ano == a.alvo:
                    return 2
    r = pipeline.rodar(conjunto, a.saida, a.alvo, n_boot=a.bootstrap, usar_lphom=a.lphom)
    print(r["conclusao"].to_string(index=False))
    print(f"\nRelatório: {a.saida / 'RELATORIO.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
