"""Avaliação de pronúncia (Agente 3 da spec) — pura, sem I/O de rede/arquivo.

Pipeline: `esperado` (script) x `transcrito` (saída do STT) são tokenizados em
palavras, alinhados com um algoritmo de alinhamento SIMPLES (difflib —
`SequenceMatcher` sobre listas de palavras), e cada par alinhado é comparado
foneticamente via ARPAbet (g2p_en) + distância de Levenshtein normalizada
(rapidfuzz). Deliberadamente NÃO usamos DTW nem alinhamento fonético completo
— "simplicidade primeiro": o app é para prática pessoal, não para um produto
de avaliação de fala robusto a qualquer ruído de transcrição.

Erros típicos de pronúncia de brasileiros em inglês (documentação para uso
futuro em textos de dica no frontend — NÃO usados como regra especial aqui;
o score fonético genérico já penaliza naturalmente esses casos porque os
fonemas ARPAbet envolvidos são de fato distantes):
  - "th" (/θ/, /ð/) substituído por /t/, /d/ ou /f/ — ex.: "think" -> "tink"
    ou "fink"; "this" -> "dis". Fonema TH/DH ausente na fonologia do
    português brasileiro.
  - Vogal epentética final — ex.: "book" -> "book-ee", "good" -> "goodji" —
    inserção de uma vogal (geralmente /i/) após consoantes finais que o PT-BR
    não permite em coda (como /k/, /d/, /g/).
  - Confusão entre "h" aspirado (inglês) e "h" mudo (português) — ex.: "hot"
    pronunciado sem aspiração, soando mais próximo de "ot".

Essas notas explicam POR QUE certas substituições fonêmicas tendem a gerar
score baixo — útil para copy de dicas no frontend — mas o algoritmo abaixo é
genérico: qualquer par de palavras com fonemas distantes é penalizado da
mesma forma, sem branches especiais por padrão de erro.
"""
from __future__ import annotations

import string
from difflib import SequenceMatcher
from functools import lru_cache

from g2p_en import G2p
from rapidfuzz.distance import Levenshtein

from config import BANDA_AMARELO_MIN, BANDA_VERDE_MIN
from schemas import Banda, PalavraAvaliada

# g2p_en carrega o CMU dict + POS tagger na primeira instanciação — feito uma
# única vez em nível de módulo e reutilizado entre chamadas de `avaliar`.
_g2p_model = G2p()

# Pontuação a remover apenas das bordas da palavra (mantém apóstrofos e
# hífens internos, ex.: "don't", "well-known").
_PUNCT_BORDAS = string.punctuation


def _normalizar(palavra: str) -> str:
    """Minúsculas + remove pontuação nas bordas, para comparação/g2p."""
    return palavra.strip(_PUNCT_BORDAS).lower()


def _tokenizar(texto: str) -> list[str]:
    return texto.split()


@lru_cache(maxsize=4096)
def _fonemas(palavra_normalizada: str) -> tuple[str, ...]:
    """Fonemas ARPAbet (g2p_en) de uma palavra já normalizada, cacheados."""
    if not palavra_normalizada:
        return ()
    # g2p_en devolve tokens de fonema e, ocasionalmente, espaços — filtramos.
    return tuple(f for f in _g2p_model(palavra_normalizada) if f.strip())


def _score_fonetico(esperada_norm: str, transcrita_norm: str) -> float:
    """1 - distância de Levenshtein normalizada entre sequências de fonemas."""
    fon_esperada = _fonemas(esperada_norm)
    fon_transcrita = _fonemas(transcrita_norm)

    max_len = max(len(fon_esperada), len(fon_transcrita))
    if max_len == 0:
        # Ambas as palavras não geraram fonemas (ex.: strings vazias) —
        # trata como equivalentes para não dividir por zero.
        return 1.0

    distancia = Levenshtein.distance(fon_esperada, fon_transcrita)
    return max(0.0, 1.0 - distancia / max_len)


def _banda_para_score(score: float) -> Banda:
    if score >= BANDA_VERDE_MIN:
        return "verde"
    if score >= BANDA_AMARELO_MIN:
        return "amarelo"
    return "vermelho"


def _avaliar_par(esperada_original: str, transcrita_original: str) -> PalavraAvaliada:
    esperada_norm = _normalizar(esperada_original)
    transcrita_norm = _normalizar(transcrita_original)
    score = _score_fonetico(esperada_norm, transcrita_norm)
    return PalavraAvaliada(
        palavra=transcrita_original,
        esperada=esperada_original,
        banda=_banda_para_score(score),
        score=score,
    )


def _palavra_omitida(esperada_original: str) -> PalavraAvaliada:
    """Palavra do script que não apareceu na transcrição -> banda cinza."""
    return PalavraAvaliada(
        palavra=esperada_original,
        esperada=esperada_original,
        banda="cinza",
        score=None,
    )


def avaliar(esperado: str, transcrito: str) -> list[PalavraAvaliada]:
    """Alinha `esperado` (script) com `transcrito` (STT) palavra a palavra.

    Alinhamento via `difflib.SequenceMatcher` sobre as listas de palavras
    normalizadas — alinhamento simples de sequências (LCS-based), não DTW.
    Trata os três casos possíveis:

    - Palavras iguais/substituídas 1:1 -> avaliadas foneticamente (verde /
      amarelo / vermelho).
    - Palavras do `esperado` sem correspondente no `transcrito` (omissão) ->
      banda "cinza", score None, `palavra` = a própria palavra esperada.
    - Palavras extras no `transcrito` sem correspondente no `esperado`
      (inserção, ex.: hesitações tipo "uh", "like", ou o alinhador simples
      "perdendo o fio"): são DESCARTADAS do resultado, e não são "encaixadas"
      à força contra a palavra esperada mais próxima. Isso evita que uma
      única inserção deslize o alinhamento do resto da frase inteira — trade-
      off deliberado de simplicidade em vez de tentar recuperação
      inteligente do alinhamento.
    """
    esperado_tokens = _tokenizar(esperado)
    transcrito_tokens = _tokenizar(transcrito)

    esperado_norm = [_normalizar(w) for w in esperado_tokens]
    transcrito_norm = [_normalizar(w) for w in transcrito_tokens]

    matcher = SequenceMatcher(a=esperado_norm, b=transcrito_norm, autojunk=False)

    resultado: list[PalavraAvaliada] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                resultado.append(_avaliar_par(esperado_tokens[i], transcrito_tokens[j]))

        elif tag == "replace":
            # Blocos de tamanhos diferentes dos dois lados: alinha
            # posicionalmente (zip simples, não DTW). Sobra do lado
            # `esperado` -> omissão (cinza). Sobra do lado `transcrito` ->
            # inserção, descartada (ver docstring acima).
            tamanho = max(i2 - i1, j2 - j1)
            for k in range(tamanho):
                i, j = i1 + k, j1 + k
                if i < i2 and j < j2:
                    resultado.append(_avaliar_par(esperado_tokens[i], transcrito_tokens[j]))
                elif i < i2:
                    resultado.append(_palavra_omitida(esperado_tokens[i]))
                # else (j < j2 mas i >= i2): palavra extra no transcrito,
                # descartada — ver comentário de "insert" abaixo.

        elif tag == "delete":
            for i in range(i1, i2):
                resultado.append(_palavra_omitida(esperado_tokens[i]))

        elif tag == "insert":
            # Palavras extras no transcrito, sem correspondente no esperado.
            # Descartadas deliberadamente (ver docstring da função).
            continue

    return resultado
