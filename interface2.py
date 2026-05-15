#interface2

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Callable
from theme import APP_THEME

class GerenciaView(tk.Frame):
    """
    Representa a tela de Gerência com layout de Tiles.
    Implementa o princípio DRY (Don't Repeat Yourself).
    """
    
    TILE_FONT = ("Segoe UI Semibold", 13)
    TILE_CONFIG = {
        "relief": "flat",
        "width": 20,
        "height": 8,
        "cursor": "hand2"
    }

    def __init__(self, master, controller):
        super().__init__(master, bg=getattr(controller, 'bg_color', APP_THEME["bg"]))
        self.theme = APP_THEME
        self.controller = controller
        self._setup_layout()
        self._create_tiles()

    def _setup_layout(self):
        """Configura a estrutura de grid principal."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Container centralizado para os tiles
        self.container = tk.Frame(self, bg=self["bg"])
        self.container.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")

        # Configura 3 colunas e 3 linhas uniformes
        for i in range(3):
            self.container.columnconfigure(i, weight=1, uniform="tile")
            self.container.rowconfigure(i, weight=1, uniform="tile")

    def _create_tiles(self):
        """Define e renderiza os botões (tiles)."""
        
        # Mapa de dados dos tiles: facilita inclusão/exclusão futura
        tiles_data = [
            {"text": "1. CAIXA\n(Tela de Vendas)", "bg": "#2196F3", "cmd": "caixa", "row": 0, "col": 0},
            {"text": "2. PRODUTOS\nCADASTRADOS", "bg": "#FF9800", "cmd": "produtos_view", "row": 0, "col": 1},
            {"text": "3. FUNCIONÁRIOS\nCADASTRADOS", "bg": "#8BC34A", "cmd": "funcionarios_view", "row": 0, "col": 2},
            
            {"text": "4. CADASTRAR\nNOVO PRODUTO", "bg": "#E91E63", "cmd": self.controller.open_cadastro_produto_dialog, "row": 1, "col": 0},
            {"text": "5. CADASTRAR\nFUNCIONÁRIO", "bg": "#00BCD4", "cmd": self.controller.open_cadastro_funcionario_dialog, "row": 1, "col": 1},
            {"text": "6. RELATÓRIOS\nDE VENDAS", "bg": "#673AB7", "cmd": "relatorios_view", "row": 1, "col": 2},
            
            {"text": "7. DADOS DA\nEMPRESA", "bg": "#009688", "cmd": self._abrir_empresa, "row": 2, "col": 0},
            {"text": "8. CONFIGURAR\nSISTEMA", "bg": "#607D8B", "cmd": "config_view", "row": 2, "col": 1},
            {"text": "9. SAIR\nDO APP", "bg": "#F44336", "cmd": self.controller.quit, "row": 2, "col": 2},
        ]

        for tile in tiles_data:
            self._build_button(tile)

    def _build_button(self, data: Dict):
        """Constrói um botão individual baseado no dicionário de dados."""
        
        # Resolve o comando: se for string, chama show_frame, se for função, executa-a
        if isinstance(data["cmd"], str):
            action = lambda: self.controller.show_frame(data["cmd"])
        else:
            action = data["cmd"]

        btn = tk.Button(
            self.container,
            text=data["text"],
            bg=data["bg"],
            fg="white",
            font=self.TILE_FONT,
            command=action,
            **self.TILE_CONFIG
        )
        
        # Efeito Hover Simples (Feedback Visual)
        base_bg = data["bg"]
        btn.bind("<Enter>", lambda _e, b=btn: b.config(relief="groove"))
        btn.bind("<Leave>", lambda _e, b=btn: b.config(relief="flat"))
        
        btn.grid(
            row=data["row"], 
            column=data["col"], 
            padx=10, 
            pady=10, 
            sticky="nsew"
        )

    def _abrir_empresa(self):
        """Encapsula múltiplas chamadas de comando em um único método."""
        self.controller.show_frame("empresa_view")
        if hasattr(self.controller, 'carregar_dados_empresa_na_tela'):
            self.controller.carregar_dados_empresa_na_tela()

class ProdutosView(tk.Frame):
    """
    View responsável pela listagem e gestão visual de produtos.
    Aplica o padrão Data-to-View para formatação de valores.
    """
    
    COLUMNS = {
        "ID": {"width": 50, "anchor": tk.CENTER},
        "Nome do Produto": {"width": 250, "anchor": tk.W},
        "Preço (R$)": {"width": 100, "anchor": tk.E},
        "Estoque": {"width": 80, "anchor": tk.CENTER},
        "Unidade": {"width": 80, "anchor": tk.CENTER},
        "SKU": {"width": 120, "anchor": tk.CENTER},
        "Cód. Barras": {"width": 150, "anchor": tk.CENTER}
    }

    def __init__(self, master, controller):
        # Assumindo que controller possui as propriedades de cor
        super().__init__(master, bg=getattr(controller, 'bg_color', '#f5f5f5'))
        self.controller = controller
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        # Remova ou comente a linha self.pack(...)
        # self.pack(fill="both", expand=True) 

        # Continue com o restante da montagem interna
        content = tk.Frame(self, bg=self.controller.bg_color)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        # ... resto do código
        
        # Header (Usando o padrão de composição)
        header = tk.Frame(self, bg=self["bg"])
        header.pack(fill="x", padx=20, pady=15)
        
        tk.Button(
            header, text="<< Voltar", 
            command=lambda: self.controller.show_frame("gerencia"),
            bg="#E7ECE4", fg="#17301F", relief="flat", cursor="hand2", font=("Segoe UI Semibold", 10), padx=14, pady=8
        ).pack(side="left")
        
        tk.Label(
            header, text="PRODUTOS CADASTRADOS", 
            font=("Segoe UI Semibold", 20), fg="#0F8F47", bg=self["bg"]
        ).pack(side="left", padx=20)

        # Treeview Container
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tree = ttk.Treeview(
            tree_frame, 
            columns=list(self.COLUMNS.keys()), 
            show='headings',
            selectmode="browse"
        )
        
        # Configuração dinâmica de colunas
        for col, config in self.COLUMNS.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=config["width"], anchor=config["anchor"])

        # Scrollbar com design integrado
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Eventos
        self.tree.bind("<Double-1>", self._on_item_double_click)

    def _format_value(self, value, unit):
        """Centraliza a lógica de formatação de negócios."""
        if unit == 'kg':
            return f"{value:.3f}".replace('.', ',')
        return f"{int(value)}"

    def refresh_data(self):
        """Limpa e recarrega os dados do banco na Treeview."""
        # Limpeza eficiente
        self.tree.delete(*self.tree.get_children())
        
        try:
            # A importação do banco deve preferencialmente ser via controller ou service layer
            from database import get_all_products
            produtos = get_all_products()
            
            for prod in produtos:
                # Mapeamento: ID, Nome, Preço, Qtd, Unidade, SKU, EAN
                id_p, nome, preco, qtd, unidade, sku, ean = prod
                
                self.tree.insert("", tk.END, values=(
                    id_p,
                    nome.upper(),
                    f"R$ {preco:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    self._format_value(qtd, unidade),
                    unidade,
                    sku,
                    ean
                ))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro de Banco", f"Falha ao carregar produtos: {e}")

    def _on_item_double_click(self, event):
        """Handler para duplo clique delegando para o controller."""
        item_id = self.tree.focus()
        if item_id:
            item_data = self.tree.item(item_id)['values']
            if hasattr(self.controller, 'on_double_click_produto'):
                self.controller.on_double_click_produto(item_data)

class FuncionariosView(tk.Frame):
    """
    View para listagem e gestão de funcionários.
    Utiliza injeção de dependência via controller para ações de UI.
    """
    
    # Definição declarativa das colunas para facilitar ajustes de layout
    COLUMN_DEFS = {
        "ID": {"width": 60, "anchor": tk.CENTER, "stretch": tk.NO},
        "Nome Completo": {"width": 300, "anchor": tk.W, "stretch": tk.YES},
        "Username": {"width": 150, "anchor": tk.W, "stretch": tk.YES},
        "Cargo": {"width": 120, "anchor": tk.CENTER, "stretch": tk.YES}
    }

    def __init__(self, master, controller):
        super().__init__(master, bg=getattr(controller, 'bg_color', '#f0f0f0'))
        self.controller = controller
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        """Constrói a interface de forma modular."""
        #self.pack(fill="both", expand=True)
        
        # --- Container de Conteúdo ---
        content = tk.Frame(self, bg=self["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Cabeçalho ---
        header = tk.Frame(content, bg=self["bg"])
        header.pack(fill="x", pady=(0, 20))
        
        tk.Button(
            header, text="<< Voltar", 
            command=lambda: self.controller.show_frame("gerencia"),
            bg="#777", fg="white", relief="flat", cursor="hand2",
            padx=10
        ).pack(side="left")
        
        tk.Label(
            header, text="FUNCIONÁRIOS CADASTRADOS", 
            font=("Segoe UI Semibold", 20), fg="#1F9D55", bg=self["bg"]
        ).pack(side="left", padx=20)

        # --- Área da Tabela (Treeview) ---
        table_container = tk.Frame(content)
        table_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_container, 
            columns=list(self.COLUMN_DEFS.keys()), 
            show='headings',
            selectmode="browse"
        )
        
        # Configuração de Colunas via Metadados
        for col, settings in self.COLUMN_DEFS.items():
            self.tree.heading(col, text=col)
            self.tree.column(
                col, 
                width=settings["width"], 
                anchor=settings["anchor"], 
                stretch=settings["stretch"]
            )

        # Scrollbar Integrada
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Bindings
        self.tree.bind("<Double-1>", self._on_double_click)

    def refresh_data(self):
        """Recarrega os dados do banco de dados com tratamento de erro."""
        # Limpa a Treeview de forma eficiente
        self.tree.delete(*self.tree.get_children())
        
        try:
            from database import get_all_employees
            # Camada de Dados: Buscando tuplas (id, nome, usuario, cargo)
            funcionarios = get_all_employees()
            
            for func in funcionarios:
                self.tree.insert("", tk.END, values=(
                    func[0], # ID
                    func[1], # Nome
                    func[2], # Usuário
                    str(func[3]).upper() # Cargo em caixa alta para padronização visual
                ))
                
        except Exception as e:
            messagebox.showerror("Erro de Dados", f"Não foi possível carregar funcionários: {str(e)}")

    def _on_double_click(self, event):
        """Delega o evento de seleção para o controller principal."""
        selection = self.tree.focus()
        if not selection:
            return
            
        item_data = self.tree.item(selection)['values']
        if hasattr(self.controller, 'on_double_click_employee'):
            self.controller.on_double_click_employee(item_data)

class RelatoriosView(tk.Frame):
    """
    View para gestão de relatórios de vendas.
    Inclui ações de CRUD e exportação delegadas ao controller.
    """
    
    COLUMNS = {
        "ID": {"width": 60, "anchor": tk.CENTER},
        "Data": {"width": 150, "anchor": tk.CENTER},
        "Total (R$)": {"width": 120, "anchor": tk.E},
        "Itens Vendidos": {"width": 450, "anchor": tk.W}
    }

    def __init__(self, master, controller):
        super().__init__(master, bg=getattr(controller, 'bg_color', '#f0f0f0'))
        self.controller = controller
        # Injeção de cores para evitar AttributeErrors
        self.colors = {
            "primary": getattr(controller, 'bg_color1', '#2196F3'),
            "white": getattr(controller, 'white_color', '#ffffff'),
            "black": getattr(controller, 'black_color', '#000000'),
            "danger": "#F44336",
            "warning": "#FFC107",
            "accent": "#FF9800"
        }
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface usando o sistema de Grid."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- Header ---
        header = tk.Frame(self, bg=self["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        tk.Button(
            header, text="<< Voltar", 
            command=lambda: self.controller.show_frame("gerencia"),
            bg="#E7ECE4", fg="#17301F", relief="flat", cursor="hand2", font=("Segoe UI Semibold", 10), padx=14, pady=8
        ).pack(side="left")
        
        tk.Label(
            header, text="RELATÓRIO DE VENDAS", 
            font=("Arial", 20, "bold"), fg="#388E3C", bg=self["bg"]
        ).pack(side="left", padx=20)

        # --- Main Content Frame ---
        content = tk.Frame(self, bg=self.colors["white"], relief="solid", bd=1)
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # --- Treeview ---
        self.tree = ttk.Treeview(content, columns=list(self.COLUMNS.keys()), show="headings")
        for col, config in self.COLUMNS.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=config["width"], anchor=config["anchor"])

        self.tree.grid(row=0, column=0, sticky="nsew")
        
        sb = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        # --- Button Bar ---
        self._create_action_buttons(content)

        # Eventos
        self.tree.bind("<Double-1>", lambda e: self.controller.show_sale_details(e))

    def _create_action_buttons(self, parent):
        """Cria e organiza os botões de ação abaixo da tabela."""
        btn_container = tk.Frame(parent, bg=self["bg"])
        btn_container.grid(row=1, column=0, columnspan=2, pady=15, sticky="ew")
        
        # Frame interno para centralização real sem 'spacer columns'
        inner_box = tk.Frame(btn_container, bg=self["bg"])
        inner_box.pack(expand=True)

        buttons = [
            ("Atualizar Relatório", self.colors["primary"], self.colors["white"], self.refresh_data),
            ("Emitir Relatório", self.colors["accent"], self.colors["black"], self.controller.show_report_print_menu),
            ("Editar Venda", self.colors["warning"], self.colors["black"], self._safe_edit),
            ("Excluir Venda", self.colors["danger"], self.colors["white"], self._safe_delete)
        ]

        for text, bg, fg, cmd in buttons:
            tk.Button(
                inner_box, text=text, font=("Arial", 11),
                bg=bg, fg=fg, relief="flat", cursor="hand2",
                command=cmd, padx=15, pady=5
            ).pack(side="left", padx=5)

    def refresh_data(self):
        """Ponto de entrada para atualização de dados."""
        self.tree.delete(*self.tree.get_children())
        if hasattr(self.controller, 'update_daily_sales_report'):
            self.controller.update_daily_sales_report()

    def _get_selection(self):
        """Helper para obter o item selecionado."""
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Seleção", "Por favor, selecione uma venda na lista.")
            return None
        return self.tree.item(sel)['values']

    def _safe_edit(self):
        data = self._get_selection()
        if data: self.controller.edit_sale(data)

    def _safe_delete(self):
        data = self._get_selection()
        if data: self.controller.delete_sale(data)


class CaixaView(tk.Frame):
    """
    Interface do Ponto de Venda (PDV).
    Focada em performance de entrada de dados e atalhos de teclado.
    """

    def __init__(self, master, controller):
        super().__init__(master, bg=getattr(controller, 'bg_color', '#f0f0f0'))
        self.controller = controller
        
        # Variáveis de Controle
        self.total_var = getattr(controller, 'total_var', tk.StringVar(value="R$ 0,00"))
        
        self._setup_layout()
        self._create_widgets()
        self._setup_bindings()

    def _setup_layout(self):
        """Define a estrutura de pesos do grid principal."""
        self.columnconfigure(0, weight=1) # Coluna de comandos/inputs
        self.columnconfigure(1, weight=3) # Coluna do carrinho (maior)
        self.rowconfigure(2, weight=1)    # Área central expande

    def _create_widgets(self):
        """Instancia os componentes visuais divididos por zonas."""
        
        # 1. BARRA DE CONTROLE (Topo)
        ctrl_frame = tk.Frame(self, bg=self["bg"])
        ctrl_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.btn_abrir = self._build_btn(ctrl_frame, "🔓 Abrir Caixa", "#008419", self.controller.abrir_caixa)
        self.btn_fechar = self._build_btn(ctrl_frame, "🔒 Fechar Caixa", "#F44336", self.controller.fechar_caixa)
        self.btn_abrir.pack(side="left", padx=10)
        self.btn_fechar.pack(side="left")

        # 2. PAINEL DE ENTRADA (Esquerda)
        input_panel = tk.LabelFrame(self, text=" Lançamento Rápido ", font=("Arial", 10, "bold"), bg="white", padx=15, pady=15)
        input_panel.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        tk.Label(input_panel, text="Produto (Nome/SKU):", bg="white").pack(anchor="w")
        self.produto_entry = ttk.Combobox(input_panel, font=("Arial", 16))
        self.produto_entry.pack(fill="x", pady=(5, 15))

        tk.Label(input_panel, text="Quantidade:", bg="white").pack(anchor="w")
        self.quantidade_entry = tk.Entry(input_panel, font=("Arial", 24, "bold"), justify="center", bd=2)
        self.quantidade_entry.pack(fill="x", pady=(5, 15))
        self.quantidade_entry.insert(0, "1")

        self.btn_add = tk.Button(input_panel, text="➕ ADICIONAR (Enter)", font=("Arial", 12, "bold"),
                               bg="#2196F3", fg="white", relief="flat", pady=10,
                               command=self.controller.adicionar_item_carrinho)
        self.btn_add.pack(fill="x", pady=10)

        # 3. CARRINHO (Direita)
        cart_panel = tk.LabelFrame(self, text=" Itens da Venda ", font=("Arial", 10, "bold"), bg="white", padx=10, pady=10)
        cart_panel.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        
        self.tree = ttk.Treeview(cart_panel, columns=("Item", "Produto", "Qtd", "Preço", "Subtotal"), show="headings")
        self._setup_treeview()
        
        # Scrollbar e Treeview pack
        sb = ttk.Scrollbar(cart_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # 4. RODAPÉ (Total e Atalhos)
        footer = tk.Frame(self, bg="#2c3e50", pady=20)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        self.lbl_total = tk.Label(footer, textvariable=self.total_var, font=("Arial", 36, "bold"), 
                                 bg="#2c3e50", fg="#2ecc71")
        self.lbl_total.pack(side="left", padx=30)

        # Container de botões F2-F5
        btn_box = tk.Frame(footer, bg="#2c3e50")
        btn_box.pack(side="right", padx=20)
        
        self._create_f_buttons(btn_box)

    def _build_btn(self, master, text, color, cmd, width=None):
        """Helper para criar botões padronizados."""
        return tk.Button(master, text=text, bg=color, fg="white", font=("Arial", 10, "bold"),
                         relief="flat", command=cmd, padx=15, pady=5, width=width)

    def _setup_treeview(self):
        """Configura as colunas da tabela de itens."""
        cols = {"Item": 50, "Produto": 300, "Qtd": 80, "Preço": 100, "Subtotal": 100}
        for col, width in cols.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center" if col != "Produto" else "w")

    def _create_f_buttons(self, master):
        """Cria a fileira de botões de atalho."""
        actions = [
            ("PESAR (F2)", "#34495e", self.controller.open_adicionar_item_dialog),
            ("LIMPAR (F3)", "#7f8c8d", self.controller.limpar_venda),
            ("NOTA (F4)", "#f39c12", self.controller.show_note_dialog),
            ("FINALIZAR (F5)", "#27ae60", self.controller.iniciar_finalizacao_venda)
        ]
        for txt, color, cmd in actions:
            btn = tk.Button(master, text=txt, bg=color, fg="white", font=("Arial", 9, "bold"),
                           relief="flat", width=12, pady=12, command=cmd)
            btn.pack(side="left", padx=3)

    def _setup_bindings(self):
        """Configura os gatilhos de teclado."""
        self.produto_entry.bind('<KeyRelease>', self.controller.update_produto_list)
        self.produto_entry.bind('<Return>', lambda e: self.controller.adicionar_item_carrinho())
        
        # Bindings focados no frame (melhor que bind_all para evitar disparos acidentais)
        self.bind_all("<F2>", lambda e: self.controller.open_adicionar_item_dialog())
        self.bind_all("<F3>", lambda e: self.controller.limpar_venda())
        self.bind_all("<F4>", lambda e: self.controller.show_note_dialog())
        self.bind_all("<F5>", lambda e: self.controller.iniciar_finalizacao_venda())

    def focus_entry(self):
        """Método utilitário para resetar o foco."""
        self.produto_entry.focus_set()


class EmpresaView(tk.Frame):
    """
    View para configuração dos dados da empresa e logotipo.
    Organizada em colunas para melhor aproveitamento de telas widescreen.
    """

    def __init__(self, master, controller):
        super().__init__(master, bg=getattr(controller, 'bg_color', '#f0f0f0'))
        self.controller = controller
        
        # Cores padronizadas
        self.white = getattr(controller, 'white_color', '#ffffff')
        self.accent = getattr(controller, 'bg_color1', '#2196F3')

        self._setup_layout()
        self._create_widgets()

    def _setup_layout(self):
        """Configura a estrutura responsiva principal."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Conteúdo central expande

    def _create_widgets(self):
        # --- HEADER ---
        header = tk.Frame(self, bg=self["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        tk.Button(header, text="<< Voltar", 
                  command=lambda: self.controller.show_frame("gerencia"),
                  bg="#777", fg="white", relief="flat", cursor="hand2"
                 ).pack(side="left")
        
        tk.Label(header, text="CONFIGURAÇÃO DA EMPRESA", font=("Arial", 20, "bold"), 
                 fg=self.accent, bg=self["bg"]).pack(side="left", padx=20)

        # --- CONTEÚDO (CARD BRANCO) ---
        card = tk.Frame(self, bg=self.white, padx=30, pady=30, relief="solid", bd=1)
        card.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        card.columnconfigure(0, weight=3) # Coluna de Campos
        card.columnconfigure(1, weight=1) # Coluna da Logo

        # --- COLUNA ESQUERDA: FORMULÁRIO ---
        self.frm_campos = tk.Frame(card, bg=self.white)
        self.frm_campos.grid(row=0, column=0, sticky="nsew", padx=(0, 30))
        self.frm_campos.columnconfigure(0, weight=1)

        self._build_form()

        # --- COLUNA DIREITA: LOGO ---
        self.frm_logo = tk.Frame(card, bg=self.white)
        self.frm_logo.grid(row=0, column=1, sticky="nsew")
        self._build_logo_section()

        # --- RODAPÉ: BOTÕES ---
        self.footer = tk.Frame(self, bg=self["bg"])
        self.footer.grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        self.footer.columnconfigure((0, 1), weight=1)

    def _build_form(self):
        """Constrói os campos de entrada de dados."""
        # Dados Básicos
        self.ent_nome = self._add_entry("Nome Fantasia:", 0)
        self.ent_razao = self._add_entry("Razão Social:", 2)
        self.ent_cnpj = self._add_entry("CNPJ:", 4, mask="cnpj")
        
        # Endereço Complexo (Grid Interno)
        self._add_label("Endereço (Rua, Nº, Bairro):", 6)
        self.ent_endereco = tk.Entry(self.frm_campos, font=("Arial", 12))
        self.ent_endereco.grid(row=7, column=0, sticky="ew", ipady=5)

        # CEP / Cidade / UF
        detalhes_frame = tk.Frame(self.frm_campos, bg=self.white)
        detalhes_frame.grid(row=8, column=0, sticky="ew", pady=(10, 0))
        detalhes_frame.columnconfigure(1, weight=1) # Cidade expande

        self.ent_cep = self._inner_entry(detalhes_frame, "CEP:", 0, 0, width=12, mask="cep")
        self.ent_cidade = self._inner_entry(detalhes_frame, "Cidade:", 0, 1)
        self.ent_uf = self._inner_entry(detalhes_frame, "UF:", 0, 2, width=5)

        # Contato
        self.ent_email = self._add_entry("E-mail:", 10)
        self.ent_telefone = self._add_entry("Telefone / WhatsApp:", 12, mask="tel")

    def _build_logo_section(self):
        """Área dedicada ao upload e preview da logo."""
        tk.Label(self.frm_logo, text="Logotipo da Empresa", font=("Arial", 12, "bold"), 
                 bg=self.white).pack(pady=(0, 10))
        
        self.preview_container = tk.Frame(self.frm_logo, bg="#E0E0E0", bd=2, relief="sunken", height=200)
        self.preview_container.pack(fill="x", pady=10)
        self.preview_container.pack_propagate(False)

        self.lbl_logo_preview = tk.Label(self.preview_container, text="Sem Logo\nSelecionado", bg="#E0E0E0")
        self.lbl_logo_preview.pack(expand=True, fill="both")

        self.btn_upload = tk.Button(self.frm_logo, text="Carregar Imagem", bg=self.accent, fg="white",
                                   command=self.controller.selecionar_logo, relief="flat", pady=8, cursor="hand2")
        self.btn_upload.pack(fill="x", pady=10)
        
        tk.Label(self.frm_logo, text="(PNG/JPG quadrado, máx 300x300)", font=("Arial", 8), 
                 fg="#888", bg=self.white).pack()

    # --- HELPERS DE INTERFACE ---
    def _add_label(self, text, row):
        tk.Label(self.frm_campos, text=text, font=("Arial", 10, "bold"), fg="#555", 
                 bg=self.white).grid(row=row, column=0, sticky="w", pady=(10, 2))

    def _add_entry(self, label, row, mask=None):
        self._add_label(label, row)
        entry = tk.Entry(self.frm_campos, font=("Arial", 12))
        entry.grid(row=row + 1, column=0, sticky="ew", ipady=5)
        if mask: self._bind_mask(entry, mask)
        return entry

    def _inner_entry(self, parent, label, row, col, width=None, mask=None):
        container = tk.Frame(parent, bg=self.white)
        container.grid(row=row, column=col, sticky="ew", padx=2)
        tk.Label(container, text=label, font=("Arial", 9, "bold"), bg=self.white).pack(anchor="w")
        entry = tk.Entry(container, font=("Arial", 12), width=width)
        entry.pack(fill="x", ipady=3)
        if mask: self._bind_mask(entry, mask)
        return entry

    def _bind_mask(self, entry, mask_type):
        """Associa funções de máscara do controller ao widget."""
        mask_map = {
            "cnpj": "aplicar_mascara_cnpj",
            "cep": "aplicar_mascara_cep",
            "tel": "aplicar_mascara_telefone"
        }
        method_name = mask_map.get(mask_type)
        if hasattr(self.controller, method_name):
            entry.bind('<KeyRelease>', getattr(self.controller, method_name))