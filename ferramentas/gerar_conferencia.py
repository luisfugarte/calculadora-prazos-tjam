#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_conferencia.py — Valida a base feriados_tjam.json e gera uma tabela de
conferencia (CSV) com o dia da semana de cada data, alem de checagens de sanidade.

Uso:
    python ferramentas/gerar_conferencia.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_JSON = RAIZ / "dados" / "feriados_tjam.json"
ARQ_CSV = RAIZ / "dados" / "conferencia_feriados.csv"

DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
TIPOS_VALIDOS = {"nacional", "estadual", "municipal", "forense", "feriado", "facultativo"}


def dentro_janela_art220(d: date) -> bool:
    """20/12 a 20/01, inclusive."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)


def main() -> int:
    base = json.loads(ARQ_JSON.read_text(encoding="utf-8"))
    feriados = base["feriados"]
    anos_meta = set(base["meta"]["anos"])

    erros: list[str] = []
    avisos: list[str] = []
    linhas: list[dict] = []

    por_data: dict[str, list[dict]] = defaultdict(list)
    por_ano_tipo: dict[int, Counter] = defaultdict(Counter)

    for item in feriados:
        bruto = item["data"]
        try:
            d = date.fromisoformat(bruto)
        except ValueError:
            erros.append(f"Data invalida: {bruto!r}")
            continue

        if item["tipo"] not in TIPOS_VALIDOS:
            erros.append(f"{bruto}: tipo desconhecido {item['tipo']!r}")
        if d.year not in anos_meta:
            avisos.append(f"{bruto}: ano fora dos anos declarados no meta")

        dia_sem = DIAS_SEMANA[d.weekday()]
        fim_de_semana = d.weekday() >= 5

        obs = []
        if fim_de_semana:
            obs.append("cai em fim de semana (redundante p/ calculo)")
        if dentro_janela_art220(d):
            obs.append("dentro da suspensao do art. 220 (redundante)")

        por_data[bruto].append(item)
        por_ano_tipo[d.year][item["tipo"]] += 1
        linhas.append({
            "data": bruto,
            "dia_semana": dia_sem,
            "tipo": item["tipo"],
            "descricao": item["descricao"],
            "observacao": "; ".join(obs),
        })

    # Duplicatas (mais de um motivo no mesmo dia) — esperado em 08/12.
    duplicatas = {k: v for k, v in por_data.items() if len(v) > 1}

    # Ordena por data.
    linhas.sort(key=lambda x: x["data"])

    with ARQ_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["data", "dia_semana", "tipo", "descricao", "observacao"])
        w.writeheader()
        w.writerows(linhas)

    # ---- Relatorio ----
    print("=" * 72)
    print("CONFERENCIA — feriados_tjam.json")
    print("=" * 72)
    print(f"Total de entradas: {len(feriados)}")
    print(f"CSV gerado em: {ARQ_CSV}")
    print()

    print("Entradas por ano e tipo:")
    for ano in sorted(por_ano_tipo):
        c = por_ano_tipo[ano]
        total = sum(c.values())
        det = ", ".join(f"{t}={c[t]}" for t in sorted(c))
        print(f"  {ano}: {total:>3}  ({det})")
    print()

    print(f"Datas com mais de um motivo (esperado em 08/12): {len(duplicatas)}")
    for k in sorted(duplicatas):
        descrs = " + ".join(i["descricao"] for i in duplicatas[k])
        print(f"  {k}: {descrs}")
    print()

    fds = [l for l in linhas if "fim de semana" in l["observacao"]]
    print(f"Feriados que caem em fim de semana (confira no PDF se procede): {len(fds)}")
    for l in fds:
        print(f"  {l['data']} ({l['dia_semana']}): {l['descricao']}")
    print()

    if avisos:
        print(f"AVISOS ({len(avisos)}):")
        for a in avisos:
            print(f"  - {a}")
        print()

    if erros:
        print(f"ERROS ({len(erros)}):")
        for e in erros:
            print(f"  - {e}")
        return 1

    print("OK — nenhum erro estrutural encontrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
