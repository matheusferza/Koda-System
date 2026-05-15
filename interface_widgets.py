import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
from branding import APP_NAME, POWERED_BY_LABEL
from dialogs import CadastroProdutoDialog, CadastroFuncionarioDialog
from database import get_all_products, get_all_employees
from utils import get_app_logo_path


def _matches_product_filters(produto, query="", initial=None):
    nome = str(produto[1] or "")
    sku = str(produto[5] or "")
    cod_barras = str(produto[6] or "")

    if initial:
        if not nome.upper().startswith(initial.upper()):
            return False

    if query:
        term = query.strip().lower()
        haystack = " ".join((nome, sku, cod_barras)).lower()
        if term not in haystack:
            return False

    return True


def _refresh_produtos_with_debounce(self, delay_ms=180):
    previous_job = getattr(self, "_produtos_search_job", None)
    if previous_job:
        try:
            self.after_cancel(previous_job)
        except Exception:
            pass

    self._produtos_search_job = self.after(delay_ms, lambda: load_produtos_to_treeview(self))


def _run_produtos_refresh_now(self):
    previous_job = getattr(self, "_produtos_search_job", None)
    if previous_job:
        try:
            self.after_cancel(previous_job)
        except Exception:
            pass
        self._produtos_search_job = None
    load_produtos_to_treeview(self)


def load_produtos_to_treeview(self):
    if not hasattr(self, "produtos_tree") or not self.produtos_tree:
        return
    self._produtos_search_job = None
    for item in self.produtos_tree.get_children():
        self.produtos_tree.delete(item)
    query = ""
    if hasattr(self, "produtos_search_var") and self.produtos_search_var is not None:
        query = self.produtos_search_var.get()

    initial = getattr(self, "produtos_alpha_filter", None)

    produtos = sorted(get_all_products(), key=lambda prod: str(prod[1] or "").lower())
    produtos = [
        prod
        for prod in produtos
        if _matches_product_filters(prod, query=query, initial=initial)
    ]

    for prod in produtos:
        self.produtos_tree.insert(
            "",
            tk.END,
            values=(
                prod[0],
                prod[1],
                f"R$ {prod[2]:.2f}".replace(".", ","),
                (
                    f"{prod[3]:.3f}".replace(".", ",")
                    if prod[4] == "kg"
                    else f"{int(prod[3])}"
                ),
                prod[4],
                prod[5],
                prod[6],
            ),
        )

    if hasattr(self, "produtos_resultado_var") and self.produtos_resultado_var is not None:
        total = len(produtos)
        filtro = f" | Letra: {initial}" if initial else ""
        self.produtos_resultado_var.set(f"{total} produto(s){filtro}")

    if hasattr(self, "produtos_alpha_buttons"):
        active_bg = getattr(self, "_produtos_alpha_active_bg", "#0F8F47")
        active_fg = getattr(self, "_produtos_alpha_active_fg", "#FFFFFF")
        idle_bg = getattr(self, "_produtos_alpha_idle_bg", "#F6F8F1")
        idle_fg = getattr(self, "_produtos_alpha_idle_fg", "#17301F")
        for letter, button in self.produtos_alpha_buttons.items():
            selected = initial == letter
            button.configure(
                bg=active_bg if selected else idle_bg,
                fg=active_fg if selected else idle_fg,
            )

    if hasattr(self, "produtos_all_button") and self.produtos_all_button is not None:
        initial_is_empty = not initial
        self.produtos_all_button.configure(
            bg=getattr(self, "_produtos_alpha_active_bg", "#0F8F47")
            if initial_is_empty
            else getattr(self, "_produtos_alpha_idle_bg", "#F6F8F1"),
            fg=getattr(self, "_produtos_alpha_active_fg", "#FFFFFF")
            if initial_is_empty
            else getattr(self, "_produtos_alpha_idle_fg", "#17301F"),
        )


def refresh_produtos_view(self):
    load_produtos_to_treeview(self)


def load_funcionarios_to_treeview(self):
    """Carrega (ou recarrega) todos os funcionários do banco de dados na Treeview."""
    if not hasattr(self, "funcionarios_tree") or not self.funcionarios_tree:
        return
    for item in self.funcionarios_tree.get_children():
        self.funcionarios_tree.delete(item)
    funcionarios = get_all_employees()
    for func in funcionarios:
        self.funcionarios_tree.insert(
            "", tk.END, values=(func[0], func[1], func[2], func[3])
        )


def create_caixa_layout(self):
    """Cria a tela de caixa com layout responsivo para notebooks."""

    for widget in self.caixa_frame.winfo_children():
        widget.destroy()

    compact_mode = self.winfo_screenwidth() <= 1366 or self.winfo_screenheight() <= 768

    outer_pad = 10 if compact_mode else 14
    section_gap = 6 if compact_mode else 8
    hero_pad_x = 18 if compact_mode else 24
    hero_pad_y = 14 if compact_mode else 22
    panel_pad = 16 if compact_mode else 22
    title_font = ("Segoe UI Black", 18 if compact_mode else 24)
    section_title_font = ("Segoe UI Semibold", 15 if compact_mode else 18)
    label_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    text_font = ("Segoe UI", 9 if compact_mode else 10)
    metric_title_font = ("Segoe UI Semibold", 8 if compact_mode else 9)
    metric_title_fontBold = ("Segoe UI", 8 if compact_mode else 9, "bold")
    metric_value_font = ("Segoe UI Black", 14 if compact_mode else 18)
    total_font = ("Segoe UI Black", 22 if compact_mode else 28)
    quantity_font = ("Segoe UI Black", 18 if compact_mode else 24)
    action_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    button_pad_y = 8 if compact_mode else 10
    entry_ipady = 5 if compact_mode else 6
    quantity_ipady = 5 if compact_mode else 10
    card_pad_x = 14 if compact_mode else 18
    card_pad_y = 12 if compact_mode else 16

    self.caixa_frame.columnconfigure(0, weight=11)
    self.caixa_frame.columnconfigure(1, weight=14)
    self.caixa_frame.rowconfigure(0, weight=0)
    self.caixa_frame.rowconfigure(1, weight=0)
    self.caixa_frame.rowconfigure(2, weight=1)
    self.caixa_frame.rowconfigure(3, weight=0)

    hero_frame = tk.Frame(self.caixa_frame, bg=self.white_color, padx=hero_pad_x, pady=hero_pad_y, relief="flat", bd=0,)
    hero_frame.grid(row=0, column=0, columnspan=2, padx=outer_pad, pady=(outer_pad, section_gap), sticky="ew",)
    hero_frame.columnconfigure(0, weight=1)
    hero_frame.columnconfigure(1, weight=0)
    hero_frame.columnconfigure(2, weight=0)

    title_block = tk.Frame(hero_frame, bg=self.white_color)
    title_block.grid(row=0, column=0, sticky="w")
    title_brand = tk.Frame(title_block, bg=self.white_color)
    title_brand.pack(anchor="w")
    try:
        logo_size = 58 if compact_mode else 68
        logo_image = Image.open(get_app_logo_path()).resize(
            (logo_size, logo_size), Image.LANCZOS
        )
        self.caixa_logo_tk = ImageTk.PhotoImage(logo_image)
        tk.Label(title_brand, image=self.caixa_logo_tk, bg=self.white_color).pack(
            side="left", padx=(0, 14)
        )
    except Exception:
        self.caixa_logo_tk = None

    title_text_block = tk.Frame(title_brand, bg=self.white_color)
    title_text_block.pack(side="left", anchor="w")
    tk.Label(
        title_text_block,
        text="Frente de Caixa",
        font=title_font,
        bg=self.white_color,
        fg=self.text_color,
    ).pack(anchor="w")
    tk.Label(
        title_text_block,
        text=APP_NAME,
        font=("Segoe UI Semibold", 9 if compact_mode else 10),
        bg=self.white_color,
        fg=self.bg_color1,
    ).pack(anchor="w", pady=(2, 0))
    tk.Label(
        title_block,
        textvariable=self.status_banner_var,
        font=text_font,
        bg=self.white_color,
        fg="#6A756A",
        wraplength=480 if compact_mode else 560,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    info_block = tk.Frame(hero_frame, bg=self.white_color)
    info_block.grid(row=0, column=2, sticky="e")
    self.caixa_operador_label = tk.Label(
        info_block,
        textvariable=self.user_summary_var,
        font=("Segoe UI Semibold", 11 if compact_mode else 12),
        bg=self.white_color,
        fg=self.text_color,
    )
    self.caixa_operador_label.pack(anchor="e", pady=(2, 6))

    status_action_row = tk.Frame(info_block, bg=self.white_color)
    status_action_row.pack(anchor="e")
    chip_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    chip_width = 14 if compact_mode else 16

    self.caixa_status_chip = tk.Label(
        status_action_row,
        textvariable=self.cash_status_var,
        font=chip_font,
        bg="#E6F4EA",
        fg=self.bg_color1,
        width=chip_width,
        anchor="center",
        padx=8,
        pady=6,
    )
    self.caixa_status_chip.pack(side="left")

    tk.Label(
        info_block,
        text=POWERED_BY_LABEL,
        font=("Segoe UI", 8 if compact_mode else 9),
        bg=self.white_color,
        fg=self.theme["text_muted"],
    ).pack(anchor="e", pady=(10, 0))

    if self.logged_user and self.logged_user.get("cargo") == "Gerente":
        self.btn_voltar_gerencia = tk.Button(
            status_action_row,
            text="Voltar para Gestão",
            command=lambda: self.show_frame("gerencia"),
            font=chip_font,
            bg="#E8F1EA",
            fg=self.text_color,
            relief="flat",
            cursor="hand2",
            width=chip_width,
            anchor="center",
            padx=8,
            pady=6,
        )
        self.btn_voltar_gerencia.pack(side="left", padx=(8, 0))

    summary_frame = tk.Frame(self.caixa_frame, bg=self.bg_color)
    summary_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(0, section_gap),
        sticky="ew",
    )
    for idx in range(4):
        summary_frame.columnconfigure(idx, weight=1)

    def make_metric(parent, column, title, variable, bg, fg):
        card = tk.Frame(parent, bg=bg, padx=card_pad_x, pady=card_pad_y)
        card.grid(row=0, column=column, padx=4, sticky="ew")
        tk.Label(card, text=title.upper(), font=metric_title_fontBold, bg=bg, fg=fg).pack(
            anchor="w"
        )
        tk.Label(
            card, textvariable=variable, font=metric_value_font, bg=bg, fg=fg
        ).pack(anchor="w", pady=(8 if compact_mode else 10, 0))

    def make_shortcuts_metric(parent, column, bg, fg):
        card = tk.Frame(parent, bg=bg, padx=card_pad_x, pady=card_pad_y)
        card.grid(row=0, column=column, padx=4, sticky="ew")
        tk.Label(card, text="ATALHOS", font=metric_title_fontBold, bg=bg, fg=fg).pack(
            anchor="w"
        )
        tk.Label(
            card,
            text="[F2] - Pesar Itens | [F3] - Limpar Venda",
            font=("Segoe UI", 8 if compact_mode else 9),
            bg=bg,
            fg=fg,
            anchor="w",
            justify="left",
        ).pack(fill="x", anchor="w", pady=(8 if compact_mode else 10, 2))
        tk.Label(
            card,
            text="[F4] - Emitir Nota | [F5] - Finalizar Venda",
            font=("Segoe UI", 8 if compact_mode else 9),
            bg=bg,
            fg=fg,
            anchor="w",
            justify="left",
        ).pack(fill="x", anchor="w")

    make_metric(summary_frame, 0, "Status do caixa", self.cash_status_var, "#E6F4EA", self.bg_color1,)
    make_shortcuts_metric(summary_frame, 1, "#EDF4FF", "#1E5AA7")
    make_metric(summary_frame, 2, "Itens no carrinho", self.cart_count_var, "#FFF1E3", "#B85C00")
    make_metric(summary_frame, 3, "Total da venda", self.total_var, "#F3ECFF", "#5E35B1")

    workspace_frame = tk.Frame(self.caixa_frame, bg=self.bg_color)
    workspace_frame.grid(
        row=2,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(0, section_gap),
        sticky="nsew",
    )
    workspace_frame.columnconfigure(0, weight=9)
    workspace_frame.columnconfigure(1, weight=16)
    workspace_frame.rowconfigure(0, weight=1)

    left_panel = tk.Frame(
        workspace_frame, bg=self.white_color, padx=panel_pad, pady=panel_pad
    )
    left_panel.grid(row=0, column=0, padx=(0, section_gap), sticky="nsew")
    left_panel.columnconfigure(0, weight=1)
    tk.Label(
        left_panel,
        text="Busque por Nome, SKU ou Código",
        font=text_font,
        bg=self.white_color,
        fg="#6A756A",
    ).grid(row=1, column=0, sticky="w", pady=(3, 14))

    tk.Label(
        left_panel,
        text="Produto",
        font=label_font,
        bg=self.white_color,
        fg=self.text_color,
    ).grid(row=2, column=0, sticky="w")
    self.produto_entry = ttk.Combobox(
        left_panel, font=("Segoe UI", 12 if compact_mode else 14)
    )
    self.produto_entry.grid(
        row=3, column=0, sticky="ew", pady=(4, 12), ipady=entry_ipady
    )

    tk.Label(
        left_panel,
        text="Quantidade",
        font=label_font,
        bg=self.white_color,
        fg=self.text_color,
    ).grid(row=4, column=0, sticky="w")
    self.quantidade_entry = tk.Entry(
        left_panel, font=quantity_font, justify="center", relief="solid", bd=1
    )
    self.quantidade_entry.grid(
        row=5, column=0, sticky="ew", pady=(4, 12), ipady=quantity_ipady
    )
    self.quantidade_entry.insert(0, "1")

    self.btn_adicionar_item = tk.Button(
        left_panel,
        text="Adicionar item  Enter",
        font=("Segoe UI Semibold", 11 if compact_mode else 12),
        bg=self.bg_color1,
        fg=self.white_color,
        command=self.adicionar_item_carrinho,
        relief="flat",
        cursor="hand2",
        pady=button_pad_y,
    )
    self.btn_adicionar_item.grid(row=6, column=0, sticky="ew")

    stack_action_cards = (
        self.winfo_screenwidth() <= 1180 or self.winfo_screenheight() <= 720
    )

    action_cards = tk.Frame(left_panel, bg=self.white_color)
    action_cards.grid(row=7, column=0, sticky="ew", pady=(12, 0))
    action_cards.columnconfigure(0, weight=1)
    action_cards.columnconfigure(1, weight=1)
    action_cards.rowconfigure(0, weight=1)
    action_cards.rowconfigure(1, weight=1)

    card_pad = 8 if compact_mode else 12
    card_gap = 8 if compact_mode else 10
    row_gap = 8 if compact_mode else 10
    hint_wrap = 180 if compact_mode else 220

    label_font = ("Segoe UI", 7 if compact_mode else 8)
    wrap = 180 if compact_mode else 220

    venda_card = tk.Frame(action_cards, bg="#EEF3FF", padx=card_pad, pady=card_pad)
    venda_card.grid(
        row=0, column=0, padx=(0, card_gap), pady=(0, row_gap), sticky="nsew"
    )

    venda_buttons = tk.Frame(venda_card, bg="#EEF3FF")
    venda_buttons.pack(fill="x")
    self.btn_add_f2 = tk.Button(
        venda_buttons,
        text="Pesar (F2)",
        font=action_font,
        bg=self.bg_color2,
        fg=self.white_color,
        command=self.open_adicionar_item_dialog,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_add_f2.pack(fill="x", pady=(0, 5))
    self.btn_limpar_venda = tk.Button(
        venda_buttons,
        text="Limpar (F3)",
        font=action_font,
        bg=self.bg_color2,
        fg=self.white_color,
        command=self.limpar_venda,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_limpar_venda.pack(fill="x", pady=(0, 5))
    self.btn_emitir_nota = tk.Button(
        venda_buttons,
        text="Emitir Nota (F4)",
        font=action_font,
        bg=self.bg_color2,
        fg=self.white_color,
        command=self.show_note_dialog,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_emitir_nota.pack(fill="x", pady=(0, 5))
    self.btn_finalizar_venda = tk.Button(
        venda_buttons,
        text="Finalizar (F5)",
        font=action_font,
        bg=self.bg_color1,
        fg=self.white_color,
        command=self.iniciar_finalizacao_venda,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_finalizar_venda.pack(fill="x")

    #atalhos = [
    #    "[F2] Pesar itens",
    #    "[F3] Limpar carrinho",
    #    "[F4] Emitir notas",
    #    "[F5] Finalizar venda",
    #]

    caixa_card = tk.Frame(action_cards, bg="#FFF8EE", padx=card_pad, pady=card_pad)
    caixa_card.grid(
        row=0, column=1, padx=(card_gap, 0), pady=(0, row_gap), sticky="nsew"
    )

    control_buttons = tk.Frame(caixa_card, bg="#FFF8EE")
    control_buttons.pack(fill="x")
    self.btn_abrir_caixa = tk.Button(
        control_buttons,
        text="Abrir Caixa",
        font=action_font,
        bg="#1D4ED8",
        fg=self.white_color,
        command=self.abrir_caixa,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_abrir_caixa.pack(fill="x", pady=(0, 5))
    self.btn_fechar_caixa = tk.Button(
        control_buttons,
        text="Fechar Caixa",
        font=action_font,
        bg="#009172",
        fg=self.white_color,
        command=self.fechar_caixa,
        relief="flat",
        cursor="hand2",
        pady=7,
    )
    self.btn_fechar_caixa.pack(fill="x", pady=(0, 5))
    label_box = tk.Frame(control_buttons, bg="#FFF8EE")
    label_box.pack(fill="x", pady=(0, 6))

    tk.Label(
        label_box,
        text=None,
        font=action_font,
        bg="#FFF8EE",
        fg="#6A756A",
        anchor="center",
        justify="center",
        padx=8,
        pady=8,
    ).pack(fill="x")

    self.btn_fechar_sistema = tk.Button(control_buttons, text="Fechar Sistema", font=action_font, bg="#C2410C", fg=self.white_color, command=self.on_closing, relief="flat", cursor="hand2", pady=7,)
    self.btn_fechar_sistema.pack(fill="x", pady=(5, 0))

    info_cards = tk.Frame(left_panel, bg=self.white_color)
    info_cards.grid(row=8, column=0, sticky="ew", pady=(12, 0))
    info_cards.columnconfigure(0, weight=1)
    info_cards.rowconfigure(0, weight=1)

    #atalhos_card = tk.Frame(info_cards, bg="#EEF3FF", padx=card_pad, pady=card_pad)
    #atalhos_card.grid(row=0, column=0, sticky="nsew")
    #tk.Label(atalhos_card, text="Atalhos do teclado.", font=("Segoe UI", 8 if compact_mode else 9), bg="#EEF3FF", fg="#6A756A", wraplength=hint_wrap, justify="left",).pack(anchor="w", pady=(0, 8))
    #for texto in atalhos:tk.Label(atalhos_card, text=texto, font=label_font, bg="#EEF3FF", fg="#6A756A", wraplength=wrap, justify="left",).pack(anchor="w", pady=0)

    right_panel = tk.Frame(workspace_frame, bg=self.white_color, padx=14 if compact_mode else 18, pady=14 if compact_mode else 18,)
    right_panel.grid(row=0, column=1, padx=(section_gap, 0), sticky="nsew")
    right_panel.columnconfigure(0, weight=1)
    right_panel.rowconfigure(1, weight=1)

    right_header = tk.Frame(right_panel, bg=self.white_color)
    right_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    right_header.columnconfigure(0, weight=1)
    tk.Label(right_header, text="Itens adicionados aparecem aqui em tempo real.", font=text_font, bg=self.white_color, fg="#6A756A",).grid(row=1, column=0, sticky="w", pady=(3, 0))

    cart_table_frame = tk.Frame(right_panel, bg=self.white_color)
    cart_table_frame.grid(row=1, column=0, sticky="nsew")
    cart_table_frame.columnconfigure(0, weight=1)
    cart_table_frame.rowconfigure(0, weight=1)

    self.carrinho_tree = ttk.Treeview(cart_table_frame, columns=("Produto", "Quantidade", "Preco Unit.", "Subtotal"), show="headings", selectmode="browse",)
    self.carrinho_tree.heading("Produto", text="Produto")
    self.carrinho_tree.heading("Quantidade", text="Quantidade")
    self.carrinho_tree.heading("Preco Unit.", text="Preco Unit.")
    self.carrinho_tree.heading("Subtotal", text="Subtotal")

    self.carrinho_tree.column("Produto", width=260 if compact_mode else 320, anchor="w")
    self.carrinho_tree.column("Quantidade", width=110 if compact_mode else 130, anchor="center")
    self.carrinho_tree.column("Preco Unit.", width=100 if compact_mode else 120, anchor="e")
    self.carrinho_tree.column("Subtotal", width=110 if compact_mode else 130, anchor="e")
    self.carrinho_tree.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(cart_table_frame, orient="vertical", command=self.carrinho_tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.carrinho_tree.configure(yscrollcommand=scrollbar.set)

    botoes_edit_frame = tk.Frame(right_panel, bg=self.white_color)
    botoes_edit_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    botoes_edit_frame.columnconfigure(0, weight=1)
    botoes_edit_frame.columnconfigure(1, weight=1)

    tk.Button(botoes_edit_frame, text="Excluir Item", bg="#C2410C", fg="white", command=self.delete_item_from_cart, relief="flat", cursor="hand2", font=action_font, pady=button_pad_y,).grid(row=0, column=0, sticky="ew", padx=(0, 5))
    tk.Button(botoes_edit_frame, text="Editar Quantidade", bg="#D97706", fg="white", command=self.edit_item_in_cart, relief="flat", cursor="hand2", font=action_font, pady=button_pad_y,).grid(row=0, column=1, sticky="ew", padx=(5, 0))
    utility_frame = tk.Frame(self.caixa_frame, bg=self.bg_color)

    self.total_label = tk.Label(utility_frame, textvariable=self.total_var, font=total_font, bg=self.bg_color, fg=self.text_color,)

    self.produto_entry.bind("<KeyRelease>", self.update_produto_list)
    self.produto_entry.bind("<Return>", self.adicionar_item_carrinho_event)

    self.bind_all("<F2>", lambda e: self.open_adicionar_item_dialog())
    self.bind_all("<F3>", lambda e: self.limpar_venda())
    self.bind_all("<F4>", lambda e: self.show_note_dialog())
    self.bind_all("<F5>", lambda e: self.iniciar_finalizacao_venda())

    self.produto_entry.focus_set()


def _mgmt_theme(self):
    return getattr(
        self,
        "theme",
        {
            "bg": getattr(self, "bg_color", "#F4F1E8"),
            "surface": getattr(self, "white_color", "#FFFDF8"),
            "surface_alt": "#F6F8F1",
            "primary": getattr(self, "bg_color1", "#0F8F47"),
            "accent": getattr(self, "bg_color2", "#FF8A1E"),
            "text": getattr(self, "text_color", "#17301F"),
            "text_muted": "#6A756A",
            "border": getattr(self, "grid_color", "#D8E0D1"),
            "danger": getattr(self, "error_color", "#C2410C"),
            "success": getattr(self, "success_color", "#1F9D55"),
            "text_on_dark": "#F8FFF9",
        },
    )


def _clear_children(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def _tiny_screen(self):
    return self.winfo_screenwidth() <= 900 or self.winfo_screenheight() <= 780


def _section_shell(parent, theme, title, subtitle=None, back_command=None):
    tiny = _tiny_screen(parent.winfo_toplevel())
    wrapper = tk.Frame(parent, bg=theme["bg"])
    wrapper.pack(
        fill="both",
        expand=True,
        padx=8 if tiny else 20,
        pady=8 if tiny else 20,
    )

    header = tk.Frame(wrapper, bg=theme["bg"])
    header.pack(fill="x", pady=(0, 16))
    if back_command is not None:
        tk.Button(
            header,
            text="Voltar",
            command=back_command,
            bg=theme["surface_alt"],
            fg=theme["text"],
            relief="flat",
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            activebackground=theme.get("primary_soft", theme["surface_alt"]),
            activeforeground=theme["text"],
            highlightthickness=1,
            highlightbackground=theme["border"],
            bd=0,
            padx=10 if tiny else 14,
            pady=6 if tiny else 8,
        ).pack(side="left")

    title_box = tk.Frame(header, bg=theme["bg"])
    title_box.pack(
        side="left",
        padx=(
            10 if tiny and back_command is not None else (16 if back_command is not None else 0),
            0,
        ),
    )
    tk.Label(
        title_box,
        text=title,
        font=("Segoe UI Black", 16 if tiny else 22),
        bg=theme["bg"],
        fg=theme["text"],
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            title_box,
            text=subtitle,
            font=("Segoe UI", 8 if tiny else 10),
            bg=theme["bg"],
            fg=theme["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

    tk.Label(
        header,
        text=APP_NAME,
        font=("Segoe UI Semibold", 8 if tiny else 9),
        bg=theme["bg"],
        fg=theme["text_muted"],
        padx=10 if tiny else 12,
        pady=6 if tiny else 7,
        relief="flat",
        highlightthickness=1,
        highlightbackground=theme["border"],
    ).pack(side="right")

    card_shell = tk.Frame(
        wrapper,
        bg=theme.get("surface_elevated", theme["surface"]),
        highlightthickness=1,
        highlightbackground=theme.get("card_edge", theme["border"]),
        relief="flat",
    )
    card_shell.pack(fill="both", expand=True)

    tk.Frame(card_shell, bg=theme["accent"], height=4).pack(fill="x")
    card = tk.Frame(
        card_shell,
        bg=theme["surface"],
        padx=10 if tiny else 22,
        pady=10 if tiny else 22,
        relief="flat",
    )
    card.pack(fill="both", expand=True)
    return wrapper, card


def _action_button(
    parent,
    text,
    command,
    bg,
    fg="white",
    side=None,
    fill=None,
    width=None,
    active_bg=None,
):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        relief="flat",
        activebackground=active_bg or bg,
        activeforeground=fg,
        cursor="hand2",
        font=("Segoe UI Semibold", 10),
        padx=14,
        pady=11,
        bd=0,
        highlightthickness=0,
        width=width,
    )
    if side:
        btn.pack(side=side, padx=4, fill=fill)
    return btn


def _dashboard_stat(parent, theme, label, value, tone_bg, tone_fg):
    tile = tk.Frame(
        parent,
        bg=theme["surface"],
        padx=14,
        pady=14,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    tk.Label(
        tile,
        text=label.upper(),
        font=("Segoe UI Semibold", 8),
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).pack(anchor="w")
    tk.Label(
        tile,
        text=value,
        font=("Segoe UI Semibold", 11),
        bg=tone_bg,
        fg=tone_fg,
        padx=10,
        pady=6,
    ).pack(anchor="w", pady=(10, 0))
    return tile


def _dashboard_tile(parent, theme, eyebrow, title, description, accent, cta, command):
    shell = tk.Frame(
        parent,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["border"],
        cursor="hand2",
    )
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(1, weight=1)

    top_line = tk.Frame(shell, bg=accent, height=4)
    top_line.grid(row=0, column=0, sticky="ew")

    body = tk.Frame(shell, bg=theme["surface"], padx=18, pady=16, cursor="hand2")
    body.grid(row=1, column=0, sticky="nsew")
    body.columnconfigure(0, weight=1)

    eyebrow_label = tk.Label(
        body,
        text=eyebrow.upper(),
        font=("Segoe UI Semibold", 8),
        bg=theme["surface"],
        fg=accent,
    )
    eyebrow_label.grid(row=0, column=0, sticky="w")

    title_label = tk.Label(
        body,
        text=title,
        font=("Segoe UI Semibold", 15),
        bg=theme["surface"],
        fg=theme["text"],
    )
    title_label.grid(row=1, column=0, sticky="w", pady=(10, 4))

    description_label = tk.Label(
        body,
        text=description,
        font=("Segoe UI", 9),
        bg=theme["surface"],
        fg=theme["text_muted"],
        wraplength=240,
        justify="left",
    )
    description_label.grid(row=2, column=0, sticky="w")

    footer = tk.Frame(body, bg=theme["surface"])
    footer.grid(row=3, column=0, sticky="ew", pady=(18, 0))
    footer.columnconfigure(0, weight=1)

    cta_label = tk.Label(
        footer,
        text=cta,
        font=("Segoe UI Semibold", 9),
        bg=theme["surface_alt"],
        fg=theme["text"],
        padx=10,
        pady=6,
    )
    cta_label.grid(row=0, column=0, sticky="w")

    action_label = tk.Label(
        footer,
        text="Acessar",
        font=("Segoe UI Semibold", 9),
        bg=theme["surface"],
        fg=accent,
    )
    action_label.grid(row=0, column=1, sticky="e")

    flat_widgets = (
        body,
        eyebrow_label,
        title_label,
        description_label,
        footer,
        action_label,
    )

    def _set_hover_state(is_hovered):
        card_bg = (
            theme.get("surface_elevated", theme["surface"])
            if is_hovered
            else theme["surface"]
        )
        border = accent if is_hovered else theme["border"]
        chip_bg = (
            theme.get("primary_soft", theme["surface_alt"])
            if is_hovered
            else theme["surface_alt"]
        )
        shell.configure(bg=card_bg, highlightbackground=border)
        for widget in flat_widgets:
            widget.configure(bg=card_bg)
        cta_label.configure(bg=chip_bg)

    def _bind_tile(widget):
        widget.bind("<Button-1>", lambda _event: command())
        widget.bind("<Enter>", lambda _event: _set_hover_state(True))
        widget.bind("<Leave>", lambda _event: _set_hover_state(False))

    for widget in (shell, top_line, cta_label, *flat_widgets):
        _bind_tile(widget)

    return shell


def create_produtos_view(self):
    theme = _mgmt_theme(self)
    tiny = _tiny_screen(self)
    _clear_children(self.produtos_view_frame)
    self.produtos_alpha_filter = getattr(self, "produtos_alpha_filter", None)
    previous_search = (
        self.produtos_search_var.get()
        if hasattr(self, "produtos_search_var") and self.produtos_search_var is not None
        else ""
    )
    self.produtos_search_var = tk.StringVar(value=previous_search)
    self.produtos_resultado_var = tk.StringVar(value="0 produto(s)")
    self.produtos_alpha_buttons = {}

    _, card = _section_shell(
        self.produtos_view_frame,
        theme,
        "Produtos Cadastrados",
        "Base completa de itens, estoque e identificadores de venda.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    search_frame = tk.Frame(card, bg=theme["surface"])
    search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8 if tiny else 14))
    search_frame.columnconfigure(0, weight=1)

    search_input_frame = tk.Frame(
        search_frame,
        bg=theme["surface_alt"],
        padx=8 if tiny else 12,
        pady=8 if tiny else 12,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    search_input_frame.grid(row=0, column=0, sticky="ew")
    search_input_frame.columnconfigure(0, weight=1)

    tk.Label(
        search_input_frame,
        text="Pesquisar produto",
        font=("Segoe UI Semibold", 9 if tiny else 10),
        bg=theme["surface_alt"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        search_input_frame,
        textvariable=self.produtos_resultado_var,
        font=("Segoe UI", 8 if tiny else 9),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=0, column=1, sticky="e", padx=(8, 0))

    search_controls = tk.Frame(search_input_frame, bg=theme["surface_alt"])
    search_controls.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(6 if tiny else 10, 0),
    )
    search_controls.columnconfigure(0, weight=1)

    search_entry = tk.Entry(
        search_controls,
        textvariable=self.produtos_search_var,
        font=("Segoe UI", 9 if tiny else 11),
        bg="#FFFFFF",
        fg=theme["text"],
        insertbackground=theme["text"],
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=theme["border"],
        highlightcolor=theme["primary"],
    )
    search_entry.grid(row=0, column=0, sticky="ew")
    search_entry.bind("<Return>", lambda _e: _run_produtos_refresh_now(self))
    self.produtos_search_var.trace_add(
        "write", lambda *_args: _refresh_produtos_with_debounce(self)
    )

    tk.Button(
        search_controls,
        text="🔎",
        command=lambda: _run_produtos_refresh_now(self),
        bg=theme["primary"],
        fg="white",
        relief="flat",
        cursor="hand2",
        font=("Segoe UI Semibold", 10),
        padx=10 if tiny else 14,
        pady=5 if tiny else 8,
    ).grid(row=0, column=1, padx=(8, 0))

    def _set_alpha_filter(letter):
        self.produtos_alpha_filter = letter
        _run_produtos_refresh_now(self)

    alpha_controls = tk.Frame(search_input_frame, bg=theme["surface_alt"])
    alpha_controls.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(6 if tiny else 10, 0),
    )
    alpha_controls.columnconfigure(0, weight=1)
    alpha_controls.columnconfigure(1, weight=0)

    self._produtos_alpha_active_bg = theme["primary"]
    self._produtos_alpha_active_fg = "#FFFFFF"
    self._produtos_alpha_idle_bg = theme["surface"]
    self._produtos_alpha_idle_fg = theme["text"]

    alpha_left = tk.Frame(alpha_controls, bg=theme["surface_alt"])
    alpha_left.grid(row=0, column=0, sticky="w")

    self.produtos_all_button = tk.Button(
        alpha_left,
        text="Todos",
        command=lambda: _set_alpha_filter(None),
        bg=theme["surface"],
        fg=theme["text"],
        relief="flat",
        cursor="hand2",
        font=("Segoe UI Semibold", 9),
        padx=8 if tiny else 10,
        pady=4 if tiny else 6,
    )
    self.produtos_all_button.pack(side="left", padx=(0, 8))

    tk.Label(
        alpha_left,
        text="De A-Z:",
        font=("Segoe UI", 9),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).pack(side="left", padx=(0, 8))

    if tiny:
        letters_frame = tk.Frame(search_input_frame, bg=theme["surface_alt"])
        letters_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            button = tk.Button(
                letters_frame,
                text=letter,
                width=2,
                command=lambda value=letter: _set_alpha_filter(value),
                bg=theme["surface"],
                fg=theme["text"],
                relief="flat",
                cursor="hand2",
                font=("Segoe UI Semibold", 7),
                padx=1,
                pady=1,
            )
            button.grid(
                row=index // 13,
                column=index % 13,
                sticky="ew",
                padx=1,
                pady=1,
            )
            letters_frame.columnconfigure(index % 13, weight=1)
            self.produtos_alpha_buttons[letter] = button

    alpha_actions = tk.Frame(alpha_controls, bg=theme["surface_alt"])
    alpha_actions.grid(
        row=1 if tiny else 0,
        column=0 if tiny else 1,
        columnspan=2 if tiny else 1,
        sticky="ew" if tiny else "e",
        pady=(6 if tiny else 0, 0),
    )
    if tiny:
        for idx in range(6):
            alpha_actions.columnconfigure(idx, weight=1)

    buttons = [
        ("Atualizar", self.refresh_produtos_view, theme["primary"]),
        ("Novo", self.open_cadastro_produto_dialog, theme["accent"]),
        ("Etiquetas", self.gerar_catalogo_etiquetas_codigos_barras, "#B45309"),
        ("Relatório", self.exportar_relatorio_estoque_csv, "#475569"),
        ("Importar", self.importar_produtos_em_massa, "#7C3AED"),
        ("CSV", self.baixar_template_importacao_produtos, "#0F766E"),
    ]
    for idx, (text, command, bg) in enumerate(buttons):
        btn = tk.Button(
            alpha_actions,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI Semibold", 8 if tiny else 9),
            padx=6 if tiny else 12,
            pady=5 if tiny else 7,
        )
        if tiny:
            btn.grid(row=0, column=idx, sticky="ew", padx=2)
        else:
            btn.pack(side="left", padx=4)

    table_wrap = tk.Frame(card, bg=theme["surface"])
    table_wrap.grid(row=1, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.columnconfigure(1, weight=0)
    table_wrap.rowconfigure(0, weight=1)

    columns = (
        "ID",
        "Nome do Produto",
        "Preço (R$)",
        "Estoque",
        "Unidade",
        "SKU",
        "Cod. Barras",
    )
    self.produtos_tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
    for col in columns:
        self.produtos_tree.heading(col, text=col)
        if col == "ID":
            self.produtos_tree.column(col, width=60, anchor=tk.CENTER)
        elif col == "Nome do Produto":
            self.produtos_tree.column(col, width=280, anchor=tk.W)
        else:
            self.produtos_tree.column(col, width=130, anchor=tk.CENTER)
    self.produtos_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.produtos_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.produtos_tree.configure(yscrollcommand=scrollbar.set)
    self.produtos_tree.bind("<Double-1>", self.on_double_click_produto)

    if not tiny:
        alpha_panel = tk.Frame(table_wrap, bg=theme["surface"], padx=6)
        alpha_panel.grid(row=0, column=2, sticky="ns", padx=(10, 0))

        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            button = tk.Button(
                alpha_panel,
                text=letter,
                width=3,
                command=lambda value=letter: _set_alpha_filter(value),
                bg=theme["surface_alt"],
                fg=theme["text"],
                relief="flat",
                cursor="hand2",
                font=("Segoe UI Semibold", 8),
                pady=1,
            )
            button.pack(fill="x", pady=1)
            self.produtos_alpha_buttons[letter] = button

    load_produtos_to_treeview(self)
    search_entry.focus_set()


def create_funcionarios_view(self):
    theme = _mgmt_theme(self)
    _clear_children(self.funcionarios_view_frame)
    _, card = _section_shell(
        self.funcionarios_view_frame,
        theme,
        "Funcionários Cadastrados",
        "Controle de usuários, cargos e permissões de operação.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    actions = tk.Frame(card, bg=theme["surface"])
    actions.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    _action_button(
        actions,
        "Atualizar Lista",
        self.refresh_funcionarios_view,
        theme["primary"],
        side="left",
    )
    _action_button(
        actions,
        "Novo Funcionário",
        self.open_cadastro_funcionario_dialog,
        theme["accent"],
        side="left",
    )

    table_wrap = tk.Frame(card, bg=theme["surface"])
    table_wrap.grid(row=1, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)

    columns = ("ID", "Nome Completo", "Username", "Cargo")
    self.funcionarios_tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
    for col in columns:
        self.funcionarios_tree.heading(col, text=col)
    self.funcionarios_tree.column("ID", width=60, anchor=tk.CENTER, stretch=tk.NO)
    self.funcionarios_tree.column("Nome Completo", width=320, anchor=tk.W)
    self.funcionarios_tree.column("Username", width=180, anchor=tk.W)
    self.funcionarios_tree.column("Cargo", width=120, anchor=tk.CENTER)
    self.funcionarios_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.funcionarios_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.funcionarios_tree.configure(yscrollcommand=scrollbar.set)
    self.funcionarios_tree.bind("<Double-1>", self.on_double_click_employee)
    load_funcionarios_to_treeview(self)


def create_empresa_view(self):
    theme = _mgmt_theme(self)
    _clear_children(self.empresa_view_frame)
    compact_mode = self.winfo_screenwidth() <= 1280 or self.winfo_screenheight() <= 800
    label_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    entry_font = ("Segoe UI", 10 if compact_mode else 11)
    title_font = ("Segoe UI Semibold", 12 if compact_mode else 14)
    body_font = ("Segoe UI", 9 if compact_mode else 10)
    preview_height = 180 if compact_mode else 220
    wrapper, card = _section_shell(
        self.empresa_view_frame,
        theme,
        "Configuração da Empresa",
        "Dados institucionais, contato e identidade visual usados nas impressões do sistema.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    canvas = tk.Canvas(card, bg=theme["surface"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    content = tk.Frame(canvas, bg=theme["surface"])
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def _sync_empresa_scroll(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    content.bind("<Configure>", _sync_empresa_scroll)
    canvas.bind("<Configure>", _sync_empresa_scroll)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=2)
    if compact_mode:
        content.columnconfigure(1, weight=0)

    form = tk.Frame(content, bg=theme["surface"])
    form.grid(row=0, column=0, sticky="nsew", padx=(0, 14 if not compact_mode else 0))
    form.columnconfigure(0, weight=1)

    def field(label, row):
        tk.Label(
            form,
            text=label,
            font=label_font,
            fg=theme["text"],
            bg=theme["surface"],
        ).grid(row=row, column=0, sticky="w", pady=(0, 4 if compact_mode else 6))
        entry = tk.Entry(
            form,
            font=entry_font,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=theme["primary"],
        )
        entry.grid(
            row=row + 1,
            column=0,
            sticky="ew",
            ipady=5 if compact_mode else 7,
            pady=(0, 10 if compact_mode else 12),
        )
        return entry

    self.empresa_nome_entry = field("Nome Fantasia", 0)
    self.empresa_razao_entry = field("Razão Social", 2)
    self.empresa_cnpj_entry = field("CNPJ", 4)
    if hasattr(self, "aplicar_mascara_cnpj"):
        self.empresa_cnpj_entry.bind("<KeyRelease>", self.aplicar_mascara_cnpj)
    self.empresa_endereco_entry = field("Endereço (Rua e Número)", 6)

    city_row = tk.Frame(form, bg=theme["surface"])
    city_row.grid(row=8, column=0, sticky="ew", pady=(0, 10 if compact_mode else 12))
    city_row.columnconfigure(0, weight=1)
    city_row.columnconfigure(1, weight=0)
    city_row.columnconfigure(2, weight=2)
    city_row.columnconfigure(3, weight=0)

    for idx, (label, attr, width) in enumerate(
        (
            ("Bairro", "empresa_bairro_entry", None),
            ("CEP", "empresa_cep_entry", 14),
            ("Cidade", "empresa_cidade_entry", None),
            ("UF", "empresa_estado_entry", 6),
        )
    ):
        box = tk.Frame(city_row, bg=theme["surface"])
        box.grid(row=0, column=idx, sticky="ew", padx=(0, 8 if idx < 3 else 0))
        tk.Label(
            box,
            text=label,
            font=label_font,
            fg=theme["text"],
            bg=theme["surface"],
        ).pack(anchor="w", pady=(0, 4 if compact_mode else 6))
        entry = tk.Entry(
            box,
            font=entry_font,
            width=width,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=theme["primary"],
        )
        entry.pack(fill="x", ipady=5 if compact_mode else 7)
        setattr(self, attr, entry)
    if hasattr(self, "aplicar_mascara_cep"):
        self.empresa_cep_entry.bind("<KeyRelease>", self.aplicar_mascara_cep)

    self.empresa_email_entry = field("E-mail", 10)
    self.empresa_telefone_entry = field("Telefone / WhatsApp", 12)
    if hasattr(self, "aplicar_mascara_telefone"):
        self.empresa_telefone_entry.bind("<KeyRelease>", self.aplicar_mascara_telefone)

    side = tk.Frame(content, bg=theme["surface_alt"], padx=16 if compact_mode else 18, pady=16 if compact_mode else 18)
    side.grid(row=0, column=1, sticky="nsew", pady=(14 if compact_mode else 0, 0))
    side.columnconfigure(0, weight=1)
    tk.Label(
        side,
        text="Identidade visual",
        font=title_font,
        bg=theme["surface_alt"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        side,
        text="Carregue a logo usada em relatórios e impressos do sistema.",
        font=body_font,
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
        wraplength=220 if compact_mode else 260,
        justify="left",
    ).grid(row=1, column=0, sticky="w", pady=(4, 12))

    preview = tk.Frame(
        side,
        bg="#E8ECE3",
        highlightthickness=1,
        highlightbackground=theme["border"],
        height=preview_height,
    )
    preview.grid(row=2, column=0, sticky="ew")
    preview.grid_propagate(False)
    preview.columnconfigure(0, weight=1)
    preview.rowconfigure(0, weight=1)
    self.logo_preview_label = tk.Label(
        preview,
        text="Sem Logo",
        bg="#E8ECE3",
        fg=theme["text_muted"],
        font=("Segoe UI Semibold", 10 if compact_mode else 12),
    )
    self.logo_preview_label.grid(row=0, column=0, sticky="nsew")

    self.btn_up_logo = tk.Button(
        side, text="Carregar Imagem", command=self.selecionar_logo
    )
    self.btn_up_logo.grid(row=3, column=0, sticky="ew", pady=(12, 0))
    self.btn_up_logo.configure(
        bg=theme["primary"],
        fg=theme["text_on_dark"],
        relief="flat",
        cursor="hand2",
        font=("Segoe UI Semibold", 9 if compact_mode else 10),
        padx=12,
        pady=8 if compact_mode else 10,
    )

    self.empresa_footer_frame = tk.Frame(content, bg=theme["surface"], pady=14)
    self.empresa_footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    self.empresa_footer_frame.columnconfigure(0, weight=1)
    self.empresa_footer_frame.columnconfigure(1, weight=1)


def create_gerencia_layout(self):
    theme = _mgmt_theme(self)
    _clear_children(self.gerencia_frame)
    _, card = _section_shell(
        self.gerencia_frame,
        theme,
        "Painel de Gestão",
        "Acesso rápido aos módulos operacionais, cadastros e conferências do sistema.",
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    user_name = (
        self.logged_user.get("nome", "Operador")
        if getattr(self, "logged_user", None)
        else "Operador"
    )
    user_role = (
        self.logged_user.get("cargo", "Gestão")
        if getattr(self, "logged_user", None)
        else "Gestão"
    )
    today_label = __import__("datetime").datetime.now().strftime("%d/%m/%Y")

    intro = tk.Frame(
        card,
        bg=theme["surface_alt"],
        padx=22,
        pady=20,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    intro.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    intro.columnconfigure(0, weight=3)
    intro.columnconfigure(1, weight=2)

    intro_left = tk.Frame(intro, bg=theme["surface_alt"])
    intro_left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
    intro_left.columnconfigure(0, weight=1)

    tk.Label(
        intro_left,
        text="KODA SYSTEM",
        font=("Segoe UI Semibold", 9),
        bg=theme["surface_alt"],
        fg=theme["accent"],
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        intro_left,
        text="Gestão premium para mercados, mercearias e hortifrutis.",
        font=("Segoe UI Black", 22),
        bg=theme["surface_alt"],
        fg=theme["text"],
        wraplength=560,
        justify="left",
    ).grid(row=1, column=0, sticky="w", pady=(8, 8))
    tk.Label(
        intro_left,
        text=(
            "Um painel mais elegante, seguro e pronto para apresentação comercial, "
            "mantendo a operação rápida no caixa, nos cadastros e nos relatórios."
        ),
        font=("Segoe UI", 10),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
        wraplength=560,
        justify="left",
    ).grid(row=2, column=0, sticky="w")

    intro_right = tk.Frame(intro, bg=theme["surface_alt"])
    intro_right.grid(row=0, column=1, sticky="nsew")
    intro_right.columnconfigure(0, weight=1)
    for idx in range(3):
        intro_right.rowconfigure(idx, weight=1)

    _dashboard_stat(
        intro_right,
        theme,
        "Sessão ativa",
        user_name,
        theme.get("primary_soft", theme["surface"]),
        theme["primary_dark"],
    ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
    _dashboard_stat(
        intro_right,
        theme,
        "Perfil operacional",
        user_role,
        theme.get("accent_soft", theme["surface"]),
        theme.get("accent_dark", theme["text"]),
    ).grid(row=1, column=0, sticky="ew", pady=8)
    _dashboard_stat(
        intro_right,
        theme,
        "Atualizado em",
        today_label,
        theme.get("surface_elevated", theme["surface"]),
        theme["text"],
    ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    grid = tk.Frame(card, bg=theme["surface"])
    grid.grid(row=1, column=0, sticky="nsew")
    for c in range(3):
        grid.columnconfigure(c, weight=1, uniform="mgmt")
    for r in range(3):
        grid.rowconfigure(r, weight=1, uniform="mgmt")

    tiles = [
        (
            "Operação",
            "Caixa",
            "Abertura, vendas assistidas, balança e fechamento em uma experiência rápida para o balcão.",
            theme["primary"],
            "Abrir operação",
            lambda: self.show_frame("caixa"),
        ),
        (
            "Catálogo",
            "Produtos",
            "Consulte estoque, preços, códigos e mantenha o mix de produtos organizado para venda.",
            theme["accent"],
            "Ver cadastro",
            lambda: self.show_frame("produtos_view"),
        ),
        (
            "Equipe",
            "Funcionários",
            "Gerencie acessos, operadores e permissões com uma visão mais profissional da equipe.",
            "#6E865D",
            "Abrir equipe",
            lambda: self.show_frame("funcionarios_view"),
        ),
        (
            "Conferência",
            "Relatório do Dia",
            "Acompanhe o desempenho do turno, revise lançamentos e mantenha o caixa sob controle.",
            "#62719A",
            "Analisar turno",
            lambda: self.show_frame("relatorios_view"),
        ),
        (
            "Histórico",
            "Relatório Geral",
            "Tenha acesso ao histórico operacional para decisões mais seguras e apresentações comerciais.",
            "#796483",
            "Ver histórico",
            lambda: self.show_frame("relatorios_gerais_view"),
        ),
        (
            "Marca",
            "Empresa",
            "Atualize dados institucionais, identidade visual e informações que fortalecem a apresentação do negócio.",
            "#3F7B73",
            "Editar empresa",
            lambda: self.show_frame("empresa_view"),
        ),
        (
            "Expansão",
            "Novo Produto",
            "Cadastre novos itens com rapidez para ampliar o catálogo sem travar a operação do caixa.",
            "#5F8A73",
            "Cadastrar item",
            self.open_cadastro_produto_dialog,
        ),
        (
            "Expansão",
            "Novo Funcionário",
            "Adicione colaboradores e prepare a equipe para novos turnos, lojas ou unidades.",
            "#876A54",
            "Cadastrar colaborador",
            self.open_cadastro_funcionario_dialog,
        ),
        (
            "Sessão",
            "Sair",
            "Encerre a sessão atual com segurança ao finalizar o atendimento ou a gestão do turno.",
            theme["danger"],
            "Encerrar acesso",
            self.on_closing,
        ),
    ]

    for idx, (eyebrow, title, desc, color, cta, action) in enumerate(tiles):
        row, col = divmod(idx, 3)
        tile = _dashboard_tile(grid, theme, eyebrow, title, desc, color, cta, action)
        tile.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")


def create_relatorios_view(self):
    theme = _mgmt_theme(self)
    _clear_children(self.relatorios_view_frame)
    _, card = _section_shell(
        self.relatorios_view_frame,
        theme,
        "Relatório do Dia",
        "Consulta diária de vendas, emissão operacional e manutenção dos lançamentos do turno.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(1, weight=1)

    actions = tk.Frame(card, bg=theme["surface"])
    actions.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    _action_button(
        actions,
        "Atualizar",
        self.update_daily_sales_report,
        theme["primary"],
        side="left",
    )
    _action_button(
        actions,
        "Emitir Relatório",
        self.show_daily_report_print_menu,
        theme["accent"],
        fg=theme["text"],
        side="left",
    )
    _action_button(actions, "Editar Venda", self.edit_sale, "#D97706", side="left")
    _action_button(
        actions, "Excluir Venda", self.delete_sale, theme["danger"], side="left"
    )

    table_wrap = tk.Frame(card, bg=theme["surface"])
    table_wrap.grid(row=1, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)

    self.relatorio_dia_tree = ttk.Treeview(
        table_wrap, columns=("ID", "Hora", "Método", "Total", "Itens"), show="headings"
    )
    for col, width, anchor in (
        ("ID", 60, tk.CENTER),
        ("Hora", 120, tk.CENTER),
        ("Método", 130, tk.CENTER),
        ("Total", 110, tk.E),
        ("Itens", 560, tk.W),
    ):
        self.relatorio_dia_tree.heading(col, text=col)
        self.relatorio_dia_tree.column(col, width=width, anchor=anchor)
    self.relatorio_dia_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.relatorio_dia_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.relatorio_dia_tree.configure(yscrollcommand=scrollbar.set)
    self.relatorio_dia_tree.bind("<Double-1>", self.show_sale_details)
    self.update_daily_sales_report()


def create_relatorios_gerais_view(self):
    theme = _mgmt_theme(self)
    _clear_children(self.relatorios_gerais_view_frame)
    _, card = _section_shell(
        self.relatorios_gerais_view_frame,
        theme,
        "Gestão de Vendas",
        "Histórico comercial com indicadores, gráfico de desempenho e relatórios por período.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(3, weight=1)

    top_actions = tk.Frame(card, bg=theme["surface"])
    top_actions.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    top_actions.columnconfigure(0, weight=1)
    top_actions.columnconfigure(1, weight=0)

    filter_box = tk.Frame(top_actions, bg=theme["surface"])
    filter_box.grid(row=0, column=0, sticky="w")
    tk.Label(
        filter_box,
        text="Período:",
        font=("Segoe UI Semibold", 10),
        bg=theme["surface"],
        fg=theme["text"],
    ).pack(side="left", padx=(0, 10))

    self.report_period_buttons = {}
    for key, label in (
        ("week", "Semana"),
        ("month", "Mês"),
        ("year", "Ano"),
        ("all", "Histórico"),
    ):
        btn = tk.Button(
            filter_box,
            text=label,
            command=lambda value=key: self.set_sales_report_period(value),
            relief="flat",
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            padx=12,
            pady=8,
        )
        btn.pack(side="left", padx=(0, 8))
        self.report_period_buttons[key] = btn

    actions = tk.Frame(top_actions, bg=theme["surface"])
    actions.grid(row=0, column=1, sticky="e")
    _action_button(
        actions,
        "Atualizar",
        self.refresh_sales_history_dashboard,
        theme["primary"],
        side="left",
    )
    _action_button(
        actions,
        "Imprimir Período",
        self.show_general_report_print_menu,
        theme["accent"],
        fg=theme["text"],
        side="left",
    )
    _action_button(actions, "Editar Venda", self.edit_sale, "#D97706", side="left")
    _action_button(
        actions, "Excluir Venda", self.delete_sale, theme["danger"], side="left"
    )

    metrics = tk.Frame(card, bg=theme["surface"])
    metrics.grid(row=1, column=0, sticky="ew", pady=(0, 14))
    for idx in range(4):
        metrics.columnconfigure(idx, weight=1)

    def metric(parent, col, title, var, bg, fg):
        box = tk.Frame(parent, bg=bg, padx=14, pady=12)
        box.grid(row=0, column=col, sticky="ew", padx=4)
        tk.Label(box, text=title, font=("Segoe UI Semibold", 9), bg=bg, fg=fg).pack(
            anchor="w"
        )
        tk.Label(box, textvariable=var, font=("Segoe UI Black", 18), bg=bg, fg=fg).pack(
            anchor="w", pady=(8, 0)
        )

    self.report_total_var = tk.StringVar(value="R$ 0,00")
    self.report_count_var = tk.StringVar(value="0 vendas")
    self.report_avg_var = tk.StringVar(value="R$ 0,00")
    self.report_best_var = tk.StringVar(value="Sem dados")
    metric(
        metrics, 0, "Faturamento", self.report_total_var, "#EAF7EC", theme["primary"]
    )
    metric(metrics, 1, "Vendas", self.report_count_var, "#FFF4E8", "#B85C00")
    metric(metrics, 2, "Ticket medio", self.report_avg_var, "#EDF4FF", "#1E5AA7")
    metric(metrics, 3, "Melhor dia", self.report_best_var, "#F4EEFF", "#6D28D9")

    chart_card = tk.Frame(card, bg=theme["surface_alt"], padx=16, pady=16)
    chart_card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
    chart_card.columnconfigure(0, weight=1)
    tk.Label(
        chart_card,
        text="Desempenho do período",
        font=("Segoe UI Semibold", 13),
        bg=theme["surface_alt"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")
    self.report_chart_caption_var = tk.StringVar(value="Sem dados para exibir.")
    tk.Label(
        chart_card,
        textvariable=self.report_chart_caption_var,
        font=("Segoe UI", 9),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=1, column=0, sticky="w", pady=(4, 10))
    self.report_chart_canvas = tk.Canvas(
        chart_card,
        height=210,
        bg="#FCFDF8",
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    self.report_chart_canvas.grid(row=2, column=0, sticky="ew")

    table_wrap = tk.Frame(card, bg=theme["surface"])
    table_wrap.grid(row=3, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)

    self.relatorio_tree = ttk.Treeview(
        table_wrap, columns=("ID", "Data", "Método", "Total", "Itens"), show="headings"
    )
    for col, width, anchor in (
        ("ID", 60, tk.CENTER),
        ("Data", 150, tk.CENTER),
        ("Método", 130, tk.CENTER),
        ("Total", 110, tk.E),
        ("Itens", 520, tk.W),
    ):
        self.relatorio_tree.heading(col, text=col)
        self.relatorio_tree.column(col, width=width, anchor=anchor)
    self.relatorio_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.relatorio_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.relatorio_tree.configure(yscrollcommand=scrollbar.set)
    self.relatorio_tree.bind("<Double-1>", self.show_sale_details)

    if not hasattr(self, "sales_report_period"):
        self.sales_report_period = "all"
    self.refresh_sales_history_dashboard()


def _premium_shell(parent, theme, accent, title=None, subtitle=None, body_pad=20):
    shell = tk.Frame(
        parent,
        bg=theme.get("surface_elevated", theme["surface"]),
        highlightthickness=1,
        highlightbackground=theme.get("card_edge", theme["border"]),
    )
    tk.Frame(shell, bg=accent, height=4).pack(fill="x")
    body = tk.Frame(shell, bg=theme["surface"], padx=body_pad, pady=body_pad)
    body.pack(fill="both", expand=True)
    if title:
        body.columnconfigure(0, weight=1)
        tk.Label(
            body,
            text=title,
            font=("Segoe UI Semibold", 15),
            bg=theme["surface"],
            fg=theme["text"],
        ).grid(row=0, column=0, sticky="w")
        if subtitle:
            tk.Label(
                body,
                text=subtitle,
                font=("Segoe UI", 9),
                bg=theme["surface"],
                fg=theme["text_muted"],
                wraplength=440,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(4, 14))
    return shell, body


def _premium_metric_card(parent, theme, title, variable, accent, chip_bg, chip_fg):
    card = tk.Frame(
        parent,
        bg=theme["surface"],
        padx=16,
        pady=14,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, 10))
    tk.Label(
        card,
        text=title.upper(),
        font=("Segoe UI Semibold", 8),
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).pack(anchor="w")
    tk.Label(
        card,
        textvariable=variable,
        font=("Segoe UI Black", 16),
        bg=chip_bg,
        fg=chip_fg,
        padx=10,
        pady=7,
    ).pack(anchor="w", pady=(10, 0))
    return card


def _create_caixa_layout_premium(self):
    for widget in self.caixa_frame.winfo_children():
        widget.destroy()

    theme = _mgmt_theme(self)
    compact_mode = self.winfo_screenwidth() <= 1366 or self.winfo_screenheight() <= 768
    outer_pad = 12 if compact_mode else 16
    section_gap = 8 if compact_mode else 10
    hero_pad_x = 22 if compact_mode else 28
    hero_pad_y = 18 if compact_mode else 24
    panel_pad = 18 if compact_mode else 24
    title_font = ("Segoe UI Black", 19 if compact_mode else 25)
    text_font = ("Segoe UI", 9 if compact_mode else 10)
    label_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    quantity_font = ("Segoe UI Black", 18 if compact_mode else 24)
    total_font = ("Segoe UI Black", 24 if compact_mode else 30)
    action_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    button_pad_y = 8 if compact_mode else 10
    entry_ipady = 5 if compact_mode else 7
    quantity_ipady = 5 if compact_mode else 10

    self.caixa_frame.configure(bg=theme["bg"])
    self.caixa_frame.columnconfigure(0, weight=11)
    self.caixa_frame.columnconfigure(1, weight=14)
    self.caixa_frame.rowconfigure(0, weight=0)
    self.caixa_frame.rowconfigure(1, weight=0)
    self.caixa_frame.rowconfigure(2, weight=1)
    self.caixa_frame.rowconfigure(3, weight=0)

    hero_shell = tk.Frame(
        self.caixa_frame,
        bg=theme.get("surface_elevated", theme["surface"]),
        highlightthickness=1,
        highlightbackground=theme.get("card_edge", theme["border"]),
    )
    hero_shell.grid(
        row=0,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(outer_pad, section_gap),
        sticky="ew",
    )
    tk.Frame(hero_shell, bg=theme["accent"], height=4).grid(
        row=0, column=0, sticky="ew", columnspan=2
    )
    hero_frame = tk.Frame(
        hero_shell,
        bg=theme["surface_alt"],
        padx=hero_pad_x,
        pady=hero_pad_y,
    )
    hero_frame.grid(row=1, column=0, sticky="ew", columnspan=2)
    hero_frame.columnconfigure(0, weight=1)
    hero_frame.columnconfigure(1, weight=0)

    title_block = tk.Frame(hero_frame, bg=theme["surface_alt"])
    title_block.grid(row=0, column=0, sticky="w")
    title_brand = tk.Frame(title_block, bg=theme["surface_alt"])
    title_brand.pack(anchor="w")
    try:
        logo_size = 58 if compact_mode else 68
        logo_image = Image.open(get_app_logo_path()).resize(
            (logo_size, logo_size), Image.LANCZOS
        )
        self.caixa_logo_tk = ImageTk.PhotoImage(logo_image)
        tk.Label(
            title_brand, image=self.caixa_logo_tk, bg=theme["surface_alt"]
        ).pack(side="left", padx=(0, 14))
    except Exception:
        self.caixa_logo_tk = None

    title_text_block = tk.Frame(title_brand, bg=theme["surface_alt"])
    title_text_block.pack(side="left", anchor="w")
    tk.Label(
        title_text_block,
        text="Frente de Caixa Premium",
        font=title_font,
        bg=theme["surface_alt"],
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        title_text_block,
        text=APP_NAME,
        font=("Segoe UI Semibold", 9 if compact_mode else 10),
        bg=theme["surface_alt"],
        fg=theme["accent"],
    ).pack(anchor="w", pady=(2, 0))
    tk.Label(
        title_block,
        textvariable=self.status_banner_var,
        font=text_font,
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
        wraplength=380 if compact_mode else 470,
        justify="left",
    ).pack(anchor="w", pady=(8, 0))

    info_block = tk.Frame(hero_frame, bg=theme["surface_alt"])
    info_block.grid(row=0, column=1, sticky="e")
    self.caixa_operador_label = tk.Label(
        info_block,
        textvariable=self.user_summary_var,
        font=("Segoe UI Semibold", 11 if compact_mode else 12),
        bg=theme["surface_alt"],
        fg=theme["text"],
    )
    self.caixa_operador_label.pack(anchor="e", pady=(2, 8))

    status_action_row = tk.Frame(info_block, bg=theme["surface_alt"])
    status_action_row.pack(anchor="e")
    chip_font = ("Segoe UI Semibold", 9 if compact_mode else 10)
    self.caixa_status_chip = tk.Label(
        status_action_row,
        textvariable=self.cash_status_var,
        font=chip_font,
        bg=theme.get("primary_soft", theme["surface"]),
        fg=theme["primary_dark"],
        anchor="center",
        padx=12,
        pady=7,
    )
    self.caixa_status_chip.pack(side="left")
    if self.logged_user and self.logged_user.get("cargo") == "Gerente":
        self.btn_voltar_gerencia = tk.Button(
            status_action_row,
            text="Voltar para Gestão",
            command=lambda: self.show_frame("gerencia"),
            font=chip_font,
            bg=theme["surface"],
            fg=theme["text"],
            relief="flat",
            activebackground=theme.get("surface_elevated", theme["surface"]),
            activeforeground=theme["text"],
            cursor="hand2",
            bd=0,
            highlightthickness=1,
            highlightbackground=theme["border"],
            padx=12,
            pady=7,
        )
        self.btn_voltar_gerencia.pack(side="left", padx=(8, 0))
    tk.Label(
        info_block,
        text=POWERED_BY_LABEL,
        font=("Segoe UI", 8 if compact_mode else 9),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).pack(anchor="e", pady=(10, 0))

    summary_frame = tk.Frame(self.caixa_frame, bg=theme["bg"])
    summary_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(0, section_gap),
        sticky="ew",
    )
    for idx in range(4):
        summary_frame.columnconfigure(idx, weight=1)

    summary_cards = (
        ("Status do caixa", self.cash_status_var, theme["primary"], theme.get("primary_soft", theme["surface_alt"]), theme["primary_dark"]),
        ("Itens no carrinho", self.cart_count_var, theme["accent"], theme.get("accent_soft", theme["surface_alt"]), theme.get("accent_dark", theme["text"])),
        ("Peso / volume", self.cart_volume_var, "#6E865D", theme.get("surface_elevated", theme["surface"]), theme["text"]),
        ("Total da venda", self.total_var, theme["primary_dark"], theme["primary_dark"], theme["text_on_dark"]),
    )
    for idx, (title, var, accent, chip_bg, chip_fg) in enumerate(summary_cards):
        card = _premium_metric_card(
            summary_frame, theme, title, var, accent, chip_bg, chip_fg
        )
        card.grid(row=0, column=idx, padx=4, sticky="ew")

    workspace_frame = tk.Frame(self.caixa_frame, bg=theme["bg"])
    workspace_frame.grid(
        row=2,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(0, section_gap),
        sticky="nsew",
    )
    workspace_frame.columnconfigure(0, weight=9)
    workspace_frame.columnconfigure(1, weight=16)
    workspace_frame.rowconfigure(0, weight=1)

    left_shell, left_panel = _premium_shell(
        workspace_frame,
        theme,
        theme["primary"],
        "Lançamento rápido",
        "Pesquisa por nome, SKU ou código, com foco em velocidade e clareza no atendimento.",
        body_pad=panel_pad,
    )
    left_shell.grid(row=0, column=0, padx=(0, section_gap), sticky="nsew")
    left_panel.columnconfigure(0, weight=1)

    search_box = tk.Frame(
        left_panel,
        bg=theme["surface_alt"],
        padx=14,
        pady=14,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    search_box.grid(row=2, column=0, sticky="ew")
    search_box.columnconfigure(0, weight=1)
    tk.Label(
        search_box,
        text="Produto",
        font=label_font,
        bg=theme["surface_alt"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        search_box,
        text="Busque por nome, SKU ou código de barras.",
        font=text_font,
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=1, column=0, sticky="w", pady=(4, 10))
    self.produto_entry = ttk.Combobox(
        search_box, font=("Segoe UI", 12 if compact_mode else 14)
    )
    self.produto_entry.grid(row=2, column=0, sticky="ew", ipady=entry_ipady)

    quantity_box = tk.Frame(left_panel, bg=theme["surface"], pady=14)
    quantity_box.grid(row=3, column=0, sticky="ew")
    quantity_box.columnconfigure(0, weight=1)
    tk.Label(
        quantity_box,
        text="Quantidade",
        font=label_font,
        bg=theme["surface"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        quantity_box,
        text="Use peso ou unidade conforme o cadastro do produto.",
        font=text_font,
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).grid(row=1, column=0, sticky="w", pady=(4, 10))
    self.quantidade_entry = tk.Entry(
        quantity_box,
        font=quantity_font,
        justify="center",
        relief="solid",
        bd=1,
        bg="#FFFFFF",
        fg=theme["text"],
        insertbackground=theme["text"],
        highlightthickness=1,
        highlightbackground=theme["border"],
        highlightcolor=theme["primary"],
    )
    self.quantidade_entry.grid(row=2, column=0, sticky="ew", ipady=quantity_ipady)
    self.quantidade_entry.insert(0, "1")

    self.btn_adicionar_item = tk.Button(
        left_panel,
        text="Adicionar item  Enter",
        font=("Segoe UI Semibold", 11 if compact_mode else 12),
        bg=theme["primary_dark"],
        fg=theme["text_on_dark"],
        activebackground=theme["primary"],
        activeforeground=theme["text_on_dark"],
        command=self.adicionar_item_carrinho,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=button_pad_y,
    )
    self.btn_adicionar_item.grid(row=4, column=0, sticky="ew", pady=(4, 0))

    action_cards = tk.Frame(left_panel, bg=theme["surface"])
    action_cards.grid(row=5, column=0, sticky="ew", pady=(14, 0))
    action_cards.columnconfigure(0, weight=1)
    action_cards.columnconfigure(1, weight=1)

    def action_panel(parent, column, accent, title, subtitle):
        shell = tk.Frame(
            parent,
            bg=theme["surface_alt"],
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        shell.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 5) if column == 0 else (5, 0),
        )
        shell.columnconfigure(0, weight=1)
        tk.Frame(shell, bg=accent, height=3).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(
            shell,
            text=title,
            font=("Segoe UI Semibold", 12),
            bg=theme["surface_alt"],
            fg=theme["text"],
        ).grid(row=1, column=0, sticky="w")
        tk.Label(
            shell,
            text=subtitle,
            font=text_font,
            bg=theme["surface_alt"],
            fg=theme["text_muted"],
            wraplength=190 if compact_mode else 220,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(4, 12))
        return shell

    venda_card = action_panel(
        action_cards,
        0,
        theme["accent"],
        "Venda assistida",
        "Ações mais usadas no atendimento, com atalhos diretos para balcão e checkout.",
    )
    self.btn_add_f2 = tk.Button(
        venda_card,
        text="Pesar itens  F2",
        font=action_font,
        bg=theme["accent"],
        fg=theme["text_on_dark"],
        activebackground=theme.get("accent_dark", theme["accent"]),
        activeforeground=theme["text_on_dark"],
        command=self.open_adicionar_item_dialog,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=7,
    )
    self.btn_add_f2.grid(row=3, column=0, sticky="ew", pady=(0, 6))
    self.btn_limpar_venda = tk.Button(
        venda_card,
        text="Limpar venda  F3",
        font=action_font,
        bg=theme["surface"],
        fg=theme["text"],
        activebackground=theme.get("surface_elevated", theme["surface"]),
        activeforeground=theme["text"],
        command=self.limpar_venda,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=1,
        highlightbackground=theme["border"],
        pady=7,
    )
    self.btn_limpar_venda.grid(row=4, column=0, sticky="ew", pady=(0, 6))
    self.btn_emitir_nota = tk.Button(
        venda_card,
        text="Emitir nota  F4",
        font=action_font,
        bg=theme["surface"],
        fg=theme["text"],
        activebackground=theme.get("surface_elevated", theme["surface"]),
        activeforeground=theme["text"],
        command=self.show_note_dialog,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=1,
        highlightbackground=theme["border"],
        pady=7,
    )
    self.btn_emitir_nota.grid(row=5, column=0, sticky="ew", pady=(0, 6))
    self.btn_finalizar_venda = tk.Button(
        venda_card,
        text="Finalizar venda  F5",
        font=action_font,
        bg=theme["primary_dark"],
        fg=theme["text_on_dark"],
        activebackground=theme["primary"],
        activeforeground=theme["text_on_dark"],
        command=self.iniciar_finalizacao_venda,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=7,
    )
    self.btn_finalizar_venda.grid(row=6, column=0, sticky="ew")

    caixa_card = action_panel(
        action_cards,
        1,
        "#6E865D",
        "Controle operacional",
        "Gestão segura de abertura, fechamento e encerramento da sessão atual.",
    )
    self.btn_abrir_caixa = tk.Button(
        caixa_card,
        text="Abrir caixa",
        font=action_font,
        bg="#466F5A",
        fg=theme["text_on_dark"],
        activebackground=theme["primary_dark"],
        activeforeground=theme["text_on_dark"],
        command=self.abrir_caixa,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=7,
    )
    self.btn_abrir_caixa.grid(row=3, column=0, sticky="ew", pady=(0, 6))
    self.btn_fechar_caixa = tk.Button(
        caixa_card,
        text="Fechar caixa",
        font=action_font,
        bg="#7A8F58",
        fg=theme["text_on_dark"],
        activebackground="#617346",
        activeforeground=theme["text_on_dark"],
        command=self.fechar_caixa,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=7,
    )
    self.btn_fechar_caixa.grid(row=4, column=0, sticky="ew", pady=(0, 6))
    self.btn_fechar_sistema = tk.Button(
        caixa_card,
        text="Fechar sistema",
        font=action_font,
        bg=theme["danger"],
        fg=theme["text_on_dark"],
        activebackground="#943A27",
        activeforeground=theme["text_on_dark"],
        command=self.on_closing,
        relief="flat",
        cursor="hand2",
        bd=0,
        pady=7,
    )
    self.btn_fechar_sistema.grid(row=5, column=0, sticky="ew")

    note_card = tk.Frame(
        left_panel,
        bg=theme.get("surface_elevated", theme["surface"]),
        padx=14,
        pady=14,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    note_card.grid(row=6, column=0, sticky="ew", pady=(14, 0))
    tk.Label(
        note_card,
        text="Atalhos e agilidade",
        font=("Segoe UI Semibold", 11),
        bg=theme.get("surface_elevated", theme["surface"]),
        fg=theme["text"],
    ).pack(anchor="w")
    tk.Label(
        note_card,
        text="[F2] Pesar itens   [F3] Limpar venda   [F4] Emitir nota   [F5] Finalizar venda",
        font=text_font,
        bg=theme.get("surface_elevated", theme["surface"]),
        fg=theme["text_muted"],
        wraplength=420 if compact_mode else 480,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    right_shell, right_panel = _premium_shell(
        workspace_frame,
        theme,
        theme["accent"],
        "Carrinho em tempo real",
        "Tudo o que entra na venda aparece aqui com leitura rápida e edição segura antes da finalização.",
        body_pad=panel_pad,
    )
    right_shell.grid(row=0, column=1, padx=(section_gap, 0), sticky="nsew")
    right_panel.columnconfigure(0, weight=1)
    right_panel.rowconfigure(3, weight=1)

    right_header = tk.Frame(right_panel, bg=theme["surface"])
    right_header.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    right_header.columnconfigure(0, weight=1)
    right_header.columnconfigure(1, weight=0)
    tk.Label(
        right_header,
        text="Resumo da venda em andamento",
        font=("Segoe UI Semibold", 11),
        bg=theme["surface"],
        fg=theme["text"],
    ).grid(row=0, column=0, sticky="w")

    chips = tk.Frame(right_header, bg=theme["surface"])
    chips.grid(row=0, column=1, sticky="e")
    tk.Label(
        chips,
        textvariable=self.cart_count_var,
        font=("Segoe UI Semibold", 9),
        bg=theme.get("primary_soft", theme["surface_alt"]),
        fg=theme["primary_dark"],
        padx=10,
        pady=6,
    ).pack(side="left", padx=(0, 6))
    tk.Label(
        chips,
        textvariable=self.cart_volume_var,
        font=("Segoe UI Semibold", 9),
        bg=theme.get("accent_soft", theme["surface_alt"]),
        fg=theme.get("accent_dark", theme["text"]),
        padx=10,
        pady=6,
    ).pack(side="left")

    cart_table_frame = tk.Frame(
        right_panel,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    cart_table_frame.grid(row=3, column=0, sticky="nsew")
    cart_table_frame.columnconfigure(0, weight=1)
    cart_table_frame.rowconfigure(0, weight=1)

    self.carrinho_tree = ttk.Treeview(
        cart_table_frame,
        columns=("Produto", "Quantidade", "Preco Unit.", "Subtotal"),
        show="headings",
        selectmode="browse",
    )
    self.carrinho_tree.heading("Produto", text="Produto")
    self.carrinho_tree.heading("Quantidade", text="Quantidade")
    self.carrinho_tree.heading("Preco Unit.", text="Preco Unit.")
    self.carrinho_tree.heading("Subtotal", text="Subtotal")
    self.carrinho_tree.column("Produto", width=260 if compact_mode else 320, anchor="w")
    self.carrinho_tree.column("Quantidade", width=110 if compact_mode else 130, anchor="center")
    self.carrinho_tree.column("Preco Unit.", width=100 if compact_mode else 120, anchor="e")
    self.carrinho_tree.column("Subtotal", width=110 if compact_mode else 130, anchor="e")
    self.carrinho_tree.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(
        cart_table_frame, orient="vertical", command=self.carrinho_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.carrinho_tree.configure(yscrollcommand=scrollbar.set)

    botoes_edit_frame = tk.Frame(right_panel, bg=theme["surface"])
    botoes_edit_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
    botoes_edit_frame.columnconfigure(0, weight=1)
    botoes_edit_frame.columnconfigure(1, weight=1)
    tk.Button(
        botoes_edit_frame,
        text="Excluir item",
        bg=theme["danger"],
        fg=theme["text_on_dark"],
        activebackground="#943A27",
        activeforeground=theme["text_on_dark"],
        command=self.delete_item_from_cart,
        relief="flat",
        cursor="hand2",
        font=action_font,
        bd=0,
        pady=button_pad_y,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
    tk.Button(
        botoes_edit_frame,
        text="Editar quantidade",
        bg=theme["accent"],
        fg=theme["text_on_dark"],
        activebackground=theme.get("accent_dark", theme["accent"]),
        activeforeground=theme["text_on_dark"],
        command=self.edit_item_in_cart,
        relief="flat",
        cursor="hand2",
        font=action_font,
        bd=0,
        pady=button_pad_y,
    ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

    utility_frame = tk.Frame(
        self.caixa_frame,
        bg=theme["surface_alt"],
        padx=18,
        pady=16,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    utility_frame.grid(
        row=3,
        column=0,
        columnspan=2,
        padx=outer_pad,
        pady=(0, outer_pad),
        sticky="ew",
    )
    utility_frame.columnconfigure(0, weight=1)
    utility_frame.columnconfigure(1, weight=0)
    tk.Label(
        utility_frame,
        text="Resumo financeiro da operação",
        font=("Segoe UI Semibold", 10),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=0, column=0, sticky="w")
    self.total_label = tk.Label(
        utility_frame,
        text=self.total_var.get(),
        font=total_font,
        bg=theme["surface_alt"],
        fg=theme["text"],
    )
    self.total_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
    tk.Label(
        utility_frame,
        text="Caixa pronto para mercados, mercearias e operação de balcão.",
        font=text_font,
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
        justify="right",
    ).grid(row=0, column=1, rowspan=2, sticky="e")

    self.produto_entry.bind("<KeyRelease>", self.update_produto_list)
    self.produto_entry.bind("<Return>", self.adicionar_item_carrinho_event)
    self.bind_all("<F2>", lambda e: self.open_adicionar_item_dialog())
    self.bind_all("<F3>", lambda e: self.limpar_venda())
    self.bind_all("<F4>", lambda e: self.show_note_dialog())
    self.bind_all("<F5>", lambda e: self.iniciar_finalizacao_venda())
    self.produto_entry.focus_set()


def _create_relatorios_view_premium(self):
    theme = _mgmt_theme(self)
    _clear_children(self.relatorios_view_frame)
    _, card = _section_shell(
        self.relatorios_view_frame,
        theme,
        "Relatório do Dia",
        "Consulta diária de vendas, emissão operacional e manutenção dos lançamentos do turno.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(3, weight=1)

    overview_shell, overview = _premium_shell(
        card,
        theme,
        theme["accent"],
        None,
        None,
        body_pad=20,
    )
    overview_shell.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    overview.columnconfigure(0, weight=2)
    overview.columnconfigure(1, weight=3)

    overview_copy = tk.Frame(overview, bg=theme["surface"])
    overview_copy.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    tk.Label(
        overview_copy,
        text="KODA SYSTEM",
        font=("Segoe UI Semibold", 9),
        bg=theme["surface"],
        fg=theme["accent"],
    ).pack(anchor="w")
    tk.Label(
        overview_copy,
        text="Acompanhamento diário com leitura executiva e pronta para impressão.",
        font=("Segoe UI Black", 19),
        bg=theme["surface"],
        fg=theme["text"],
        wraplength=420,
        justify="left",
    ).pack(anchor="w", pady=(8, 8))
    self.daily_report_caption_var = tk.StringVar(
        value="Atualize a conferência do dia para refletir as vendas mais recentes."
    )
    tk.Label(
        overview_copy,
        textvariable=self.daily_report_caption_var,
        font=("Segoe UI", 9),
        bg=theme["surface"],
        fg=theme["text_muted"],
        wraplength=420,
        justify="left",
    ).pack(anchor="w")

    stats = tk.Frame(overview, bg=theme["surface"])
    stats.grid(row=0, column=1, sticky="nsew")
    for idx in range(2):
        stats.columnconfigure(idx, weight=1)
        stats.rowconfigure(idx, weight=1)
    self.daily_report_total_var = tk.StringVar(value="R$ 0,00")
    self.daily_report_count_var = tk.StringVar(value="0 vendas")
    self.daily_report_avg_var = tk.StringVar(value="R$ 0,00")
    self.daily_report_best_var = tk.StringVar(value="Sem vendas")
    daily_metrics = (
        ("Faturamento", self.daily_report_total_var, theme["primary"], theme.get("primary_soft", theme["surface_alt"]), theme["primary_dark"]),
        ("Vendas", self.daily_report_count_var, theme["accent"], theme.get("accent_soft", theme["surface_alt"]), theme.get("accent_dark", theme["text"])),
        ("Ticket médio", self.daily_report_avg_var, "#6E865D", theme.get("surface_elevated", theme["surface"]), theme["text"]),
        ("Maior venda", self.daily_report_best_var, "#796483", theme.get("surface_elevated", theme["surface"]), theme["text"]),
    )
    for idx, (title, variable, accent, chip_bg, chip_fg) in enumerate(daily_metrics):
        tile = _premium_metric_card(
            stats, theme, title, variable, accent, chip_bg, chip_fg
        )
        row, col = divmod(idx, 2)
        tile.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

    actions_shell, actions = _premium_shell(
        card,
        theme,
        theme["primary"],
        "Ações do relatório",
        "Atualize, imprima ou ajuste lançamentos sem sair do fluxo de conferência.",
        body_pad=18,
    )
    actions_shell.grid(row=1, column=0, sticky="ew", pady=(0, 14))
    actions_row = tk.Frame(actions, bg=theme["surface"])
    actions_row.grid(row=2, column=0, sticky="w")
    _action_button(
        actions_row,
        "Atualizar",
        self.update_daily_sales_report,
        theme["primary"],
        side="left",
        active_bg=theme["primary_dark"],
    )
    _action_button(
        actions_row,
        "Emitir relatório",
        self.show_daily_report_print_menu,
        theme["accent"],
        side="left",
        active_bg=theme.get("accent_dark", theme["accent"]),
    )
    _action_button(
        actions_row,
        "Editar venda",
        self.edit_sale,
        "#6E865D",
        side="left",
        active_bg="#55704A",
    )
    _action_button(
        actions_row,
        "Excluir venda",
        self.delete_sale,
        theme["danger"],
        side="left",
        active_bg="#943A27",
    )

    table_shell, table_body = _premium_shell(
        card,
        theme,
        theme["accent"],
        "Vendas registradas hoje",
        "Duplo clique para abrir detalhes do lançamento e revisar o conteúdo da venda.",
        body_pad=18,
    )
    table_shell.grid(row=3, column=0, sticky="nsew")
    table_body.columnconfigure(0, weight=1)
    table_body.rowconfigure(2, weight=1)

    table_wrap = tk.Frame(
        table_body,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    table_wrap.grid(row=2, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)

    self.relatorio_dia_tree = ttk.Treeview(
        table_wrap, columns=("ID", "Hora", "Método", "Total", "Itens"), show="headings"
    )
    for col, width, anchor in (
        ("ID", 60, tk.CENTER),
        ("Hora", 120, tk.CENTER),
        ("Método", 130, tk.CENTER),
        ("Total", 110, tk.E),
        ("Itens", 560, tk.W),
    ):
        self.relatorio_dia_tree.heading(col, text=col)
        self.relatorio_dia_tree.column(col, width=width, anchor=anchor)
    self.relatorio_dia_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.relatorio_dia_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.relatorio_dia_tree.configure(yscrollcommand=scrollbar.set)
    self.relatorio_dia_tree.bind("<Double-1>", self.show_sale_details)
    self.update_daily_sales_report()


def _create_relatorios_gerais_view_premium(self):
    theme = _mgmt_theme(self)
    _clear_children(self.relatorios_gerais_view_frame)
    _, card = _section_shell(
        self.relatorios_gerais_view_frame,
        theme,
        "Gestão de Vendas",
        "Histórico comercial com indicadores, gráfico de desempenho e relatórios por período.",
        back_command=lambda: self.show_frame("gerencia"),
    )
    card.columnconfigure(0, weight=1)
    card.rowconfigure(4, weight=1)

    intro_shell, intro = _premium_shell(card, theme, theme["accent"], None, None, body_pad=20)
    intro_shell.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    intro.columnconfigure(0, weight=2)
    intro.columnconfigure(1, weight=1)
    left = tk.Frame(intro, bg=theme["surface"])
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    tk.Label(
        left,
        text="KODA SYSTEM",
        font=("Segoe UI Semibold", 9),
        bg=theme["surface"],
        fg=theme["accent"],
    ).pack(anchor="w")
    tk.Label(
        left,
        text="Histórico comercial com leitura premium para gestão e tomada de decisão.",
        font=("Segoe UI Black", 20),
        bg=theme["surface"],
        fg=theme["text"],
        wraplength=520,
        justify="left",
    ).pack(anchor="w", pady=(8, 8))
    tk.Label(
        left,
        text="Filtre períodos, acompanhe indicadores e apresente o desempenho do negócio com uma visualização mais profissional.",
        font=("Segoe UI", 9),
        bg=theme["surface"],
        fg=theme["text_muted"],
        wraplength=520,
        justify="left",
    ).pack(anchor="w")

    right = tk.Frame(intro, bg=theme["surface"])
    right.grid(row=0, column=1, sticky="nsew")
    tk.Label(
        right,
        text="Período ativo",
        font=("Segoe UI Semibold", 9),
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).pack(anchor="w")
    self.report_period_caption_var = tk.StringVar(value="Histórico completo")
    tk.Label(
        right,
        textvariable=self.report_period_caption_var,
        font=("Segoe UI Semibold", 12),
        bg=theme.get("primary_soft", theme["surface_alt"]),
        fg=theme["primary_dark"],
        padx=12,
        pady=8,
    ).pack(anchor="w", pady=(10, 0))

    filter_shell, filter_body = _premium_shell(
        card,
        theme,
        theme["primary"],
        "Períodos e ações",
        "Escolha um intervalo, atualize o painel e emita o relatório do período selecionado.",
        body_pad=18,
    )
    filter_shell.grid(row=1, column=0, sticky="ew", pady=(0, 14))
    filter_body.columnconfigure(0, weight=1)
    filter_body.columnconfigure(1, weight=0)

    filter_box = tk.Frame(filter_body, bg=theme["surface"])
    filter_box.grid(row=2, column=0, sticky="w")
    tk.Label(
        filter_box,
        text="Período:",
        font=("Segoe UI Semibold", 10),
        bg=theme["surface"],
        fg=theme["text"],
    ).pack(side="left", padx=(0, 10))

    self.report_period_buttons = {}
    for key, label in (
        ("week", "Semana"),
        ("month", "Mês"),
        ("year", "Ano"),
        ("all", "Histórico"),
    ):
        btn = tk.Button(
            filter_box,
            text=label,
            command=lambda value=key: self.set_sales_report_period(value),
            relief="flat",
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            padx=12,
            pady=8,
            bd=0,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        btn.pack(side="left", padx=(0, 8))
        self.report_period_buttons[key] = btn

    actions = tk.Frame(filter_body, bg=theme["surface"])
    actions.grid(row=2, column=1, sticky="e")
    _action_button(
        actions,
        "Atualizar",
        self.refresh_sales_history_dashboard,
        theme["primary"],
        side="left",
        active_bg=theme["primary_dark"],
    )
    _action_button(
        actions,
        "Imprimir período",
        self.show_general_report_print_menu,
        theme["accent"],
        side="left",
        active_bg=theme.get("accent_dark", theme["accent"]),
    )
    _action_button(
        actions,
        "Editar venda",
        self.edit_sale,
        "#6E865D",
        side="left",
        active_bg="#55704A",
    )
    _action_button(
        actions,
        "Excluir venda",
        self.delete_sale,
        theme["danger"],
        side="left",
        active_bg="#943A27",
    )

    metrics = tk.Frame(card, bg=theme["surface"])
    metrics.grid(row=2, column=0, sticky="ew", pady=(0, 14))
    for idx in range(4):
        metrics.columnconfigure(idx, weight=1)

    self.report_total_var = tk.StringVar(value="R$ 0,00")
    self.report_count_var = tk.StringVar(value="0 vendas")
    self.report_avg_var = tk.StringVar(value="R$ 0,00")
    self.report_best_var = tk.StringVar(value="Sem dados")
    metric_cards = (
        ("Faturamento", self.report_total_var, theme["primary"], theme.get("primary_soft", theme["surface_alt"]), theme["primary_dark"]),
        ("Vendas", self.report_count_var, theme["accent"], theme.get("accent_soft", theme["surface_alt"]), theme.get("accent_dark", theme["text"])),
        ("Ticket médio", self.report_avg_var, "#62719A", theme.get("surface_elevated", theme["surface"]), theme["text"]),
        ("Melhor dia", self.report_best_var, "#796483", theme.get("surface_elevated", theme["surface"]), theme["text"]),
    )
    for idx, (title, variable, accent, chip_bg, chip_fg) in enumerate(metric_cards):
        box = _premium_metric_card(
            metrics, theme, title, variable, accent, chip_bg, chip_fg
        )
        box.grid(row=0, column=idx, sticky="ew", padx=4)

    chart_shell, chart_body = _premium_shell(
        card,
        theme,
        theme["accent"],
        "Desempenho do período",
        "Evolução do faturamento conforme o intervalo selecionado.",
        body_pad=18,
    )
    chart_shell.grid(row=3, column=0, sticky="ew", pady=(0, 14))
    chart_body.columnconfigure(0, weight=1)
    self.report_chart_caption_var = tk.StringVar(value="Sem dados para exibir.")
    tk.Label(
        chart_body,
        textvariable=self.report_chart_caption_var,
        font=("Segoe UI", 9),
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).grid(row=2, column=0, sticky="w", pady=(0, 10))
    self.report_chart_canvas = tk.Canvas(
        chart_body,
        height=210,
        bg=theme.get("surface_elevated", "#FCFDF8"),
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    self.report_chart_canvas.grid(row=3, column=0, sticky="ew")

    table_shell, table_body = _premium_shell(
        card,
        theme,
        theme["primary"],
        "Histórico detalhado",
        "Duplo clique para abrir detalhes e revisar lançamentos do período filtrado.",
        body_pad=18,
    )
    table_shell.grid(row=4, column=0, sticky="nsew")
    table_body.columnconfigure(0, weight=1)
    table_body.rowconfigure(2, weight=1)

    table_wrap = tk.Frame(
        table_body,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    table_wrap.grid(row=2, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)

    self.relatorio_tree = ttk.Treeview(
        table_wrap, columns=("ID", "Data", "Método", "Total", "Itens"), show="headings"
    )
    for col, width, anchor in (
        ("ID", 60, tk.CENTER),
        ("Data", 150, tk.CENTER),
        ("Método", 130, tk.CENTER),
        ("Total", 110, tk.E),
        ("Itens", 520, tk.W),
    ):
        self.relatorio_tree.heading(col, text=col)
        self.relatorio_tree.column(col, width=width, anchor=anchor)
    self.relatorio_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        table_wrap, orient="vertical", command=self.relatorio_tree.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.relatorio_tree.configure(yscrollcommand=scrollbar.set)
    self.relatorio_tree.bind("<Double-1>", self.show_sale_details)

    if not hasattr(self, "sales_report_period"):
        self.sales_report_period = "all"
    self.refresh_sales_history_dashboard()


def _create_caixa_layout_vibrant(self):
    for widget in self.caixa_frame.winfo_children():
        widget.destroy()

    theme = _mgmt_theme(self)
    compact_mode = self.winfo_screenwidth() <= 1366 or self.winfo_screenheight() <= 768
    outer_pad = 10 if compact_mode else 16
    section_gap = 8 if compact_mode else 10
    hero_pad = 14 if compact_mode else 24
    panel_pad = 12 if compact_mode else 20
    title_font = ("Segoe UI Black", 17 if compact_mode else 24)
    section_font = ("Segoe UI Semibold", 13 if compact_mode else 17)
    text_font = ("Segoe UI", 8 if compact_mode else 10)
    label_font = ("Segoe UI Semibold", 8 if compact_mode else 10)
    quantity_font = ("Segoe UI Black", 14 if compact_mode else 22)
    action_font = ("Segoe UI Semibold", 8 if compact_mode else 10)
    total_font = ("Segoe UI Black", 22 if compact_mode else 32)
    entry_ipady = 4 if compact_mode else 7
    quantity_ipady = 4 if compact_mode else 9

    blue_soft = "#EAF3FF"
    blue_strong = "#2268D6"
    olive_soft = "#EEF8DD"
    olive_strong = "#5C8A1E"

    self.caixa_frame.configure(bg=theme["bg"])
    self.caixa_frame.columnconfigure(0, weight=1)
    self.caixa_frame.rowconfigure(2, weight=1)

    hero_shell = tk.Frame(
        self.caixa_frame,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["card_edge"],
    )
    hero_shell.grid(
        row=0,
        column=0,
        padx=outer_pad,
        pady=(outer_pad, section_gap),
        sticky="ew",
    )
    hero_shell.columnconfigure(0, weight=7)
    hero_shell.columnconfigure(1, weight=5)

    brand_panel = tk.Frame(hero_shell, bg=theme["primary_dark"], padx=hero_pad, pady=hero_pad)
    brand_panel.grid(row=0, column=0, sticky="nsew")
    brand_panel.columnconfigure(1, weight=1)

    try:
        logo_size = 58 if compact_mode else 70
        logo_image = Image.open(get_app_logo_path()).resize(
            (logo_size, logo_size), Image.LANCZOS
        )
        self.caixa_logo_tk = ImageTk.PhotoImage(logo_image)
        tk.Label(brand_panel, image=self.caixa_logo_tk, bg=theme["primary_dark"]).grid(
            row=0, column=0, rowspan=3, sticky="nw", padx=(0, 14)
        )
    except Exception:
        self.caixa_logo_tk = None

    tk.Label(
        brand_panel,
        text="KODA SYSTEM",
        font=("Segoe UI Semibold", 9),
        bg=theme["primary_dark"],
        fg="#B7F7CF",
    ).grid(row=0, column=1, sticky="w")
    tk.Label(
        brand_panel,
        text="Frente de Caixa",
        font=title_font,
        bg=theme["primary_dark"],
        fg=theme["text_on_dark"],
    ).grid(row=1, column=1, sticky="w", pady=(4, 4))
    tk.Label(
        brand_panel,
        textvariable=self.status_banner_var,
        font=text_font,
        bg=theme["primary_dark"],
        fg="#E3FFF0",
        wraplength=420 if compact_mode else 620,
        justify="left",
    ).grid(row=2, column=1, sticky="w")

    side_panel = tk.Frame(hero_shell, bg=theme["surface_alt"], padx=hero_pad, pady=hero_pad)
    side_panel.grid(row=0, column=1, sticky="nsew")
    side_panel.columnconfigure(0, weight=1)
    tk.Label(
        side_panel,
        textvariable=self.user_summary_var,
        font=("Segoe UI Semibold", 10 if compact_mode else 13),
        bg=theme["surface_alt"],
        fg=theme["text"],
        justify="right",
    ).grid(row=0, column=0, sticky="e")

    top_chips = tk.Frame(side_panel, bg=theme["surface_alt"])
    top_chips.grid(row=1, column=0, sticky="e", pady=(10, 10))
    self.caixa_status_chip = tk.Label(
        top_chips,
        textvariable=self.cash_status_var,
        font=("Segoe UI Semibold", 9 if compact_mode else 10),
        bg=theme["primary_soft"],
        fg=theme["primary_dark"],
        padx=10,
        pady=6,
    )
    self.caixa_status_chip.pack(side="left")
    if self.logged_user and self.logged_user.get("cargo") == "Gerente":
        self.btn_voltar_gerencia = tk.Button(
            top_chips,
            text="Voltar para Gestão",
            command=lambda: self.show_frame("gerencia"),
            font=("Segoe UI Semibold", 8 if compact_mode else 10),
            bg=theme["accent"],
            fg=theme["text_on_dark"],
            activebackground=theme["accent_dark"],
            activeforeground=theme["text_on_dark"],
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=10,
            pady=6,
        )
        self.btn_voltar_gerencia.pack(side="left", padx=(8, 0))

    #tk.Label(
    #    side_panel,
    #    text="Pronto para atendimento ágil, conferência rápida e operação de balcão.",
    #    font=text_font,
    #    bg=theme["surface_alt"],
    #    fg=theme["text_muted"],
    #    wraplength=220 if compact_mode else 360,
    #    justify="right",
    #).grid(row=2, column=0, sticky="e")
    tk.Label(
        side_panel,
        text=POWERED_BY_LABEL,
        font=("Segoe UI", 8 if compact_mode else 9),
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=2, column=0, sticky="e", pady=(14, 0))


    metrics = tk.Frame(self.caixa_frame, bg=theme["bg"])
    metrics.grid(row=1, column=0, padx=outer_pad, pady=(0, section_gap), sticky="ew")
    for idx in range(4):
        metrics.columnconfigure(idx, weight=1)

    def metric_card(parent, col, title, variable, bg, fg, accent):
        card = tk.Frame(
            parent,
            bg=bg,
            padx=12 if compact_mode else 16,
            pady=10 if compact_mode else 14,
            highlightthickness=1,
            highlightbackground=theme["card_edge"],
        )
        card.grid(row=0, column=col, sticky="ew", padx=4)
        tk.Frame(card, bg=accent, height=4).pack(fill="x", pady=(0, 8 if compact_mode else 10))
        tk.Label(
            card,
            text=title.upper(),
            font=("Segoe UI Semibold", 7 if compact_mode else 8),
            bg=bg,
            fg=fg,
        ).pack(anchor="w")
        tk.Label(
            card,
            textvariable=variable,
            font=("Segoe UI Black", 13 if compact_mode else 18),
            bg=bg,
            fg=fg,
        ).pack(anchor="w", pady=(6 if compact_mode else 8, 0))

    metric_card(metrics, 0, "Status do caixa", self.cash_status_var, "#E6FFF0", theme["primary_dark"], theme["primary"])
    metric_card(metrics, 1, "Itens no carrinho", self.cart_count_var, "#FFF1DE", theme["accent_dark"], theme["accent"])
    metric_card(metrics, 2, "Peso / volume", self.cart_volume_var, blue_soft, blue_strong, blue_strong)
    metric_card(metrics, 3, "Total da venda", self.total_var, "#DFF9E7", theme["primary_dark"], theme["primary_dark"])

    workspace = tk.Frame(self.caixa_frame, bg=theme["bg"])
    workspace.grid(row=2, column=0, padx=outer_pad, pady=(0, section_gap), sticky="nsew")
    workspace.columnconfigure(0, weight=7 if compact_mode else 8)
    workspace.columnconfigure(1, weight=13 if compact_mode else 12)
    workspace.rowconfigure(0, weight=1)

    left_card = tk.Frame(
        workspace,
        bg=theme["surface"],
        padx=panel_pad,
        pady=panel_pad,
        highlightthickness=1,
        highlightbackground=theme["card_edge"],
    )
    left_card.grid(row=0, column=0, sticky="nsew", padx=(0, section_gap))
    left_card.columnconfigure(0, weight=1)
    tk.Frame(left_card, bg=theme["primary"], height=4).grid(row=0, column=0, sticky="ew")
    #tk.Label(
    #    left_card,
    #    text="Lançamento rápido",
    #    font=section_font,
    #    bg=theme["surface"],
    #    fg=theme["text"],
    #).grid(row=1, column=0, sticky="w", pady=(12, 4))
    #tk.Label(
    #    left_card,
    #    text=(
    #        "Digite o produto, ajuste a quantidade e conclua sem perder ritmo."
    #        if compact_mode
    #        else "Digite o produto, ajuste a quantidade e conclua sem perder ritmo no atendimento."
    #    ),
    #    font=text_font,
    #    bg=theme["surface"],
    #    fg=theme["text_muted"],
    #    wraplength=360 if compact_mode else 420,
    #    justify="left",
    #).grid(row=2, column=0, sticky="w", pady=(0, 12))

    product_box = tk.Frame(
        left_card,
        bg=theme["surface_alt"],
        padx=12 if compact_mode else 14,
        pady=12 if compact_mode else 14,
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    product_box.grid(row=3, column=0, sticky="ew")
    product_box.columnconfigure(0, weight=1)
    tk.Label(product_box, text="Produto", font=label_font, bg=theme["surface_alt"], fg=theme["text"]).grid(row=0, column=0, sticky="w")
    tk.Label(
        product_box,
        text="Nome, SKU ou código de barras." if compact_mode else "Busca por nome, SKU ou código de barras.",
        font=text_font,
        bg=theme["surface_alt"],
        fg=theme["text_muted"],
    ).grid(row=1, column=0, sticky="w", pady=(4, 10))
    self.produto_entry = ttk.Combobox(product_box, font=("Segoe UI", 12 if compact_mode else 14))
    self.produto_entry.grid(row=2, column=0, sticky="ew", ipady=entry_ipady)

    if compact_mode:
        control_row = tk.Frame(left_card, bg=theme["surface"])
        control_row.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        control_row.columnconfigure(0, weight=1)
        control_row.columnconfigure(1, weight=1)

        quantity_box = tk.Frame(
            control_row,
            bg=blue_soft,
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground="#C9DEFF",
        )
        quantity_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        quantity_box.columnconfigure(0, weight=1)
        tk.Label(
            quantity_box,
            text="Quantidade",
            font=label_font,
            bg=blue_soft,
            fg=blue_strong,
        ).grid(row=0, column=0, sticky="w")
        self.quantidade_entry = tk.Entry(
            quantity_box,
            font=quantity_font,
            justify="center",
            relief="solid",
            bd=1,
            bg="#FFFFFF",
            fg=theme["text"],
            insertbackground=theme["text"],
            highlightthickness=1,
            highlightbackground="#B6D2FB",
            highlightcolor=blue_strong,
        )
        self.quantidade_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=quantity_ipady)
        self.quantidade_entry.insert(0, "1")

        add_box = tk.Frame(
            control_row,
            bg=theme["primary_soft"],
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        add_box.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        add_box.columnconfigure(0, weight=1)
        tk.Label(
            add_box,
            text="Ação principal",
            font=label_font,
            bg=theme["primary_soft"],
            fg=theme["primary_dark"],
        ).grid(row=0, column=0, sticky="w")
        self.btn_adicionar_item = tk.Button(
            add_box,
            text="Adicionar  Enter",
            font=("Segoe UI Semibold", 10),
            bg=theme["primary_dark"],
            fg=theme["text_on_dark"],
            activebackground=theme["primary"],
            activeforeground=theme["text_on_dark"],
            command=self.adicionar_item_carrinho,
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=9,
        )
        self.btn_adicionar_item.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        actions_grid = tk.Frame(left_card, bg=theme["surface"])
        actions_grid.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        for idx in range(3):
            actions_grid.columnconfigure(idx, weight=1)
        for idx in range(3):
            actions_grid.rowconfigure(idx, weight=1)

        def grid_button(parent, row, column, text, bg, fg, command, active_bg=None, span=1):
            btn = tk.Button(
                parent,
                text=text,
                font=action_font,
                bg=bg,
                fg=fg,
                activebackground=active_bg or bg,
                activeforeground=fg,
                command=command,
                relief="flat",
                cursor="hand2",
                bd=0,
                pady=8,
            )
            btn.grid(
                row=row,
                column=column,
                columnspan=span,
                sticky="ew",
                padx=3,
                pady=3,
            )
            return btn

        self.btn_add_f2 = grid_button(actions_grid, 0, 0, "Pesar F2", theme["accent"], theme["text_on_dark"], self.open_adicionar_item_dialog, theme["accent_dark"])
        self.btn_limpar_venda = grid_button(actions_grid, 0, 1, "Limpar F3", "#FFF4E7", theme["accent_dark"], self.limpar_venda, "#FFE9CC")
        self.btn_emitir_nota = grid_button(actions_grid, 0, 2, "Nota F4", blue_soft, blue_strong, self.show_note_dialog, "#DBEBFF")
        self.btn_finalizar_venda = grid_button(actions_grid, 1, 0, "Finalizar F5", theme["primary_dark"], theme["text_on_dark"], self.iniciar_finalizacao_venda, theme["primary"])
        self.btn_abrir_caixa = grid_button(actions_grid, 1, 1, "Abrir caixa", "#E4FFF0", theme["primary_dark"], self.abrir_caixa, "#D6F9E4")
        self.btn_fechar_caixa = grid_button(actions_grid, 1, 2, "Fechar caixa", olive_soft, olive_strong, self.fechar_caixa, "#E5F4CB")
        self.btn_fechar_sistema = grid_button(actions_grid, 2, 0, "Fechar sistema", theme["danger"], theme["text_on_dark"], self.on_closing, "#BF332D", span=3)
    else:
        lower_inputs = tk.Frame(left_card, bg=theme["surface"])
        lower_inputs.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        lower_inputs.columnconfigure(0, weight=1)
        lower_inputs.columnconfigure(1, weight=1)

        quantity_box = tk.Frame(
            lower_inputs,
            bg=blue_soft,
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightbackground="#C9DEFF",
        )
        quantity_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        quantity_box.columnconfigure(0, weight=1)
        tk.Label(quantity_box, text="Quantidade", font=label_font, bg=blue_soft, fg=blue_strong).grid(row=0, column=0, sticky="w")
        tk.Label(
            quantity_box,
            text="Peso ou unidade conforme o cadastro.",
            font=text_font,
            bg=blue_soft,
            fg=blue_strong,
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))
        self.quantidade_entry = tk.Entry(
            quantity_box,
            font=quantity_font,
            justify="center",
            relief="solid",
            bd=1,
            bg="#FFFFFF",
            fg=theme["text"],
            insertbackground=theme["text"],
            highlightthickness=1,
            highlightbackground="#B6D2FB",
            highlightcolor=blue_strong,
        )
        self.quantidade_entry.grid(row=2, column=0, sticky="ew", ipady=quantity_ipady)
        self.quantidade_entry.insert(0, "1")

        add_box = tk.Frame(
            lower_inputs,
            bg=theme["primary_soft"],
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        add_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        add_box.columnconfigure(0, weight=1)
        tk.Label(add_box, text="Ação principal", font=label_font, bg=theme["primary_soft"], fg=theme["primary_dark"]).grid(row=0, column=0, sticky="w")
        tk.Label(
            add_box,
            text="Confirme o item com Enter ou pelo botão abaixo.",
            font=text_font,
            bg=theme["primary_soft"],
            fg=theme["primary_dark"],
            wraplength=180 if compact_mode else 220,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))
        self.btn_adicionar_item = tk.Button(
            add_box,
            text="Adicionar item  Enter",
            font=("Segoe UI Semibold", 11 if compact_mode else 12),
            bg=theme["primary_dark"],
            fg=theme["text_on_dark"],
            activebackground=theme["primary"],
            activeforeground=theme["text_on_dark"],
            command=self.adicionar_item_carrinho,
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=10,
        )
        self.btn_adicionar_item.grid(row=2, column=0, sticky="ew")

        actions_grid = tk.Frame(left_card, bg=theme["surface"])
        actions_grid.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        for idx in range(2):
            actions_grid.columnconfigure(idx, weight=1)
        for idx in range(4):
            actions_grid.rowconfigure(idx, weight=1)

        def grid_button(parent, row, column, text, bg, fg, command, active_bg=None, span=1):
            btn = tk.Button(
                parent,
                text=text,
                font=action_font,
                bg=bg,
                fg=fg,
                activebackground=active_bg or bg,
                activeforeground=fg,
                command=command,
                relief="flat",
                cursor="hand2",
                bd=0,
                pady=9,
            )
            btn.grid(row=row, column=column, columnspan=span, sticky="ew", padx=4, pady=4)
            return btn

        self.btn_add_f2 = grid_button(actions_grid, 0, 0, "Pesar itens  F2", theme["accent"], theme["text_on_dark"], self.open_adicionar_item_dialog, theme["accent_dark"])
        self.btn_limpar_venda = grid_button(actions_grid, 0, 1, "Limpar venda  F3", "#FFF4E7", theme["accent_dark"], self.limpar_venda, "#FFE9CC")
        self.btn_emitir_nota = grid_button(actions_grid, 1, 0, "Emitir nota  F4", blue_soft, blue_strong, self.show_note_dialog, "#DBEBFF")
        self.btn_finalizar_venda = grid_button(actions_grid, 1, 1, "Finalizar venda  F5", theme["primary_dark"], theme["text_on_dark"], self.iniciar_finalizacao_venda, theme["primary"])
        self.btn_abrir_caixa = grid_button(actions_grid, 2, 0, "Abrir caixa", "#E4FFF0", theme["primary_dark"], self.abrir_caixa, "#D6F9E4")
        self.btn_fechar_caixa = grid_button(actions_grid, 2, 1, "Fechar caixa", olive_soft, olive_strong, self.fechar_caixa, "#E5F4CB")
        self.btn_fechar_sistema = grid_button(actions_grid, 3, 0, "Fechar sistema", theme["danger"], theme["text_on_dark"], self.on_closing, "#BF332D", span=2)

    right_card = tk.Frame(
        workspace,
        bg=theme["surface"],
        padx=panel_pad,
        pady=panel_pad,
        highlightthickness=1,
        highlightbackground=theme["card_edge"],
    )
    right_card.grid(row=0, column=1, sticky="nsew", padx=(section_gap, 0))
    right_card.columnconfigure(0, weight=1)
    right_card.rowconfigure(4, weight=1)
    tk.Frame(right_card, bg=theme["accent"], height=4).grid(row=0, column=0, sticky="ew")
    #tk.Label(
    #    right_card,
    #    text="Carrinho em tempo real",
    #    font=section_font,
    #    bg=theme["surface"],
    #    fg=theme["text"],
    #).grid(row=1, column=0, sticky="w", pady=(12, 4))
    #tk.Label(
    #    right_card,
    #    text=(
    #        "Visualização clara para editar, conferir e fechar."
    #        if compact_mode
    #        else "Visualização clara da venda para editar, conferir e fechar com segurança."
    #    ),
    #    font=text_font,
    #    bg=theme["surface"],
    #    fg=theme["text_muted"],
    #    wraplength=520 if compact_mode else 640,
    #    justify="left",
    #).grid(row=2, column=0, sticky="w", pady=(0, 12))

    header_row = tk.Frame(right_card, bg=theme["surface"])
    header_row.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    header_row.columnconfigure(0, weight=1)
    tk.Label(
        header_row,
        text="Itens da venda",
        font=("Segoe UI Semibold", 10),
        bg=theme["surface"],
        fg=theme["text_muted"],
    ).grid(row=0, column=0, sticky="w")

    table_wrap = tk.Frame(
        right_card,
        bg=theme["surface"],
        highlightthickness=1,
        highlightbackground=theme["border"],
    )
    table_wrap.grid(row=4, column=0, sticky="nsew")
    table_wrap.columnconfigure(0, weight=1)
    table_wrap.rowconfigure(0, weight=1)
    self.carrinho_tree = ttk.Treeview(
        table_wrap,
        columns=("Produto", "Quantidade", "Preco Unit.", "Subtotal"),
        show="headings",
        selectmode="browse",
    )
    self.carrinho_tree.heading("Produto", text="Produto")
    self.carrinho_tree.heading("Quantidade", text="Quantidade")
    self.carrinho_tree.heading("Preco Unit.", text="Preco Unit.")
    self.carrinho_tree.heading("Subtotal", text="Subtotal")
    self.carrinho_tree.column("Produto", width=260 if compact_mode else 340, anchor="w")
    self.carrinho_tree.column("Quantidade", width=120 if compact_mode else 135, anchor="center")
    self.carrinho_tree.column("Preco Unit.", width=110 if compact_mode else 125, anchor="e")
    self.carrinho_tree.column("Subtotal", width=120 if compact_mode else 135, anchor="e")
    self.carrinho_tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.carrinho_tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.carrinho_tree.configure(yscrollcommand=scrollbar.set)

    edit_row = tk.Frame(right_card, bg=theme["surface"])
    edit_row.grid(row=5, column=0, sticky="ew", pady=(12, 0))
    edit_row.columnconfigure(0, weight=1)
    edit_row.columnconfigure(1, weight=1)
    tk.Button(
        edit_row,
        text="Excluir item",
        bg=theme["danger"],
        fg=theme["text_on_dark"],
        activebackground="#BF332D",
        activeforeground=theme["text_on_dark"],
        command=self.delete_item_from_cart,
        relief="flat",
        cursor="hand2",
        font=action_font,
        bd=0,
        pady=10,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
    tk.Button(
        edit_row,
        text="Editar quantidade",
        bg=theme["accent"],
        fg=theme["text_on_dark"],
        activebackground=theme["accent_dark"],
        activeforeground=theme["text_on_dark"],
        command=self.edit_item_in_cart,
        relief="flat",
        cursor="hand2",
        font=action_font,
        bd=0,
        pady=10,
    ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

    self.total_label = tk.Label(
        self.caixa_frame,
        text=self.total_var.get(),
        font=total_font,
        bg=theme["bg"],
        fg=theme["bg"],
    )

    self.produto_entry.bind("<KeyRelease>", self.update_produto_list)
    self.produto_entry.bind("<Return>", self.adicionar_item_carrinho_event)
    self.bind_all("<F2>", lambda e: self.open_adicionar_item_dialog())
    self.bind_all("<F3>", lambda e: self.limpar_venda())
    self.bind_all("<F4>", lambda e: self.show_note_dialog())
    self.bind_all("<F5>", lambda e: self.iniciar_finalizacao_venda())
    self.produto_entry.focus_set()


create_caixa_layout = _create_caixa_layout_vibrant
create_relatorios_view = _create_relatorios_view_premium
create_relatorios_gerais_view = _create_relatorios_gerais_view_premium
