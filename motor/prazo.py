#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prazo.py — Calculo de prazos processuais civeis em dias uteis (CPC/2015), TJAM.

Regras:
  - art. 219: prazos em dias uteis.
  - art. 224, caput: exclui o dia do comeco, inclui o do vencimento.
  - art. 224, par. 1: comeco/vencimento protraidos para o proximo dia util.
  - art. 224, par. 2: data de publicacao = 1o dia util seguinte a disponibilizacao.
  - art. 224, par. 3: contagem inicia no 1o dia util seguinte ao da publicacao.
  - art. 220: suspensao dos prazos de 20/12 a 20/01 (tratada no calendario).
  - art. 229 / 180 / 183 / 186: prazo em dobro (litisconsortes, MP, Fazenda, Defensoria).

Modos de termo inicial:
  - "intimacao":          'data' = dia da intimacao/ciencia (excluido); inicia no dia util seguinte.
  - "publicacao_diario":  'data' = disponibilizacao no DJe; aplica par. 2 e par. 3.
  - "inicio_direto":      'data' = 1o dia da contagem (protraido ao proximo dia util se preciso).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .calendario import CalendarioTJAM, DIAS_SEMANA

MODOS = ("intimacao", "publicacao_diario", "inicio_direto")


@dataclass
class PassoMemoria:
    data: date
    dia_semana: str
    contado: bool
    indice: int | None      # numero do dia no prazo, se contado
    categoria: str
    detalhe: str


@dataclass
class ResultadoPrazo:
    data_evento: date
    modo: str
    dias_nominais: int
    dias_efetivos: int          # com dobro aplicado
    dobro: bool
    data_publicacao: date | None
    inicio_contagem: date
    termo_final: date
    descricao_prazo: str | None
    memoria: list[PassoMemoria] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        return (
            f"Termo final: {self.termo_final.strftime('%d/%m/%Y')} "
            f"({DIAS_SEMANA[self.termo_final.weekday()]})"
        )


def calcular_prazo(
    cal: CalendarioTJAM,
    data_evento: date,
    dias: int,
    modo: str = "intimacao",
    dobro: bool = False,
    descricao: str | None = None,
) -> ResultadoPrazo:
    if modo not in MODOS:
        raise ValueError(f"modo invalido: {modo!r}. Use um de {MODOS}.")
    if dias < 1:
        raise ValueError("dias deve ser >= 1")

    n = dias * (2 if dobro else 1)

    data_publicacao: date | None = None
    if modo == "intimacao":
        inicio = cal.dia_util_seguinte(data_evento)
    elif modo == "publicacao_diario":
        data_publicacao = cal.dia_util_seguinte(data_evento)   # par. 2
        inicio = cal.dia_util_seguinte(data_publicacao)        # par. 3
    else:  # inicio_direto
        inicio = cal.proximo_dia_util(data_evento)

    # inicio e o dia 1; o termo final e o n-esimo dia util a partir dele (inclusive).
    termo_final = inicio if n == 1 else cal.adicionar_dias_uteis(inicio, n - 1)

    avisos: list[str] = []
    if not cal.cobre_periodo(data_evento, termo_final):
        avisos.append(
            "O periodo do calculo abrange anos fora da base de feriados carregada "
            f"({sorted(cal.anos)[0]}-{sorted(cal.anos)[-1]}); o resultado pode ignorar "
            "feriados nao cadastrados."
        )
    limite_cpc = date.fromisoformat(cal.meta.get("cpc_dias_uteis_desde", "2016-03-18"))
    if data_evento < limite_cpc:
        avisos.append(
            f"Evento anterior a {limite_cpc.strftime('%d/%m/%Y')} (vigencia da contagem em "
            "dias uteis do CPC/2015). Antes disso, prazos corriam em dias corridos."
        )

    memoria = _montar_memoria(cal, data_evento, data_publicacao, inicio, termo_final, modo)

    return ResultadoPrazo(
        data_evento=data_evento,
        modo=modo,
        dias_nominais=dias,
        dias_efetivos=n,
        dobro=dobro,
        data_publicacao=data_publicacao,
        inicio_contagem=inicio,
        termo_final=termo_final,
        descricao_prazo=descricao,
        memoria=memoria,
        avisos=avisos,
    )


def _montar_memoria(
    cal: CalendarioTJAM,
    data_evento: date,
    data_publicacao: date | None,
    inicio: date,
    termo_final: date,
    modo: str,
) -> list[PassoMemoria]:
    passos: list[PassoMemoria] = []
    indice = 0
    d = data_evento
    while d <= termo_final:
        cls = cal.classificar(d)
        contado = False
        idx = None
        categoria = cls.categoria
        detalhe = cls.detalhe

        if d == data_evento and modo in ("intimacao", "publicacao_diario"):
            categoria = "evento"
            detalhe = (
                "Disponibilizacao no DJe (art. 224, par. 2) - excluida"
                if modo == "publicacao_diario"
                else "Dia da intimacao/ciencia - excluido (art. 224)"
            )
        elif d == data_publicacao:
            categoria = "publicacao"
            detalhe = "Data de publicacao (art. 224, par. 2) - excluida; contagem inicia no dia util seguinte"
        elif d >= inicio and cls.corre_prazo:
            indice += 1
            idx = indice
            contado = True

        passos.append(PassoMemoria(
            data=d,
            dia_semana=DIAS_SEMANA[d.weekday()],
            contado=contado,
            indice=idx,
            categoria=categoria,
            detalhe=detalhe,
        ))
        d += timedelta(days=1)
    return passos
