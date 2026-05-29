#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli_prazo.py — Testa o motor de calculo no terminal, com memoria de calculo.

Exemplos:
  python cli_prazo.py --data 08/07/2025 --dias 15
  python cli_prazo.py --data 08/07/2025 --dias 15 --modo publicacao_diario
  python cli_prazo.py --data 12/12/2024 --dias 15 --memoria
  python cli_prazo.py --data 08/07/2025 --dias 15 --dobro
"""
from __future__ import annotations

import argparse
from datetime import date

from motor import CalendarioTJAM, CatalogoPrazos, calcular_prazo
from motor.calendario import DIAS_SEMANA


def parse_data(s: str) -> date:
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"data invalida: {s!r} (use dd/mm/aaaa)")


def main() -> int:
    p = argparse.ArgumentParser(description="Calculadora de prazos processuais civeis - TJAM")
    p.add_argument("--data", type=parse_data,
                   help="data do evento (intimacao/disponibilizacao/inicio), dd/mm/aaaa")
    p.add_argument("--dias", type=int, help="numero de dias uteis do prazo")
    p.add_argument("--prazo", help="id de prazo nomeado do CPC (use --listar-prazos para ver)")
    p.add_argument("--modo", default="intimacao",
                   choices=["intimacao", "publicacao_diario", "inicio_direto"])
    p.add_argument("--dobro", action="store_true", help="prazo em dobro (art. 229/180/183/186)")
    p.add_argument("--memoria", action="store_true", help="exibe a memoria de calculo dia a dia")
    p.add_argument("--listar-prazos", action="store_true", help="lista o catalogo e sai")
    args = p.parse_args()

    catalogo = CatalogoPrazos()

    if args.listar_prazos:
        for cat in catalogo.categorias:
            print(f"\n# {cat}")
            for pr in catalogo.por_categoria(cat):
                print(f"  {pr.id:<28} {pr.dias:>2}d  {pr.nome}  [{pr.fundamento}]")
        return 0

    if not args.data or (args.dias is None and not args.prazo):
        p.error("informe --data e (--dias OU --prazo). Use --listar-prazos para ver os prazos.")

    cal = CalendarioTJAM()
    if args.prazo:
        pr = catalogo.obter(args.prazo)
        dias = pr.dias
        print(f"Prazo nomeado: {pr.nome} - {pr.dias} dias uteis ({pr.fundamento})")
        if pr.observacao:
            print(f"  nota: {pr.observacao}")
    else:
        dias = args.dias
    r = calcular_prazo(cal, args.data, dias, modo=args.modo, dobro=args.dobro)

    def fmt(d: date) -> str:
        return f"{d.strftime('%d/%m/%Y')} ({DIAS_SEMANA[d.weekday()]})"

    print("=" * 60)
    print(f"Evento ({args.modo}):  {fmt(r.data_evento)}")
    if r.data_publicacao:
        print(f"Publicacao (DJe):    {fmt(r.data_publicacao)}")
    print(f"Inicio da contagem:  {fmt(r.inicio_contagem)}")
    print(f"Prazo:               {r.dias_nominais} dias uteis"
          + (f" x2 = {r.dias_efetivos}" if r.dobro else ""))
    print("-" * 60)
    print(f">>> TERMO FINAL:     {fmt(r.termo_final)}")
    print("=" * 60)

    for a in r.avisos:
        print(f"[aviso] {a}")

    if args.memoria:
        print("\nMemoria de calculo:")
        for passo in r.memoria:
            marca = f"dia {passo.indice:>3}" if passo.contado else "       -"
            print(f"  {passo.data.strftime('%d/%m/%Y')} {passo.dia_semana:<13} {marca}  {passo.detalhe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
