import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from PIL import Image, ImageTk

# Importações de dependências externas (conforme os teus ficheiros originais)
from balanca import BalancaSerial
from utils import resource_path
from dialogs import (
    CadastroProdutoDialog, CadastroFuncionarioDialog, EdicaoCarrinhoDialog,
    AdicionarItemDialog, EdicaoVendaDialog, OpenCloseCaixaDialog,
    ImprimirDialog, EmpresaInfoDialog, FinalizarVendaDialog
)
from database import (
    get_all_products, get_all_employees, get_daily_sales, 
    get_cash_register_status, get_company_info, add_product,
    update_product, add_employee, update_employee_db,
    add_sale, get_sale_by_id, delete_product, delete_employee_db
)

# =========================================================================
# CLASSES DE INTERFACE (VIEWS)
# =========================================================================

class GerenciaView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=controller.bg_color)
        self.controller = controller
        self._setup_layout()

    def _setup_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Título
        tk.Label(self, text="MENU DE GESTÃO", font=("Arial", 24, "bold"), 
                 bg=self.controller.bg_color, fg="#333").grid(row=0, column=0, pady=20)

        container = tk.Frame(self, bg=self.controller.bg_color)
        container.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        for i in range(3):
            container.columnconfigure(i, weight=1, uniform="tile")
            container.rowconfigure(i, weight=1, uniform="tile")

        tiles = [
            ("1. CAIXA\n(Vendas)", "#2196F3", "caixa", 0, 0),
            ("2. PRODUTOS\nCADASTRADOS", "#FF9800", "produtos", 0, 1),
            ("3. FUNCIONÁRIOS", "#8BC34A", "funcionarios", 0, 2),
            ("4. NOVO PRODUTO", "#E91E63", self.controller.open_cadastro_produto_dialog, 1, 0),
            ("5. NOVO FUNCIONÁRIO", "#00BCD4", self.controller.open_cadastro_funcionario_dialog, 1, 1),
            ("6. RELATÓRIOS", "#673AB7", "relatorios", 1, 2),
            ("7. EMPRESA", "#009688", "empresa", 2, 0),
            ("8. CONFIGURAÇÕES", "#607D8B", "config", 2, 1),
            ("9. SAIR", "#F44336", self.controller.quit, 2, 2)
        ]

        for text, color, cmd, r, c in tiles:
            action = (lambda m=cmd: self.controller.show_frame(m)) if isinstance(cmd, str) else cmd
            tk.Button(container, text=text, bg=color, fg="white", font=("Arial", 12, "bold"),
                      relief="flat", cursor="hand2", command=action).grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

# --- PRODUTOS VIEW ---
class ProdutosView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=controller.bg_color)
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        header = tk.Frame(self, bg=self["bg"])
        header.pack(fill="x", padx=20, pady=15)
        tk.Button(header, text="<< Voltar", command=lambda: self.controller.show_frame("gerencia"), 
                  bg="#777", fg="white", relief="flat").pack(side="left")
        tk.Label(header, text="PRODUTOS", font=("Arial", 18, "bold"), bg=self["bg"]).pack(side="left", padx=20)

        self.tree = ttk.Treeview(self, columns=("ID", "Nome", "Preço", "Estoque"), show='headings')
        for col in ("ID", "Nome", "Preço", "Estoque"): self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.controller.on_double_click_produto)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in get_all_products():
            self.tree.insert("", "end", values=(p[0], p[1], f"R$ {p[2]:.2f}", p[3]))

# --- CAIXA VIEW (PDV) ---
class CaixaView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=controller.bg_color)
        self.controller = controller
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(1, weight=3)
        self.rowconfigure(1, weight=1)

        # Barra Superior
        top = tk.Frame(self, bg=self["bg"])
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        tk.Button(top, text="<< Menu Principal", command=lambda: self.controller.show_frame("gerencia")).pack(side="left")

        # Painel Esquerdo
        left = tk.LabelFrame(self, text=" Lançamento ", bg="white", padx=10, pady=10)
        left.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        tk.Label(left, text="Produto:", bg="white").pack(anchor="w")
        self.produto_entry = ttk.Combobox(left, font=("Arial", 14))
        self.produto_entry.pack(fill="x", pady=5)
        
        tk.Label(left, text="Qtd:", bg="white").pack(anchor="w")
        self.qty_entry = tk.Entry(left, font=("Arial", 20), justify="center")
        self.qty_entry.pack(fill="x", pady=5)
        self.qty_entry.insert(0, "1")

        tk.Button(left, text="ADICIONAR (Enter)", bg="#2196F3", fg="white", 
                  command=self.controller.adicionar_item_carrinho, pady=10).pack(fill="x", pady=20)

        # Painel Direito (Carrinho)
        right = tk.LabelFrame(self, text=" Itens da Venda ", bg="white", padx=10, pady=10)
        right.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        self.tree = ttk.Treeview(right, columns=("Produto", "Qtd", "Total"), show="headings")
        for col in ("Produto", "Qtd", "Total"): self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        # Rodapé Total
        footer = tk.Frame(self, bg="#2c3e50", pady=20)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.total_lbl = tk.Label(footer, textvariable=self.controller.total_var, 
                                 font=("Arial", 36, "bold"), bg="#2c3e50", fg="#2ecc71")
        self.total_lbl.pack(side="left", padx=30)
        
        tk.Button(footer, text="FINALIZAR (F5)", bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
                  command=self.controller.iniciar_finalizacao_venda, padx=20).pack(side="right", padx=20)

# =========================================================================
# CONTROLLER PRINCIPAL
# =========================================================================

class FrutariaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão Comercial - Frutaria")
        self.geometry("1200x750")
        
        # Configurações Globais
        self.bg_color = "#F0F2F5"
        self.white_color = "#FFFFFF"
        self.total_var = tk.StringVar(value="R$ 0,00")
        self.carrinho_itens = []
        
        # Container de Telas
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self._init_all_views()
        self.show_frame("gerencia")
        self._bind_shortcuts()

    def _init_all_views(self):
        # Mapeamento de classes
        view_classes = {
            "gerencia": GerenciaView,
            "produtos": ProdutosView,
            "caixa": CaixaView
            # Adicione EmpresaView, FuncionariosView, etc., conforme criarmos as classes
        }
        
        for name, F in view_classes.items():
            frame = F(master=self.container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, page_name):
        frame = self.frames.get(page_name)
        if frame:
            frame.tkraise()
            if hasattr(frame, 'refresh'): frame.refresh()
            if page_name == "caixa": self.frames["caixa"].produto_entry.focus_set()

    def _bind_shortcuts(self):
        self.bind_all("<F5>", lambda e: self.iniciar_finalizacao_venda())
        self.bind_all("<Escape>", lambda e: self.show_frame("gerencia"))

    # --- Lógica de Negócio ---
    def adicionar_item_carrinho(self):
        # Implementar lógica de busca e adição aqui
        messagebox.showinfo("Caixa", "Funcionalidade de adição em processamento...")

    def iniciar_finalizacao_venda(self):
        if not self.carrinho_itens:
            messagebox.showwarning("Aviso", "Carrinho vazio!")
            return
        FinalizarVendaDialog(self, total=0.0, callback=None)

    def open_cadastro_produto_dialog(self):
        CadastroProdutoDialog(self, callback=lambda: self.show_frame("produtos"))

    def open_cadastro_funcionario_dialog(self):
        CadastroFuncionarioDialog(self, callback=None)

    def on_double_click_produto(self, event):
        # Lógica de edição ao clicar duas vezes
        pass

if __name__ == "__main__":
    app = FrutariaApp()
    app.mainloop()