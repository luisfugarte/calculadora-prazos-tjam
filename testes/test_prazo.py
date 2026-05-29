#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do motor de calculo de prazos (TJAM).

Roda com pytest (`python -m pytest`) ou direto (`python testes/test_prazo.py`).
Os gabaritos abaixo foram conferidos manualmente contra a base 2016-2026.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import CalendarioTJAM, calcular_prazo  # noqa: E402
from motor.calendario import FIM_DE_SEMANA, RECESSO, UTIL  # noqa: E402

CAL = CalendarioTJAM()


def _venc(data_evento, dias, modo="intimacao", dobro=False):
    return calcular_prazo(CAL, data_evento, dias, modo=modo, dobro=dobro).termo_final


# ---------------------------------------------------------------- navegacao
def test_proximo_dia_util_pula_feriado_e_fim_de_semana():
    # 2025-04-17 (qui, Quinta Santa), 18 (Paixao), 19-20 (fds), 21 (Tiradentes)
    assert CAL.proximo_dia_util(date(2025, 4, 17)) == date(2025, 4, 22)
    # dia util permanece
    assert CAL.proximo_dia_util(date(2025, 7, 9)) == date(2025, 7, 9)


def test_dia_util_seguinte_e_estrito():
    assert CAL.dia_util_seguinte(date(2025, 7, 9)) == date(2025, 7, 10)
    # sexta -> segunda
    assert CAL.dia_util_seguinte(date(2025, 7, 11)) == date(2025, 7, 14)


def test_classificar_categorias():
    assert CAL.classificar(date(2025, 7, 9)).categoria == UTIL
    assert CAL.classificar(date(2025, 9, 7)).categoria == FIM_DE_SEMANA   # domingo
    assert CAL.classificar(date(2025, 12, 25)).categoria == RECESSO       # Natal na janela art. 220
    assert CAL.classificar(date(2025, 8, 11)).corre_prazo is False        # ponto facultativo
    assert CAL.classificar(date(2025, 7, 9)).corre_prazo is True


# ---------------------------------------------------------------- contagem basica
def test_15_dias_uteis_simples():
    # intimacao ter 08/07/2025 -> inicio qua 09/07 -> 15o dia util = 29/07
    assert _venc(date(2025, 7, 8), 15) == date(2025, 7, 29)


def test_dies_a_quo_pula_fim_de_semana():
    # intimacao sexta -> inicia segunda
    assert _venc(date(2025, 7, 11), 5) == date(2025, 7, 18)


def test_pula_varios_feriados_no_meio():
    # intimacao ter 15/04/2025; feriados 17,18,21 -> 5o dia util = 25/04
    assert _venc(date(2025, 4, 15), 5) == date(2025, 4, 25)


def test_um_dia():
    assert _venc(date(2025, 7, 8), 1) == date(2025, 7, 9)


# ---------------------------------------------------------------- recesso / art. 220
def test_prazo_cruza_recesso_art220():
    # intimacao qui 12/12/2024, 15 dias: suspende 20/12-20/01, retoma 21/01/2025
    assert _venc(date(2024, 12, 12), 15) == date(2025, 2, 3)


def test_intimacao_dentro_do_recesso_inicia_apos_20_jan():
    # intimacao 10/01/2025 (dentro da janela) -> inicia 21/01/2025
    r = calcular_prazo(CAL, date(2025, 1, 10), 15)
    assert r.inicio_contagem == date(2025, 1, 21)
    assert r.termo_final == date(2025, 2, 10)


# ---------------------------------------------------------------- publicacao no DJe
def test_publicacao_diario_aplica_par2_e_par3():
    # disponibilizacao ter 08/07/2025 -> publicacao qua 09/07 -> inicio qui 10/07 -> 15o = 30/07
    r = calcular_prazo(CAL, date(2025, 7, 8), 15, modo="publicacao_diario")
    assert r.data_publicacao == date(2025, 7, 9)
    assert r.inicio_contagem == date(2025, 7, 10)
    assert r.termo_final == date(2025, 7, 30)


# ---------------------------------------------------------------- inicio direto
def test_inicio_direto_conta_a_propria_data():
    assert _venc(date(2025, 7, 9), 15, modo="inicio_direto") == date(2025, 7, 29)


def test_inicio_direto_protrai_fim_de_semana():
    # sabado 12/07 -> dia 1 = segunda 14/07 -> 5o = 18/07
    assert _venc(date(2025, 7, 12), 5, modo="inicio_direto") == date(2025, 7, 18)


# ---------------------------------------------------------------- dobro
def test_prazo_em_dobro():
    r = calcular_prazo(CAL, date(2025, 7, 8), 15, dobro=True)
    assert r.dias_efetivos == 30
    assert r.termo_final == date(2025, 8, 20)


# ---------------------------------------------------------------- memoria e avisos
def test_memoria_conta_dias_certos():
    r = calcular_prazo(CAL, date(2025, 7, 8), 15)
    contados = [p for p in r.memoria if p.contado]
    assert len(contados) == 15
    assert contados[0].data == date(2025, 7, 9)
    assert contados[0].indice == 1
    assert contados[-1].data == date(2025, 7, 29)
    assert contados[-1].indice == 15


def test_aviso_fora_da_base():
    # 2027 nao esta na base -> deve avisar
    r = calcular_prazo(CAL, date(2027, 6, 1), 15)
    assert any("fora da base" in a for a in r.avisos)


def test_aviso_antes_do_cpc():
    r = calcular_prazo(CAL, date(2016, 3, 1), 5)
    assert any("dias corridos" in a for a in r.avisos)


# ---------------------------------------------------------------- runner sem pytest
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
