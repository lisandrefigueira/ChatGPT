"""Hora de cada voto e tipo de habilitação, a partir dos logs das urnas (log.jez).

Uso: python -I scripts/logs_horario_voto.py <arquivo_arqurnatot_UF.zip> <data dd/mm/aaaa> <saida.csv>
Gera uma linha por voto computado no dia: seção, hora local e se a habilitação foi biométrica.
"""
import csv
import io
import sys
import zipfile
from multiprocessing import Pool

CAMINHO = DIA = None


def _ini(caminho, dia):
    global CAMINHO, DIA, Z
    CAMINHO, DIA = caminho, dia
    Z = zipfile.ZipFile(caminho)


def processar(nome):
    with zipfile.ZipFile(io.BytesIO(Z.read(nome))) as interno:
        texto = interno.read(interno.namelist()[0]).decode("latin-1")
    sec = nome.split("-")[0]
    linhas, biom, manual, inicio = [], False, False, None
    for ln in texto.splitlines():
        if not ln.startswith(DIA):
            continue
        p = ln.split("\t")
        if len(p) < 5 or p[3] != "VOTA":
            continue
        msg, hora = p[4], p[0][11:19]
        if msg.startswith("Identificador do eleitor digitado"):
            biom, manual, inicio = False, False, hora
        elif msg.startswith("Tipo de habilitação do eleitor [biométrica]"):
            biom = True
        elif msg.startswith("Solicitação de dado pessoal do eleitor para habilitação manual"):
            manual = True
        elif msg.startswith("O voto do eleitor foi computado"):
            linhas.append((sec, inicio, hora, int(biom), int(manual)))
    return linhas


if __name__ == "__main__":
    arq, dia, saida = sys.argv[1], sys.argv[2], sys.argv[3]
    with zipfile.ZipFile(arq) as z:
        nomes = [n for n in z.namelist() if n.endswith("-log.jez")]
    with Pool(4, initializer=_ini, initargs=(arq, dia)) as pool, open(saida, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["secao", "hora_habilitacao", "hora_voto", "biometrica", "habilitacao_manual"])
        n = 0
        for linhas in pool.imap_unordered(processar, nomes, chunksize=50):
            w.writerows(linhas)
            n += len(linhas)
    print(len(nomes), "urnas;", n, "votos")
