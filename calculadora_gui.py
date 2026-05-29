#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculadora_gui.py — Interface grafica da Calculadora de Prazos Processuais Civeis (TJAM).

Stack: CustomTkinter (mesmo padrao visual do anonimizador).
Nucleo de calculo: pacote `motor` (engine testado).
"""
from __future__ import annotations

import calendar as _cal
from datetime import date, datetime
from tkinter import messagebox

import customtkinter as ctk

from motor import CalendarioTJAM, CatalogoPrazos, calcular_prazo
from motor.calendario import DIAS_SEMANA

# ── Paleta (consistente com o anonimizador) ─────────────────────────────────────
AZUL = "#4361ee"
AZUL_HOVER = "#3a56d4"
VERDE = "#2d9e6e"
VERDE_HOVER = "#248a5e"
CIANO = "#4cc9f0"
AVISO = "#f0a500"
ERRO_COR = "#ff6b6b"
FUNDO_CAIXA = ("gray88", "#1a1a2e")
NAO_UTIL_BG = ("#f3c9cf", "#3a2030")
NAO_UTIL_FG = ("#9c2633", "#ff8fa0")

MODOS = {
    "Intimacao / ciencia": "intimacao",
    "Publicacao no DJe": "publicacao_diario",
    "Inicio direto": "inicio_direto",
}
AJUDA_MODO = {
    "intimacao": "Exclui o dia da intimacao; inicia no 1o dia util seguinte (art. 224).",
    "publicacao_diario": "Data = disponibilizacao no DJe; aplica art. 224, §2 e §3.",
    "inicio_direto": "Data = 1o dia da contagem (vai ao proximo dia util, se preciso).",
}
MESES = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DOW = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]


def _fmt(d: date) -> str:
    return f"{d.strftime('%d/%m/%Y')} ({DIAS_SEMANA[d.weekday()]})"


# ════════════════════════════════════════════════════════════════════════════════
# POPUP DE CALENDARIO (tambem mostra dias nao uteis em vermelho)
# ════════════════════════════════════════════════════════════════════════════════
class CalendarioPopup(ctk.CTkToplevel):
    def __init__(self, master, calendario: CalendarioTJAM, data_inicial: date, on_select):
        super().__init__(master)
        self.title("Selecionar data")
        self.geometry("320x340")
        self.resizable(False, False)
        self._calendario = calendario
        self._on_select = on_select
        self._ano = data_inicial.year
        self._mes = data_inicial.month
        self._sel = data_inicial

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=8, pady=(10, 4))
        ctk.CTkButton(topo, text="‹", width=32, command=self._mes_anterior).pack(side="left")
        self._lbl = ctk.CTkLabel(topo, font=ctk.CTkFont(size=14, weight="bold"))
        self._lbl.pack(side="left", expand=True)
        ctk.CTkButton(topo, text="›", width=32, command=self._mes_seguinte).pack(side="right")

        self._grade = ctk.CTkFrame(self, fg_color="transparent")
        self._grade.pack(fill="both", expand=True, padx=8, pady=4)

        ctk.CTkLabel(self, text="Vermelho = dia nao util (TJAM)",
                     font=ctk.CTkFont(size=10), text_color=ERRO_COR).pack(pady=(0, 8))

        self.after(60, self._tornar_modal)
        self._render()

    def _tornar_modal(self):
        try:
            self.grab_set()
        except Exception:
            pass

    def _mes_anterior(self):
        self._mes -= 1
        if self._mes < 1:
            self._mes, self._ano = 12, self._ano - 1
        self._render()

    def _mes_seguinte(self):
        self._mes += 1
        if self._mes > 12:
            self._mes, self._ano = 1, self._ano + 1
        self._render()

    def _render(self):
        for w in self._grade.winfo_children():
            w.destroy()
        self._lbl.configure(text=f"{MESES[self._mes - 1]} {self._ano}")
        for c in range(7):
            self._grade.grid_columnconfigure(c, weight=1)
            ctk.CTkLabel(self._grade, text=DOW[c], font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="gray60").grid(row=0, column=c, padx=1, pady=1)
        semanas = _cal.Calendar(firstweekday=6).monthdayscalendar(self._ano, self._mes)
        for r, semana in enumerate(semanas, start=1):
            for c, dia in enumerate(semana):
                if dia == 0:
                    continue
                d = date(self._ano, self._mes, dia)
                nao_util = not self._calendario.corre_prazo(d)
                if d == self._sel:
                    fg, hover, txt, borda = AZUL, AZUL_HOVER, "white", 0
                elif nao_util:
                    fg, hover, txt, borda = NAO_UTIL_BG, NAO_UTIL_BG, NAO_UTIL_FG, 0
                else:
                    fg, hover, txt, borda = "transparent", AZUL, ("gray10", "gray90"), 1
                ctk.CTkButton(
                    self._grade, text=str(dia), width=36, height=30,
                    fg_color=fg, hover_color=hover, text_color=txt,
                    border_width=borda, border_color="gray40",
                    font=ctk.CTkFont(size=12),
                    command=lambda dd=d: self._escolher(dd),
                ).grid(row=r, column=c, padx=1, pady=1, sticky="nsew")

    def _escolher(self, d: date):
        self._on_select(d)
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════════
# JANELA PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════════
class CalculadoraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Prazos Processuais — TJAM")
        self.geometry("1000x680")
        self.minsize(920, 620)

        self.calendario = CalendarioTJAM()
        self.catalogo = CatalogoPrazos()
        self._nome_para_id: dict[str, str] = {}

        self._cabecalho()
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=16, pady=14)
        self._painel_esquerdo(corpo)
        self._painel_direito(corpo)
        self._trocar_tipo(self.tipo_var.get())
        self._atualizar_prazos()

    # ── cabecalho ───────────────────────────────────────────────────────────────
    def _cabecalho(self):
        hdr = ctk.CTkFrame(self, corner_radius=0, height=60, fg_color=("gray82", "#0f0f24"))
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚖  Calculadora de Prazos Processuais",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=CIANO).pack(side="left", padx=20)
        ctk.CTkLabel(hdr, text="TJAM  |  CPC/2015 — dias uteis (art. 219, 220, 224, 229)  |  2016–2026",
                     font=ctk.CTkFont(size=11), text_color="gray55").pack(side="left", padx=6)
        ctk.CTkSegmentedButton(hdr, values=["Escuro", "Claro"], width=120,
                               command=lambda v: ctk.set_appearance_mode("dark" if v == "Escuro" else "light"),
                               font=ctk.CTkFont(size=11)).pack(side="right", padx=16)

    # ── painel esquerdo (entradas) ────────────────────────────────────────────────
    def _painel_esquerdo(self, parent):
        esq = ctk.CTkScrollableFrame(parent, width=350, corner_radius=12)
        esq.pack(side="left", fill="y", padx=(0, 14))

        ctk.CTkLabel(esq, text="Tipo de calculo",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.tipo_var = ctk.StringVar(value="Prazo nomeado")
        ctk.CTkSegmentedButton(esq, values=["Prazo nomeado", "Contador de dias"],
                               variable=self.tipo_var, command=self._trocar_tipo).pack(fill="x", padx=16)

        self.frm_entrada = ctk.CTkFrame(esq, fg_color="transparent")
        self.frm_entrada.pack(fill="x")

        # --- prazo nomeado ---
        self.frm_nomeado = ctk.CTkFrame(self.frm_entrada, fg_color="transparent")
        self.cat_var = ctk.StringVar(value=self.catalogo.categorias[0])
        ctk.CTkOptionMenu(self.frm_nomeado, variable=self.cat_var,
                          values=self.catalogo.categorias,
                          command=lambda *_: self._atualizar_prazos()).pack(fill="x", padx=16, pady=(10, 4))
        self.prazo_var = ctk.StringVar()
        self.menu_prazo = ctk.CTkOptionMenu(self.frm_nomeado, variable=self.prazo_var, values=[""],
                                            command=lambda *_: self._mostrar_info_prazo())
        self.menu_prazo.pack(fill="x", padx=16, pady=4)
        self.lbl_info = ctk.CTkLabel(self.frm_nomeado, text="", font=ctk.CTkFont(size=11),
                                     text_color="gray60", wraplength=300, justify="left")
        self.lbl_info.pack(anchor="w", padx=16, pady=(2, 6))

        # --- contador ---
        self.frm_contador = ctk.CTkFrame(self.frm_entrada, fg_color="transparent")
        ctk.CTkLabel(self.frm_contador, text="Numero de dias uteis",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(10, 2))
        self.ent_dias = ctk.CTkEntry(self.frm_contador, placeholder_text="ex.: 15")
        self.ent_dias.pack(fill="x", padx=16, pady=(0, 6))

        self._sep(esq)

        # --- termo inicial ---
        ctk.CTkLabel(esq, text="Termo inicial",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(0, 4))
        self.modo_var = ctk.StringVar(value=list(MODOS.keys())[0])
        ctk.CTkOptionMenu(esq, variable=self.modo_var, values=list(MODOS.keys()),
                          command=lambda *_: self._atualizar_ajuda_modo()).pack(fill="x", padx=16)
        self.lbl_ajuda = ctk.CTkLabel(esq, text=AJUDA_MODO["intimacao"], font=ctk.CTkFont(size=11),
                                      text_color="gray60", wraplength=300, justify="left")
        self.lbl_ajuda.pack(anchor="w", padx=16, pady=(4, 6))

        self._sep(esq)

        # --- data do evento ---
        ctk.CTkLabel(esq, text="Data do evento",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(0, 4))
        linha = ctk.CTkFrame(esq, fg_color="transparent")
        linha.pack(fill="x", padx=16)
        self.ent_data = ctk.CTkEntry(linha, placeholder_text="dd/mm/aaaa")
        self.ent_data.pack(side="left", fill="x", expand=True)
        self.ent_data.insert(0, date.today().strftime("%d/%m/%Y"))
        ctk.CTkButton(linha, text="📅", width=42, command=self._abrir_calendario).pack(side="left", padx=(6, 0))

        self.dobro_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(esq, text="Prazo em dobro (art. 229/180/183/186)",
                        variable=self.dobro_var, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkButton(esq, text="▶  CALCULAR", height=46,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=VERDE, hover_color=VERDE_HOVER,
                      command=self._calcular).pack(fill="x", padx=16, pady=(8, 14))

    # ── painel direito (resultado) ──────────────────────────────────────────────
    def _painel_direito(self, parent):
        dir_ = ctk.CTkFrame(parent, corner_radius=12)
        dir_.pack(side="left", fill="both", expand=True)

        card = ctk.CTkFrame(dir_, fg_color=FUNDO_CAIXA, corner_radius=10)
        card.pack(fill="x", padx=14, pady=(14, 6))
        ctk.CTkLabel(card, text="TERMO FINAL", font=ctk.CTkFont(size=12),
                     text_color="gray60").pack(anchor="w", padx=16, pady=(10, 0))
        self.lbl_termo = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=26, weight="bold"),
                                      text_color=CIANO)
        self.lbl_termo.pack(anchor="w", padx=16, pady=(0, 4))
        self.lbl_resumo = ctk.CTkLabel(card, text="Preencha os dados e clique em CALCULAR.",
                                       font=ctk.CTkFont(size=12), text_color=("gray20", "gray75"),
                                       justify="left", wraplength=540)
        self.lbl_resumo.pack(anchor="w", padx=16, pady=(0, 10))

        self.lbl_avisos = ctk.CTkLabel(dir_, text="", font=ctk.CTkFont(size=11), text_color=AVISO,
                                       justify="left", wraplength=560)
        self.lbl_avisos.pack(anchor="w", padx=18, pady=(0, 2))

        barra = ctk.CTkFrame(dir_, fg_color="transparent")
        barra.pack(fill="x", padx=14)
        ctk.CTkLabel(barra, text="Memoria de calculo",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", pady=(4, 2))
        ctk.CTkButton(barra, text="Copiar", width=80, height=26,
                      fg_color="transparent", border_width=1, text_color=("gray20", "gray75"),
                      command=self._copiar).pack(side="right", pady=(4, 2))

        self.txt = ctk.CTkTextbox(dir_, font=ctk.CTkFont(family="Courier New", size=12), wrap="none")
        self.txt.pack(fill="both", expand=True, padx=14, pady=(2, 14))
        self.txt.tag_config("contado", foreground=VERDE)
        self.txt.tag_config("pulado", foreground="#8a8a8a")
        self.txt.tag_config("evento", foreground=CIANO)
        self.txt.tag_config("cab", foreground=AZUL)
        self.txt.configure(state="disabled")

    # ── utilitarios de UI ─────────────────────────────────────────────────────────
    @staticmethod
    def _sep(parent):
        ctk.CTkFrame(parent, height=1, fg_color="gray35").pack(fill="x", padx=16, pady=12)

    def _trocar_tipo(self, valor: str):
        self.frm_nomeado.pack_forget()
        self.frm_contador.pack_forget()
        if valor == "Prazo nomeado":
            self.frm_nomeado.pack(fill="x")
        else:
            self.frm_contador.pack(fill="x")

    def _atualizar_prazos(self):
        itens = self.catalogo.por_categoria(self.cat_var.get())
        self._nome_para_id = {p.nome: p.id for p in itens}
        nomes = list(self._nome_para_id.keys())
        self.menu_prazo.configure(values=nomes)
        if nomes:
            self.prazo_var.set(nomes[0])
        self._mostrar_info_prazo()

    def _mostrar_info_prazo(self):
        pid = self._nome_para_id.get(self.prazo_var.get())
        if not pid:
            self.lbl_info.configure(text="")
            return
        p = self.catalogo.obter(pid)
        texto = f"{p.dias} dias uteis — {p.fundamento}"
        if not p.admite_dobro:
            texto += "\n(nao admite dobro)"
        if p.observacao:
            texto += f"\n{p.observacao}"
        self.lbl_info.configure(text=texto)

    def _atualizar_ajuda_modo(self):
        self.lbl_ajuda.configure(text=AJUDA_MODO[MODOS[self.modo_var.get()]])

    def _parse_data(self) -> date | None:
        bruto = self.ent_data.get().strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(bruto, fmt).date()
            except ValueError:
                continue
        messagebox.showerror("Data invalida", f"Nao entendi a data {bruto!r}.\nUse o formato dd/mm/aaaa.")
        return None

    def _abrir_calendario(self):
        inicial = self._parse_data_silencioso() or date.today()
        CalendarioPopup(self, self.calendario, inicial, self._definir_data)

    def _parse_data_silencioso(self) -> date | None:
        bruto = self.ent_data.get().strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(bruto, fmt).date()
            except ValueError:
                continue
        return None

    def _definir_data(self, d: date):
        self.ent_data.delete(0, "end")
        self.ent_data.insert(0, d.strftime("%d/%m/%Y"))

    # ── calculo ────────────────────────────────────────────────────────────────────
    def _calcular(self):
        d = self._parse_data()
        if d is None:
            return

        descricao = None
        if self.tipo_var.get() == "Prazo nomeado":
            pid = self._nome_para_id.get(self.prazo_var.get())
            if not pid:
                messagebox.showerror("Prazo", "Selecione um prazo nomeado.")
                return
            prazo = self.catalogo.obter(pid)
            dias = prazo.dias
            descricao = f"{prazo.nome} ({prazo.fundamento})"
            if self.dobro_var.get() and not prazo.admite_dobro:
                messagebox.showwarning(
                    "Prazo em dobro",
                    f"O prazo '{prazo.nome}' nao admite dobro; calculando sem dobrar.")
                dobro = False
            else:
                dobro = self.dobro_var.get()
        else:
            try:
                dias = int(self.ent_dias.get().strip())
                if dias < 1:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Numero de dias", "Informe um numero inteiro de dias >= 1.")
                return
            dobro = self.dobro_var.get()

        modo = MODOS[self.modo_var.get()]
        try:
            r = calcular_prazo(self.calendario, d, dias, modo=modo, dobro=dobro, descricao=descricao)
        except ValueError as e:
            messagebox.showerror("Erro de calculo", str(e))
            return
        self._mostrar_resultado(r)

    def _mostrar_resultado(self, r):
        self.lbl_termo.configure(
            text=f"{r.termo_final.strftime('%d/%m/%Y')}  ({DIAS_SEMANA[r.termo_final.weekday()]})")

        partes = []
        if r.descricao_prazo:
            partes.append(r.descricao_prazo)
        partes.append(f"Evento: {_fmt(r.data_evento)}")
        if r.data_publicacao:
            partes.append(f"Publicacao (DJe): {_fmt(r.data_publicacao)}")
        partes.append(f"Inicio: {_fmt(r.inicio_contagem)}")
        prazo_txt = f"{r.dias_nominais} dias uteis"
        if r.dobro:
            prazo_txt += f" em dobro = {r.dias_efetivos}"
        partes.append(f"Prazo: {prazo_txt}")
        self.lbl_resumo.configure(text="\n".join(partes))

        self.lbl_avisos.configure(text="\n".join(f"⚠ {a}" for a in r.avisos))

        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("end", f"{'Data':<12}{'Dia da semana':<16}{'#':>3}  Motivo\n", "cab")
        self.txt.insert("end", "-" * 64 + "\n", "cab")
        for p in r.memoria:
            num = str(p.indice) if p.contado else ""
            linha = f"{p.data.strftime('%d/%m/%Y'):<12}{p.dia_semana:<16}{num:>3}  {p.detalhe}\n"
            if p.contado:
                tag = "contado"
            elif p.categoria in ("evento", "publicacao"):
                tag = "evento"
            else:
                tag = "pulado"
            self.txt.insert("end", linha, tag)
        self.txt.configure(state="disabled")
        self._ultimo_texto = self.lbl_termo.cget("text")

    def _copiar(self):
        try:
            conteudo = "TERMO FINAL: " + self.lbl_termo.cget("text") + "\n\n"
            conteudo += self.lbl_resumo.cget("text") + "\n\n"
            conteudo += self.txt.get("1.0", "end")
            self.clipboard_clear()
            self.clipboard_append(conteudo)
        except Exception:
            pass


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = CalculadoraApp()
    app.mainloop()


if __name__ == "__main__":
    main()
