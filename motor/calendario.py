#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calendario.py — Carrega a base de dias nao uteis do TJAM e classifica cada data.

Regras aplicadas pelo motor (nao listadas dia a dia na base):
  - Sabados e domingos.
  - Suspensao do curso dos prazos (CPC, art. 220): 20/12 a 20/01, inclusive.
    O recesso forense do TJAM (20/12 a 06/01) esta contido nessa janela.
A base JSON traz feriados (nacional/estadual/municipal/forense/feriado),
pontos facultativos e eventuais suspensoes extraordinarias.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .recursos import caminho_recurso

CAMINHO_PADRAO = caminho_recurso("dados/feriados_tjam.json")

DIAS_SEMANA = [
    "segunda-feira", "terca-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sabado", "domingo",
]

# Categorias possiveis para um dia.
UTIL = "util"
FIM_DE_SEMANA = "fim_de_semana"
RECESSO = "recesso"          # janela do art. 220 / recesso forense
SUSPENSAO = "suspensao"      # suspensao extraordinaria
FERIADO = "feriado"
FACULTATIVO = "facultativo"


@dataclass(frozen=True)
class Feriado:
    data: date
    tipo: str
    descricao: str


@dataclass(frozen=True)
class Classificacao:
    """Resultado de classificar um dia."""
    corre_prazo: bool
    categoria: str
    detalhe: str


class CalendarioTJAM:
    def __init__(self, caminho: str | Path | None = None):
        dados = json.loads(Path(caminho or CAMINHO_PADRAO).read_text(encoding="utf-8"))
        self.meta = dados["meta"]
        self.anos: set[int] = set(self.meta["anos"])
        self.legenda: dict[str, str] = self.meta.get("legenda_tipos", {})

        self._feriados: dict[date, list[Feriado]] = {}
        for it in dados["feriados"]:
            d = date.fromisoformat(it["data"])
            self._feriados.setdefault(d, []).append(Feriado(d, it["tipo"], it["descricao"]))

        self._suspensoes: list[tuple[date, date, str]] = []
        for s in dados.get("suspensoes_extraordinarias", []):
            self._suspensoes.append((
                date.fromisoformat(s["inicio"]),
                date.fromisoformat(s["fim"]),
                s.get("descricao", "Suspensao extraordinaria de prazos"),
            ))

        a = self.meta["suspensao_art220"]
        self._art220_de = tuple(int(x) for x in a["de"].split("-"))    # (mes, dia) inicio em dezembro
        self._art220_ate = tuple(int(x) for x in a["ate"].split("-"))  # (mes, dia) fim em janeiro

    # ---- consultas elementares ----
    def em_art220(self, d: date) -> bool:
        md = (d.month, d.day)
        return md >= self._art220_de or md <= self._art220_ate

    def suspensao_no_dia(self, d: date) -> str | None:
        for ini, fim, desc in self._suspensoes:
            if ini <= d <= fim:
                return desc
        return None

    def feriados_no_dia(self, d: date) -> list[Feriado]:
        return self._feriados.get(d, [])

    def _label(self, tipo: str) -> str:
        return self.legenda.get(tipo, tipo)

    def classificar(self, d: date) -> Classificacao:
        """Por que (ou nao) o prazo corre nesse dia. Ordem de prioridade do motivo."""
        if d.weekday() >= 5:
            return Classificacao(False, FIM_DE_SEMANA, DIAS_SEMANA[d.weekday()].capitalize())

        if self.em_art220(d):
            extras = self.feriados_no_dia(d)
            nota = ""
            if extras:
                nota = " (" + "; ".join(f.descricao for f in extras) + ")"
            return Classificacao(
                False, RECESSO,
                f"Recesso forense / suspensao de prazos (CPC, art. 220){nota}",
            )

        susp = self.suspensao_no_dia(d)
        if susp:
            return Classificacao(False, SUSPENSAO, susp)

        feriados = self.feriados_no_dia(d)
        if feriados:
            so_facultativo = all(f.tipo == "facultativo" for f in feriados)
            categoria = FACULTATIVO if so_facultativo else FERIADO
            detalhe = "; ".join(f"{self._label(f.tipo)}: {f.descricao}" for f in feriados)
            return Classificacao(False, categoria, detalhe)

        return Classificacao(True, UTIL, "Dia util")

    def corre_prazo(self, d: date) -> bool:
        return self.classificar(d).corre_prazo

    # ---- navegacao por dias uteis ----
    def proximo_dia_util(self, d: date) -> date:
        """Menor dia util >= d (retorna o proprio d se ja for util)."""
        while not self.corre_prazo(d):
            d += timedelta(days=1)
        return d

    def dia_util_seguinte(self, d: date) -> date:
        """Menor dia util estritamente > d."""
        return self.proximo_dia_util(d + timedelta(days=1))

    def adicionar_dias_uteis(self, ancora: date, n: int) -> date:
        """Retorna o n-esimo dia util apos 'ancora' (a ancora e excluida). n >= 1."""
        if n < 1:
            raise ValueError("n deve ser >= 1")
        d = ancora
        contagem = 0
        while contagem < n:
            d += timedelta(days=1)
            if self.corre_prazo(d):
                contagem += 1
        return d

    def cobre_periodo(self, inicio: date, fim: date) -> bool:
        """True se todos os anos do periodo estao na base (para alertar sobre lacunas)."""
        return all(ano in self.anos for ano in range(inicio.year, fim.year + 1))
