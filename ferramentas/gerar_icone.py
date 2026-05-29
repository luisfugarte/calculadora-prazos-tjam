#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_icone.py — Gera o icone da aplicacao (calendario com check verde) em PNG e ICO.
Desenha em alta resolucao e reduz, para bordas suaves. Usa apenas Pillow.

Uso:  python ferramentas/gerar_icone.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
PNG = RAIZ / "calculadora_icon.png"
ICO = RAIZ / "calculadora_icon.ico"

AZUL = (67, 97, 238)
AZUL_ESC = (58, 86, 212)
CIANO = (76, 201, 240)
VERDE = (45, 158, 110)
ESCURO = (24, 24, 46)
BRANCO = (255, 255, 255)

S = 1024  # resolucao de desenho


def fundo_gradiente() -> Image.Image:
    faixa = Image.new("RGB", (1, S))
    for y in range(S):
        t = y / (S - 1)
        faixa.putpixel((0, y), (
            int(AZUL[0] + (AZUL_ESC[0] - AZUL[0]) * t),
            int(AZUL[1] + (AZUL_ESC[1] - AZUL[1]) * t),
            int(AZUL[2] + (AZUL_ESC[2] - AZUL[2]) * t),
        ))
    return faixa.resize((S, S)).convert("RGBA")


def gerar() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # quadrado arredondado com gradiente
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [S * 0.06, S * 0.06, S * 0.94, S * 0.94], radius=S * 0.20, fill=255)
    img.paste(fundo_gradiente(), (0, 0), mask)

    d = ImageDraw.Draw(img)

    # corpo do calendario (branco)
    cl, cr, ct, cb = S * 0.23, S * 0.77, S * 0.33, S * 0.75
    d.rounded_rectangle([cl, ct, cr, cb], radius=S * 0.05, fill=BRANCO)

    # faixa superior (ciano)
    hb = ct + S * 0.11
    d.rounded_rectangle([cl, ct, cr, hb], radius=S * 0.05, fill=CIANO)
    d.rectangle([cl, ct + S * 0.06, cr, hb], fill=CIANO)

    # argolas do calendario
    for cx in (cl + (cr - cl) * 0.30, cl + (cr - cl) * 0.70):
        d.rounded_rectangle(
            [cx - S * 0.016, ct - S * 0.045, cx + S * 0.016, ct + S * 0.035],
            radius=S * 0.016, fill=ESCURO)

    # check verde no corpo
    p1 = (cl + (cr - cl) * 0.20, ct + (cb - ct) * 0.58)
    p2 = (cl + (cr - cl) * 0.43, ct + (cb - ct) * 0.80)
    p3 = (cl + (cr - cl) * 0.82, ct + (cb - ct) * 0.32)
    w = int(S * 0.05)
    d.line([p1, p2, p3], fill=VERDE, width=w, joint="curve")
    for pt in (p1, p2, p3):  # arredonda as pontas
        d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=VERDE)

    return img


def main():
    img = gerar()
    icone = img.resize((256, 256), Image.LANCZOS)
    icone.save(PNG)
    icone.save(ICO, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"PNG: {PNG}")
    print(f"ICO: {ICO}")


if __name__ == "__main__":
    main()
