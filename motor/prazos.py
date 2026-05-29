#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prazos.py — Catalogo de prazos nomeados do CPC (dias uteis) e atalho de calculo.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .calendario import CalendarioTJAM
from .prazo import ResultadoPrazo, calcular_prazo
from .recursos import caminho_recurso

CAMINHO_PADRAO = caminho_recurso("dados/prazos_cpc.json")


@dataclass(frozen=True)
class PrazoNomeado:
    id: str
    nome: str
    dias: int
    categoria: str
    fundamento: str
    admite_dobro: bool
    observacao: str


class CatalogoPrazos:
    def __init__(self, caminho: str | Path | None = None):
        dados = json.loads(Path(caminho or CAMINHO_PADRAO).read_text(encoding="utf-8"))
        self.meta = dados["meta"]
        self.categorias: list[str] = self.meta["categorias"]
        self._por_id: dict[str, PrazoNomeado] = {}
        self.itens: list[PrazoNomeado] = []
        for p in dados["prazos"]:
            item = PrazoNomeado(
                id=p["id"], nome=p["nome"], dias=int(p["dias"]),
                categoria=p["categoria"], fundamento=p["fundamento"],
                admite_dobro=bool(p["admite_dobro"]), observacao=p.get("observacao", ""),
            )
            if item.id in self._por_id:
                raise ValueError(f"id de prazo duplicado: {item.id!r}")
            self._por_id[item.id] = item
            self.itens.append(item)

    def obter(self, prazo_id: str) -> PrazoNomeado:
        return self._por_id[prazo_id]

    def por_categoria(self, categoria: str) -> list[PrazoNomeado]:
        return [p for p in self.itens if p.categoria == categoria]


def calcular_prazo_nomeado(
    cal: CalendarioTJAM,
    catalogo: CatalogoPrazos,
    prazo_id: str,
    data_evento: date,
    modo: str = "intimacao",
    dobro: bool = False,
) -> ResultadoPrazo:
    prazo = catalogo.obter(prazo_id)
    return calcular_prazo(
        cal, data_evento, prazo.dias, modo=modo, dobro=dobro,
        descricao=f"{prazo.nome} ({prazo.fundamento})",
    )
