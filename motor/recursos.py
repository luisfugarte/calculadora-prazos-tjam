#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recursos.py — Resolve o caminho de arquivos de dados tanto em desenvolvimento
quanto dentro de um executavel PyInstaller (onde os recursos sao extraidos
para sys._MEIPASS).
"""
from __future__ import annotations

import sys
from pathlib import Path


def caminho_recurso(relativo: str) -> Path:
    """Caminho absoluto de um recurso (ex.: 'dados/feriados_tjam.json')."""
    base = getattr(sys, "_MEIPASS", None)
    if base:  # rodando empacotado (PyInstaller)
        return Path(base) / relativo
    # rodando do codigo-fonte: raiz do projeto = pai do diretorio 'motor'
    return Path(__file__).resolve().parent.parent / relativo
