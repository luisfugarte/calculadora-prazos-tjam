#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes do catalogo de prazos nomeados do CPC."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import (  # noqa: E402
    CalendarioTJAM, CatalogoPrazos, calcular_prazo, calcular_prazo_nomeado,
)

CAL = CalendarioTJAM()
CAT = CatalogoPrazos()


def test_catalogo_carrega_e_ids_unicos():
    assert len(CAT.itens) > 0
    ids = [p.id for p in CAT.itens]
    assert len(ids) == len(set(ids))


def test_categorias_validas():
    validas = set(CAT.categorias)
    for p in CAT.itens:
        assert p.categoria in validas, f"{p.id}: categoria fora da lista"
        assert p.dias >= 1


def test_prazos_conhecidos():
    assert CAT.obter("contestacao").dias == 15
    assert CAT.obter("embargos_declaracao").dias == 5
    assert CAT.obter("pagamento_execucao").dias == 3
    assert CAT.obter("apelacao").dias == 15


def test_nomeado_bate_com_generico():
    # apelacao = 15 dias; deve dar o mesmo termo final que o contador generico de 15.
    ev = date(2025, 7, 8)
    r_nom = calcular_prazo_nomeado(CAL, CAT, "apelacao", ev)
    r_gen = calcular_prazo(CAL, ev, 15)
    assert r_nom.termo_final == r_gen.termo_final == date(2025, 7, 29)
    assert r_nom.descricao_prazo and "Apelacao" in r_nom.descricao_prazo


def test_embargos_declaracao_5_dias():
    # ED 5 dias, intimacao ter 08/07/2025 -> 5o dia util = 15/07/2025
    r = calcular_prazo_nomeado(CAL, CAT, "embargos_declaracao", date(2025, 7, 8))
    assert r.termo_final == date(2025, 7, 15)


def test_dobro_em_prazo_nomeado():
    r = calcular_prazo_nomeado(CAL, CAT, "contestacao", date(2025, 7, 8), dobro=True)
    assert r.dias_efetivos == 30
    assert r.termo_final == date(2025, 8, 20)


def _rodar_tudo():
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  FALHA {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"  ERRO  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(_rodar_tudo())
