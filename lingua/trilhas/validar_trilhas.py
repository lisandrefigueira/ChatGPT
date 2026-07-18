#!/usr/bin/env python3
"""Validador das trilhas de diálogo (lingua/trilhas/*.json).

Convenção de nó terminal
------------------------
O último nó de uma trilha (o fim do roteiro) usa, em `proximo`, o valor
sentinela `"fim"` (por exemplo `{"padrao": "fim"}`). Esse valor NÃO precisa
corresponder a um `id` de nó existente no arquivo — ele sinaliza ao motor de
diálogo do app que o roteiro acabou e que a conversa deve seguir em modo
livre (usando `modo_livre_seed`). Qualquer outro valor referenciado em
`proximo` DEVE corresponder ao `id` de algum nó dentro do mesmo arquivo.

O que este script faz
----------------------
1. Carrega `schema.json` (JSON Schema draft-07) do mesmo diretório.
2. Valida todo arquivo `*.json` do diretório (exceto o próprio `schema.json`)
   contra esse schema.
3. Verifica que todo alvo de `proximo` de todo nó aponta para um `id` de nó
   existente no mesmo arquivo, ou é o sentinela `"fim"`.
4. Verifica que `resposta_alvo` e cada item de `alternativas_aceitas` de
   cada nó podem ser fonemizados sem erro pelo `g2p_en` (checagem leve de
   sanidade do texto em inglês). Este script é autocontido: não importa
   `backend/pronuncia.py` nem nenhum outro módulo do projeto, apenas
   `g2p_en` diretamente, para não criar dependência cruzada com o trabalho
   de outro agente.
5. Imprime um resumo PASS/FAIL por arquivo e sai com código 1 se qualquer
   arquivo falhar, ou 0 se todos passarem.

Uso
---
    cd lingua/trilhas
    python3 validar_trilhas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERRO: pacote 'jsonschema' não encontrado. Instale com: pip install jsonschema")
    sys.exit(1)

try:
    from g2p_en import G2p
except ImportError:
    print("ERRO: pacote 'g2p_en' não encontrado. Instale com: pip install g2p-en")
    sys.exit(1)


SENTINELA_FIM = "fim"

TRILHAS_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = TRILHAS_DIR / "schema.json"


def carregar_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def encontrar_arquivos_trilha() -> list[Path]:
    arquivos = sorted(
        p for p in TRILHAS_DIR.glob("*.json") if p.name != "schema.json"
    )
    return arquivos


def validar_schema(dados: dict, schema: dict, erros: list[str]) -> None:
    validador = jsonschema.Draft7Validator(schema)
    for erro in sorted(validador.iter_errors(dados), key=lambda e: list(e.path)):
        caminho = "/".join(str(p) for p in erro.path) or "<raiz>"
        erros.append(f"schema: em '{caminho}': {erro.message}")


def validar_branches(dados: dict, erros: list[str]) -> None:
    nos = dados.get("nos", [])
    if not isinstance(nos, list):
        return
    ids_existentes = {no.get("id") for no in nos if isinstance(no, dict)}

    total_branch_points = 0
    for no in nos:
        if not isinstance(no, dict):
            continue
        no_id = no.get("id", "<sem id>")
        proximo = no.get("proximo", {})
        if not isinstance(proximo, dict):
            continue
        if "padrao" not in proximo:
            erros.append(f"proximo: nó '{no_id}' não tem chave 'padrao' de fallback")
        if len(proximo) > 1:
            total_branch_points += 1
        for chave, alvo in proximo.items():
            if alvo == SENTINELA_FIM:
                continue
            if alvo not in ids_existentes:
                erros.append(
                    f"proximo: nó '{no_id}' chave '{chave}' aponta para "
                    f"'{alvo}', que não existe como id de nó neste arquivo "
                    f"(e não é o sentinela '{SENTINELA_FIM}')"
                )

    if total_branch_points < 2:
        erros.append(
            f"branches: apenas {total_branch_points} nó(s) com mais de uma "
            f"chave em 'proximo' (mínimo exigido: 2 pontos de ramificação reais)"
        )


def validar_fonemas(dados: dict, g2p: "G2p", erros: list[str]) -> None:
    nos = dados.get("nos", [])
    if not isinstance(nos, list):
        return
    for no in nos:
        if not isinstance(no, dict):
            continue
        no_id = no.get("id", "<sem id>")

        textos = []
        resposta_alvo = no.get("resposta_alvo")
        if isinstance(resposta_alvo, str):
            textos.append(("resposta_alvo", resposta_alvo))
        for i, alt in enumerate(no.get("alternativas_aceitas") or []):
            if isinstance(alt, str):
                textos.append((f"alternativas_aceitas[{i}]", alt))

        for campo, texto in textos:
            try:
                fonemas = g2p(texto)
                if not fonemas:
                    erros.append(
                        f"g2p_en: nó '{no_id}' campo '{campo}' produziu "
                        f"lista de fonemas vazia para: {texto!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - queremos capturar qualquer falha do g2p
                erros.append(
                    f"g2p_en: nó '{no_id}' campo '{campo}' lançou exceção "
                    f"ao fonemizar {texto!r}: {exc!r}"
                )


def main() -> int:
    schema = carregar_schema()
    arquivos = encontrar_arquivos_trilha()

    if not arquivos:
        print("Nenhum arquivo de trilha encontrado (além de schema.json).")
        return 1

    print("Inicializando g2p_en (pode demorar alguns segundos na primeira vez)...")
    g2p = G2p()

    resultados: list[tuple[str, bool, list[str], int]] = []

    for caminho in arquivos:
        erros: list[str] = []
        try:
            with caminho.open("r", encoding="utf-8") as f:
                dados = json.load(f)
        except json.JSONDecodeError as exc:
            erros.append(f"json: falha ao parsear arquivo: {exc}")
            resultados.append((caminho.name, False, erros, 0))
            continue

        validar_schema(dados, schema, erros)

        # Só faz sentido checar branches/fonemas se a estrutura básica bateu
        # o suficiente para termos uma lista de nós.
        if isinstance(dados.get("nos"), list):
            validar_branches(dados, erros)
            validar_fonemas(dados, g2p, erros)

        n_nos = len(dados.get("nos", [])) if isinstance(dados.get("nos"), list) else 0
        resultados.append((caminho.name, len(erros) == 0, erros, n_nos))

    print()
    print("=" * 72)
    print("RESUMO DA VALIDAÇÃO DE TRILHAS")
    print("=" * 72)

    algum_falhou = False
    for nome, ok, erros, n_nos in resultados:
        status = "PASS" if ok else "FAIL"
        if not ok:
            algum_falhou = True
        print(f"[{status}] {nome} ({n_nos} nós)")
        for erro in erros:
            print(f"        - {erro}")

    print("=" * 72)
    total = len(resultados)
    passou = sum(1 for _, ok, _, _ in resultados if ok)
    print(f"{passou}/{total} arquivo(s) passaram na validação.")
    print("=" * 72)

    return 1 if algum_falhou else 0


if __name__ == "__main__":
    sys.exit(main())
