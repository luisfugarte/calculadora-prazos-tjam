# -*- mode: python ; coding: utf-8 -*-
"""
Spec da Calculadora de Prazos Processuais Civeis (TJAM).
Executavel leve: customtkinter + biblioteca padrao. Embute os dados (JSON).
Build:  pyinstaller calculadora_gui.spec --noconfirm
"""
from PyInstaller.utils.hooks import collect_all

# customtkinter precisa dos seus temas/fontes; darkdetect e dependencia dele.
ctk_d, ctk_b, ctk_h = collect_all('customtkinter')
dd_d,  dd_b,  dd_h  = collect_all('darkdetect')

# Bases de dados embutidas (mantendo a pasta 'dados/' dentro do bundle).
dados = [
    ('dados/feriados_tjam.json', 'dados'),
    ('dados/prazos_cpc.json', 'dados'),
]

# Icone opcional: se existir 'calculadora_icon.ico' na pasta, e usado.
import os
ICONE = 'calculadora_icon.ico' if os.path.exists('calculadora_icon.ico') else None

a = Analysis(
    ['calculadora_gui.py'],
    pathex=[],
    binaries=ctk_b + dd_b,
    datas=ctk_d + dd_d + dados,
    hiddenimports=ctk_h + dd_h + [
        'tkinter', 'tkinter.messagebox',
        'customtkinter', 'darkdetect',
        'motor', 'motor.calendario', 'motor.prazo', 'motor.prazos', 'motor.recursos',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # NAO excluir PIL/Pillow: o customtkinter importa 'from PIL import Image'
        # ao ser carregado; sem ele o executavel fecha com "No module named 'PIL'".
        'numpy', 'pandas', 'scipy', 'matplotlib',
        'spacy', 'thinc', 'torch', 'tensorflow', 'sklearn',
        'pdfplumber', 'pdfminer', 'IPython', 'jupyter',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Calculadora_Prazos_TJAM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=ICONE,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
