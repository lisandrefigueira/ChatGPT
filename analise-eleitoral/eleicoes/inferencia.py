"""Inferência ecológica R x C entre 1º e 2º turno, seção a seção.

Três estimadores complementares, todos replicáveis:

* ``goodman_restrito``: regressão de Goodman (1953) com as restrições lógicas
  (probabilidades em [0, 1], linhas somando 1), ponderada pelo eleitorado. É
  resolvida exatamente por gradiente projetado acelerado (FISTA) sobre
  estatísticas suficientes, o que permite bootstrap barato.
* ``goodman_local``: o mesmo estimador ajustado dentro de cada UF (ou de cada
  município, como sensibilidade) e agregado depois. Reduz o viés de
  agregação, porque a matriz de transição pode variar entre regiões.
* ``lphom``: programação linear de Romero, Pavía, Martín & Romero (2020,
  *Sociological Methods & Research*), minimizando desvios absolutos.

Mais os limites determinísticos de Duncan & Davis (1953), que não dependem de
modelo nenhum.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from . import config
from .dados import candidatos

LINHAS = ["A", "B", "OUTROS", "BRANCO_NULO", "ABSTENCAO"]
COLUNAS = ["A", "B", "BRANCO_NULO", "ABSTENCAO"]


def tabelas_transicao(t1: pd.DataFrame, t2: pd.DataFrame, fin: list[str]) -> pd.DataFrame:
    """Junta as mesmas seções nos dois turnos e monta as categorias (contagens)."""
    a, b = fin
    r1 = t1.rename(columns={c: f"{c}_1" for c in t1.columns if c not in config.CHAVE})
    r2 = t2.rename(columns={c: f"{c}_2" for c in t2.columns if c not in config.CHAVE})
    m = r1.merge(r2, on=config.CHAVE, how="inner")
    out1 = [f"{c}_1" for c in candidatos(t1) if c not in fin]
    df = pd.DataFrame({k: m[k] for k in config.CHAVE})
    df["X_A"] = m[f"{a}_1"]
    df["X_B"] = m[f"{b}_1"]
    df["X_OUTROS"] = m[out1].sum(axis=1) if out1 else 0
    df["X_BRANCO_NULO"] = m["BRANCOS_1"] + m["NULOS_1"]
    df["X_ABSTENCAO"] = (m["APTOS_1"] - m["COMPARECIMENTO_1"]).clip(lower=0)
    df["Y_A"] = m[f"{a}_2"]
    df["Y_B"] = m[f"{b}_2"]
    df["Y_BRANCO_NULO"] = m["BRANCOS_2"] + m["NULOS_2"]
    df["Y_ABSTENCAO"] = (m["APTOS_2"] - m["COMPARECIMENTO_2"]).clip(lower=0)
    df["APTOS_1"] = m["APTOS_1"]
    df["APTOS_2"] = m["APTOS_2"]
    df.attrs["secoes_t1"] = len(t1)
    df.attrs["secoes_t2"] = len(t2)
    return df


def _matrizes(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    X = df[[f"X_{c}" for c in LINHAS]].to_numpy(float)
    Y = df[[f"Y_{c}" for c in COLUNAS]].to_numpy(float)
    nx = X.sum(1, keepdims=True)
    ny = Y.sum(1, keepdims=True)
    ok = (nx[:, 0] > 0) & (ny[:, 0] > 0)
    # Proporções de cada turno; o eleitorado quase não muda entre turnos.
    return X[ok] / nx[ok], Y[ok] / ny[ok], nx[ok, 0], X[ok]


def _projetar_simplex(V: np.ndarray) -> np.ndarray:
    """Projeta cada linha (última dimensão) no simplex de probabilidades."""
    u = np.sort(V, axis=-1)[..., ::-1]
    css = np.cumsum(u, axis=-1) - 1
    k = np.arange(1, V.shape[-1] + 1)
    cond = u - css / k > 0
    rho = cond.shape[-1] - 1 - np.argmax(cond[..., ::-1], axis=-1)
    theta = np.take_along_axis(css, rho[..., None], axis=-1) / (rho[..., None] + 1)
    return np.maximum(V - theta, 0)


def _fista(G: np.ndarray, H: np.ndarray, iters: int = 3000, tol: float = 1e-9) -> np.ndarray:
    """min_P tr(P'GP) - 2 tr(H'P), P com linhas no simplex; em lote (M, I, ...)."""
    M, I, _ = G.shape
    J = H.shape[2]
    L = 2 * np.linalg.eigvalsh(G)[:, -1][:, None, None] + 1e-12
    P = np.full((M, I, J), 1.0 / J)
    Z, t = P.copy(), 1.0
    for _ in range(iters):
        grad = 2 * (G @ Z - H)
        Pn = _projetar_simplex(Z - grad / L)
        tn = (1 + np.sqrt(1 + 4 * t * t)) / 2
        Z = Pn + ((t - 1) / tn) * (Pn - P)
        passo = np.abs(Pn - P).max()
        P, t = Pn, tn
        if passo < tol:
            break
    return P


def _estatisticas(x, y, w):
    xw = x * w[:, None]
    return xw.T @ x, xw.T @ y


def goodman_restrito(df: pd.DataFrame, n_boot: int = 0, rng=None) -> dict:
    x, y, w, _ = _matrizes(df)
    G, H = _estatisticas(x, y, w)
    P = _fista(G[None], H[None])[0]
    res = {"P": pd.DataFrame(P, index=LINHAS, columns=COLUNAS)}
    if n_boot:
        rng = rng or np.random.default_rng(config.SEMENTE)
        Gs, Hs = [], []
        for _ in range(n_boot):
            c = rng.poisson(1.0, len(w)).astype(float)  # bootstrap de Poisson
            g, h = _estatisticas(x, y, w * c)
            Gs.append(g)
            Hs.append(h)
        Pb = _fista(np.array(Gs), np.array(Hs))
        res.update(_ic(Pb))
    return res


def goodman_local(df: pd.DataFrame, grupo=("SG_UF",), n_boot: int = 0, rng=None) -> dict:
    """Ajusta dentro de cada grupo (por padrão, a UF) e agrega os fluxos.

    Com ``grupo=("SG_UF", "CD_MUNICIPIO")`` ajusta por município, e municípios
    com poucas seções usam a estimativa da UF. Na validação sintética o ajuste
    municipal teve viés para cima nos fluxos pequenos (efeito de fronteira em
    amostras pequenas), por isso ele é só análise de sensibilidade.
    """
    x, y, w, Xc = _matrizes(df)
    ok_rows = (df[[f"X_{c}" for c in LINHAS]].sum(axis=1) > 0) & (df[[f"Y_{c}" for c in COLUNAS]].sum(axis=1) > 0)
    d = df.loc[ok_rows, list(grupo)].reset_index(drop=True)
    cod_grupo = d.groupby(list(grupo)).ngroup().to_numpy()
    cod_uf = d.groupby(["SG_UF"]).ngroup().to_numpy()
    n_por_grupo = np.bincount(cod_grupo)
    usa_uf = n_por_grupo[cod_grupo] < config.MIN_SECOES_MUNICIPIO
    # Unidades de estimação: municípios grandes + "resto da UF".
    uni = np.where(usa_uf, n_por_grupo.size + cod_uf, cod_grupo)
    _, uni = np.unique(uni, return_inverse=True)

    def fluxos(peso):
        U = uni.max() + 1
        I, J = x.shape[1], y.shape[1]
        G = np.zeros((U, I, I))
        H = np.zeros((U, I, J))
        xw = x * peso[:, None]
        np.add.at(G, uni, xw[:, :, None] * x[:, None, :])
        np.add.at(H, uni, xw[:, :, None] * y[:, None, :])
        P = _fista(G, H, iters=1500)
        tot = np.zeros((U, I))
        np.add.at(tot, uni, Xc * (peso / w)[:, None])
        F = (tot[:, :, None] * P).sum(0)
        return F / F.sum(1, keepdims=True)

    P = fluxos(w)
    res = {"P": pd.DataFrame(P, index=LINHAS, columns=COLUNAS), "unidades": int(uni.max() + 1)}
    if n_boot:
        rng = rng or np.random.default_rng(config.SEMENTE + 1)
        Pb = np.array([fluxos(w * rng.poisson(1.0, len(w))) for _ in range(n_boot)])
        res.update(_ic(Pb))
    return res


def lphom(df: pd.DataFrame) -> pd.DataFrame:
    """Romero et al. (2020): min sum |Y - X P|, P estocástica por linha (contagens)."""
    X = df[[f"X_{c}" for c in LINHAS]].to_numpy(float)
    Y = df[[f"Y_{c}" for c in COLUNAS]].to_numpy(float)
    # Ajusta Y ao total de X em cada seção (eleitorado praticamente igual).
    ny = Y.sum(1, keepdims=True)
    Y = np.where(ny > 0, Y / np.where(ny > 0, ny, 1) * X.sum(1, keepdims=True), 0)
    K, I = X.shape
    J = Y.shape[1]
    nP = I * J
    nE = K * J
    # variáveis: P (I*J), e+ (K*J), e- (K*J)
    from scipy.sparse import coo_matrix, hstack, identity, kron

    A_fit = kron(identity(J, format="csr"), coo_matrix(X)).tocsr()  # (K*J) x (I*J) com P em ordem coluna
    A_eq = hstack([A_fit, identity(nE), -identity(nE)]).tocsr()
    b_eq = Y.T.reshape(-1)
    # linhas de P somam 1 (P em ordem coluna: índice j*I + i)
    rows = np.repeat(np.arange(I), J)
    cols = np.array([j * I + i for i in range(I) for j in range(J)])
    A_soma = coo_matrix((np.ones(nP), (rows, cols)), shape=(I, nP + 2 * nE))
    from scipy.sparse import vstack

    A = vstack([A_eq, A_soma]).tocsr()
    b = np.concatenate([b_eq, np.ones(I)])
    c = np.concatenate([np.zeros(nP), np.ones(2 * nE)])
    r = linprog(c, A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    if not r.success:
        raise RuntimeError(r.message)
    P = r.x[:nP].reshape(J, I).T
    return pd.DataFrame(P, index=LINHAS, columns=COLUNAS)


def limites_deterministicos(df: pd.DataFrame) -> pd.DataFrame:
    """Fatos que valem sem modelo algum, somados sobre as seções.

    * ``perda_liquida_minima``: soma de max(0, X_i - Y_i). Pelo menos esse número
      de eleitores do 1º turno de cada finalista não repetiu o voto nele (ou foi
      substituído por outro eleitor) — é um piso, não uma estimativa.
    * Limites de Duncan-Davis para o fluxo A->B e B->A: max(0, X_i + Y_j - N) e
      min(X_i, Y_j) por seção.
    """
    N = df[[f"X_{c}" for c in LINHAS]].sum(axis=1)
    linhas = {}
    for s, o in (("A", "B"), ("B", "A")):
        Xi, Yi, Yo = df[f"X_{s}"], df[f"Y_{s}"], df[f"Y_{o}"]
        linhas[s] = {
            "votos_1t": Xi.sum(),
            "votos_2t": Yi.sum(),
            "perda_liquida_minima": (Xi - Yi).clip(lower=0).sum(),
            f"fluxo_{s}_para_{o}_min": (Xi + Yo - N).clip(lower=0).sum(),
            f"fluxo_{s}_para_{o}_max": np.minimum(Xi, Yo).sum(),
        }
    return pd.DataFrame(linhas).T


def _ic(Pb: np.ndarray) -> dict:
    a = (1 - config.NIVEL_IC) / 2
    return {
        "P_inf": pd.DataFrame(np.quantile(Pb, a, axis=0), index=LINHAS, columns=COLUNAS),
        "P_sup": pd.DataFrame(np.quantile(Pb, 1 - a, axis=0), index=LINHAS, columns=COLUNAS),
        "P_boot": Pb,
    }


def migracao(P: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Converte a matriz de transição em número estimado de eleitores por fluxo."""
    tot = df[[f"X_{c}" for c in LINHAS]].sum().to_numpy()
    return P.mul(tot, axis=0)
