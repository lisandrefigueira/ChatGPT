"""Testes do módulo `pronuncia` (Agente 3 — avaliação de pronúncia).

Os pares de palavras usados como exemplo de erro (think/tink, the/de etc.)
foram escolhidos observando a distância fonêmica ARPAbet real via g2p_en —
ver módulo `pronuncia.py` para a lista de erros típicos PT-BR -> EN que
motivam essas escolhas.
"""
from __future__ import annotations

import pytest

from config import BANDA_AMARELO_MIN, BANDA_VERDE_MIN
from pronuncia import avaliar


# ---------------------------------------------------------------------------
# Correspondências perfeitas -> banda verde
# ---------------------------------------------------------------------------
def test_frase_toda_correta_e_toda_verde():
    resultado = avaliar("The cat sat on the mat", "The cat sat on the mat")

    assert len(resultado) == 6
    assert all(p.banda == "verde" for p in resultado)
    assert all(p.score == pytest.approx(1.0) for p in resultado)
    # esperada/palavra batem com o texto original (preservando capitalização)
    assert resultado[0].palavra == "The"
    assert resultado[0].esperada == "The"


def test_palavras_isoladas_identicas_sao_verdes():
    resultado = avaliar("hello world", "hello world")

    assert [p.banda for p in resultado] == ["verde", "verde"]
    assert resultado[0].score == pytest.approx(1.0)
    assert resultado[1].score == pytest.approx(1.0)


def test_normalizacao_ignora_maiusculas_e_pontuacao():
    # "Hello!" (esperado) vs "hello" (transcrito) — mesma palavra, apenas
    # diferindo em maiúscula/pontuação -> ainda deve pontuar 1.0 (verde).
    resultado = avaliar("Hello, world!", "hello world")

    assert len(resultado) == 2
    assert resultado[0].banda == "verde"
    assert resultado[0].score == pytest.approx(1.0)
    # `palavra` preserva o texto tal como transcrito (sem forçar minúsculas)
    assert resultado[0].palavra == "hello"
    assert resultado[0].esperada == "Hello,"


# ---------------------------------------------------------------------------
# Substituições fonêmicas parciais -> banda amarelo
# ---------------------------------------------------------------------------
def test_think_tink_troca_th_por_t_e_amarelo():
    # TH IH1 NG K  vs  T IH1 NG K -> distância 1 / 4 fonemas = score 0.75
    resultado = avaliar("think", "tink")

    assert len(resultado) == 1
    p = resultado[0]
    assert p.banda == "amarelo"
    assert p.score == pytest.approx(0.75)
    assert BANDA_AMARELO_MIN <= p.score < BANDA_VERDE_MIN


def test_think_fink_troca_th_por_f_e_amarelo():
    resultado = avaliar("think", "fink")

    p = resultado[0]
    assert p.banda == "amarelo"
    assert p.score == pytest.approx(0.75)


def test_three_tree_e_amarelo():
    # TH R IY1 vs T R IY1 -> distância 1 / 3 fonemas ~= 0.667
    resultado = avaliar("three", "tree")

    p = resultado[0]
    assert p.banda == "amarelo"
    assert p.score == pytest.approx(0.6667, abs=0.01)


def test_good_goodji_vogal_epentetica_fica_no_limite_amarelo():
    # G UH1 D vs G UH1 D JH IY0 -> distância 2 / 5 fonemas = score 0.6,
    # exatamente no limiar de BANDA_AMARELO_MIN.
    resultado = avaliar("good", "goodji")

    p = resultado[0]
    assert p.score == pytest.approx(0.6)
    assert p.banda == "amarelo"


# ---------------------------------------------------------------------------
# Substituições fonêmicas severas -> banda vermelho
# ---------------------------------------------------------------------------
def test_the_de_e_vermelho():
    # DH AH0 vs D IY1 -> nenhum fonema em comum na mesma posição, score baixo
    resultado = avaliar("the", "de")

    p = resultado[0]
    assert p.banda == "vermelho"
    assert p.score < BANDA_AMARELO_MIN


def test_hot_ot_h_aspirado_silencioso_e_vermelho():
    # HH AA1 T vs AO1 T — omissão do H aspirado + vogal diferente
    resultado = avaliar("hot", "ot")

    p = resultado[0]
    assert p.banda == "vermelho"
    assert p.score < BANDA_AMARELO_MIN


def test_palavra_completamente_diferente_e_vermelho():
    resultado = avaliar("cat", "dog")

    p = resultado[0]
    assert p.banda == "vermelho"
    assert p.score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Palavras omitidas -> banda cinza
# ---------------------------------------------------------------------------
def test_palavra_omitida_no_meio_da_frase_e_cinza():
    resultado = avaliar("I would like a coffee", "I would like coffee")

    bandas = [p.banda for p in resultado]
    assert bandas == ["verde", "verde", "verde", "cinza", "verde"]

    omitida = resultado[3]
    assert omitida.banda == "cinza"
    assert omitida.score is None
    assert omitida.palavra == "a"
    assert omitida.esperada == "a"


def test_frase_totalmente_omitida_e_toda_cinza():
    resultado = avaliar("good morning teacher", "")

    assert len(resultado) == 3
    assert all(p.banda == "cinza" for p in resultado)
    assert all(p.score is None for p in resultado)
    assert [p.palavra for p in resultado] == ["good", "morning", "teacher"]


# ---------------------------------------------------------------------------
# Palavras inseridas (extras) -> descartadas, não corrompem o alinhamento
# ---------------------------------------------------------------------------
def test_palavra_inserida_no_meio_e_descartada_sem_afetar_resto():
    resultado = avaliar("I would like a coffee please", "I would like uh a coffee please")

    # "uh" não existe no esperado e não deve aparecer no resultado, nem
    # deslocar o alinhamento das palavras seguintes.
    assert [p.esperada for p in resultado] == [
        "I", "would", "like", "a", "coffee", "please",
    ]
    assert all(p.banda == "verde" for p in resultado)
    assert not any(p.palavra == "uh" for p in resultado)


def test_palavra_inserida_no_final_e_descartada():
    resultado = avaliar("This is a good book", "This is a good book indeed")

    assert len(resultado) == 5
    assert [p.esperada for p in resultado] == ["This", "is", "a", "good", "book"]
    assert all(p.banda == "verde" for p in resultado)


# ---------------------------------------------------------------------------
# Frase completa com mistura de bandas
# ---------------------------------------------------------------------------
def test_frase_completa_com_mistura_de_bandas():
    resultado = avaliar(
        "I think this is a very good book",
        "I tink this is very good",
    )

    assert [p.esperada for p in resultado] == [
        "I", "think", "this", "is", "a", "very", "good", "book",
    ]
    assert [p.banda for p in resultado] == [
        "verde",    # I / I
        "amarelo",  # think / tink
        "verde",    # this / this
        "verde",    # is / is
        "cinza",    # a (omitida)
        "verde",    # very / very
        "verde",    # good / good
        "cinza",    # book (omitida)
    ]

    think = resultado[1]
    assert think.palavra == "tink"
    assert think.score == pytest.approx(0.75)

    a_omitida = resultado[4]
    assert a_omitida.score is None
    assert a_omitida.palavra == "a"

    book_omitida = resultado[7]
    assert book_omitida.score is None
    assert book_omitida.palavra == "book"


def test_todas_bandas_possiveis_em_uma_unica_chamada():
    # verde (hello/hello), amarelo (think/tink), vermelho (the/de),
    # cinza (world omitida)
    resultado = avaliar("hello think the world", "hello tink de")

    bandas = [p.banda for p in resultado]
    assert bandas == ["verde", "amarelo", "vermelho", "cinza"]
    assert {"verde", "amarelo", "vermelho", "cinza"} == set(bandas)


# ---------------------------------------------------------------------------
# Casos vazios / defensivos
# ---------------------------------------------------------------------------
def test_esperado_e_transcrito_vazios_retorna_lista_vazia():
    assert avaliar("", "") == []


def test_score_e_none_apenas_para_cinza():
    resultado = avaliar("good morning", "good")

    for p in resultado:
        if p.banda == "cinza":
            assert p.score is None
        else:
            assert p.score is not None
