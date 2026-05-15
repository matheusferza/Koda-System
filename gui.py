import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import ast
import csv
import shutil
import base64
from PIL import Image, ImageTk, ImageDraw
from branding import (
    APP_NAME,
    APP_VERSION,
    APP_SUBTITLE,
    APP_DESCRIPTION,
    APP_ABOUT_HEADING,
    APP_ABOUT_HIGHLIGHTS,
    COPYRIGHT_LABEL,
    POWERED_BY_LABEL,
    REPORT_FOOTER,
    REPORT_HEADER,
    format_window_title,
    get_page_title,
)
from datetime import datetime
import sqlite3
import json
import ctypes
import re
import win32print
import win32api
import win32ui
import io
import os
import sys

from dialogs import (
    CadastroProdutoDialog,
    CadastroFuncionarioDialog,
    EdicaoCarrinhoDialog,
    AdicionarItemDialog,
    EdicaoVendaDialog,
    OpenCloseCaixaDialog,
    ImprimirDialog,
    EmpresaInfoDialog,
    FinalizarVendaDialog,
)
from dialogs import build_dialog_shell, make_form_label, make_entry, style_button
from balanca import BalancaSerial
from utils import (
    DB_PATH,
    ensure_runtime_dir,
    get_app_icon_path,
    get_app_logo_path,
    resource_path,
)
from theme import APP_THEME, configure_ttk_styles
from database import (
    get_db_connection,
    setup_database,
    add_product,
    get_all_products,
    get_product_by_id,
    get_product_by_name,
    get_product_by_sku,
    get_product_by_barcode,
    get_product_by_code,
    update_product,
    filter_products_for_combobox,
    delete_product_db,
    add_employee,
    get_all_employees,
    get_employee_by_id,
    get_employee_by_username_and_password,
    is_manager,
    update_product_stock,
    add_sale,
    get_daily_sales,
    verify_and_add_initial_users,
    delete_sale_db,
    update_sale_db,
    get_sale_by_id,
    delete_employee_db,
    update_employee_db,
    get_cash_register_status,
    open_cash_register_db,
    close_cash_register_db,
    get_daily_sales_total,
    get_daily_sales_payment_summary,
    get_open_cash_register_initial_value,
    save_company_info,
    get_company_info,
    delete_company_info,
)
from barcode_labels import gerar_catalogo_codigos_barras
from interface_widgets import (
    create_caixa_layout,
    create_gerencia_layout,
    create_produtos_view,
    create_funcionarios_view,
    create_relatorios_view,
    create_relatorios_gerais_view,
    create_empresa_view,
)

from interface2 import (
    GerenciaView,
    ProdutosView,
    FuncionariosView,
    RelatoriosView,
    CaixaView,
    EmpresaView,
)


class FrutariaApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(format_window_title("Operação"))
        self.monitorando_balanca = True
        self.logged_user = None
        self.is_cash_register_open = False
        self.current_cash_register_id = None
        self.initial_cash_value = 0.0
        self.temp_logo_path = None
        self.current_page = None
        self.nav_buttons = {}
        self.theme = APP_THEME
        self.bg_color = self.theme["bg"]
        self.bg_color1 = self.theme["primary"]
        self.bg_color2 = self.theme["accent"]
        self.header_bg = self.theme["nav"]
        self.white_color = self.theme["surface"]
        self.black_color = "#000000"
        self.text_color = self.theme["text"]
        self.error_color = self.theme["danger"]
        self.success_color = self.theme["success"]
        self.header_color = self.theme["primary_dark"]
        self.btn_color = self.theme["primary"]
        self.grid_color = self.theme["border"]
        self.active_tab_color = self.theme["nav_active"]

        self.configure(bg=self.bg_color)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        initial_w = min(1440, max(760, screen_w - 20))
        initial_h = min(900, max(700, screen_h - 60))
        self.geometry(f"{initial_w}x{initial_h}")
        self.minsize(740, 680)
        self.is_fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.style = ttk.Style(self)
        configure_ttk_styles(self.style)
        self.carrinho_itens = []
        self.total_var = tk.StringVar(value="TOTAL: R$ 0,00")
        self.status_banner_var = tk.StringVar(value="Sistema pronto para operação.")
        self.cash_status_var = tk.StringVar(value="Caixa fechado")
        self.user_summary_var = tk.StringVar(value="")
        self.page_title_var = tk.StringVar(value="Painel")
        self.cart_count_var = tk.StringVar(value="0 itens")
        self.cart_volume_var = tk.StringVar(value="0,000")
        try:
            icon_path = get_app_icon_path()
            icon_image = Image.open(icon_path)
            self.icon_tk = ImageTk.PhotoImage(icon_image)
            self.iconphoto(False, self.icon_tk)
        except Exception as e:
            print(f"Erro ao carregar o í­cone: {e}")
        try:
            self.balanca = BalancaSerial(porta="AUTO")
            self.balanca_instance = self.balanca
        except Exception as e:
            messagebox.showerror(
                "Erro de Balança", f"Não foi possível conectar na COM3. Erro: {e}"
            )
            self.balanca = None
            self.balanca_instance = None
        self.frames = {}
        self.main_app_frame = tk.Frame(self, bg=self.bg_color)
        self.frames["main_app"] = self.main_app_frame
        self.nav_bar = tk.Frame(self.main_app_frame, bg=self.header_bg, width=220)
        self.container = tk.Frame(self.main_app_frame, bg=self.bg_color)
        self.caixa_frame = tk.Frame(self.container, bg=self.bg_color)
        self.gerencia_frame = tk.Frame(self.container, bg=self.bg_color)
        self.produtos_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.funcionarios_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.relatorios_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.empresa_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.frames.update(
            {
                "caixa": self.caixa_frame,
                "gerencia": self.gerencia_frame,
                "produtos_view": self.produtos_view_frame,
                "funcionarios_view": self.funcionarios_view_frame,
                "relatorios_view": self.relatorios_view_frame,
                "empresa_view": self.empresa_view_frame,
            }
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_main_app_layout()
        self.balanca_ativa = True
        self.balanca_is_active = False
        self.monitorar_balanca()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def _set_status_banner(self, message):
        self.status_banner_var.set(message)

    def _update_cash_status_chip(self):
        status_text = "Caixa aberto" if self.is_cash_register_open else "Caixa fechado"
        self.cash_status_var.set(status_text)
        if hasattr(self, "caixa_status_chip"):
            if self.is_cash_register_open:
                self.caixa_status_chip.config(
                    bg=self.theme.get("primary_soft", "#E6F4EA"),
                    fg=self.theme.get("primary_dark", self.bg_color1),
                )
            else:
                self.caixa_status_chip.config(
                    bg=self.theme.get("danger_soft", "#FEE2E2"),
                    fg=self.theme.get("danger", "#B91C1C"),
                )

    def _update_navigation_state(self):
        for page_name, button in self.nav_buttons.items():
            is_active = page_name == self.current_page
            button.configure(
                bg=self.active_tab_color if is_active else self.header_bg,
                fg=self.white_color,
                activebackground=self.active_tab_color,
            )

    def _apply_shell_for_page(self, page_name):
        cargo = self.logged_user.get("cargo") if self.logged_user else "Caixa"
        show_sidebar = cargo == "Gerente" and page_name != "caixa"

        if show_sidebar:
            if not self.nav_bar.winfo_manager():
                self.nav_bar.pack(side="left", fill="y")
            self.container.pack_forget()
            self.container.pack(
                side="left", fill="both", expand=True, padx=(0, 18), pady=18
            )
        else:
            if self.nav_bar.winfo_manager():
                self.nav_bar.pack_forget()
            self.container.pack_forget()
            self.container.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        for page_name, button in self.nav_buttons.items():
            is_active = page_name == self.current_page
            button.configure(
                bg=self.active_tab_color if is_active else self.header_bg,
                fg=self.white_color,
                activebackground=self.active_tab_color,
            )

    def _complete_cash_opening(self, valor_inicial, show_success=True):
        open_cash_register_db(valor_inicial)
        self.initial_cash_value = valor_inicial
        self.is_cash_register_open = True
        status = get_cash_register_status()
        self.current_cash_register_id = status.get("id")
        self._set_status_banner(
            f"Caixa aberto com troco inicial de R$ {valor_inicial:.2f}."
        )
        self.update_ui_state()
        if show_success:
            messagebox.showinfo(
                "Sucesso", f"Caixa aberto com R$ {valor_inicial:.2f}", parent=self
            )

    def _request_cash_opening_value(
        self, title, label_text, confirm_text="Iniciar Caixa"
    ):
        dialog = OpenCloseCaixaDialog(
            self,
            title,
            label_text,
            lambda valor: self._complete_cash_opening(valor, show_success=True),
            confirm_text=confirm_text,
        )
        return dialog.confirmed

    def _handle_cash_access_startup(self):
        cargo = self.logged_user.get("cargo") if self.logged_user else "Caixa"

        if cargo == "Gerente":
            self._set_status_banner("Informe o troco inicial para iniciar o caixa.")
            confirmed = self._request_cash_opening_value(
                "Iniciar Caixa",
                "Informe o valor inicial de troco para abrir o caixa.",
                confirm_text="Iniciar Caixa",
            )
            if not confirmed:
                self._set_status_banner(
                    "Caixa fechado. Informe o troco inicial para iniciar as vendas."
                )
            return

        self._set_status_banner("Abertura de caixa exige autorização do gerente.")
        autorizado = self.prompt_manager_credentials(
            "Insira as credênciais do gerente para liberar este caixa."
        )
        if not autorizado:
            messagebox.showwarning(
                    "Acesso não autorizado",
                    "O acesso ao caixa foi cancelado porque a autorização do gerente não foi informada.",
                parent=self,
            )
            self.after(100, self.destroy)
            return

        confirmed = self._request_cash_opening_value(
            "Troco Inicial do Caixa",
            "Informe o valor inicial de troco para este operador iniciar o caixa.",
            confirm_text="Liberar Caixa",
        )
        if not confirmed:
            messagebox.showinfo(
                "Acesso cancelado",
                "O caixa não foi iniciado. O aplicativo será encerrado.",
                parent=self,
            )
            self.after(100, self.destroy)

    def create_nav_buttons(self):
        """Cria a navegação lateral com identidade mais profissional."""
        if not self.logged_user:
            return

        for widget in self.nav_bar.winfo_children():
            widget.destroy()

        role = self.logged_user.get("cargo", "Caixa")
        user_name = self.logged_user.get("nome", "Usuário")
        self.user_summary_var.set(f"{user_name} | {role}")

        tiny_nav = self.winfo_screenwidth() <= 900 or self.winfo_screenheight() <= 780
        compact_nav = tiny_nav or (
            self.winfo_screenwidth() <= 1280 or self.winfo_screenheight() <= 800
        )
        nav_width = 112 if tiny_nav else (188 if compact_nav else 220)
        brand_logo_size = 24 if tiny_nav else (30 if compact_nav else 44)
        brand_title_font = (
            "Segoe UI Black",
            9 if tiny_nav else (12 if compact_nav else 14),
        )
        body_font = ("Segoe UI", 7 if tiny_nav else (8 if compact_nav else 9))
        button_font = (
            "Segoe UI Semibold",
            8 if tiny_nav else (10 if compact_nav else 11),
        )
        profile_name_font = (
            "Segoe UI Semibold",
            8 if tiny_nav else (10 if compact_nav else 12),
        )
        chip_font = (
            "Segoe UI Semibold",
            8 if tiny_nav else (10 if compact_nav else 11),
        )
        status_wrap = 84 if tiny_nav else (128 if compact_nav else 155)
        nav_outline = self.theme.get("nav_border", "#314238")
        nav_muted = self.theme.get("nav_muted", "#D9EBDD")
        nav_soft = self.theme.get("primary_soft", self.active_tab_color)

        self.nav_bar.configure(width=nav_width)
        self.nav_bar.pack_propagate(False)

        brand_frame = tk.Frame(
            self.nav_bar,
            bg=self.header_bg,
            padx=8 if tiny_nav else (14 if compact_nav else 18),
            pady=8 if tiny_nav else (14 if compact_nav else 18),
        )
        brand_frame.pack(fill="x")
        brand_top = tk.Frame(brand_frame, bg=self.header_bg)
        brand_top.pack(fill="x")
        brand_word_font = ("Segoe UI Black", 9 if tiny_nav else (11 if compact_nav else 13))

        brand_top.grid_columnconfigure(0, weight=0)
        brand_top.grid_columnconfigure(1, weight=1)
        try:
            logo_image = Image.open(get_app_logo_path()).resize(
                (brand_logo_size, brand_logo_size), Image.LANCZOS
            )
            self.nav_logo_tk = ImageTk.PhotoImage(logo_image)
            tk.Label(
                brand_top,
                image=self.nav_logo_tk,
                bg=self.header_bg,
            ).grid(
                row=0,
                column=0,
                rowspan=2,
                sticky="w",
                padx=(0, 8 if tiny_nav else (10 if compact_nav else 12)),
            )
        except Exception:
            self.nav_logo_tk = None

            tk.Label(
                brand_top,
                text="LOGO",
                font=("Segoe UI Semibold", 8 if tiny_nav else (9 if compact_nav else 10)),
                bg=self.header_bg,
                fg=nav_muted,
            ).grid(
                row=0,
                column=0,
                rowspan=2,
                sticky="w",
                padx=(0, 8 if tiny_nav else (10 if compact_nav else 12)),
            )

        tk.Label(
            brand_top,
            text="KODA",
            font=brand_word_font,
            bg=self.header_bg,
            fg=self.white_color,
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            brand_top,
            text="SYSTEM",
            font=brand_word_font,
            bg=self.header_bg,
            fg=self.white_color,
        ).grid(row=1, column=1, sticky="nw")
        #tk.Label(
        #    brand_frame,
        #    text=APP_SUBTITLE,
        #    wraplength=status_wrap,
        #    justify="left",
        #    font=body_font,
        #    bg=self.header_bg,
        #    fg="#D9EBDD",
        #).pack(anchor="w", pady=(8, 0))
        profile_frame = tk.Frame(
            self.nav_bar,
            bg=self.active_tab_color,
            padx=12 if compact_nav else 16,
            pady=10 if compact_nav else 14,
            highlightthickness=1,
            highlightbackground=nav_outline,
            bd=0,
        )
        profile_frame.pack(
            fill="x",
            padx=12 if compact_nav else 14,
            pady=(0, 14 if compact_nav else 18),
        )
        tk.Label(
            profile_frame,
            text=user_name,
            font=profile_name_font,
            bg=self.active_tab_color,
            fg=self.white_color,
            wraplength=status_wrap,
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            profile_frame,
            text=role,
            font=body_font,
            bg=self.active_tab_color,
            fg=nav_muted,
        ).pack(anchor="w", pady=(4, 0))

        nav_items = [("gerencia", "Gerência")]
        if role == "Gerente":
            nav_items.extend(
                [
                    ("produtos_view", "Produtos"),
                    ("funcionarios_view", "Funcionários"),
                    ("relatorios_view", "Relatórios"),
                    ("relatorios_gerais_view", "Histórico"),
                    ("empresa_view", "Empresa"),
                ]
            )


        nav_buttons_frame = tk.Frame(
            self.nav_bar, bg=self.header_bg, padx=12 if compact_nav else 14
        )
        nav_buttons_frame.pack(fill="x")
        tk.Label(
            nav_buttons_frame,
            text="NAVEGAÇÃO",
            font=("Segoe UI Semibold", 8 if compact_nav else 9),
            bg=self.header_bg,
            fg=nav_muted,
        ).pack(anchor="w", pady=(0, 8))
        self.nav_buttons = {}

        for page_name, label in nav_items:
            button = tk.Button(
                nav_buttons_frame,
                text=label,
                font=button_font,
                bg=self.header_bg,
                fg=self.white_color,
                relief="flat",
                activebackground=self.active_tab_color,
                activeforeground=self.white_color,
                bd=0,
                highlightthickness=1,
                highlightbackground=nav_outline,
                anchor="w",
                padx=12 if compact_nav else 18,
                pady=9 if compact_nav else 12,
                cursor="hand2",
                command=lambda name=page_name: self.show_frame(name),
            )
            button.pack(fill="x", pady=3 if compact_nav else 4)
            self.nav_buttons[page_name] = button

        status_frame = tk.Frame(
            self.nav_bar,
            bg=self.header_bg,
            padx=12 if compact_nav else 14,
            pady=12 if compact_nav else 14,
            highlightthickness=1,
            highlightbackground=nav_outline,
            bd=0,
        )
        status_frame.pack(side="bottom", fill="x", padx=12 if compact_nav else 14)
        tk.Label(
            status_frame,
            text="STATUS DA SESSÃO",
            font=("Segoe UI Semibold", 8 if compact_nav else 9),
            bg=self.header_bg,
            fg=nav_muted,
        ).pack(anchor="w")
        tk.Label(
            status_frame,
            textvariable=self.cash_status_var,
            font=chip_font,
            bg=nav_soft,
            fg=self.header_bg,
            padx=10,
            pady=6,
        ).pack(anchor="w", pady=(6, 2))
        tk.Label(
            status_frame,
            textvariable=self.status_banner_var,
            wraplength=status_wrap,
            justify="left",
            font=body_font,
            bg=self.header_bg,
            fg=nav_muted,
        ).pack(anchor="w", pady=(0, 12))
        tk.Label(
            status_frame,
            #text=f"{POWERED_BY_LABEL}\n{COPYRIGHT_LABEL}",
            text=f"{COPYRIGHT_LABEL}",
            wraplength=status_wrap,
            justify="left",
            font=("Segoe UI", 7 if compact_nav else 8),
            bg=self.header_bg,
            fg=nav_muted,
        ).pack(anchor="w", pady=(0, 12))

        about_button = tk.Button(
            status_frame,
            text="Sobre o sistema",
            command=self.show_about_dialog,
            font=("Segoe UI Semibold", 9 if compact_nav else 10),
            bg=self.theme.get("primary_soft", nav_soft),
            fg=self.text_color,
            activebackground=self.theme.get("primary_soft", nav_soft),
            activeforeground=self.text_color,
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=12 if compact_nav else 16,
            pady=8 if compact_nav else 10,
        )
        about_button.pack(fill="x", pady=(0, 8))

        tk.Button(
            status_frame,
            text="Sair do sistema",
            command=self.on_closing,
            font=("Segoe UI Semibold", 9 if compact_nav else 10),
            bg=self.bg_color2,
            fg=self.white_color,
            activebackground=self.theme.get("accent_dark", self.bg_color2),
            activeforeground=self.white_color,
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=12 if compact_nav else 16,
            pady=8 if compact_nav else 10,
        ).pack(fill="x")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self)
        theme, card, body = build_dialog_shell(
            about_window,
            self,
            title=f"Sobre o {APP_NAME}",
            subtitle=APP_ABOUT_HEADING,
            size=(760, 500),
            controller=self,
        )
        body.columnconfigure(0, weight=1)

        hero = tk.Frame(body, bg=theme["surface"])
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        hero.columnconfigure(1, weight=1)

        try:
            logo_image = Image.open(get_app_logo_path()).resize((74, 74), Image.LANCZOS)
            self.about_logo_tk = ImageTk.PhotoImage(logo_image)
            tk.Label(hero, image=self.about_logo_tk, bg=theme["surface"]).grid(
                row=0,
                column=0,
                rowspan=2,
                sticky="nw",
                padx=(0, 16),
            )
        except Exception:
            self.about_logo_tk = None

        tk.Label(
            hero,
            text=APP_NAME,
            font=("Segoe UI Black", 24),
            bg=theme["surface"],
            fg=theme["text"],
        ).grid(row=0, column=1, sticky="w")
        tk.Label(
            hero,
            text=f"Versao {APP_VERSION} | {APP_SUBTITLE}",
            font=("Segoe UI Semibold", 10),
            bg=theme["surface"],
            fg=theme["primary"],
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        description_card = tk.Frame(
            body,
            bg=theme["surface_alt"],
            padx=16,
            pady=16,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        description_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        tk.Label(
            description_card,
            text=APP_DESCRIPTION,
            font=("Segoe UI", 10),
            bg=theme["surface_alt"],
            fg=theme["text"],
            wraplength=640,
            justify="left",
        ).pack(anchor="w")

        highlights_card = tk.Frame(
            body,
            bg=theme["surface"],
            highlightthickness=1,
            highlightbackground=theme["border"],
            padx=16,
            pady=16,
        )
        highlights_card.grid(row=2, column=0, sticky="nsew")
        body.rowconfigure(2, weight=1)

        tk.Label(
            highlights_card,
            text="Recursos principais",
            font=("Segoe UI Semibold", 13),
            bg=theme["surface"],
            fg=theme["text"],
        ).pack(anchor="w")

        for item in APP_ABOUT_HIGHLIGHTS:
            tk.Label(
                highlights_card,
                text=f"- {item}",
                font=("Segoe UI", 10),
                bg=theme["surface"],
                fg=theme["text_muted"],
                wraplength=640,
                justify="left",
            ).pack(anchor="w", pady=(10, 0))

        footer = tk.Frame(body, bg=theme["surface"])
        footer.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        footer.columnconfigure(0, weight=1)

        tk.Label(
            footer,
            text=f"{POWERED_BY_LABEL} | {COPYRIGHT_LABEL}",
            font=("Segoe UI", 9),
            bg=theme["surface"],
            fg=theme["text_muted"],
        ).grid(row=0, column=0, sticky="w")

        close_button = tk.Button(footer, text="Fechar", command=about_window.destroy)
        style_button(close_button, "primary", theme)
        close_button.grid(row=0, column=1, sticky="e")

    def show_startup_alerts(self):
        """Sincroniza o estado inicial e direciona o usuário para o shell correto."""
        if self.logged_user:
            self._set_status_banner(f"Sessão iniciada por {self.logged_user['nome']}.")

        status_info = get_cash_register_status()
        if status_info["status"] == "aberto":
            self.is_cash_register_open = True
            self.current_cash_register_id = status_info["id"]
            self.initial_cash_value = status_info["valor_abertura"]
            self._set_status_banner(
                f"Caixa #{self.current_cash_register_id} retomado com abertura de R$ {self.initial_cash_value:.2f}."
            )
        else:
            self.is_cash_register_open = False
            self.current_cash_register_id = None
            self.initial_cash_value = 0.0
            if self.logged_user and self.logged_user.get("cargo") == "Gerente":
                self._set_status_banner(
                    "Gestão pronta. Abra o módulo Caixa quando quiser iniciar o atendimento."
                )
            else:
                self._set_status_banner(
                    "Caixa fechado. Aguarde autorização e informe o troco inicial."
                )

        self.update_ui_state()

    def on_closing(self):
        caixa_status = get_cash_register_status()
        caixa_aberto = caixa_status.get("status") == "aberto"

        if caixa_aberto:
            response = messagebox.askyesno(
                "Caixa Aberto",
                "O caixa ainda está aberto. Se sair agora, ele continuará aberto no sistema.\n\nDeseja sair mesmo assim?",
                parent=self,
            )
            if not response:
                print("Fechamento do aplicativo cancelado. Caixa permanece aberto.")
                return
            print("App fechado. Caixa mantido aberto no banco de dados para recuperacao.")
        else:
            print("App fechado. Caixa ja estava fechado.")

        try:
            if self.balanca:
                self.balanca.fechar()
        finally:
            self.destroy()

    def setup_interface_by_role(self):
        """Configura a casca principal da aplicações após o login."""
        self.main_app_frame.pack(fill="both", expand=True)
        self.create_nav_buttons()
        create_caixa_layout(self)

        initial_page = (
            "caixa"
            if self.logged_user and self.logged_user.get("cargo") == "Caixa"
            else "gerencia"
        )
        self.show_frame(initial_page)
        self.update_ui_state()

    def show_frame(self, page_name):
        """Mostra a página solicitada, atualiza o estado visual e recarrega dados."""
        if (
            page_name != "caixa"
            and self.logged_user
            and self.logged_user.get("cargo") != "Gerente"
        ):
            messagebox.showwarning(
                "Acesso Negado", "Você não tem permissão para acessar a Gerência."
            )
            return

        frame = self.frames.get(page_name)
        if frame is None:
            return

        self._apply_shell_for_page(page_name)

        if page_name == "caixa":
            create_caixa_layout(self)
            if not self.is_cash_register_open:
                self._handle_cash_access_startup()
                if (
                    self.logged_user
                    and self.logged_user.get("cargo") == "Caixa"
                    and not self.winfo_exists()
                ):
                    return
        elif page_name == "gerencia":
            create_gerencia_layout(self)
        elif page_name == "produtos_view":
            self.refresh_produtos_view()
        elif page_name == "funcionarios_view":
            self.refresh_funcionarios_view()
        elif page_name == "relatorios_view":
            self.update_daily_sales_report()
        elif page_name == "empresa_view":
            self.carregar_dados_empresa_na_tela()

        frame.tkraise()
        self.current_page = page_name
        self.page_title_var.set(get_page_title(page_name))
        self._update_navigation_state()

        if page_name == "caixa" and hasattr(self, "produto_entry"):
            self.produto_entry.focus_set()

    def create_main_app_layout(self):
        """Constrói os layouts dentro de cada frame."""
        for page_name, frame in self.frames.items():
            if page_name not in ["main_app"]:
                frame.place(x=0, y=0, relwidth=1, relheight=1)
        create_caixa_layout(self)
        create_gerencia_layout(self)

        create_produtos_view(self)

        create_funcionarios_view(self)
        create_relatorios_view(self)
        create_empresa_view(self)

        print("LAYOUTS: create_main_app_layout concluí­do.")

    '''def create_main_app_layout(self):
        """
        Constrói e registra as classes de interface dentro do container principal.
        Substitui a necessidade de chamar múltiplas funções de criações manuais.
        """
        print("LAYOUTS: Inicializando Views baseadas em Classes...")
        view_map = {
            "gerencia": GerenciaView,
            "caixa": CaixaView,
            "produtos": ProdutosView,
            "funcionarios": FuncionariosView,
            "relatorios": RelatoriosView,
            "empresa": EmpresaView
        }
        for page_name, ViewClass in view_map.items():
            print(f"LAYOUTS: Criando {page_name}...")
            frame = ViewClass(master=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        print("LAYOUTS: Todas as views foram instanciadas com sucesso.")'''

    def open_empresa_info_dialog(self):
        EmpresaInfoDialog(self)
        self.show_frame("empresa_view")
        self.carregar_dados_empresa_na_tela()

    def selecionar_logo(self):
        """Abre diálogo para escolher imagem."""
        file_path = filedialog.askopenfilename(
            title="Selecione a Logo da Empresa",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.ico")],
        )

        if file_path:
            self.temp_logo_path = file_path
            self.exibir_preview_logo(file_path)

    def exibir_preview_logo(self, path):
        """Atualiza o label de imagem na tela."""
        try:
            img = Image.open(path)
            img = img.resize((150, 150))
            photo = ImageTk.PhotoImage(img)
            self.logo_preview_label.config(image=photo, text="")
            self.logo_preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar imagem: {e}")

    def aplicar_mascara_cnpj(self, event=None):
        widget = self.empresa_cnpj_entry
        texto = widget.get()
        texto_limpo = "".join(filter(str.isdigit, texto))
        if len(texto_limpo) > 14:
            texto_limpo = texto_limpo[:14]

        novo_texto = ""
        for i, char in enumerate(texto_limpo):
            if i == 2 or i == 5:
                novo_texto += "."
            elif i == 8:
                novo_texto += "/"
            elif i == 12:
                novo_texto += "-"
            novo_texto += char

        if texto != novo_texto:
            widget.delete(0, tk.END)
            widget.insert(0, novo_texto)
            if event and event.keysym.lower() not in [
                "backspace",
                "delete",
                "left",
                "right",
            ]:
                widget.icursor(tk.END)

    def aplicar_mascara_telefone(self, event=None):
        widget = self.empresa_telefone_entry
        texto = widget.get()
        texto_limpo = "".join(filter(str.isdigit, texto))
        if len(texto_limpo) > 11:
            texto_limpo = texto_limpo[:11]

        novo_texto = ""
        if len(texto_limpo) > 0:
            novo_texto += "(" + texto_limpo[:2]
        if len(texto_limpo) > 2:
            novo_texto += ") "
            if len(texto_limpo) > 7:
                novo_texto += texto_limpo[2:7] + "-" + texto_limpo[7:]
            else:
                novo_texto += texto_limpo[2:6] + "-" + texto_limpo[6:]

        if texto != novo_texto:
            widget.delete(0, tk.END)
            widget.insert(0, novo_texto)
            if event and event.keysym.lower() not in [
                "backspace",
                "delete",
                "left",
                "right",
            ]:
                widget.icursor(tk.END)

    def aplicar_mascara_cep(self, event=None):
        """Aplica a máscara XXXXX-XXX no campo de CEP."""
        widget = self.empresa_cep_entry
        texto = widget.get()
        texto_limpo = "".join(filter(str.isdigit, texto))
        if len(texto_limpo) > 8:
            texto_limpo = texto_limpo[:8]

        novo_texto = ""
        for i, char in enumerate(texto_limpo):
            if i == 5:
                novo_texto += "-"
            novo_texto += char

        if texto != novo_texto:
            widget.delete(0, tk.END)
            widget.insert(0, novo_texto)
            if event and event.keysym.lower() not in [
                "backspace",
                "delete",
                "left",
                "right",
            ]:
                widget.icursor(tk.END)

    def set_empresa_inputs_state(self, state):
        """
        Define o estado dos campos de entrada.
        state: 'normal' (editável) ou 'readonly' (apenas leitura)
        """
        campos = [
            self.empresa_nome_entry,
            self.empresa_razao_entry,
            self.empresa_cnpj_entry,
            self.empresa_endereco_entry,
            self.empresa_bairro_entry,
            self.empresa_cidade_entry,
            self.empresa_estado_entry,
            self.empresa_cep_entry,
            self.empresa_telefone_entry,
            self.empresa_email_entry,
        ]

        tk_state = tk.NORMAL if state == "edit" else tk.DISABLED
        bg_color_active = self.white_color
        bg_color_disabled = "#F0F0F0"  # Cor de fundo quando desativado

        for entry in campos:
            entry.config(state=tk_state)
            entry.config(bg=bg_color_active if state == "edit" else bg_color_disabled)
        if hasattr(self, "btn_up_logo") and self.btn_up_logo is not None:
            if state == "edit":
                self.btn_up_logo.config(state=tk.NORMAL, bg="#2196F3", cursor="hand2")
            else:
                self.btn_up_logo.config(
                    state=tk.DISABLED, bg="#CCCCCC", cursor=""
                )  # Cor cinza para desativado

    def update_empresa_buttons(self, mode):
        """
        Atualiza os botões do rodapé baseado no modo.
        mode: 'edit' (botão Salvar) ou 'view' (botões Editar/Excluir)
        """
        for widget in self.empresa_footer_frame.winfo_children():
            widget.destroy()

        compact_mode = self.winfo_screenwidth() <= 1280 or self.winfo_screenheight() <= 800
        button_font = ("Segoe UI Semibold", 10 if compact_mode else 11)
        button_width = 18 if compact_mode else 20
        side_pad = 8 if compact_mode else 10

        if mode == "edit":
            btn_salvar = tk.Button(
                self.empresa_footer_frame,
                text="Salvar Dados",
                font=button_font,
                bg=self.bg_color1,
                fg="white",
                width=button_width,
                command=self.salvar_dados_empresa,
                relief="flat",
                cursor="hand2",
                pady=8 if compact_mode else 10,
            )
            btn_salvar.pack()

        elif mode == "view":
            btn_editar = tk.Button(
                self.empresa_footer_frame,
                text="EDITAR",
                font=button_font,
                bg="#FF9800",
                fg="white",
                width=button_width - 2,
                command=self.habilitar_edicao_empresa,
                relief="flat",
                cursor="hand2",
                pady=8 if compact_mode else 10,
            )
            btn_editar.pack(side="left", padx=side_pad, expand=True)

            btn_excluir = tk.Button(
                self.empresa_footer_frame,
                text="EXCLUIR",
                font=button_font,
                bg="#F44336",
                fg="white",
                width=button_width - 2,
                command=self.excluir_dados_empresa,
                relief="flat",
                cursor="hand2",
                pady=8 if compact_mode else 10,
            )
            btn_excluir.pack(side="left", padx=side_pad, expand=True)

    def habilitar_edicao_empresa(self):
        self.set_empresa_inputs_state("edit")
        self.update_empresa_buttons("edit")

    def excluir_dados_empresa(self):
        if messagebox.askyesno(
            "Confirmar", "Tem certeza que deseja excluir os dados da empresa?"
        ):
            try:
                delete_company_info()
                self.habilitar_edicao_empresa()

                campos = [
                    self.empresa_nome_entry,
                    self.empresa_razao_entry,
                    self.empresa_cnpj_entry,
                    self.empresa_endereco_entry,
                    self.empresa_bairro_entry,
                    self.empresa_cidade_entry,
                    self.empresa_estado_entry,
                    self.empresa_cep_entry,
                    self.empresa_telefone_entry,
                    self.empresa_email_entry,
                ]
                for entry in campos:
                    entry.delete(0, tk.END)

                self.logo_preview_label.config(image="", text="Sem Logo")
                self.temp_logo_path = None

                messagebox.showinfo("Sucesso", "Dados excluí­dos.")
                self.habilitar_edicao_empresa()

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}")

    def salvar_dados_empresa(self):
        """Coleta dados, salva e bloqueia a tela."""
        nome = self.empresa_nome_entry.get()
        razao = self.empresa_razao_entry.get()
        cnpj = self.empresa_cnpj_entry.get()
        endereco = self.empresa_endereco_entry.get()
        bairro = self.empresa_bairro_entry.get()
        cidade = self.empresa_cidade_entry.get()
        estado = self.empresa_estado_entry.get()
        cep = self.empresa_cep_entry.get()
        telefone = self.empresa_telefone_entry.get()
        email = self.empresa_email_entry.get()

        if not nome:
            messagebox.showwarning("Atenção", "O Nome Fantasia é obrigatório.")
            return
        logo_final_path = ""
        if self.temp_logo_path:
            try:
                dest_dir = ensure_runtime_dir("dados_empresa")

                file_ext = os.path.splitext(self.temp_logo_path)[1]
                logo_final_path = os.path.join(dest_dir, f"logo_empresa{file_ext}")
                shutil.copy(self.temp_logo_path, logo_final_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar arquivo de logo: {e}")
                return
        else:
            info_atual = get_company_info()
            if info_atual:
                logo_final_path = info_atual["logo_path"]

        try:
            save_company_info(
                nome,
                razao,
                cnpj,
                endereco,
                bairro,
                cidade,
                estado,
                cep,
                telefone,
                email,
                logo_final_path,
            )

            messagebox.showinfo("Sucesso", "Dados da empresa salvos com sucesso!")

            self.set_empresa_inputs_state("view")
            self.update_empresa_buttons("view")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar no banco: {e}")

    def carregar_dados_empresa_na_tela(self):
        info = get_company_info()
        self.set_empresa_inputs_state("edit")
        campos = [
            self.empresa_nome_entry,
            self.empresa_razao_entry,
            self.empresa_cnpj_entry,
            self.empresa_endereco_entry,
            self.empresa_bairro_entry,
            self.empresa_cidade_entry,
            self.empresa_estado_entry,
            self.empresa_cep_entry,
            self.empresa_telefone_entry,
            self.empresa_email_entry,
        ]
        for entry in campos:
            entry.delete(0, tk.END)

        if info:
            self.empresa_nome_entry.insert(0, info["nome_fantasia"] or "")
            self.empresa_razao_entry.insert(0, info["razao_social"] or "")
            self.empresa_cnpj_entry.insert(0, info["cnpj"] or "")
            self.empresa_endereco_entry.insert(0, info["endereco"] or "")
            self.empresa_bairro_entry.insert(0, info.get("bairro", "") or "")
            self.empresa_cidade_entry.insert(0, info["cidade"] or "")
            self.empresa_estado_entry.insert(0, info["estado"] or "")
            self.empresa_cep_entry.insert(0, info["cep"] or "")
            self.empresa_telefone_entry.insert(0, info["telefone"] or "")
            self.empresa_email_entry.insert(0, info["email"] or "")

            if info["logo_path"] and os.path.exists(info["logo_path"]):
                self.exibir_preview_logo(info["logo_path"])
            else:
                self.logo_preview_label.config(image="", text="Sem Logo")

            self.set_empresa_inputs_state("view")
            self.update_empresa_buttons("view")

        else:
            self.logo_preview_label.config(image="", text="Sem Logo")
            self.set_empresa_inputs_state("edit")
            self.update_empresa_buttons("edit")

    def refresh_produtos_view(self):
        from interface_widgets import load_produtos_to_treeview

        load_produtos_to_treeview(self)

    def refresh_funcionarios_view(self):
        from interface_widgets import load_funcionarios_to_treeview

        load_funcionarios_to_treeview(self)

    def salvar_produto_via_dialog(self, data):
        """Recebe dados do diálogo, valida, salva e atualiza a lista."""
        try:
            nome = data["nome"].strip()
            preco = float(str(data["preco"]).replace(",", "."))
            estoque = float(str(data["estoque"]).replace(",", "."))
            unidade = data["unidade"]
            cod_barras = data["cod_barras"].strip()
            sku = data["sku"].strip()

            if not nome or preco <= 0 or estoque < 0 or unidade not in ["kg", "un"]:
                messagebox.showerror(
                    "Erro",
                    "Por favor, preencha todos os campos obrigatórios corretamente (Nome, Preço > 0, Estoque >= 0, Unidade válida).",
                )
                return False

            add_product(nome, preco, estoque, unidade, sku, cod_barras)
            self.update_product_list()
            messagebox.showinfo("Sucesso", f"Produto '{nome}' adicionado com sucesso!")
            return True

        except ValueError:
            messagebox.showerror("Erro", "Preço e Estoque devem ser números válidos.")
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar produto: {e}")
            return False

    def open_cadastro_produto_dialog(self):
        """Abre o diálogo de cadastro de produto (chamado pelo Tile)."""
        CadastroProdutoDialog(self, controller=self)

    def exportar_relatorio_estoque_csv(self):
        produtos = get_all_products()
        if not produtos:
            messagebox.showinfo(
                "Relatório de Estoque",
                "Não há produtos cadastrados para exportar.",
                parent=self,
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar Relatório de Estoque",
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")],
            initialfile=f"relatorio_estoque_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        )
        if not file_path:
            return

        produtos = sorted(produtos, key=lambda item: str(item[1] or "").lower())
        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(
                ["id", "nome", "preco", "estoque", "unidade", "sku", "codigo_barras"]
            )
            writer.writerows(produtos)

        messagebox.showinfo(
            "Relatório de Estoque",
            f"Relatório exportado com sucesso para:\n{file_path}",
            parent=self,
        )

    def gerar_catalogo_etiquetas_codigos_barras(self):
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar Catálogo de Códigos de Barras",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile=f"catalogo_codigos_barras_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        )
        if not file_path:
            return

        try:
            resultado = gerar_catalogo_codigos_barras(file_path, gerar_imagens=True)
        except Exception as exc:
            messagebox.showerror(
                "Catálogo de Códigos",
                f"Não foi possível gerar as etiquetas.\nErro: {exc}",
                parent=self,
            )
            return

        abrir = messagebox.askyesno(
            "Catálogo de Códigos",
            (
                f"Catálogo gerado com sucesso com {resultado['total']} produto(s).\n\n"
                f"PDF:\n{resultado['pdf']}\n\n"
                "Deseja abrir o PDF agora?"
            ),
            parent=self,
        )
        if abrir:
            try:
                os.startfile(resultado["pdf"])
            except Exception as exc:
                messagebox.showwarning(
                    "Catálogo de Códigos",
                    f"O PDF foi gerado, mas não foi possível abrir automaticamente.\nErro: {exc}",
                    parent=self,
                )

    def baixar_template_importacao_produtos(self):
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar Template de Importação",
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")],
            initialfile="template_importacao_produtos.csv",
        )
        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(
                ["acao", "nome", "preco", "estoque", "unidade", "sku", "cod_barras"]
            )
            writer.writerow(["novo", "EXEMPLO PRODUTO", "4.95", "20", "un", "", ""])
            writer.writerow(["atualizar", "EXEMPLO PRODUTO", "5.45", "25", "un", "", ""])

        messagebox.showinfo(
            "Template de Importação",
            (
                "Template salvo com sucesso.\n\n"
                "A coluna 'acao' é opcional e aceita:\n"
                "- novo\n"
                "- atualizar\n\n"
                "Se SKU e código de barras forem deixados em branco, o sistema gera automaticamente."
            ),
            parent=self,
        )

    def importar_produtos_em_massa(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Selecionar CSV de Produtos",
            filetypes=[("Arquivo CSV", "*.csv")],
        )
        if not file_path:
            return

        duplicate_mode = messagebox.askyesnocancel(
            "Importação em Massa",
            (
                "Se o arquivo tiver produtos já cadastrados:\n\n"
                "Sim = atualizar os produtos existentes\n"
                "Não = ignorar os duplicados\n"
                "Cancelar = abortar a importação"
            ),
            parent=self,
        )
        if duplicate_mode is None:
            return
        update_existing = bool(duplicate_mode)

        try:
            with open(file_path, "r", encoding="utf-8-sig", newline="") as csvfile:
                sample = csvfile.read(2048)
                csvfile.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                except csv.Error:
                    class _Dialect:
                        delimiter = ";"
                    dialect = _Dialect()

                reader = csv.DictReader(csvfile, delimiter=dialect.delimiter)
                expected = {"nome", "preco", "estoque", "unidade"}
                headers = {header.strip().lower() for header in (reader.fieldnames or [])}
                if not expected.issubset(headers):
                    messagebox.showerror(
                        "Importação em Massa",
                        "O CSV precisa ter pelo menos as colunas: nome, preco, estoque, unidade.",
                        parent=self,
                    )
                    return

                adicionados = 0
                atualizados = 0
                erros = []
                produtos_existentes = get_all_products()
                produtos_por_id = {produto[0]: produto for produto in produtos_existentes}
                nomes_existentes = {
                    str(produto[1] or "").strip().upper(): produto
                    for produto in produtos_existentes
                }
                skus_existentes = {
                    str(produto[5] or "").strip(): produto
                    for produto in produtos_existentes
                    if produto[5]
                }
                codigos_existentes = {
                    str(produto[6] or "").strip(): produto
                    for produto in produtos_existentes
                    if produto[6]
                }
                for line_no, row in enumerate(reader, start=2):
                    try:
                        acao = str(row.get("acao", "") or "").strip().lower()
                        nome = str(row.get("nome", "")).strip()
                        preco = float(str(row.get("preco", "")).replace(",", "."))
                        estoque = float(str(row.get("estoque", "")).replace(",", "."))
                        unidade = str(row.get("unidade", "")).strip().lower()
                        sku = str(row.get("sku", "") or "").strip()
                        cod_barras = str(row.get("cod_barras", "") or "").strip()
                        normalized_name = nome.upper()

                        if not nome or preco <= 0 or estoque < 0 or unidade not in {"kg", "un"}:
                            raise ValueError("dados obrigatórios inválidos")
                        if acao and acao not in {"novo", "atualizar"}:
                            raise ValueError("acao inválida: use 'novo' ou 'atualizar'")
                        existente = None
                        if cod_barras and cod_barras in codigos_existentes:
                            existente = codigos_existentes[cod_barras]
                        elif sku and sku in skus_existentes:
                            existente = skus_existentes[sku]
                        elif normalized_name in nomes_existentes:
                            existente = nomes_existentes[normalized_name]

                        if existente:
                            if acao == "novo":
                                raise ValueError("produto já cadastrado e a ação está como 'novo'")
                            if acao != "atualizar" and not update_existing:
                                raise ValueError("produto já cadastrado")

                            produto_id = existente[0]
                            sku_final = sku or existente[5]
                            cod_barras_final = cod_barras or existente[6]
                            update_product(
                                produto_id,
                                nome,
                                preco,
                                estoque,
                                unidade,
                                sku_final,
                                cod_barras_final,
                            )
                            atualizado = get_product_by_id(produto_id)
                            produtos_por_id[produto_id] = atualizado
                            nomes_existentes[str(atualizado[1] or "").strip().upper()] = atualizado
                            if atualizado[5]:
                                skus_existentes[str(atualizado[5]).strip()] = atualizado
                            if atualizado[6]:
                                codigos_existentes[str(atualizado[6]).strip()] = atualizado
                            atualizados += 1
                            continue

                        if acao == "atualizar":
                            raise ValueError("produto não encontrado para atualizar")

                        add_product(nome, preco, estoque, unidade, sku, cod_barras)
                        novo_produto = get_product_by_name(nome)
                        if novo_produto:
                            produtos_por_id[novo_produto[0]] = novo_produto
                            nomes_existentes[str(novo_produto[1] or "").strip().upper()] = novo_produto
                            if novo_produto[5]:
                                skus_existentes[str(novo_produto[5]).strip()] = novo_produto
                            if novo_produto[6]:
                                codigos_existentes[str(novo_produto[6]).strip()] = novo_produto
                        adicionados += 1
                    except Exception as exc:
                        erros.append(f"Linha {line_no}: {exc}")

            self.refresh_produtos_view()

            if erros:
                preview = "\n".join(erros[:8])
                suffix = "\n..." if len(erros) > 8 else ""
                messagebox.showwarning(
                    "Importação concluída com ressalvas",
                    (
                        f"{adicionados} produto(s) importado(s) com sucesso.\n"
                        f"{atualizados} produto(s) atualizado(s).\n"
                        f"{len(erros)} linha(s) com erro.\n\n"
                        f"{preview}{suffix}"
                    ),
                    parent=self,
                )
            else:
                messagebox.showinfo(
                    "Importação em Massa",
                    (
                        f"{adicionados} produto(s) importado(s) com sucesso.\n"
                        f"{atualizados} produto(s) atualizado(s)."
                    ),
                    parent=self,
                )
        except Exception as exc:
            messagebox.showerror(
                "Importação em Massa",
                f"Não foi possível importar o arquivo.\nErro: {exc}",
                parent=self,
            )

    def update_product_list(self):
        self.refresh_produtos_view()

    def atualizar_produto_via_dialog(self, produto_id, produto_data):
        """Método chamado pelo diálogo para atualizar o produto no BD."""
        try:
            new_nome = produto_data["nome"]
            new_preco = produto_data["preco"]
            new_estoque = produto_data["estoque"]
            new_unidade = produto_data["unidade"]
            new_sku = produto_data["sku"]
            new_cod_barras = produto_data["cod_barras"]
            update_product(
                produto_id,
                new_nome,
                new_preco,
                new_estoque,
                new_unidade,
                new_sku,
                new_cod_barras,
            )

            messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
            self.update_product_list()
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível atualizar o produto: {e}")
            return False

    def update_product_list(self):
        """Limpa e preenche a Treeview de produtos."""
        self.refresh_produtos_view()

    def edit_product(self):
        """Abre o diálogo de cadastro/edição para editar um produto selecionado."""
        selected_item = self.produtos_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione um produto para editar."
            )
            return

        item_data = self.produtos_tree.item(selected_item)["values"]
        produto_id = item_data[0]
        try:
            produto_completo = get_product_by_id(produto_id)
            if not produto_completo:
                messagebox.showerror(
                    "Erro", "Produto não encontrado no banco de dados."
                )
                return
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados",
                f"Não foi possível carregar os dados do produto: {e}",
            )
            return
        CadastroProdutoDialog(self, self, product_data=produto_completo)

    def delete_product(self):
        selected_item = self.produtos_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione um produto para excluir."
            )
            return
        item_data = self.produtos_tree.item(selected_item)["values"]
        produto_id = item_data[0]
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o produto '{item_data[1]}'?",
        ):
            try:
                delete_product_db(produto_id)
                messagebox.showinfo("Sucesso", "Produto excluí­do com sucesso!")
                self.update_product_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir o produto: {e}")

    def salvar_funcionario_via_dialog(self, data):
        """
        Recebe os dados do formulário de funcionário (cadastro), valida e salva no DB.
        Retorna True se sucesso, False caso contrário.
        """
        nome = data["nome"].strip()
        usuario = data["usuario"].strip()
        senha = data["senha"]
        cargo = data["cargo"]
        if not nome or not usuario or not senha or not cargo:
            messagebox.showerror(
                "Erro de Cadastro", "Todos os campos são obrigatórios."
            )
            return False

        if len(senha) < 4:
            messagebox.showerror(
                "Erro de Cadastro", "A senha deve ter pelo menos 4 caracteres."
            )
            return False
        try:
            add_employee(nome, usuario, cargo, senha)
            messagebox.showinfo(
                "Sucesso", f"Funcionário '{nome}' ({usuario}) cadastrado com sucesso!"
            )
            self.update_employee_list()
            return True

        except Exception as e:
            if "UNIQUE constraint failed: funcionarios.usuario" in str(e):
                messagebox.showerror(
                    "Erro de Banco de Dados",
                    "O nome de usuário já está sendo usado. Por favor, escolha outro.",
                )
            else:
                messagebox.showerror(
                    "Erro de Banco de Dados",
                    f"Não foi possível adicionar o funcionário: {e}",
                )
            return False

    def atualizar_funcionario_via_dialog(self, funcionario_id, data):
        """
        Recebe o ID e os dados do formulário de funcionário (edição), valida e atualiza o DB.
        Retorna True se sucesso, False caso contrário.
        """
        nome = data["nome"].strip()
        usuario = data["usuario"].strip()
        nova_senha = data["senha"]
        cargo = data["cargo"]
        if not nome or not usuario or not cargo:
            messagebox.showerror(
                "Erro de edição", "Os campos Nome, Usuário e Cargo são obrigatórios."
            )
            return False

        if nova_senha and len(nova_senha) < 4:
            messagebox.showerror(
                "Erro de edição",
                "A nova senha, se informada, deve ter pelo menos 4 caracteres.",
            )
            return False
        try:
            update_employee_db(
                funcionario_id, nome, usuario, cargo, nova_senha if nova_senha else None
            )
            messagebox.showinfo(
                "Sucesso", f"Funcionário '{nome}' ({usuario}) atualizado com sucesso!"
            )
            self.update_employee_list()
            return True

        except Exception as e:
            if "UNIQUE constraint failed: funcionarios.usuario" in str(e):
                messagebox.showerror(
                    "Erro de Banco de Dados",
                    "O nome de usuário já está sendo usado. Por favor, escolha outro.",
                )
            else:
                messagebox.showerror(
                    "Erro de Banco de Dados",
                    f"Não foi possível atualizar o funcionário: {e}",
                )
            return False

    def on_double_click_produto(self, event):
        """Método chamado ao dar duplo clique na treeview de produtos."""
        self.edit_product()

    def on_double_click_employee(self, event):
        """Método chamado ao dar duplo clique na treeview de funcionários."""
        self.edit_employee()

    def on_double_click_relatorio(self, event):
        """Método chamado ao dar duplo clique na treeview de relatórios/vendas."""
        self.edit_sale()

    def update_employee_list(self):
        """Limpa e preenche a Treeview de funcionários."""
        for item in self.funcionarios_tree.get_children():
            self.funcionarios_tree.delete(item)

        funcionarios = get_all_employees()

        for funcionario in funcionarios:
            self.funcionarios_tree.insert(
                "",
                "end",
                values=(funcionario[0], funcionario[1], funcionario[2], funcionario[3]),
            )

    def iniciar_finalizacao_venda(self):
        """
        Inicia o processo de finalização, abrindo o diálogo de pagamento.
        """
        total_venda = self.calcular_total_carrinho()

        if total_venda <= 0:
            messagebox.showwarning("Atenção", "O carrinho está vazio.")
            return
        FinalizarVendaDialog(self, total_venda, self.finalizar_venda_callback)

    def finalizar_venda_callback(self, metodo_pagamento, valor_pago, troco):
        """
        Callback chamado pelo diálogo para registrar a venda no DB.
        """
        total_venda = self.calcular_total_carrinho()
        try:
            user_id = self.logged_user.get("id", 1)
            itens_carrinho = [dict(item) for item in self.carrinho_itens]
            itens_carrinho_json = json.dumps(itens_carrinho)
            venda_id = add_sale(
                user_id,
                total_venda,
                itens_carrinho_json,
                metodo_pagamento,
                valor_pago,
                troco,
            )
            if hasattr(self, "update_daily_sales_report"):
                self.update_daily_sales_report()

            should_print = messagebox.askyesno(
                "Cupom Fiscal",
                "Deseja imprimir cupom fiscal?",
                parent=self,
            )

            if should_print:
                self.emitir_nota("completa", None)
            else:
                messagebox.showinfo(
                    "Venda Concluída",
                    f"Venda nº {venda_id} no valor de R${total_venda:.2f} foi registrada com sucesso!",
                    parent=self,
                )

            self.carrinho_itens = []
            self.atualizar_carrinho_treeview()
            self.atualizar_total()

        except Exception as e:
            messagebox.showerror("Erro de Venda", f"Falha ao registrar a venda: {e}")

    def delete_employee(self):
        selected_item = self.funcionarios_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione um funcionário para excluir."
            )
            return
        item_data = self.funcionarios_tree.item(selected_item)["values"]
        funcionario_id = item_data[0]
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o funcionário '{item_data[1]}' (Usuário: {item_data[2]})?",
        ):
            try:
                delete_employee_db(funcionario_id)
                messagebox.showinfo("Sucesso", "funcionário excluído com sucesso!")
                self.update_employee_list()
            except Exception as e:
                messagebox.showerror(
                    "Erro no Banco de Dados",
                    f"Não foi possível excluir o funcionário: {e}",
                )

    def edit_employee(self):
        """Abre a janela unificada (CadastroFuncionarioDialog) para editar um funcionário selecionado."""

        selected_item = self.funcionarios_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione um funcionário para editar."
            )
            return

        item_data = self.funcionarios_tree.item(selected_item)["values"]
        funcionario_id = item_data[0]

        try:
            employee_completo = get_employee_by_id(funcionario_id)
            if not employee_completo:
                messagebox.showerror(
                    "Erro", "funcionário não encontrado no banco de dados."
                )
                return

        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível carregar os dados do funcionário: {e}"
            )
            return
        CadastroFuncionarioDialog(self, self, employee_data=employee_completo)

    def open_cadastro_funcionario_dialog(self):
        """Abre o diálogo de cadastro de funcionário (chamado pelo Tile)."""
        CadastroFuncionarioDialog(self, controller=self)

    def edit_sale(self):
        selected_item = self.relatorio_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione uma venda para editar."
            )
            return

        venda_data = self.relatorio_tree.item(selected_item)["values"]
        EdicaoVendaDialog(
            self, self, venda_data, on_save=self.update_daily_sales_report
        )

    def delete_sale(self):
        selected_item = self.relatorio_tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Nenhum Item Selecionado", "Selecione uma venda para excluir."
            )
            return
        item_data = self.relatorio_tree.item(selected_item)["values"]
        venda_id = item_data[0]
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a venda '{venda_id}'? Esta ação não pode ser desfeita.",
        ):
            try:
                delete_sale_db(venda_id)
                messagebox.showinfo("Sucesso", "Venda excluí­da com sucesso!")
                self.update_daily_sales_report()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir a venda: {e}")

    def update_daily_sales_report(self):
        for item in self.relatorio_tree.get_children():
            self.relatorio_tree.delete(item)

        vendas = get_daily_sales()

        for venda in vendas:

            try:
                venda_id, id_func, data, total, itens_str, metodo, vp, troco_val = venda
            except ValueError:
                venda_id = venda[0]
                data = venda[2]
                total = venda[3]
                itens_str = venda[4]

            try:
                itens_list = json.loads(itens_str)
            except json.JSONDecodeError:
                try:
                    itens_list = ast.literal_eval(itens_str)
                except:
                    itens_list = []
            itens_resumo = ", ".join([f"{item['nome']}" for item in itens_list])
            self.relatorio_tree.insert(
                "", "end", values=(venda_id, data, f"R$ {total:.2f}", itens_resumo)
            )

    def show_sale_details(self, event):
        selected_item = self.relatorio_tree.selection()
        if not selected_item:
            return
        item_data = self.relatorio_tree.item(selected_item)["values"]
        venda_id, data, total, _ = item_data
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT itens_vendidos FROM vendas WHERE id=?", (venda_id,))
        itens_str = cursor.fetchone()[0]
        conn.close()
        try:
            itens_list = json.loads(itens_str)
        except json.JSONDecodeError:
            itens_list = ast.literal_eval(itens_str)
        details_text = f"Detalhes da Venda {venda_id}\n\n"
        for item in itens_list:
            details_text += f"Produto: {item['nome']}\n"
            details_text += f"Quantidade: {item['quantidade']:.2f}\n"
            details_text += f"Subtotal: R$ {item['subtotal']:.2f}\n"
            details_text += "----------------------------------\n"
        messagebox.showinfo(f"Detalhes da Venda {venda_id}", details_text)

    def show_report_print_menu(self):
        """
        Abre um novo diálogo para selecionar o tipo de relatório a ser visualizado/impresso.
        """
        report_dialog = tk.Toplevel(self.master)
        report_dialog.title("Emitir Relatórios do Dia")
        if hasattr(self, "icon_tk"):
            report_dialog.iconphoto(False, self.icon_tk)
        self.center_window(report_dialog, 600, 300)
        report_dialog.configure(bg=self.bg_color)
        report_dialog.transient(self.master)
        report_dialog.grab_set()
        report_dialog.grid_columnconfigure(0, weight=1)

        tk.Label(
            report_dialog,
            text="Escolha o tipo de relatório:",
            font=("Arial", 22, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
        ).grid(row=0, column=0, pady=(20, 10), sticky="n")

        botoes_frame = tk.Frame(report_dialog, bg=self.bg_color)
        botoes_frame.grid(row=1, column=0, pady=10)
        botoes_frame.grid_columnconfigure(0, weight=1)

        btn_simplificado = tk.Button(
            botoes_frame,
            text="Relatório Simplificado",
            font=("Arial", 15),
            bg="#4CAF50",
            fg=self.white_color,
            command=lambda: self.show_report_preview("simplificado", report_dialog),
            relief="flat",
        )
        btn_simplificado.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        btn_completo = tk.Button(
            botoes_frame,
            text="Relatório Completo",
            font=("Arial", 15),
            bg="#2196F3",
            fg=self.white_color,
            command=lambda: self.show_report_preview("completo", report_dialog),
            relief="flat",
        )
        btn_completo.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

    def show_report_preview(self, tipo_relatorio, parent_window):
        """
        Cria uma nova janela para pré-visualizar o relatório antes da impressão.
        """
        parent_window.destroy()

        report_text = self.generate_report_text(tipo_relatorio)

        report_window = tk.Toplevel(self.master)
        report_window.title(f"Pré-visualização do Relatório")
        if hasattr(self, "icon_tk"):
            report_window.iconphoto(False, self.icon_tk)
        report_window.transient(self.master)
        report_window.grab_set()

        text_widget = tk.Text(report_window, width=80, height=25, font=("Courier", 10))
        text_widget.insert(tk.END, report_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(padx=10, pady=10)

        btn_frame = tk.Frame(report_window)
        btn_frame.pack(pady=10)

        btn_print = tk.Button(
            btn_frame,
            text="Imprimir",
            command=lambda: self.imprimir_relatorio_selecionado(
                tipo_relatorio, report_window
            ),
        )
        btn_print.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text="Fechar", command=report_window.destroy)
        btn_close.pack(side="left", padx=5)

    def imprimir_relatorio_selecionado(self, tipo_relatorio, window_to_close):
        """
        Função auxiliar para chamar a função de impressão correta e fechar a janela.
        """
        window_to_close.destroy()
        if tipo_relatorio == "simplificado":
            self.imprimir_relatorio_geral()
        else:
            self.imprimir_relatorio_diario()

    def generate_report_text(self, tipo_relatorio):
        """
        Gera o conteúdo de texto do relatório.
        """
        vendas = get_daily_sales()
        empresa_info = get_company_info()

        nome_empresa = (
            empresa_info.get("nome_fantasia", "Nome da Empresa")
            if empresa_info
            else "Nome da Empresa"
        )

        if tipo_relatorio == "simplificado":
            imprime = "---------------------------------------\n"
            imprime += f"       {nome_empresa.upper():<20}     \n"
            imprime += "       RELATÓRIO DE VENDAS DIÁRIAS     \n"
            imprime += f"Data: {datetime.now().strftime('%d/%m/%Y')}\n"
            imprime += "---------------------------------------\n"
            imprime += "ID     | Venda (R$)\n"
            imprime += "---------------------------------------\n"

            total_geral = 0

            for venda in vendas:
                venda_id = venda[0]
                total = venda[3]

                venda_id_formatada = str(venda_id)[:4]
                imprime += f"{venda_id_formatada:<6} | R$ {total:.2f}\n"
                total_geral += total

            imprime += "---------------------------------------\n"
            imprime += f"TOTAL GERAL DO DIA: R$ {total_geral:.2f}\n"
            imprime += "---------------------------------------\n"
            imprime += f"{REPORT_FOOTER}\n"
            return imprime

        elif tipo_relatorio == "completo":
            imprime = "---------------------------------------\n"
            imprime += f"       {nome_empresa.upper():<20}     \n"
            imprime += "       RELATÓRIO DE VENDAS DIÁRIAS     \n"
            imprime += f"Data: {datetime.now().strftime('%d/%m/%Y')}\n"
            imprime += "---------------------------------------\n"
            total_geral = 0

            for venda in vendas:
                venda_id = venda[0]
                data_hora = venda[2]
                total = venda[3]
                itens_str = venda[4]
                hora_formatada = data_hora[11:16] if len(data_hora) > 16 else "--:--"

                imprime += f"Venda: {str(venda_id)[:4]} | Hora: {hora_formatada} | Total: R${total:.2f}\n"

                try:
                    itens_list = json.loads(itens_str)
                except json.JSONDecodeError:
                    try:
                        itens_list = ast.literal_eval(itens_str)
                    except:
                        itens_list = []

                for item in itens_list:
                    qtd = item["quantidade"]
                    valor_unitario = item["subtotal"] / qtd if qtd > 0 else 0

                    unidade_medida = item.get("unidade", "un")
                    if unidade_medida == "unidade":
                        unidade_medida = "un"

                    imprime += f"  - {item['nome']}\n"
                    imprime += f"      {qtd:.2f} {unidade_medida} x R${valor_unitario:.2f} = R${item['subtotal']:.2f}\n"
                imprime += "\n"
                total_geral += total

            imprime += "---------------------------------------\n"
            imprime += f"TOTAL GERAL DO DIA: R$ {total_geral:.2f}\n"
            imprime += "---------------------------------------\n"
            imprime += f"{REPORT_FOOTER}\n"
            return imprime

        return ""

    def imprimir_relatorio_geral(self):
        try:
            imprime = self.generate_report_text("simplificado")

            handle = win32print.OpenPrinter(self.printer_name)
            job_info = win32print.StartDocPrinter(
                handle, 1, ("Relatório Simplificado", None, "RAW")
            )
            win32print.StartPagePrinter(handle)

            imprime += "\n" * 5
            win32print.WritePrinter(handle, imprime.encode("cp860", errors="replace"))

            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)

            messagebox.showinfo(
                "Impressão",
                "Relatório de vendas enviado para a impressora com sucesso!",
            )

        except Exception as e:
            messagebox.showerror(
                "Erro de Impressão",
                f"Ocorreu um erro durante a impressão. Verifique se o nome da impressora está correto e se ela está ligada. Erro: {e}",
            )

    def imprimir_relatorio_diario(self):
        try:
            imprime = self.generate_report_text("completo")

            handle = win32print.OpenPrinter(self.printer_name)
            job_info = win32print.StartDocPrinter(
                handle, 1, ("Relatório de Vendas", None, "RAW")
            )
            win32print.StartPagePrinter(handle)

            imprime += "\n" * 5
            win32print.WritePrinter(handle, imprime.encode("cp860", errors="replace"))
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)
            messagebox.showinfo(
                "Impressão",
                "Relatório de vendas enviado para a impressora com sucesso!",
            )
        except Exception as e:
            messagebox.showerror(
                "Erro de Impressão", f"Ocorreu um erro durante a impressão. Erro: {e}"
            )

    def _build_company_receipt_header_lines(self, width=42):
        empresa_info = get_company_info() or {}

        nome_fantasia = (empresa_info.get("nome_fantasia") or "").strip()
        endereco = (empresa_info.get("endereco") or "").strip()
        bairro = (empresa_info.get("bairro") or "").strip()
        cidade = (empresa_info.get("cidade") or "").strip()
        estado = (empresa_info.get("estado") or "").strip()
        cep = (empresa_info.get("cep") or "").strip()

        if not nome_fantasia:
            return [
                f"{'EMPRESA NÃO CADASTRADA':^{width}}",
                f"{'Cadastre os dados da empresa':^{width}}",
            ]

        lines = [f"{nome_fantasia.upper():^{width}}"]

        if endereco:
            lines.append(endereco[:width])

        bairro_cidade_estado_cep = ""
        if bairro:
            bairro_cidade_estado_cep = bairro

        if cep:
            bairro_cidade_estado_cep = (
                f"{bairro_cidade_estado_cep} | {cep}"
                if bairro_cidade_estado_cep
                else cep
            )

        cidade_estado = ""
        if cidade and estado:
            cidade_estado = f"{cidade} - {estado}"
        elif cidade:
            cidade_estado = cidade
        elif estado:
            cidade_estado = estado

        if cidade_estado:
            bairro_cidade_estado_cep = (
                f"{bairro_cidade_estado_cep} | {cidade_estado}"
                if bairro_cidade_estado_cep
                else cidade_estado
            )

        if bairro_cidade_estado_cep:
            lines.append(bairro_cidade_estado_cep[:width])
        elif not endereco:
            lines.append(f"{'Endereço não cadastrado':^{width}}")

        return lines

    def emitir_nota(self, tipo_nota, parent_window=None):
        if parent_window is not None and parent_window.winfo_exists():
            parent_window.destroy()
        note_text = self._build_note_text(tipo_nota)
        ImprimirDialog(self, note_text, tipo_nota)

    def imprimir_nota_simplificada(self):
        """Envia a nota de venda simplificada para a impressora."""

        empresa_info = get_company_info()
        nome_fantasia = (
            empresa_info.get("nome_fantasia", "EMPRESA NAO CADASTRADA")
            if empresa_info
            else "EMPRESA NAO CADASTRADA"
        )
        PRODUTO_WIDTH_SIMP = 10
        QTD_UN_WIDTH_SIMP = 6
        VALOR_UN_STR_WIDTH_SIMP = 8
        TOTAL_WIDTH_SIMP = 6
        SEPARATOR_SIMPLIFICADA_STR = "------------------------------------------"
        SEPARATOR_SIMPLIFICADA_TXT = "--------EMPRESA NAO CADASTRADA--------"
        try:
            handle = win32print.OpenPrinter(self.printer_name)
            job_info = win32print.StartDocPrinter(
                handle, 1, ("Nota Simplificada", None, "RAW")
            )
            win32print.StartPagePrinter(handle)

            imprime = ""
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            imprime += f"{nome_fantasia.upper():^42}\n"
            imprime += f"\n"
            imprime += f"Data: {current_time}\n"
            imprime += f"\n"
            imprime += f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            imprime += (
                f"{'PRODUTO':<10} | {'QTD/UN':<6} | {'PREÇO':<8} | {'TOTAL':<6}\n"
            )
            imprime += f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            imprime += f"\n"

            total = 0
            for item in self.carrinho_itens:
                unidade_display = item["unidade"]
                if unidade_display == "unidade":
                    unidade_display = "un"
                item_name = item["nome"][:PRODUTO_WIDTH_SIMP].ljust(PRODUTO_WIDTH_SIMP)
                qtd_un_str = f"{item['quantidade']:.2f}{unidade_display}".ljust(
                    QTD_UN_WIDTH_SIMP
                )
                valor_un_str = f"R${item['preco']:.2f}".ljust(VALOR_UN_STR_WIDTH_SIMP)
                total_str = f"R${item['subtotal']:.2f}".ljust(TOTAL_WIDTH_SIMP)

                line = f"{item_name} | {qtd_un_str} | {valor_un_str} | {total_str}\n"
                imprime += line
                total += item["subtotal"]
            imprime += f"\n"
            imprime += f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            imprime += f"TOTAL: R$ {total:.2f}\n"
            imprime += f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            imprime += f"\n"
            imprime += f"{'Obrigado pela preferência':^42}\n"
            imprime += f"{'Volte Sempre':^42}\n" + "\n" * 5

            win32print.WritePrinter(handle, imprime.encode("cp860", errors="replace"))

            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)

            messagebox.showinfo(
                "Impressão", "Nota simplificada enviada para a impressora com sucesso!"
            )

        except Exception as e:
            messagebox.showerror(
                "Erro de Impressão",
                f"Ocorreu um erro durante a impressão. Verifique se o nome da impressora está correto e se ela está ligada. Erro: {e}",
            )

    def imprimir_nota_completa(self):
        """Envia a nota de venda completa para a impressora."""
        ITEM_WIDTH = 2
        PRODUTO_WIDTH = 14
        QTD_UN_WIDTH = 5
        VALOR_UN_WIDTH = 7
        TOTAL_WIDTH = 7
        SEPARATOR_COMPLETA_STR = "------------------------------------------"

        handle = None

        try:
            handle = win32print.OpenPrinter(self.printer_name)
            win32print.StartDocPrinter(handle, 1, ("Nota Completa", None, "RAW"))
            win32print.StartPagePrinter(handle)

            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            company_header = self._build_company_receipt_header_lines(42)
            company_header_text = "".join(f"{line}\n" for line in company_header[1:])
            header = (
                f"{company_header[0]}\n"
                f"\n"
                f"{company_header_text}"
                f"Data e Hora: {current_time}\n"
                f"\n"
                f"{SEPARATOR_COMPLETA_STR}\n"
                f"{'CUPOM FISCAL':^42}\n"
                f"{SEPARATOR_COMPLETA_STR}\n"
                f"{'Nº':<{ITEM_WIDTH}}|{'PRODUTO':<{PRODUTO_WIDTH}}|{'QTD/UN':<{QTD_UN_WIDTH}}|{'PREÇO':<{VALOR_UN_WIDTH}}|{'TOTAL':<{TOTAL_WIDTH}}\n"
                f"{SEPARATOR_COMPLETA_STR}\n"
                f"\n"
            )
            win32print.WritePrinter(handle, header.encode("cp860", errors="replace"))

            total = 0
            for i, item in enumerate(self.carrinho_itens, 1):
                unidade_display = item["unidade"]
                if unidade_display == "unidade":
                    unidade_display = "un"

                item_name = item["nome"][:PRODUTO_WIDTH].ljust(PRODUTO_WIDTH)
                qtd_un_str = f"{item['quantidade']:.2f}{unidade_display}".ljust(
                    QTD_UN_WIDTH
                )
                valor_un_str = f"R${item['preco']:.2f}".ljust(VALOR_UN_WIDTH)
                total_str = f"R${item['subtotal']:.2f}".ljust(TOTAL_WIDTH)

                line = (
                    f"{i:<{ITEM_WIDTH}}|"
                    f"{item_name}|"
                    f"{qtd_un_str}|"
                    f"{valor_un_str}|"
                    f"{total_str}\n"
                )

                win32print.WritePrinter(handle, line.encode("cp860", errors="replace"))
                total += item["subtotal"]
            footer_text = (
                f"\n"
                f"{SEPARATOR_COMPLETA_STR}\n"
                f"TOTAL: R$ {total:.2f}\n"
                f"{SEPARATOR_COMPLETA_STR}\n"
                f"\n"
                f"{'Obrigado pela preferência':^42}\n"
                f"{'Volte Sempre':^42}\n" + "\n" * 5
            )
            win32print.WritePrinter(
                handle, footer_text.encode("cp860", errors="replace")
            )
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)

            messagebox.showinfo(
                "Impressão", "Nota completa enviada para a impressora com sucesso!"
            )

        except Exception as e:
            messagebox.showerror(
                "Erro de Impressão",
                f"Ocorreu um erro durante a impressão. Verifique se o nome da impressora está correto e se ela está ligada. Erro: {e}",
            )

        finally:
            if handle:
                win32print.ClosePrinter(handle)

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        window.geometry(f"{width}x{height}+{x}+{y}")

    def monitorar_balanca(self):
        if not self.monitorando_balanca:
            self.monitor_balanca_job = None
            return

        if self.balanca:
            peso = self.balanca.ler_peso_instantaneo()
            self.balanca_peso_lido = peso

            if (
                self.balanca_ativa
                and self.balanca_is_active
                and hasattr(self, "quantidade_entry")
            ):
                self.quantidade_entry.delete(0, tk.END)
                self.quantidade_entry.insert(0, f"{peso:.3f}".replace(".", ","))

        self.monitor_balanca_job = self.after(180, self.monitorar_balanca)

    def get_peso_balanca(self):
        """Obtém o pultimo peso disponí­vel sem bloquear a interface."""
        if self.balanca:
            return self.balanca.ler_peso_instantaneo()
        messagebox.showwarning(
            "Balança", "A balança não está conectada ou não pode ser aberta."
        )
        return 0.0

    def _limpar_campos_entrada(self):
        if hasattr(self, "produto_entry"):
            self.produto_entry.set("")
        if hasattr(self, "quantidade_entry"):
            self.quantidade_entry.delete(0, tk.END)
            self.quantidade_entry.insert(0, "1")
        if hasattr(self, "produto_entry"):
            self.produto_entry.focus_set()

    def _adicionar_item_ao_carrinho_core(
        self, entrada, quantidade, is_barcode=False, produto_direto=None
    ):
        produto = produto_direto

        if not produto:
            if is_barcode:
                produto = get_product_by_barcode(entrada) or get_product_by_sku(entrada)
            else:
                produto = (
                    get_product_by_sku(entrada)
                    or get_product_by_barcode(entrada)
                    or get_product_by_name(entrada)
                )

        if not produto or quantidade <= 0:
            return False

        nome_produto = produto[1]
        preco_unitario = produto[2]
        unidade = produto[4]
        subtotal = preco_unitario * quantidade

        item_existente = next(
            (item for item in self.carrinho_itens if item["nome"] == nome_produto), None
        )
        if item_existente:
            item_existente["quantidade"] += quantidade
            item_existente["subtotal"] += subtotal
        else:
            self.carrinho_itens.append(
                {
                    "nome": nome_produto,
                    "quantidade": quantidade,
                    "preco": preco_unitario,
                    "unidade": unidade,
                    "subtotal": subtotal,
                }
            )

        self.atualizar_carrinho_treeview()
        self.atualizar_total()
        return True

    def adicionar_item_carrinho(
        self, produto_balanca=None, quantidade_balanca=None, subtotal_balanca=None
    ):
        if not self.is_cash_register_open:
            messagebox.showwarning("Caixa Fechado", "Abra o caixa primeiro.")
            return

        if produto_balanca is not None:
            sucesso = self._adicionar_item_ao_carrinho_core(
                entrada=None,
                quantidade=quantidade_balanca,
                is_barcode=False,
                produto_direto=produto_balanca,
            )
            if sucesso:
                self._limpar_campos_entrada()
                self.ativar_monitor_balanca()
            else:
                messagebox.showerror("Erro", "Erro ao adicionar item da balança.")
            return

        if not hasattr(self, "produto_entry"):
            return

        entrada = self.produto_entry.get().strip()
        if not entrada:
            return

        try:
            quantidade = float(self.quantidade_entry.get().replace(",", ".") or "1")
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        eh_barcode = entrada.isdigit() and len(entrada) >= 4
        if self._adicionar_item_ao_carrinho_core(
            entrada, quantidade, is_barcode=eh_barcode
        ):
            self._limpar_campos_entrada()
        else:
            messagebox.showerror("Erro", f"Produto '{entrada}' não encontrado.")

    def adicionar_item_carrinho_event(self, event):
        self.adicionar_item_carrinho()

    def update_produto_list(self, event):
        query = self.produto_entry.get()
        self.produto_entry["values"] = filter_products_for_combobox(query)

    def open_adicionar_item_dialog(self, event=None):
        self.desativar_monitor_balanca()
        self.parar_monitor_balanca()

        AdicionarItemDialog(
            self,
            self.atualizar_carrinho_treeview,
            self.adicionar_item_carrinho,
            self.balanca_instance,
        )

    def open_adicionar_item_dialog_event(self, event):
        self.open_adicionar_item_dialog()

    def parar_monitor_balanca(self):
        self.monitorando_balanca = False
        if self.monitor_balanca_job is not None:
            self.after_cancel(self.monitor_balanca_job)
            self.monitor_balanca_job = None

    def desativar_monitor_balanca(self):
        self.balanca_ativa = False
        self.balanca_is_active = False

    def ativar_monitor_balanca(self):
        self.balanca_ativa = True
        self.monitorando_balanca = True
        if self.monitor_balanca_job is None:
            self.monitorar_balanca()

    def adicionar_item_direto_callback(self, produto, quantidade, subtotal):
        self.carrinho_itens.append(
            {
                "id": produto[0],
                "nome": produto[1],
                "quantidade": quantidade,
                "preco": produto[2],
                "unidade": produto[4],
                "subtotal": subtotal,
            }
        )
        self.atualizar_carrinho_treeview()
        self.atualizar_total()
        self._limpar_campos_entrada()
        self.ativar_monitor_balanca()

    def limpar_item_dialog_event(self, event):
        self.limpar_venda()

    def emitir_nota_dialog_event(self, event):
        self.show_note_dialog()

    def finalizar_venda_dialog_event(self, event):
        self.finalizar_venda()

    def delete_item_from_cart(self):
        """Remove um item do carrinho."""
        selected_items = self.carrinho_tree.selection()
        if not selected_items:
            messagebox.showwarning("Seleção", "Selecione um item para excluir.")
            return
        cargo_atual = self.logged_user.get("cargo") if self.logged_user else "Caixa"

        if cargo_atual == "Caixa":
            if not self.prompt_manager_credentials():
                return

        if messagebox.askyesno(
            "Confirmar", "Deseja realmente remover este item?", parent=self
        ):
            selected_item = selected_items[0]
            index = self.carrinho_tree.index(selected_item)
            if 0 <= index < len(self.carrinho_itens):
                del self.carrinho_itens[index]
                self.atualizar_carrinho_treeview()
                self.atualizar_total()

    def edit_item_in_cart(self):
        """Edita a quantidade de um item selecionado no carrinho."""
        selected_items = self.carrinho_tree.selection()
        if not selected_items:
            messagebox.showwarning("Seleção", "Selecione um item para editar.")
            return
        selected_item = selected_items[0]
        index = self.carrinho_tree.index(selected_item)
        if not (0 <= index < len(self.carrinho_itens)):
            messagebox.showwarning(
                "Seleção", "Não foi possível localizar o item selecionado."
            )
            return
        item_data = self.carrinho_itens[index]
        cargo_atual = self.logged_user.get("cargo") if self.logged_user else "Caixa"

        if cargo_atual == "Caixa":
            if not self.prompt_manager_credentials():
                return
        EdicaoCarrinhoDialog(self, self, item_data, index)

    def prompt_manager_credentials(
        self, instruction_text="Insira as credenciais de um gerente para prosseguir:"
    ):
        approved = {"value": False}
        auth_window = tk.Toplevel(self)
        theme, card, body = build_dialog_shell(
            auth_window,
            self,
            "Acesso de Gerente",
            subtitle=instruction_text,
            size=(460, 420),
            controller=self,
        )

        form = tk.Frame(body, bg=theme["surface"])
        form.pack(fill="x", pady=(4, 16))

        make_form_label(form, "Usuário", theme).pack(anchor="w")
        user_entry = make_entry(form, theme)
        user_entry.pack(fill="x", ipady=8, pady=(6, 12))

        make_form_label(form, "Senha", theme).pack(anchor="w")
        pass_entry = make_entry(form, theme, show="*")
        pass_entry.pack(fill="x", ipady=8, pady=(6, 0))

        def close_dialog():
            auth_window.destroy()

        def check_credentials():
            username = user_entry.get().strip()
            password = pass_entry.get().strip()
            if is_manager(username, password):
                approved["value"] = True
                close_dialog()
            else:
                messagebox.showerror(
                    "Acesso Negado",
                    "Usuário ou senha de gerente inválidos.",
                    parent=auth_window,
                )
                pass_entry.delete(0, tk.END)
                pass_entry.focus_set()

        action = tk.Frame(body, bg=theme["surface"])
        action.pack(fill="x")
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)

        btn_ok = tk.Button(action, text="Validar", command=check_credentials)
        style_button(btn_ok, "primary", theme).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        btn_cancel = tk.Button(action, text="Cancelar", command=close_dialog)
        style_button(btn_cancel, "secondary", theme).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        user_entry.focus_set()
        user_entry.bind("<Return>", lambda _e: pass_entry.focus_set())
        pass_entry.bind("<Return>", lambda _e: check_credentials())
        auth_window.protocol("WM_DELETE_WINDOW", close_dialog)
        auth_window.wait_window()
        return approved["value"]

    def update_carrinho_tree(self):
        """Atualiza a lista visual do carrinho e recalcula o total."""
        for i in self.carrinho_tree.get_children():
            self.carrinho_tree.delete(i)

        total_geral = 0
        for idx, item in enumerate(self.carrinho_itens, 1):
            self.carrinho_tree.insert(
                "",
                "end",
                values=(
                    idx,
                    item["nome"],
                    f"{item['quantidade']:.3f} {item['unidade']}",
                    f"R$ {item['preco']:.2f}",
                    f"R$ {item['subtotal']:.2f}",
                ),
            )
            total_geral += item["subtotal"]
        self.total_label.config(text=f"TOTAL: R$ {total_geral:.2f}")

    def atualizar_treeview(self):
        """Atualiza a lista visual de itens no Treeview do Caixa."""
        try:
            if not hasattr(self, "tree") or self.tree is None:
                print("ERRO: O widget 'self.tree' não existe.")
                return
            for i in self.tree.get_children():
                self.tree.delete(i)
            print(
                f"DEBUG: A atualizar Treeview. Itens no carrinho: {len(self.carrinho_itens)}"
            )
            for item in self.carrinho_itens:
                preco_unit = f"R$ {float(item['preco']):.2f}"
                qtd_formatada = f"{float(item['quantidade']):.3f} {item['unidade']}"
                subtotal_formatado = f"R$ {float(item['subtotal']):.2f}"

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        item["id"],
                        item["nome"],
                        preco_unit,
                        qtd_formatada,
                        subtotal_formatado,
                    ),
                )
            self.atualizar_total()

        except Exception as e:
            print(f"ERRO CRÍTICO ao atualizar treeview: {e}")

    def atualizar_carrinho_treeview(self):
        """Limpa a tabela visual e redesenha com os itens da memória."""
        try:
            for item in self.carrinho_tree.get_children():
                self.carrinho_tree.delete(item)
            for item in self.carrinho_itens:
                unidade = str(item.get("unidade", "UN") or "UN").strip().upper()
                if unidade == "KG":
                    qtd_str = f"{item['quantidade']:.3f} KG"
                else:
                    qtd_str = f"{int(round(float(item['quantidade'])))} UN"
                self.carrinho_tree.insert(
                    "",
                    "end",
                    values=(
                        item["nome"],
                        qtd_str,
                        f"R$ {item['preco']:.2f}",
                        f"R$ {item['subtotal']:.2f}",
                    ),
                )
            if self.carrinho_tree.get_children():
                ultimo_item = self.carrinho_tree.get_children()[-1]
                self.carrinho_tree.see(ultimo_item)

            self.atualizar_total()
            print(f"DEBUG: Treeview atualizado com {len(self.carrinho_itens)} itens.")

        except Exception as e:
            print(f"ERRO ao atualizar Treeview: {e}")

    def atualizar_total(self):
        """Recalcula o valor total da venda e atualiza os indicadores do PDV."""
        try:
            total = sum(item["subtotal"] for item in self.carrinho_itens)
            quantidade_total = sum(
                float(item["quantidade"]) for item in self.carrinho_itens
            )
            itens_total = len(self.carrinho_itens)

            if hasattr(self, "total_var"):
                self.total_var.set(f"R$ {total:.2f}".replace(".", ","))
            if hasattr(self, "cart_count_var"):
                sufixo = "item" if itens_total == 1 else "itens"
                self.cart_count_var.set(f"{itens_total} {sufixo}")
            if hasattr(self, "cart_volume_var"):
                self.cart_volume_var.set(f"{quantidade_total:.3f}".replace(".", ","))

            self.update_idletasks()
        except Exception as e:
            print(f"ERRO ao atualizar total: {e}")

    def limpar_venda(self):
        self.carrinho_itens = []
        self.atualizar_carrinho_treeview()
        self.atualizar_total()
        self._set_status_banner("Venda limpa. Pronto para um novo atendimento.")

    def finalizar_venda(self):
        if not self.is_cash_register_open:
            messagebox.showwarning(
                "Caixa Fechado",
                "O caixa está fechado. Abra o caixa para iniciar vendas.",
            )
            return
        if not self.carrinho_itens:
            messagebox.showwarning(
                "Carrinho Vazio", "Adicione itens ao carrinho para finalizar a venda."
            )
            return

        total = sum(item["subtotal"] for item in self.carrinho_itens)
        itens_vendidos = []
        stock_warnings = []
        for item in self.carrinho_itens:
            produto_db = get_product_by_name(item["nome"])

            if produto_db:
                estoque_atual = produto_db[3]
                if estoque_atual < item["quantidade"]:
                    stock_warnings.append(
                        f"{item['nome']} (Disponí­vel: {estoque_atual} {item['unidade']})"
                    )
                itens_vendidos.append(
                    {
                        "nome": item["nome"],
                        "quantidade": item["quantidade"],
                        "subtotal": item["subtotal"],
                        "unidade": item["unidade"],
                    }
                )
        if stock_warnings:
            warning_message = "AVISO - ESTOQUE INSUFICIENTE:\n\n"
            warning_message += (
                "As seguintes vendas excederam o estoque atual:\n- "
                + "\n- ".join(stock_warnings)
            )
            warning_message += "\nA venda será finalizada e o estoque será atualizado (podendo ficar negativo)."
            messagebox.showwarning("Aviso de Estoque", warning_message)
        for item in self.carrinho_itens:
            update_product_stock(item["nome"], item["quantidade"])
        venda_id = add_sale(total, itens_vendidos)

        messagebox.showinfo(
            "Venda Concluída",
            f"Venda nº {venda_id} no valor de R${total:.2f} foi registrada com sucesso!",
        )
        self.limpar_venda()

    def center_window(self, window, width, height):
        """Calcula a posição (x, y) para centralizar a 'window' na tela."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        window.geometry(f"{width}x{height}+{x}+{y}")

    def calcular_total_carrinho(self):
        """Calcula o valor total de todos os itens no carrinho."""

        total = 0.0
        for item in self.carrinho_itens:
            try:
                total += item["subtotal"]
            except TypeError:
                pass

        return total

    def show_note_dialog(self):
        if not self.carrinho_itens:
            messagebox.showwarning(
                "Carrinho Vazio", "Adicione itens ao carrinho para emitir uma nota."
            )
            return

        note_dialog = tk.Toplevel(self)
        theme, card, body = build_dialog_shell(
            note_dialog,
            self,
            "Emitir Nota",
            subtitle="Escolha o formato de nota desejado para continuar.",
            size=(620, 420),
            controller=self,
        )

        options = tk.Frame(body, bg=theme["surface"])
        options.pack(fill="both", expand=True)
        options.columnconfigure(0, weight=1)
        options.columnconfigure(1, weight=1)

        simple_card = tk.Frame(options, bg="#EEF7F0", padx=18, pady=18)
        simple_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(
            simple_card,
            text="Nota Simplificada",
            font=("Segoe UI Semibold", 14),
            bg="#EEF7F0",
            fg=self.text_color,
        ).pack(anchor="w")
        tk.Label(
            simple_card,
            text="Versão objetiva para atendimento rápido no caixa.",
            font=("Segoe UI", 8),
            bg="#EEF7F0",
            fg="#5F6B63",
            wraplength=180,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))
        btn_simple = tk.Button(
            simple_card,
            text="Emitir Simplificada",
            command=lambda: self.emitir_nota("simplificada", note_dialog),
        )
        style_button(btn_simple, "primary", theme).pack(fill="x")

        full_card = tk.Frame(options, bg="#EEF3FF", padx=18, pady=18)
        full_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(
            full_card,
            text="Nota Completa",
            font=("Segoe UI Semibold", 14),
            bg="#EEF3FF",
            fg=self.text_color,
        ).pack(anchor="w")
        tk.Label(
            full_card,
            text="Modelo detalhado para conferência completa da venda.",
            font=("Segoe UI", 8),
            bg="#EEF3FF",
            fg="#5F6B63",
            wraplength=180,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))
        btn_full = tk.Button(
            full_card,
            text="Emitir Completa",
            command=lambda: self.emitir_nota("completa", note_dialog),
        )
        style_button(btn_full, "warning", theme).pack(fill="x")

    def update_ui_state(self):
        """Atualiza o estado dos widgets de acordo com o status do caixa."""
        caixa_status = get_cash_register_status()
        status = caixa_status["status"]

        if status == "aberto":
            self.cash_register_id = caixa_status["id"]
            self.current_cash_register_id = caixa_status["id"]
            self.is_cash_register_open = True
            self.btn_abrir_caixa.config(state=tk.DISABLED)
            self.btn_fechar_caixa.config(state=tk.NORMAL)
            self.btn_adicionar_item.config(state=tk.NORMAL)
            self.btn_finalizar_venda.config(state=tk.NORMAL)
            self.btn_limpar_venda.config(state=tk.NORMAL)
            self.btn_emitir_nota.config(state=tk.NORMAL)
            self.btn_add_f2.config(state=tk.NORMAL)
        else:
            self.cash_register_id = None
            self.current_cash_register_id = None
            self.is_cash_register_open = False
            self.btn_abrir_caixa.config(state=tk.NORMAL)
            self.btn_fechar_caixa.config(state=tk.DISABLED)
            self.btn_adicionar_item.config(state=tk.DISABLED)
            self.btn_finalizar_venda.config(state=tk.DISABLED)
            self.btn_limpar_venda.config(state=tk.DISABLED)
            self.btn_emitir_nota.config(state=tk.DISABLED)
            self.btn_add_f2.config(state=tk.DISABLED)

        self._update_cash_status_chip()
        self._update_navigation_state()

    def abrir_caixa(self):
        if self.is_cash_register_open:
            messagebox.showinfo("Aviso", "O caixa já está aberto.")
            return

        cargo = self.logged_user.get("cargo") if self.logged_user else "Caixa"
        if cargo == "Caixa":
            autorizado = self.prompt_manager_credentials(
                "Insira as credenciais do gerente para abrir o caixa deste operador."
            )
            if not autorizado:
                return

        self._request_cash_opening_value(
            "Abrir Caixa",
            "Valor de abertura do caixa (troco inicial em R$):",
            confirm_text="Abrir Caixa",
        )

    def fechar_caixa(self):
        if not self.is_cash_register_open:
            messagebox.showinfo("Aviso", "O caixa já está fechado.")
            return

        def on_confirm_fechamento(valor_final):
            total_vendas = get_daily_sales_total()
            valor_abertura = (
                self.initial_cash_value or get_open_cash_register_initial_value()
            )
            close_cash_register_db(
                self.current_cash_register_id, valor_final, total_vendas
            )
            self.is_cash_register_open = False
            self.current_cash_register_id = None

            diferenca = valor_final - (valor_abertura + total_vendas)
            status_msg = (
                "Batido" if abs(diferenca) < 0.01 else f"Diferença: R$ {diferenca:.2f}"
            )

            messagebox.showinfo(
                "Caixa Fechado", f"Caixa fechado com sucesso.\n{status_msg}"
            )
            self.update_ui_state()

        OpenCloseCaixaDialog(
            self, "Fechar Caixa", "Valor em Caixa (Dinheiro):", on_confirm_fechamento
        )


def _styled_text_dialog(
    app, title, subtitle, content, size=(760, 520), accent="#EEF7F0"
):
    dialog = tk.Toplevel(app)
    theme, card, body = build_dialog_shell(
        dialog, app, title, subtitle=subtitle, size=size, controller=app
    )

    text_frame = tk.Frame(body, bg=theme["surface"])
    text_frame.pack(fill="both", expand=True)

    text_widget = tk.Text(
        text_frame,
        wrap="word",
        font=("Consolas", 10),
        bg="#FCFDF8",
        fg=theme["text"],
        relief="flat",
        padx=12,
        pady=12,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    text_widget.insert("1.0", content)
    text_widget.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    footer = tk.Frame(body, bg=theme["surface"])
    footer.pack(fill="x", pady=(16, 0))
    btn_close = tk.Button(footer, text="Fechar", command=dialog.destroy)
    style_button(btn_close, "secondary", theme).pack(side="right")
    return dialog


def _frutaria_handle_cash_access_startup_v2(self):
    status = get_cash_register_status()
    if status.get("status") == "aberto":
        self.is_cash_register_open = True
        self.current_cash_register_id = status.get("id")
        self.cash_register_id = status.get("id")
        self.initial_cash_value = status.get("valor_abertura", 0.0)
        self._set_status_banner(
            f"Caixa #{self.current_cash_register_id} retomado com abertura de R$ {self.initial_cash_value:.2f}."
        )
        self.update_ui_state()
        return True

    cargo = self.logged_user.get("cargo") if self.logged_user else "Caixa"

    if cargo == "Gerente":
        self._set_status_banner("Informe o troco inicial para iniciar o caixa.")
        confirmed = self._request_cash_opening_value(
            "Iniciar Caixa",
            "Informe o valor inicial de troco para abrir o caixa.",
            confirm_text="Iniciar Caixa",
        )
        if not confirmed:
            self._set_status_banner(
                "Caixa fechado. Informe o troco inicial para iniciar as vendas."
            )
        return confirmed

    self._set_status_banner("Abertura de caixa exige autorização do gerente.")
    autorizado = self.prompt_manager_credentials(
        "Insira as credenciais do gerente para liberar este caixa."
    )
    if not autorizado:
        messagebox.showwarning(
            "Acesso não autorizado",
            "O acesso ao caixa foi cancelado porque a autorização do gerente não foi informada.",
            parent=self,
        )
        self.after(100, self.destroy)
        return False

    confirmed = self._request_cash_opening_value(
        "Troco Inicial do Caixa",
        "Informe o valor inicial de troco para este operador iniciar o caixa.",
        confirm_text="Liberar Caixa",
    )
    if not confirmed:
        messagebox.showinfo(
            "Acesso cancelado",
            "O caixa não foi iniciado. O aplicativo será encerrado.",
            parent=self,
        )
        self.after(100, self.destroy)
    return confirmed


def _frutaria_update_ui_state_v2(self):
    caixa_status = get_cash_register_status()
    status = caixa_status["status"]
    aberto = status == "aberto"

    self.cash_register_id = caixa_status.get("id") if aberto else None
    self.current_cash_register_id = caixa_status.get("id") if aberto else None
    self.is_cash_register_open = aberto
    if aberto:
        self.initial_cash_value = caixa_status.get(
            "valor_abertura", self.initial_cash_value
        )

    controls = [
        (getattr(self, "btn_abrir_caixa", None), tk.DISABLED if aberto else tk.NORMAL),
        (getattr(self, "btn_fechar_caixa", None), tk.NORMAL if aberto else tk.DISABLED),
        (
            getattr(self, "btn_adicionar_item", None),
            tk.NORMAL if aberto else tk.DISABLED,
        ),
        (
            getattr(self, "btn_finalizar_venda", None),
            tk.NORMAL if aberto else tk.DISABLED,
        ),
        (getattr(self, "btn_limpar_venda", None), tk.NORMAL if aberto else tk.DISABLED),
        (getattr(self, "btn_emitir_nota", None), tk.NORMAL if aberto else tk.DISABLED),
        (getattr(self, "btn_add_f2", None), tk.NORMAL if aberto else tk.DISABLED),
    ]
    for widget, state in controls:
        if widget is not None:
            widget.config(state=state)

    if hasattr(self, "produto_entry"):
        self.produto_entry.config(state="normal" if aberto else "disabled")
    if hasattr(self, "quantidade_entry"):
        self.quantidade_entry.config(state="normal" if aberto else "disabled")

    self._update_cash_status_chip()
    self._update_navigation_state()


def _frutaria_open_adicionar_item_dialog_v2(self, event=None):
    if get_cash_register_status().get("status") != "aberto":
        messagebox.showwarning("Caixa Fechado", "Abra o caixa primeiro.", parent=self)
        return
    self.desativar_monitor_balanca()
    self.parar_monitor_balanca()
    AdicionarItemDialog(
        self,
        self.atualizar_carrinho_treeview,
        self.adicionar_item_carrinho,
        self.balanca_instance,
    )


def _frutaria_show_note_dialog_v2(self):
    if get_cash_register_status().get("status") != "aberto":
        messagebox.showwarning("Caixa Fechado", "Abra o caixa primeiro.", parent=self)
        return
    return FrutariaApp.__dict__["_original_show_note_dialog"](self)


def _frutaria_fechar_caixa_v2(self):
    if get_cash_register_status().get("status") != "aberto":
        messagebox.showinfo("Aviso", "O caixa já está fechado.")
        self.update_ui_state()
        return

    total_vendas = get_daily_sales_total()
    valor_abertura = self.initial_cash_value or get_open_cash_register_initial_value()
    pagamentos = get_daily_sales_payment_summary()

    def on_confirm_fechamento(resumo_fechamento):
        status = get_cash_register_status()
        caixa_id = (
            status.get("id")
            or self.current_cash_register_id
            or getattr(self, "cash_register_id", None)
        )
        if not caixa_id:
            messagebox.showerror(
                "Erro",
                "Nenhum caixa aberto foi encontrado para fechamento.",
                parent=self,
            )
            self.update_ui_state()
            return

        total_conferido = float(resumo_fechamento["total_conferido"])
        lucro_dia = float(resumo_fechamento["lucro_dia"])
        diferenca = float(resumo_fechamento["diferenca"])
        close_cash_register_db(caixa_id, total_conferido, total_vendas)

        self.carrinho_itens = []
        if hasattr(self, "atualizar_carrinho_treeview"):
            self.atualizar_carrinho_treeview()
        if hasattr(self, "atualizar_total"):
            self.atualizar_total()
        if hasattr(self, "_limpar_campos_entrada"):
            self._limpar_campos_entrada()

        self.is_cash_register_open = False
        self.current_cash_register_id = None
        self.cash_register_id = None
        self.initial_cash_value = 0.0
        self._set_status_banner("Caixa fechado. Pronto para uma nova abertura.")

        diferenca_msg = (
            "Caixa batido"
            if abs(diferenca) < 0.01
        else f"Diferença apurada: R$ {diferenca:.2f}"
        )
        messagebox.showinfo(
            "Caixa Fechado",
            (
                "Caixa fechado com sucesso.\n"
                f"Lucro do dia: R$ {lucro_dia:.2f}\n"
                f"{diferenca_msg}"
            ),
            parent=self,
        )
        self.update_ui_state()

    OpenCloseCaixaDialog(
        self,
        "Fechar Caixa",
        "Confira os valores apurados e confirme o fechamento do caixa.",
        on_confirm_fechamento,
        confirm_text="Concluir Fechamento",
        close_summary={
            "valor_abertura": valor_abertura,
            "total_vendas": total_vendas,
            "pagamentos": pagamentos,
        },
    )


if "_original_show_note_dialog" not in FrutariaApp.__dict__:
    FrutariaApp._original_show_note_dialog = FrutariaApp.show_note_dialog
FrutariaApp._handle_cash_access_startup = _frutaria_handle_cash_access_startup_v2
FrutariaApp.update_ui_state = _frutaria_update_ui_state_v2
FrutariaApp.open_adicionar_item_dialog = _frutaria_open_adicionar_item_dialog_v2
FrutariaApp.show_note_dialog = _frutaria_show_note_dialog_v2
FrutariaApp.fechar_caixa = _frutaria_fechar_caixa_v2


def _frutaria_parse_sale_items(self, itens_str):
    if not itens_str:
        return []
    try:
        return json.loads(itens_str)
    except Exception:
        try:
            return ast.literal_eval(itens_str)
        except Exception:
            return []


def _frutaria_build_sales_chart_points(self, sales, period_key=None):
    import calendar

    period = period_key or getattr(self, "sales_report_period", "all")
    totals = {}

    if period == "week":
        for sale in sales:
            key = sale["data"].strftime("%a")
            totals[key] = totals.get(key, 0.0) + sale["total"]
        ordered = []
        abbrs = list(calendar.day_abbr)
        for key in abbrs:
            ordered.append((key, totals.get(key, 0.0)))
        return ordered

    if period == "month":
        for sale in sales:
            key = sale["data"].strftime("%d/%m")
            totals[key] = totals.get(key, 0.0) + sale["total"]
        return sorted(
            totals.items(), key=lambda item: datetime.strptime(item[0], "%d/%m")
        )

    if period == "year":
        for sale in sales:
            key = sale["data"].strftime("%m")
            totals[key] = totals.get(key, 0.0) + sale["total"]
        ordered = []
        for month in range(1, 13):
            label = calendar.month_abbr[month].capitalize()
            ordered.append((label, totals.get(f"{month:02d}", 0.0)))
        return ordered

    for sale in sales:
        key = sale["data"].strftime("%Y-%m")
        totals[key] = totals.get(key, 0.0) + sale["total"]

    ordered_keys = sorted(totals.keys())[-12:]
    return [
        (datetime.strptime(key, "%Y-%m").strftime("%b/%y").capitalize(), totals[key])
        for key in ordered_keys
    ]


def _frutaria_draw_sales_history_chart(self, points):
    canvas = getattr(self, "report_chart_canvas", None)
    if canvas is None:
        return

    canvas.delete("all")
    canvas.update_idletasks()
    width = max(canvas.winfo_width(), 640)
    height = max(canvas.winfo_height(), 210)
    left = 52
    right = width - 24
    top = 20
    bottom = height - 34
    theme = getattr(self, "theme", APP_THEME)

    canvas.create_rectangle(
        0,
        0,
        width,
        height,
        fill=theme.get("surface_elevated", "#FCFDF8"),
        outline="",
    )

    if not points:
        canvas.create_text(
            width / 2,
            height / 2,
            text="Sem vendas no período selecionado.",
            fill=theme["text_muted"],
            font=("Segoe UI", 11),
        )
        return

    values = [value for _, value in points]
    max_value = max(values) if values else 0.0
    if max_value <= 0:
        max_value = 1.0

    grid_steps = 4
    for step in range(grid_steps + 1):
        y = top + ((bottom - top) / grid_steps) * step
        canvas.create_line(left, y, right, y, fill=theme["border"])
        value = max_value * (1 - (step / grid_steps))
        canvas.create_text(
            left - 8,
            y,
            text=f"R$ {value:,.0f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
            anchor="e",
            fill=theme["text_muted"],
            font=("Segoe UI", 8),
        )

    canvas.create_line(left, top, left, bottom, fill=theme["border"], width=1)
    canvas.create_line(left, bottom, right, bottom, fill=theme["border"], width=1)

    if len(points) == 1:
        x_positions = [left + ((right - left) / 2)]
    else:
        step_x = (right - left) / (len(points) - 1)
        x_positions = [left + step_x * index for index in range(len(points))]

    line_points = []
    for index, (label, value) in enumerate(points):
        x = x_positions[index]
        y = bottom - ((value / max_value) * (bottom - top))
        line_points.extend([x, y])
        canvas.create_oval(
            x - 4,
            y - 4,
            x + 4,
            y + 4,
            fill=theme["accent"],
            outline=theme["surface"],
            width=1,
        )
        canvas.create_text(
            x,
            bottom + 16,
            text=label,
            fill=theme["text"],
            font=("Segoe UI", 8),
        )

    if len(line_points) >= 4:
        canvas.create_line(*line_points, fill=theme["primary_dark"], width=3, smooth=True)


def _frutaria_refresh_sales_history_dashboard(self):
    sales, period_label = self._fetch_sales_history(
        getattr(self, "sales_report_period", "all")
    )
    self.sales_history_cache = sales
    self.sales_report_period_label = period_label
    if hasattr(self, "report_period_caption_var"):
        self.report_period_caption_var.set(period_label)

    tree = getattr(self, "relatorio_tree", None)
    if tree is not None:
        for item in tree.get_children():
            tree.delete(item)

    total_value = sum(sale["total"] for sale in sales)
    sale_count = len(sales)
    average_ticket = total_value / sale_count if sale_count else 0.0

    best_day = "Sem dados"
    if sales:
        daily_totals = {}
        for sale in sales:
            key = sale["data"].strftime("%d/%m/%Y")
            daily_totals[key] = daily_totals.get(key, 0.0) + sale["total"]
        best_label, best_total = max(daily_totals.items(), key=lambda item: item[1])
        best_day = (
            f"{best_label} | R$ {best_total:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    if hasattr(self, "report_total_var"):
        self.report_total_var.set(
            f"R$ {total_value:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    if hasattr(self, "report_count_var"):
        self.report_count_var.set(f"{sale_count} vendas")
    if hasattr(self, "report_avg_var"):
        self.report_avg_var.set(
            f"R$ {average_ticket:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    if hasattr(self, "report_best_var"):
        self.report_best_var.set(best_day)

    if tree is not None:
        for sale in sales:
            items_summary = ", ".join(
                item.get("nome", "Item") for item in sale["itens"]
            )
            if len(items_summary) > 88:
                items_summary = items_summary[:85] + "..."
            tree.insert(
                "",
                "end",
                values=(
                    sale["id"],
                    sale["data"].strftime("%d/%m/%Y %H:%M"),
                    sale["metodo"],
                    f"R$ {sale['total']:,.2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", "."),
                    items_summary or "Sem itens detalhados",
                ),
            )

    points = self._build_sales_chart_points(
        sales, getattr(self, "sales_report_period", "all")
    )
    if hasattr(self, "report_chart_caption_var"):
        if points and sale_count:
            self.report_chart_caption_var.set(
                f"{period_label} | {sale_count} vendas registradas | gráfico de faturamento."
            )
        else:
            self.report_chart_caption_var.set(
                f"{period_label} | sem vendas registradas."
            )
    self._draw_sales_history_chart(points)

    for key, button in getattr(self, "report_period_buttons", {}).items():
        selected = key == getattr(self, "sales_report_period", "all")
        button.configure(
            bg=self.theme["primary_dark"] if selected else self.theme["surface"],
            fg=self.theme["text_on_dark"] if selected else self.theme["text"],
            activebackground=(
                self.theme["primary"]
                if selected
                else self.theme.get("surface_elevated", self.theme["surface"])
            ),
            activeforeground=(
                self.theme["text_on_dark"] if selected else self.theme["text"]
            ),
            highlightbackground=(
                self.theme["primary_dark"] if selected else self.theme["border"]
            ),
        )


def _frutaria_set_sales_report_period(self, period_key):
    self.sales_report_period = period_key
    self.refresh_sales_history_dashboard()


def _frutaria_generate_management_report_text(
    self, report_type="completo", period_key=None
):
    sales, period_label = self._fetch_sales_history(
        period_key or getattr(self, "sales_report_period", "all")
    )
    total_value = sum(sale["total"] for sale in sales)
    methods = {}
    for sale in sales:
        methods[sale["metodo"]] = methods.get(sale["metodo"], 0) + 1

    lines = []
    lines.append(REPORT_HEADER)
    lines.append(f"Período: {period_label}")
    lines.append(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    lines.append("-" * 64)
    lines.append(f"Total de vendas: {len(sales)}")
    lines.append(
        f"Faturamento: R$ {total_value:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    ticket = (total_value / len(sales)) if sales else 0.0
    lines.append(
        f"Ticket medio: R$ {ticket:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    if methods:
        resumo_metodos = ", ".join(
            f"{name}: {count}" for name, count in sorted(methods.items())
        )
        lines.append(f"Pagamentos: {resumo_metodos}")
    lines.append("-" * 64)

    if report_type == "simplificado":
        for sale in sales:
            lines.append(
                f"#{sale['id']:04d} | {sale['data'].strftime('%d/%m/%Y %H:%M')} | {sale['metodo']:<10} | "
                f"R$ {sale['total']:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        if not sales:
            lines.append("Nenhuma venda encontrada neste período.")
        lines.extend(("", REPORT_FOOTER))
        return "\n".join(lines)

    for sale in sales:
        lines.append(
            f"Venda #{sale['id']} | {sale['data'].strftime('%d/%m/%Y %H:%M')} | {sale['metodo']} | "
            f"R$ {sale['total']:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        for item in sale["itens"]:
            nome = item.get("nome", "Item")
            quantidade = float(item.get("quantidade", 0.0) or 0.0)
            subtotal = float(item.get("subtotal", 0.0) or 0.0)
            lines.append(
                f"  - {nome} | qtd {quantidade:.3f} | subtotal R$ {subtotal:,.2f}".replace(
                    ",", "X"
                )
                .replace(".", ",")
                .replace("X", ".")
            )
        lines.append("")

    if not sales:
        lines.append("Nenhuma venda encontrada neste período.")
    lines.extend(("", REPORT_FOOTER))
    return "\n".join(lines)


def _frutaria_print_management_report(self, report_type="completo", period_key=None):
    report_text = self.generate_management_report_text(report_type, period_key)
    job_name = (
        "Relatório Gerencial - Simplificado"
        if report_type == "simplificado"
        else "Relatório Gerencial - Completo"
    )
    return self._send_text_to_printer(report_text, job_name)


def _frutaria_show_report_preview_v2(self, report_type, parent_window):
    if parent_window is not None:
        parent_window.destroy()

    report_text = self.generate_management_report_text(report_type)
    report_window = tk.Toplevel(self)
    title = (
        "Preview do Relatório Simplificado"
        if report_type == "simplificado"
        else "Preview do Relatório Completo"
    )
    theme, card, body = build_dialog_shell(
        report_window,
        self,
        title,
        subtitle=f"Período ativo: {getattr(self, 'sales_report_period_label', 'Histórico completo')}",
        size=(900, 660),
        controller=self,
    )
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)

    text_frame = tk.Frame(body, bg=theme["surface"])
    text_frame.grid(row=0, column=0, sticky="nsew")
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    text_widget = tk.Text(
        text_frame,
        font=("Consolas", 10),
        bg="#FCFDF8",
        fg=theme["text"],
        relief="flat",
        padx=14,
        pady=14,
        wrap="word",
    )
    text_widget.grid(row=0, column=0, sticky="nsew")
    text_widget.insert("1.0", report_text)
    text_widget.configure(state="disabled")

    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_widget.configure(yscrollcommand=scrollbar.set)

    actions = tk.Frame(body, bg=theme["surface"])
    actions.grid(row=1, column=0, sticky="ew", pady=(14, 0))
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)
    actions.columnconfigure(2, weight=1)

    style_button(
        tk.Button(actions, text="Fechar", command=report_window.destroy), "muted", theme
    ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
    style_button(
        tk.Button(
            actions,
            text="Imprimir",
            command=lambda: self.print_management_report(report_type),
        ),
        "primary",
        theme,
    ).grid(row=0, column=1, sticky="ew", padx=8)
    style_button(
        tk.Button(
            actions,
            text="Atualizar Dados",
            command=lambda: [
                self.refresh_sales_history_dashboard(),
                report_window.destroy(),
                self.show_report_preview(report_type, None),
            ],
        ),
        "accent",
        theme,
    ).grid(row=0, column=2, sticky="ew", padx=(8, 0))


def _frutaria_show_report_print_menu_v2(self):
    report_dialog = tk.Toplevel(self)
    period_label = getattr(self, "sales_report_period_label", "Histórico completo")
    theme, card, body = build_dialog_shell(
        report_dialog,
        self,
        "Emitir Relatório Gerencial",
        subtitle=f"Selecione o formato para o período ativo: {period_label}.",
        size=(620, 360),
        controller=self,
    )
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=1)

    simple_card = tk.Frame(
        body,
        bg="#EAF7EC",
        padx=18,
        pady=18,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    simple_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    full_card = tk.Frame(
        body,
        bg="#EDF4FF",
        padx=18,
        pady=18,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    full_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    body.rowconfigure(0, weight=1)

    tk.Label(
        simple_card,
        text="Simplificado",
        font=("Segoe UI Semibold", 15),
        bg="#EAF7EC",
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        simple_card,
        text="Resumo executivo com vendas, faturamento e forma de pagamento.",
        wraplength=220,
        justify="left",
        font=("Segoe UI", 10),
        bg="#EAF7EC",
        fg=theme["text_muted"],
    ).pack(anchor="w", pady=(8, 16))
    style_button(
        tk.Button(
            simple_card,
            text="Abrir Preview",
            command=lambda: self.show_report_preview("simplificado", report_dialog),
        ),
        "primary",
        theme,
    ).pack(fill="x")

    tk.Label(
        full_card,
        text="Completo",
        font=("Segoe UI Semibold", 15),
        bg="#EDF4FF",
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        full_card,
        text="Lista detalhada de vendas e itens para auditoria e impressão operacional.",
        wraplength=220,
        justify="left",
        font=("Segoe UI", 10),
        bg="#EDF4FF",
        fg=theme["text_muted"],
    ).pack(anchor="w", pady=(8, 16))
    style_button(
        tk.Button(
            full_card,
            text="Abrir Preview",
            command=lambda: self.show_report_preview("completo", report_dialog),
        ),
        "accent",
        theme,
    ).pack(fill="x")


FrutariaApp._parse_sale_items = _frutaria_parse_sale_items
FrutariaApp._build_sales_chart_points = _frutaria_build_sales_chart_points
FrutariaApp._draw_sales_history_chart = _frutaria_draw_sales_history_chart
FrutariaApp.refresh_sales_history_dashboard = _frutaria_refresh_sales_history_dashboard
FrutariaApp.set_sales_report_period = _frutaria_set_sales_report_period
FrutariaApp.generate_management_report_text = _frutaria_generate_management_report_text
FrutariaApp.print_management_report = _frutaria_print_management_report
FrutariaApp.show_report_preview = _frutaria_show_report_preview_v2
FrutariaApp.show_report_print_menu = _frutaria_show_report_print_menu_v2


def _frutaria_get_active_report_tree(self):
    if getattr(self, "current_page", None) == "relatorios_view":
        return getattr(self, "relatorio_dia_tree", None)
    return getattr(self, "relatorio_tree", None)


def _frutaria_create_main_app_layout_v2(self):
    if not hasattr(self, "relatorios_gerais_view_frame"):
        self.relatorios_gerais_view_frame = tk.Frame(self.container, bg=self.bg_color)
        self.frames["relatorios_gerais_view"] = self.relatorios_gerais_view_frame

    for page_name, frame in self.frames.items():
        if page_name != "main_app":
            frame.place(x=0, y=0, relwidth=1, relheight=1)

    create_caixa_layout(self)
    create_gerencia_layout(self)
    create_produtos_view(self)
    create_funcionarios_view(self)
    create_relatorios_view(self)
    create_relatorios_gerais_view(self)
    create_empresa_view(self)
    print("LAYOUTS: create_main_app_layout concluido.")


def _frutaria_show_frame_v3(self, page_name):
    if (
        page_name != "caixa"
        and self.logged_user
        and self.logged_user.get("cargo") != "Gerente"
    ):
        messagebox.showwarning(
            "Acesso Negado", "Você não tem permissão para acessar a Gerência."
        )
        return

    frame = self.frames.get(page_name)
    if frame is None:
        return

    self._apply_shell_for_page(page_name)

    if page_name == "caixa":
        create_caixa_layout(self)
        if not self.is_cash_register_open:
            self._handle_cash_access_startup()
            if (
                self.logged_user
                and self.logged_user.get("cargo") == "Caixa"
                and not self.winfo_exists()
            ):
                return
    elif page_name == "gerencia":
        create_gerencia_layout(self)
    elif page_name == "produtos_view":
        self.refresh_produtos_view()
    elif page_name == "funcionarios_view":
        self.refresh_funcionarios_view()
    elif page_name == "relatorios_view":
        create_relatorios_view(self)
        self.update_daily_sales_report()
    elif page_name == "relatorios_gerais_view":
        create_relatorios_gerais_view(self)
        self.refresh_sales_history_dashboard()
    elif page_name == "empresa_view":
        create_empresa_view(self)
        self.carregar_dados_empresa_na_tela()

    frame.tkraise()
    self.current_page = page_name
    self.page_title_var.set(get_page_title(page_name))
    self._update_navigation_state()

    if page_name == "caixa" and hasattr(self, "produto_entry"):
        self.produto_entry.focus_set()


def _frutaria_update_daily_sales_report_v2(self):
    tree = getattr(self, "relatorio_dia_tree", None)
    if tree is None:
        return

    sales, label = self._fetch_sales_history("today")
    self.daily_sales_cache = sales
    self.daily_report_period_label = label
    if hasattr(self, "daily_report_caption_var"):
        self.daily_report_caption_var.set(
            f"{label} | acompanhe o fechamento operacional e valide as vendas registradas."
        )

    for item in tree.get_children():
        tree.delete(item)

    total_value = sum(sale["total"] for sale in sales)
    sale_count = len(sales)
    average_ticket = total_value / sale_count if sale_count else 0.0
    best_sale = max((sale["total"] for sale in sales), default=0.0)

    if hasattr(self, "daily_report_total_var"):
        self.daily_report_total_var.set(
            f"R$ {total_value:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    if hasattr(self, "daily_report_count_var"):
        self.daily_report_count_var.set(f"{sale_count} vendas")
    if hasattr(self, "daily_report_avg_var"):
        self.daily_report_avg_var.set(
            f"R$ {average_ticket:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    if hasattr(self, "daily_report_best_var"):
        self.daily_report_best_var.set(
            (
                f"R$ {best_sale:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            if sale_count
            else "Sem vendas"
        )

    for sale in sales:
        items_summary = ", ".join(item.get("nome", "Item") for item in sale["itens"])
        if len(items_summary) > 88:
            items_summary = items_summary[:85] + "..."
        tree.insert(
            "",
            "end",
            values=(
                sale["id"],
                sale["data"].strftime("%H:%M"),
                sale["metodo"],
                f"R$ {sale['total']:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
                items_summary or "Sem itens detalhados",
            ),
        )


def _frutaria_show_daily_report_print_menu(self):
    report_dialog = tk.Toplevel(self)
    period_label = getattr(
        self, "daily_report_period_label", f"Dia {datetime.now().strftime('%d/%m/%Y')}"
    )
    theme, card, body = build_dialog_shell(
        report_dialog,
        self,
        "Emitir Relatório do Dia",
        subtitle=f"Selecione o formato para o período ativo: {period_label}.",
        size=(620, 360),
        controller=self,
    )
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=1)

    simple_card = tk.Frame(
        body,
        bg="#EAF7EC",
        padx=18,
        pady=18,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    simple_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    full_card = tk.Frame(
        body,
        bg="#EDF4FF",
        padx=18,
        pady=18,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    full_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    body.rowconfigure(0, weight=1)

    tk.Label(
        simple_card,
        text="Simplificado",
        font=("Segoe UI Semibold", 15),
        bg="#EAF7EC",
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        simple_card,
        text="Resumo rápido das vendas do dia para conferência e impressão operacional.",
        wraplength=220,
        justify="left",
        font=("Segoe UI", 10),
        bg="#EAF7EC",
        fg=theme["text_muted"],
    ).pack(anchor="w", pady=(8, 16))
    style_button(
        tk.Button(
            simple_card,
            text="Abrir Preview",
            command=lambda: self.show_daily_report_preview(
                "simplificado", report_dialog
            ),
        ),
        "primary",
        theme,
    ).pack(fill="x")

    tk.Label(
        full_card,
        text="Completo",
        font=("Segoe UI Semibold", 15),
        bg="#EDF4FF",
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        full_card,
        text="Detalhamento das vendas e itens do dia para auditoria do fechamento.",
        wraplength=220,
        justify="left",
        font=("Segoe UI", 10),
        bg="#EDF4FF",
        fg=theme["text_muted"],
    ).pack(anchor="w", pady=(8, 16))
    style_button(
        tk.Button(
            full_card,
            text="Abrir Preview",
            command=lambda: self.show_daily_report_preview("completo", report_dialog),
        ),
        "accent",
        theme,
    ).pack(fill="x")


def _frutaria_show_daily_report_preview(self, report_type, parent_window):
    if parent_window is not None:
        parent_window.destroy()

    report_text = self.generate_management_report_text(report_type, "today")
    report_window = tk.Toplevel(self)
    title = (
        "Preview do Relatório Diário Simplificado"
        if report_type == "simplificado"
        else "Preview do Relatório Diário Completo"
    )
    theme, card, body = build_dialog_shell(
        report_window,
        self,
        title,
        subtitle=f"Período ativo: {getattr(self, 'daily_report_period_label', f'Dia {datetime.now().strftime('%d/%m/%Y')}')}",
        size=(900, 660),
        controller=self,
    )
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)

    text_frame = tk.Frame(body, bg=theme["surface"])
    text_frame.grid(row=0, column=0, sticky="nsew")
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    text_widget = tk.Text(
        text_frame,
        font=("Consolas", 10),
        bg="#FCFDF8",
        fg=theme["text"],
        relief="flat",
        padx=14,
        pady=14,
        wrap="word",
    )
    text_widget.grid(row=0, column=0, sticky="nsew")
    text_widget.insert("1.0", report_text)
    text_widget.configure(state="disabled")

    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_widget.configure(yscrollcommand=scrollbar.set)

    actions = tk.Frame(body, bg=theme["surface"])
    actions.grid(row=1, column=0, sticky="ew", pady=(14, 0))
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)
    actions.columnconfigure(2, weight=1)

    style_button(
        tk.Button(actions, text="Fechar", command=report_window.destroy), "muted", theme
    ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
    style_button(
        tk.Button(
            actions,
            text="Imprimir",
            command=lambda: self.print_management_report(report_type, "today"),
        ),
        "primary",
        theme,
    ).grid(row=0, column=1, sticky="ew", padx=8)
    style_button(
        tk.Button(
            actions,
            text="Atualizar Dados",
            command=lambda: [
                self.update_daily_sales_report(),
                report_window.destroy(),
                self.show_daily_report_preview(report_type, None),
            ],
        ),
        "accent",
        theme,
    ).grid(row=0, column=2, sticky="ew", padx=(8, 0))


def _frutaria_show_general_report_print_menu(self):
    return self.show_report_print_menu()


def _frutaria_edit_sale_v3(self):
    tree = self._get_active_report_tree()
    if tree is None:
        return
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning(
            "Nenhuma venda selecionada", "Selecione uma venda para editar.", parent=self
        )
        return
    venda_data = tree.item(selected_items[0])["values"]
    callback = (
        self.update_daily_sales_report
        if getattr(self, "current_page", None) == "relatorios_view"
        else self.refresh_sales_history_dashboard
    )
    EdicaoVendaDialog(self, self, venda_data, on_save=callback)


def _frutaria_delete_sale_v3(self):
    tree = self._get_active_report_tree()
    if tree is None:
        return
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning(
            "Nenhuma venda selecionada",
            "Selecione uma venda para excluir.",
            parent=self,
        )
        return
    venda_data = tree.item(selected_items[0])["values"]
    venda_id = venda_data[0]
    if not messagebox.askyesno(
        "Confirmar exclusão",
                f"Deseja excluir a venda #{venda_id}? Esta ação não pode ser desfeita.",
        parent=self,
    ):
        return
    try:
        delete_sale_db(venda_id)
        if getattr(self, "current_page", None) == "relatorios_view":
            self.update_daily_sales_report()
        else:
            self.refresh_sales_history_dashboard()
        messagebox.showinfo("Sucesso", "Venda excluida com sucesso.", parent=self)
    except Exception as exc:
        messagebox.showerror(
            "Erro", f"Não foi possível excluir a venda: {exc}", parent=self
        )


def _frutaria_show_sale_details_v3(self, event=None):
    tree = self._get_active_report_tree()
    if tree is None:
        return
    selected_items = tree.selection()
    if not selected_items:
        return
    venda_data = tree.item(selected_items[0])["values"]
    venda_id = venda_data[0]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data_venda, total, metodo_pagamento, itens_vendidos FROM vendas WHERE id=?",
        (venda_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        messagebox.showwarning(
            "Venda não encontrada",
            "Não foi possível carregar os detalhes da venda.",
            parent=self,
        )
        return

    data_venda, total, metodo, itens_str = row
    itens = self._parse_sale_items(itens_str)
    lines = [
        f"Venda #{venda_id}",
        f'Data: {datetime.strptime(data_venda, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")}',
        f'Metodo: {(metodo or "N/D").title()}',
        f"Total: R$ {float(total or 0.0):,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
        "",
        "Itens registrados:",
    ]
    for item in itens:
        quantidade = float(item.get("quantidade", 0.0) or 0.0)
        subtotal = float(item.get("subtotal", 0.0) or 0.0)
        lines.append(
            f"- {item.get('nome', 'Item')} | qtd {quantidade:.3f} | subtotal R$ {subtotal:,.2f}".replace(
                ",", "X"
            )
            .replace(".", ",")
            .replace("X", ".")
        )

    subtitulo = (
        "Conferência completa da venda selecionada."
        if getattr(self, "current_page", None) == "relatorios_gerais_view"
        else "Detalhamento da venda do dia selecionada."
    )
    _styled_text_dialog(
        self,
        f"Detalhes da Venda {venda_id}",
        subtitulo,
        "\n".join(lines),
        size=(760, 540),
    )


FrutariaApp._get_active_report_tree = _frutaria_get_active_report_tree
FrutariaApp.create_main_app_layout = _frutaria_create_main_app_layout_v2
FrutariaApp.show_frame = _frutaria_show_frame_v3
FrutariaApp.update_daily_sales_report = _frutaria_update_daily_sales_report_v2
FrutariaApp.show_daily_report_print_menu = _frutaria_show_daily_report_print_menu
FrutariaApp.show_daily_report_preview = _frutaria_show_daily_report_preview
FrutariaApp.show_general_report_print_menu = _frutaria_show_general_report_print_menu
FrutariaApp.edit_sale = _frutaria_edit_sale_v3
FrutariaApp.delete_sale = _frutaria_delete_sale_v3
FrutariaApp.show_sale_details = _frutaria_show_sale_details_v3


def _frutaria_resolve_printer_name_v2(self):
    available = []
    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        available = [item[2] for item in win32print.EnumPrinters(flags)]
    except Exception:
        available = []

    requested = getattr(self, "printer_name", None)
    if requested and requested in available:
        return requested

    preferred_tokens = ("MP-4200", "BEMATECH", "MP4200")
    for name in available:
        upper = name.upper()
        if any(token in upper for token in preferred_tokens):
            return name

    try:
        default_printer = win32print.GetDefaultPrinter()
        if default_printer and default_printer in available:
            return default_printer
    except Exception:
        pass

    return available[0] if available else None


def _frutaria_build_note_text(self, tipo_nota):
    ITEM_WIDTH = 2
    PRODUTO_WIDTH = 12
    QTD_UN_WIDTH_SIMP = 6
    VALOR_UN_STR_WIDTH_SIMP = 6
    TOTAL_WIDTH_SIMP = 6
    QTD_UN_WIDTH = 6
    VALOR_UN_WIDTH = 6
    TOTAL_WIDTH = 6
    SEPARATOR_COMPLETA_STR = "--------------------------------------"

    PRODUTO_WIDTH_SIMP = 12
    SEPARATOR_SIMPLIFICADA_STR = "--------------------------------------"

    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    company_header = self._build_company_receipt_header_lines(38)
    company_header_text = "".join(f"{line}\n" for line in company_header[1:])

    if tipo_nota == "simplificada":
        note_text = (
            f"{company_header[0]}\n"
            f"\n"
            f"{company_header_text}"
            f"Data: {current_time}\n"
            f"\n"
            f"CUPOM NÃO FISCAL\n"
            f"Documento apenas para conferência\n"
            f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            f"\n"
        )
        total = 0.0
        for item in self.carrinho_itens:
            unidade_display = item["unidade"]
            if unidade_display == "unidade":
                unidade_display = "un"
            item_name = item["nome"][:PRODUTO_WIDTH_SIMP].ljust(PRODUTO_WIDTH_SIMP)
            qtd_un_str = f"{item['quantidade']:.2f}{unidade_display}".ljust(
                QTD_UN_WIDTH_SIMP
            )
            valor_un_str = f"R${item['preco']:.2f}".ljust(VALOR_UN_STR_WIDTH_SIMP)
            total_str = f"R${item['subtotal']:.2f}".ljust(TOTAL_WIDTH_SIMP)
            note_text += f"{item_name}|{qtd_un_str}|{valor_un_str}|{total_str}\n"
            total += item["subtotal"]
        note_text += (
            f"\n{SEPARATOR_SIMPLIFICADA_STR}\n"
            f"TOTAL: R${total:.2f}\n"
            f"{SEPARATOR_SIMPLIFICADA_STR}\n"
            f"\n"
            f"Obrigado pela preferência\n"
            f"Volte Sempre\n"
            f"{REPORT_FOOTER}\n"
        )
        return note_text

    note_text = (
        f"{company_header[0]}\n"
        f"\n"
        f"{company_header_text}"
        f"Data e Hora: {current_time}\n"
        f"\n"
        f"{SEPARATOR_COMPLETA_STR}\n"
        f"CUPOM NÃO FISCAL\n"
        f"Documento apenas para conferência\n"
        f"{SEPARATOR_COMPLETA_STR}\n"
        f"{'IT':<{ITEM_WIDTH}}|{'PRODUTO':<{PRODUTO_WIDTH}}|{'QTD/UN':<{QTD_UN_WIDTH}}|{'PRECO':<{VALOR_UN_WIDTH}}|{'TOTAL':<{TOTAL_WIDTH}}\n"
        f"{SEPARATOR_COMPLETA_STR}\n"
        f"\n"
    )
    total = 0.0
    for i, item in enumerate(self.carrinho_itens, 1):
        item_name = item["nome"][:PRODUTO_WIDTH].ljust(PRODUTO_WIDTH)
        unidade_display = item["unidade"]
        if unidade_display == "unidade":
            unidade_display = "un"
        qtd_un_str = f"{item['quantidade']:.2f}{unidade_display}".ljust(QTD_UN_WIDTH)
        valor_un_str = f"R${item['preco']:.2f}".ljust(VALOR_UN_WIDTH)
        total_str = f"R${item['subtotal']:.2f}".ljust(TOTAL_WIDTH)
        note_text += (
            f"{i:<{ITEM_WIDTH}}|"
            f"{item_name}|"
            f"{qtd_un_str}|"
            f"{valor_un_str}|"
            f"{total_str}\n"
        )
        total += item["subtotal"]
    note_text += (
        f"\n{SEPARATOR_COMPLETA_STR}\n"
        f"TOTAL: R${total:.2f}\n"
        f"{SEPARATOR_COMPLETA_STR}\n"
        f"\n"
        f"Obrigado pela preferência\n"
        f"Volte sempre\n"
        f"{REPORT_FOOTER}\n"
    )
    return note_text


def _frutaria_imprimir_nota_simplificada_v2(self):
    return self._send_text_to_printer(
        self._build_note_text("simplificada"), "Nota Simplificada"
    )


def _frutaria_imprimir_nota_completa_v2(self):
    return self._send_text_to_printer(
        self._build_note_text("completa"), "Nota Completa"
    )


def _frutaria_imprimir_relatorio_geral_v2(self):
    return self._send_text_to_printer(
        self.generate_report_text("simplificado"), "Relatório Simplificado"
    )


def _frutaria_imprimir_relatorio_diario_v2(self):
    return self._send_text_to_printer(
        self.generate_report_text("completo"), "Relatório de Vendas"
    )


FrutariaApp._resolve_printer_name = _frutaria_resolve_printer_name_v2
FrutariaApp._build_note_text = _frutaria_build_note_text
FrutariaApp.imprimir_nota_simplificada = _frutaria_imprimir_nota_simplificada_v2
FrutariaApp.imprimir_nota_completa = _frutaria_imprimir_nota_completa_v2
FrutariaApp.imprimir_relatorio_geral = _frutaria_imprimir_relatorio_geral_v2
FrutariaApp.imprimir_relatorio_diario = _frutaria_imprimir_relatorio_diario_v2


def _frutaria_normalize_print_text_v2(self, text):
    import unicodedata

    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\n", "\r\n")
    return normalized


def _frutaria_print_text_via_gdi(self, printer_name, text, job_name):
    dc = None
    font = None
    try:
        payload = self._normalize_print_text(text).replace("\r\n", "\n").split("\n")
        dc = win32ui.CreateDC()
        dc.CreatePrinterDC(printer_name)

        printable_width = dc.GetDeviceCaps(8)
        printable_height = dc.GetDeviceCaps(10)

        dc.StartDoc(job_name)
        dc.StartPage()

        font = win32ui.CreateFont(
            {
                "name": "Consolas",
                "height": -24,
                "weight": 500,
            }
        )
        dc.SelectObject(font)

        left_margin = 24
        top_margin = 24
        line_height = 28
        y = top_margin

        for raw_line in payload:
            line = raw_line.expandtabs(4)
            if y + line_height > printable_height - 40:
                dc.EndPage()
                dc.StartPage()
                dc.SelectObject(font)
                y = top_margin
            remaining = line or " "
            while remaining:
                chunk = remaining[:48]
                test = chunk
                while (
                    dc.GetTextExtent(test)[0] > printable_width - (left_margin * 2)
                    and len(test) > 1
                ):
                    test = test[:-1]
                chunk = test.rstrip() or " "
                dc.TextOut(left_margin, y, chunk)
                y += line_height
                remaining = remaining[len(chunk) :].lstrip()
                if y + line_height > printable_height - 40 and remaining:
                    dc.EndPage()
                    dc.StartPage()
                    dc.SelectObject(font)
                    y = top_margin
                if not remaining:
                    break

        dc.EndPage()
        dc.EndDoc()
        return True
    finally:
        try:
            if font is not None:
                font.DeleteObject()
        except Exception:
            pass
        try:
            if dc is not None:
                dc.DeleteDC()
        except Exception:
            pass


def _frutaria_send_text_to_printer_v3(self, text, job_name):
    printer_name = self._resolve_printer_name()
    if not printer_name:
        messagebox.showerror(
            "Impressão",
            "Nenhuma impressora compatível foi encontrada. Verifique a MP-4200 TH no Windows.",
            parent=self,
        )
        return False

    printer_upper = printer_name.upper()
    try:
        if any(token in printer_upper for token in ("MP-4200", "BEMATECH", "MP4200")):
            self._print_text_via_gdi(printer_name, text, job_name)
        else:
            payload = self._normalize_print_text(text) + "\r\n" * 8
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(handle, 1, (job_name, None, "RAW"))
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(
                    handle, payload.encode("cp850", errors="replace")
                )
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
        messagebox.showinfo(
            "Impressão", f"Relatório enviado para {printer_name}.", parent=self
        )
        return True
    except Exception as exc:
        messagebox.showerror(
            "Erro de Impressão",
            f"Não foi possível imprimir em {printer_name}. Erro: {exc}",
            parent=self,
        )
        return False


FrutariaApp._print_text_via_gdi = _frutaria_print_text_via_gdi
FrutariaApp._normalize_print_text = _frutaria_normalize_print_text_v2
FrutariaApp._send_text_to_printer = _frutaria_send_text_to_printer_v3


def _frutaria_format_payment_method(self, metodo):
    raw = str(metodo or "N/D").strip()
    mapping = {
        "CARTAO_CREDITO": "Cartão de Crédito",
        "CARTAO_DEBITO": "Cartão de Débito",
        "QR_CODE": "QR Code",
        "PIX": "PIX",
        "DINHEIRO": "Dinheiro",
        "N/D": "N/D",
    }
    if raw in mapping:
        return mapping[raw]
    pretty = raw.replace("_", " ").strip()
    return pretty.title() if pretty else "N/D"


def _frutaria_fetch_sales_history_v3(self, period_key=None):
    from datetime import timedelta

    period = period_key or getattr(self, "sales_report_period", "all")
    now = datetime.now()
    start_dt = None
    end_dt = None
    label = "Histórico completo"

    if period == "today":
        start_dt = datetime(now.year, now.month, now.day)
        end_dt = start_dt + timedelta(days=1)
        label = f"Dia {now.strftime('%d/%m/%Y')}"
    elif period == "week":
        start_date = now.date() - timedelta(days=now.weekday())
        start_dt = datetime.combine(start_date, datetime.min.time())
        label = "Semana atual"
    elif period == "month":
        start_dt = datetime(now.year, now.month, 1)
        label = now.strftime("%B de %Y").capitalize()
    elif period == "year":
        start_dt = datetime(now.year, 1, 1)
        label = f"Ano {now.year}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, id_funcionario, data_venda, total, itens_vendidos, metodo_pagamento, valor_pago, troco FROM vendas ORDER BY data_venda DESC, id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    sales = []
    for row in rows:
        (
            venda_id,
            funcionario_id,
            data_venda,
            total,
            itens_str,
            metodo,
            valor_pago,
            troco,
        ) = row
        try:
            dt = datetime.strptime(data_venda, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt >= end_dt:
            continue
        items = self._parse_sale_items(itens_str)
        sales.append(
            {
                "id": venda_id,
                "funcionario_id": funcionario_id,
                "data": dt,
                "total": float(total or 0.0),
                "itens": items,
                "metodo": self._format_payment_method(metodo),
                "valor_pago": float(valor_pago or 0.0),
                "troco": float(troco or 0.0),
            }
        )

    return sales, label


def _frutaria_show_sale_details_v4(self, event=None):
    tree = self._get_active_report_tree()
    if tree is None:
        return
    selected_items = tree.selection()
    if not selected_items:
        return
    venda_data = tree.item(selected_items[0])["values"]
    venda_id = venda_data[0]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data_venda, total, metodo_pagamento, itens_vendidos FROM vendas WHERE id=?",
        (venda_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        messagebox.showwarning(
            "Venda não encontrada",
            "Não foi possível carregar os detalhes da venda.",
            parent=self,
        )
        return

    data_venda, total, metodo, itens_str = row
    itens = self._parse_sale_items(itens_str)
    lines = [
        f"Venda #{venda_id}",
        f'Data: {datetime.strptime(data_venda, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")}',
        f"Metodo: {self._format_payment_method(metodo)}",
        f"Total: R$ {float(total or 0.0):,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
        "",
        "Itens registrados:",
    ]
    for item in itens:
        quantidade = float(item.get("quantidade", 0.0) or 0.0)
        subtotal = float(item.get("subtotal", 0.0) or 0.0)
        lines.append(
            f"- {item.get('nome', 'Item')} | qtd {quantidade:.3f} | subtotal R$ {subtotal:,.2f}".replace(
                ",", "X"
            )
            .replace(".", ",")
            .replace("X", ".")
        )

    subtitulo = (
        "Conferência completa da venda selecionada."
        if getattr(self, "current_page", None) == "relatorios_gerais_view"
        else "Detalhamento da venda do dia selecionada."
    )
    _styled_text_dialog(
        self,
        f"Detalhes da Venda {venda_id}",
        subtitulo,
        "\n".join(lines),
        size=(760, 540),
    )


FrutariaApp._format_payment_method = _frutaria_format_payment_method
FrutariaApp._fetch_sales_history = _frutaria_fetch_sales_history_v3
FrutariaApp.show_sale_details = _frutaria_show_sale_details_v4
