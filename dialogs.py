#dialogs
# dialogs.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime
import sqlite3, ast
import json
import os
import sys
import time
import shutil # Para copiar a imagem da logo
# Importe a função de troco (se a colocou no utils.py)
from utils import calcular_troco, get_app_icon_path, resource_path # Certifique-se de importar calcular_troco
from theme import APP_THEME
# Importa as funções do banco de dados
from database import (
    get_db_connection, setup_database, add_product, get_all_products, get_product_by_id, get_product_by_name, get_product_by_name_balaca, get_product_by_sku, get_product_by_barcode, get_product_by_code,
    update_product, filter_products_for_combobox, delete_product_db, add_employee, get_all_employees,get_employee_by_id,
    get_employee_by_username_and_password, is_manager, update_product_stock,
    add_sale, get_daily_sales, verify_and_add_initial_users,
    delete_sale_db, update_sale_db, get_sale_by_id,
    delete_employee_db, update_employee_db,
    get_cash_register_status, open_cash_register_db, close_cash_register_db,
    get_daily_sales_total, get_open_cash_register_initial_value, get_company_info, save_company_info
)


def dialog_theme(controller=None):
    theme = dict(APP_THEME)
    if controller is not None:
        theme.update({
            "bg": getattr(controller, "bg_color", theme["bg"]),
            "surface": getattr(controller, "white_color", theme["surface"]),
            "primary": getattr(controller, "bg_color1", theme["primary"]),
            "text": getattr(controller, "text_color", theme["text"]),
            "danger": getattr(controller, "error_color", theme["danger"]),
            "success": getattr(controller, "success_color", theme["success"]),
        })
    return theme


def setup_dialog_window(window, parent, title, size):
    window.title(title)
    window.transient(parent)
    window.grab_set()
    try:
        window.iconphoto(False, parent.icon_tk)
    except Exception:
        try:
            icon_image = Image.open(get_app_icon_path())
            window.icon_tk = ImageTk.PhotoImage(icon_image)
            window.iconphoto(False, window.icon_tk)
        except Exception:
            pass
    width, height = size
    window.geometry(f"{width}x{height}")
    window.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def build_dialog_shell(window, parent, title=None, subtitle=None, size=(760, 420), controller=None):
    theme = dialog_theme(controller or parent)
    setup_dialog_window(window, parent, title or "", size)
    window.configure(bg=theme["bg"])

    outer = tk.Frame(window, bg=theme["bg"], padx=18, pady=18)
    outer.pack(fill="both", expand=True)

    card = tk.Frame(outer, bg=theme["surface"], padx=22, pady=22, relief="flat", bd=0, highlightthickness=1, highlightbackground=theme["border"])
    card.pack(fill="both", expand=True)

    if title or subtitle:
        header = tk.Frame(card, bg=theme["surface"])
        header.pack(fill="x", pady=(0, 16))
        if title:
            tk.Label(header, text=title, font=("Segoe UI Semibold", 20), bg=theme["surface"], fg=theme["text"]).pack(anchor="w")
        if subtitle:
            tk.Label(
                header,
                text=subtitle,
                font=("Segoe UI", 10),
                bg=theme["surface"],
                fg=theme["text_muted"],
                wraplength=max(size[0] - 160, 280),
                justify="left",
            ).pack(anchor="w", pady=(6 if title else 0, 0))

    body = tk.Frame(card, bg=theme["surface"])
    body.pack(fill="both", expand=True)
    return theme, card, body


def make_form_label(parent, text, theme):
    return tk.Label(parent, text=text, font=("Segoe UI Semibold", 10), bg=theme["surface"], fg=theme["text"])


def make_entry(parent, theme, **kwargs):
    return tk.Entry(parent, font=("Segoe UI", 11), bg="#FFFFFF", fg=theme["text"], insertbackground=theme["text"], relief="solid", bd=1, highlightthickness=1, highlightbackground=theme["border"], highlightcolor=theme["primary"], **kwargs)


def style_button(button, role, theme):
    palette = {
        "primary": (theme["primary"], theme["text_on_dark"]),
        "danger": (theme["danger"], theme["text_on_dark"]),
        "secondary": (theme["surface_alt"], theme["text"]),
        "warning": (theme["accent"], theme["text_on_dark"]),
        "success": (theme["success"], theme["text_on_dark"]),
    }
    bg, fg = palette.get(role, palette["secondary"])
    button.configure(bg=bg, fg=fg, relief="flat", cursor="hand2", font=("Segoe UI Semibold", 10), padx=14, pady=10, activebackground=bg, activeforeground=fg)
    return button


from balanca import BalancaSerial # 📌 IMPORTAR BALANCA

# classe cadastro de produtos
class CadastroProdutoDialog(tk.Toplevel):
    def __init__(self, parent, controller, product_data=None):
        # Inicializa a Toplevel (nova janela)
        super().__init__(parent)
        self.controller = controller

        # 📌 2. Adicione este código para aplicar o ícone da janela principal
        try:
            # Acessa o objeto PhotoImage (parent.icon_tk) que deve estar na janela principal
            self.iconphoto(False, parent.icon_tk) 
        except Exception:
            # Ignora se falhar, o ícone principal não é crucial para o funcionamento
            pass 

        # Armazena os dados do produto para edição
        self.product_data = product_data 
        self.is_editing = product_data is not None
        self.transient(parent)  # Mantém a janela no topo da principal
        self.grab_set()         # Bloqueia interação com a janela principal

        # Título dinâmico
        if self.is_editing:
             self.title("Editar Produto")
        else:
             self.title("Cadastrar Novo Produto")
             
        self.configure(bg=controller.bg_color)

        # 📌 AQUI VOCÊ DEFINE A LARGURA E ALTURA DA JANELA:
        self.geometry("900x450")
        # Se quiser um pouco mais alta para comportar todo o formulário:
        # self.geometry("600x350")

        # Centraliza a janela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

        # Chama a função para construir o formulário
        self.create_form_widgets()

    def create_form_widgets(self):
        # Replicamos o layout do formulário original aqui
        cadastro_produto_frame = tk.Frame(self, bg=self.controller.white_color, padx=15, pady=15, relief="solid", bd=1)
        cadastro_produto_frame.pack(padx=20, pady=20, fill="both", expand=True)
        cadastro_produto_frame.columnconfigure(0, weight=1)

        # TÍTULO DINÂMICO
        title_text = "EDITAR PRODUTO" if self.is_editing else "CADASTRAR PRODUTO"
        tk.Label(cadastro_produto_frame, text=title_text, font=("Arial", 20, "bold"), 
                 bg=self.controller.white_color, fg=self.controller.bg_color1).grid(row=0, column=0, pady=5, sticky="ew")
        
        form_frame = tk.Frame(cadastro_produto_frame, bg=self.controller.white_color)
        form_frame.grid(row=1, column=0, sticky="ew", padx=10)
        
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        
         # --- Linhas do Formulário (o layout dos campos permanece o mesmo) ---
        # Nome e Cód. Barras
        tk.Label(form_frame, text="Nome:", bg=self.controller.white_color).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.produto_nome_entry = tk.Entry(form_frame)
        self.produto_nome_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form_frame, text="Cód. Barras:", bg=self.controller.white_color).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.cod_barras_entry = tk.Entry(form_frame)
        self.cod_barras_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Preço e Estoque
        tk.Label(form_frame, text="Preço (R$):", bg=self.controller.white_color).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.produto_preco_entry = tk.Entry(form_frame)
        self.produto_preco_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        tk.Label(form_frame, text="Estoque (kg/un):", bg=self.controller.white_color).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.produto_estoque_entry = tk.Entry(form_frame)
        self.produto_estoque_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Unidade e SKU
        tk.Label(form_frame, text="Unidade:", bg=self.controller.white_color).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.produto_unidade_entry = ttk.Combobox(form_frame, values=["kg", "un"])
        self.produto_unidade_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.produto_unidade_entry.set("un")
        
        tk.Label(form_frame, text="SKU:", bg=self.controller.white_color).grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.sku_entry = tk.Entry(form_frame)
        self.sku_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

        # --- PREENCHIMENTO DOS DADOS (NOVO) ---
        # --- PREENCHIMENTO DOS DADOS (NOVO) ---
        if self.is_editing:
            # ORDEM CORRETA DO DB: (id, nome, preco, estoque, unidade, cod_barras[5], sku[6])
            data = self.product_data
            
            self.produto_nome_entry.insert(0, data[1]) # nome
            self.produto_preco_entry.insert(0, f"{data[2]:.2f}".replace('.', ',')) # preco
            self.produto_estoque_entry.insert(0, f"{data[3]:.2f}".replace('.', ',')) # estoque
            self.produto_unidade_entry.set(data[4]) # unidade
            
            # 📌 CORREÇÃO PARA CÓD. BARRAS: Converte para string vazia se for None
            cod_barras_str = str(data[5]) if data[5] is not None else ""
            self.cod_barras_entry.insert(0, cod_barras_str)
            
            # 📌 CORREÇÃO PARA SKU: Converte para string vazia se for None
            sku_str = str(data[6]) if data[6] is not None else ""
            self.sku_entry.insert(0, sku_str)



        # --- Frame de Ações ---
        action_frame = tk.Frame(cadastro_produto_frame, bg=self.controller.white_color)
        action_frame.grid(row=2, column=0, pady=15, sticky="ew") 
        
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        # 📌 Cor e Texto Dinâmicos
        btn_text = "Salvar Alterações" if self.is_editing else "Adicionar Produto"
        
        # Cor Única de Sucesso (Verde) para ambas as ações de salvar
        btn_bg_color = "#008419" # Verde-padrão de sucesso (ou use self.controller.bg_color1)


        btn_add_produto = tk.Button(action_frame, text=btn_text, 
                                     font=("Arial", 12), 
                                     bg=btn_bg_color, # Usando a cor dinâmica ou padrão
                                     fg=self.controller.white_color, 
                                     command=self.salvar_e_fechar, relief="flat")
        btn_add_produto.grid(row=0, column=0, padx=5, sticky="e") 

        # Botão CANCELAR 
        btn_cancelar = tk.Button(action_frame, text="Cancelar",
                                 font=("Arial", 12), 
                                 bg="#F44336",
                                 fg=self.controller.white_color, 
                                 command=self.destroy, relief="flat")
        btn_cancelar.grid(row=0, column=1, padx=5, sticky="w")

    def salvar_e_fechar(self):
        """Coleta os dados e chama a função apropriada (salvar ou atualizar) no controller."""
        
        # Coleta e limpa os dados
        try:
            produto_data = {
                'nome': self.produto_nome_entry.get(),
                # Converte para float e usa . como separador decimal
                'preco': float(self.produto_preco_entry.get().replace(',', '.')), 
                'estoque': float(self.produto_estoque_entry.get().replace(',', '.')), 
                'unidade': self.produto_unidade_entry.get(),
                'cod_barras': self.cod_barras_entry.get(),
                'sku': self.sku_entry.get()
            }
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Os campos Preço e Estoque devem ser números válidos.")
            return
        
        success = False
        
        if self.is_editing:
            # Modo EDIÇÃO: Chama a nova função de atualização no controller
            produto_id = self.product_data[0]
            success = self.controller.atualizar_produto_via_dialog(produto_id, produto_data)
            
        else:
            # Modo CADASTRO: Chama a função de salvamento existente
            success = self.controller.salvar_produto_via_dialog(produto_data)
            
        if success:
            self.destroy()

# NOVA CLASSE PARA CADASTRO/EDIÇÃO DE FUNCIONÁRIOS
class CadastroFuncionarioDialog(tk.Toplevel):
    # Aceita 'employee_data' para modo de edição
    def __init__(self, parent, controller, employee_data=None):
        # Inicializa a Toplevel (nova janela)
        super().__init__(parent)
        self.controller = controller  # Referência à FrutariaApp
        
        # 📌 NOVAS VARIÁVEIS PARA EDIÇÃO
        self.employee_data = employee_data
        self.is_editing = employee_data is not None

        self.transient(parent)
        self.grab_set()

        # 📌 2. Adicione este código para aplicar o ícone da janela principal
        try:
            # Acessa o objeto PhotoImage (parent.icon_tk) que deve estar na janela principal
            self.iconphoto(False, parent.icon_tk) 
        except Exception:
            # Ignora se falhar, o ícone principal não é crucial para o funcionamento
            pass 

        # Título dinâmico
        dialog_title = "Editar Funcionário" if self.is_editing else "Cadastrar Novo Funcionário"
        self.title(dialog_title)
        self.configure(bg=self.controller.bg_color)

        self.geometry("900x450")
        
        # Centraliza a janela (o código de centralização não precisa de alteração)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

        self.create_form_widgets()

    def create_form_widgets(self):
        cadastro_funcionario_frame = tk.Frame(self, bg=self.controller.white_color, padx=15, pady=15, relief="solid", bd=1)
        cadastro_funcionario_frame.pack(padx=20, pady=20, fill="both", expand=True)
        cadastro_funcionario_frame.columnconfigure(0, weight=1)

        # 📌 TÍTULO DINÂMICO
        title_text = "EDITAR FUNCIONÁRIO" if self.is_editing else "CADASTRAR FUNCIONÁRIO"
        tk.Label(cadastro_funcionario_frame, text=title_text, font=("Arial", 20, "bold"), 
                 bg=self.controller.white_color, fg=self.controller.bg_color1).grid(row=0, column=0, pady=5, sticky="ew")
        
        form_frame = tk.Frame(cadastro_funcionario_frame, bg=self.controller.white_color)
        form_frame.grid(row=1, column=0, sticky="ew", padx=10)
        
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        
        # --- Linhas do Formulário ---
        # Nome
        tk.Label(form_frame, text="Nome Completo:", bg=self.controller.white_color).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.funcionario_nome_entry = tk.Entry(form_frame)
        self.funcionario_nome_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Usuário e Cargo
        tk.Label(form_frame, text="Usuário:", bg=self.controller.white_color).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.funcionario_usuario_entry = tk.Entry(form_frame)
        self.funcionario_usuario_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form_frame, text="Cargo:", bg=self.controller.white_color).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.funcionario_cargo_entry = ttk.Combobox(form_frame, values=["Caixa", "Gerente"])
        self.funcionario_cargo_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.funcionario_cargo_entry.set("Caixa") 

        # Senha
        tk.Label(form_frame, text="Senha:", bg=self.controller.white_color).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.funcionario_senha_entry = tk.Entry(form_frame, show="*")
        self.funcionario_senha_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # 📌 PREENCHIMENTO DOS DADOS (PARA EDIÇÃO)
        if self.is_editing:
            # Assumindo a ordem da sua busca (ID, Nome, Usuário, Senha, Cargo)
            data = self.employee_data 
            # ID: data[0]
            self.funcionario_nome_entry.insert(0, data[1]) # Nome
            self.funcionario_usuario_entry.insert(0, data[2]) # Usuário
            # 💡 OBS: Não preenchemos a senha. O campo fica vazio, e o usuário digita uma nova.
            # Se não digitar, sua lógica de update no banco deve manter a senha antiga.
            self.funcionario_cargo_entry.set(data[4]) # Cargo
            
        # O Frame de Ações ocupa toda a largura abaixo do formulário
        action_frame = tk.Frame(cadastro_funcionario_frame, bg=self.controller.white_color)
        action_frame.grid(row=2, column=0, pady=15, sticky="ew")
        
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        
        # 📌 COR E TEXTO DINÂMICOS
        btn_text = "Salvar Alterações" if self.is_editing else "Adicionar Funcionário"
        btn_bg_color = "#4CAF50" # Cor de Sucesso (Verde) para Salvar/Adicionar

        # Botão Salvar
        btn_add_funcionario = tk.Button(action_frame, 
                                        text=btn_text,
                                        font=("Arial", 12),
                                        bg=self.controller.bg_color1, 
                                        fg=self.controller.white_color, 
                                        command=self.salvar_e_fechar, 
                                        relief="flat")
        btn_add_funcionario.grid(row=0, column=0, padx=5, sticky="e")

        # Botão CANCELAR
        btn_cancelar = tk.Button(action_frame, 
                                 text="Cancelar",
                                 font=("Arial", 12),
                                 bg="#F44336", 
                                 fg=self.controller.white_color, 
                                 command=self.destroy, 
                                 relief="flat")
        btn_cancelar.grid(row=0, column=1, padx=5, sticky="w")

    def salvar_e_fechar(self):
        """Coleta os dados, chama a função de salvar/editar do controller e fecha."""
        
        funcionario_data = {
            'nome': self.funcionario_nome_entry.get(),
            'usuario': self.funcionario_usuario_entry.get(),
            'senha': self.funcionario_senha_entry.get(), # Se for edição e estiver vazio, o controller deve ignorar a mudança de senha
            'cargo': self.funcionario_cargo_entry.get()
        }
        
        success = False
        
        if self.is_editing:
            # Modo EDIÇÃO: Passa o ID e os novos dados para a função de update
            employee_id = self.employee_data[0]
            success = self.controller.atualizar_funcionario_via_dialog(employee_id, funcionario_data)
        else:
            # Modo CADASTRO: Chama a função de salvamento existente
            success = self.controller.salvar_funcionario_via_dialog(funcionario_data)
            
        if success:
            self.destroy()

class EdicaoCarrinhoDialog(tk.Toplevel):
    def __init__(self, parent, controller, item_data, item_index):
        super().__init__(parent)
        self.controller = controller
        self.item_data = item_data
        self.item_index = item_index
        # 📌 2. Adicione este código para aplicar o ícone da janela principal
        try:
            # Acessa o objeto PhotoImage (parent.icon_tk) que deve estar na janela principal
            self.iconphoto(False, parent.icon_tk) 
        except Exception:
            # Ignora se falhar, o ícone principal não é crucial para o funcionamento
            pass 
        self.transient(parent)
        self.grab_set()
        self.title("Editar Item do Carrinho")
        self.configure(bg=self.controller.bg_color)
        self.geometry("600x500")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal com estilo
        main_frame = tk.Frame(self, bg=self.controller.white_color, padx=15, pady=15, relief="solid", bd=1)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1)

        # Título
        tk.Label(main_frame, text="EDITAR QUANTIDADE", 
                 font=("Arial", 16, "bold"), 
                 bg=self.controller.white_color, 
                 fg=self.controller.bg_color1).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")

        # Informação do Produto
        tk.Label(main_frame, text=f"Produto:", bg=self.controller.white_color).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Label(main_frame, text=self.item_data['nome'], font=("Arial", 10, "bold"), 
                 bg=self.controller.white_color, fg=self.controller.text_color).grid(row=1, column=1, padx=5, pady=5, sticky="w")
                 
        # Unidade
        unidade_display = self.item_data.get('unidade', 'un')
        if unidade_display == 'unidade':
            unidade_display = 'un'

        # Campo de Nova Quantidade
        tk.Label(main_frame, text=f"Nova Quantidade ({unidade_display}):", bg=self.controller.white_color).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.new_qty_entry = tk.Entry(main_frame, font=("Arial", 10))
        # Insere a quantidade atual formatada
        self.new_qty_entry.insert(0, f"{self.item_data['quantidade']:.3f}".replace('.', ','))
        self.new_qty_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.new_qty_entry.bind('<Return>', lambda event: self.save_changes()) # Salvar com Enter

        # Frame de Ações
        action_frame = tk.Frame(main_frame, bg=self.controller.white_color)
        action_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Botão Salvar
        btn_salvar = tk.Button(action_frame, text="Salvar Alterações", 
                                 font=("Arial", 10), bg=self.controller.bg_color1, fg=self.controller.white_color, 
                                 command=self.save_changes, relief="flat")
        btn_salvar.pack(side="left", padx=10)

        # Botão Cancelar
        btn_cancelar = tk.Button(action_frame, text="Cancelar", 
                                 font=("Arial", 10), bg="#F44336", fg=self.controller.white_color, 
                                 command=self.destroy, relief="flat")
        btn_cancelar.pack(side="left", padx=10)

    def save_changes(self):
        try:
            # Pega o valor e substitui vírgula por ponto para conversão
            new_qty_str = self.new_qty_entry.get().replace(',', '.')
            new_qty = float(new_qty_str)
            
            if new_qty <= 0:
                messagebox.showerror("Erro", "Quantidade deve ser maior que zero.")
                return

            # Atualiza o carrinho na classe principal (FrutariaApp)
            self.controller.carrinho[self.item_index]["quantidade"] = new_qty
            self.controller.carrinho[self.item_index]["subtotal"] = new_qty * self.item_data["preco"]
            
            self.controller.atualizar_carrinho_treeview()
            self.controller.atualizar_total()
            
            messagebox.showinfo("Sucesso", "Item atualizado no carrinho.")
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida. Use apenas números.")

class AdicionarItemDialog(tk.Toplevel):
    STABLE_SAMPLES_REQUIRED = 4
    STABLE_DELTA = 0.003
    WEIGHT_TIMEOUT_SECONDS = 8.0

    def __init__(self, parent, callback, callback_adicionar, balanca_instance=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.callback_adicionar = callback_adicionar
        self.balanca = balanca_instance

        self.monitorando_balanca = True
        self.balanca_ativa = False
        self.produto_selecionado = None
        self._ultimo_peso = None
        self._stable_count = 0
        self._stable_weight = None
        self._kg_started_at = None
        self._timed_out = False

        self.title("Adicionar Item (F2)")
        self.geometry("480x920")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.produto_entry.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        self.loop_leitura_balanca()

    def setup_ui(self):
        main_frame = tk.Frame(self, padx=20, pady=20, bg="#f4f4f4")
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Buscar Produto (Nome ou SKU):", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(anchor="w")

        self.produto_var = tk.StringVar()
        self.produto_entry = ttk.Combobox(main_frame, textvariable=self.produto_var, font=("Arial", 14))
        self.produto_entry.pack(fill="x", pady=(5, 18))
        self.produto_entry.bind('<<ComboboxSelected>>', self.verificar_tipo_produto)
        self.produto_entry.bind('<KeyRelease>', self.filtrar_produtos)

        self.quant_frame = tk.LabelFrame(main_frame, text="Quantidade / Peso (KG)", font=("Arial", 10, "bold"), padx=12, pady=12)
        self.quant_frame.pack(fill="x", pady=(0, 12))

        self.quantidade_var = tk.StringVar(value="1")
        self.quantidade_entry = tk.Entry(self.quant_frame, textvariable=self.quantidade_var, font=("Arial", 24, "bold"), justify="center", width=10)
        self.quantidade_entry.pack(pady=(2, 8))

        self.status_conexao = tk.Label(self.quant_frame, text="Conexão da balança: verificando...", fg="#666666", font=("Arial", 9, "bold"))
        self.status_conexao.pack(anchor="w")

        self.status_balanca = tk.Label(self.quant_frame, text="Peso: aguardando produto por KG...", fg="#666666", font=("Arial", 9, "italic"))
        self.status_balanca.pack(anchor="w", pady=(6, 0))

        self.status_estabilidade = tk.Label(self.quant_frame, text="Estabilidade: não iniciada", fg="#666666", font=("Arial", 9))
        self.status_estabilidade.pack(anchor="w", pady=(4, 0))

        helper_frame = tk.Frame(main_frame, bg="#f4f4f4")
        helper_frame.pack(fill="x", pady=(0, 14))

        title_font = ("Arial", 10, "bold")
        text_font = ("Arial", 9)

        tk.Label(
            helper_frame,
            text="Fluxo rápido:",
            font=title_font,
            bg="#f4f4f4"
        ).pack(anchor="w")

        steps = [
            "1. Escolha um produto por KG.",
            "2. Aguarde peso estável.",
            "3. Pressione Enter para adicionar."
        ]

        for step in steps:
            tk.Label(
                helper_frame,
                text=step,
                font=text_font,
                bg="#f4f4f4",
                fg="#555555",
                wraplength=410,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))
        btn_frame = tk.Frame(main_frame, bg="#f4f4f4")
        btn_frame.pack(fill="x", side="bottom", pady=10)

        tk.Button(btn_frame, text="CANCELAR (Esc)", bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), command=self.ao_fechar, width=15).pack(side="left")
        tk.Button(btn_frame, text="ADICIONAR (Enter)", bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), command=self.confirmar, width=15).pack(side="right")

        self.bind('<Return>', lambda _e: self.confirmar())
        self.bind('<Escape>', lambda _e: self.ao_fechar())

    def filtrar_produtos(self, event):
        busca = self.produto_var.get().upper()
        if len(busca) > 1:
            self.produto_entry['values'] = filter_products_for_combobox(busca)

    def _reset_weight_tracking(self):
        self._ultimo_peso = None
        self._stable_count = 0
        self._stable_weight = None
        self._kg_started_at = time.monotonic() if self.balanca_ativa else None
        self._timed_out = False

    def verificar_tipo_produto(self, event=None):
        try:
            texto = self.produto_var.get().strip()
            if not texto:
                return

            nome_selecionado = texto.split(" - ")[0]
            self.produto_selecionado = get_product_by_name(nome_selecionado)
            if not self.produto_selecionado:
                return

            unidade = self.produto_selecionado[4].upper()
            if unidade == 'KG':
                self.balanca_ativa = True
                self.quantidade_entry.config(state='normal')
                self.quantidade_entry.delete(0, tk.END)
                self.status_balanca.config(text="Peso: aguardando leitura da balança...", fg="#0b6d36")
                self.status_estabilidade.config(text="Estabilidade: coletando amostras...", fg="#666666")
                self._reset_weight_tracking()
            else:
                self.balanca_ativa = False
                self.quantidade_var.set("1")
                self.status_balanca.config(text="Produto unitario. Quantidade manual.", fg="#1d4ed8")
                self.status_estabilidade.config(text="Estabilidade: não se aplica", fg="#666666")
        except Exception as e:
            print(f"Erro ao verificar produto: {e}")

    def _atualizar_status_conexao(self, status):
        if status.get("connected"):
            self.status_conexao.config(text="Conexão da balança: online", fg="#0b6d36")
        else:
            erro = status.get("last_error") or "sem resposta"
            self.status_conexao.config(text=f"Conexão da balança: offline ({erro})", fg="#b91c1c")

    def _processar_estabilidade(self, peso):
        if self._ultimo_peso is None or abs(peso - self._ultimo_peso) <= self.STABLE_DELTA:
            self._stable_count += 1
        else:
            self._stable_count = 1

        self._ultimo_peso = peso
        self._stable_weight = peso

        if self._stable_count >= self.STABLE_SAMPLES_REQUIRED and peso > 0.005:
            self.status_estabilidade.config(text=f"Estabilidade: peso confirmado em {peso:.3f} kg", fg="#0b6d36")
            return True

        self.status_estabilidade.config(
            text=f"Estabilidade: {self._stable_count}/{self.STABLE_SAMPLES_REQUIRED} leituras semelhantes",
            fg="#a16207",
        )
        return False

    def loop_leitura_balanca(self):
        if not self.monitorando_balanca:
            return

        status = self.balanca.obter_status() if self.balanca else {
            "connected": False,
            "weight": 0.0,
            "last_read_age": None,
            "last_error": "Balança indisponível",
        }
        self._atualizar_status_conexao(status)

        if self.balanca_ativa and self.balanca:
            peso = status.get("weight", 0.0)
            self.quantidade_entry.delete(0, tk.END)
            self.quantidade_entry.insert(0, f"{peso:.3f}".replace('.', ','))

            if self._kg_started_at and time.monotonic() - self._kg_started_at > self.WEIGHT_TIMEOUT_SECONDS and peso <= 0.005:
                self._timed_out = True
                self.status_balanca.config(text="Peso: timeout de leitura. Confira a conexão ou reposicione o item.", fg="#b91c1c")
                self.status_estabilidade.config(text="Estabilidade: aguardando nova leitura valida", fg="#b91c1c")
            else:
                if peso <= 0.005:
                    self.status_balanca.config(text="Peso: aguardando item na balança...", fg="#666666")
                    self.status_estabilidade.config(text="Estabilidade: aguardando peso mínimo", fg="#666666")
                    self._stable_count = 0
                else:
                    self._timed_out = False
                    estavel = self._processar_estabilidade(peso)
                    if estavel:
                        self.status_balanca.config(text=f"Peso: {peso:.3f} kg pronto para adicionar", fg="#0b6d36")
                    else:
                        self.status_balanca.config(text=f"Peso: {peso:.3f} kg em estabilizacao...", fg="#a16207")
        elif self.produto_selecionado:
            self.status_estabilidade.config(text="Estabilidade: não se aplica", fg="#666666")

        self.after(150, self.loop_leitura_balanca)

    def _peso_estavel_para_confirmar(self, quantidade):
        if not self.balanca_ativa:
            return True
        return (
            quantidade > 0.005
            and self._stable_weight is not None
            and abs(quantidade - self._stable_weight) <= self.STABLE_DELTA
            and self._stable_count >= self.STABLE_SAMPLES_REQUIRED
            and not self._timed_out
        )

    def confirmar(self):
        if not self.produto_selecionado:
            self.verificar_tipo_produto()
            if not self.produto_selecionado:
                messagebox.showwarning("Atenção", "Selecione um produto válido.", parent=self)
                return

        try:
            qtd_str = self.quantidade_entry.get().replace(',', '.')
            quantidade = float(qtd_str or '0')
        except ValueError:
            messagebox.showerror("Erro", "Quantidade invalida. Digite apenas números.", parent=self)
            return

        if quantidade <= 0:
            messagebox.showwarning("Erro", "Quantidade invalida.", parent=self)
            return

        if self.balanca_ativa and not self._peso_estavel_para_confirmar(quantidade):
            messagebox.showwarning(
                "Peso ainda não estabilizado",
                "Aguarde o peso ficar estavel antes de adicionar o item.",
                parent=self,
            )
            return

        preco_unitario = self.produto_selecionado[2]
        subtotal = preco_unitario * quantidade
        self.callback_adicionar(self.produto_selecionado, quantidade, subtotal)
        self.ao_fechar()

    def ao_fechar(self):
        self.monitorando_balanca = False
        self.balanca_ativa = False
        if hasattr(self.parent, "ativar_monitor_balanca"):
            self.parent.ativar_monitor_balanca()
        self.grab_release()
        self.destroy()

class EdicaoVendaDialog(tk.Toplevel):
    def __init__(self, parent, controller, venda_data, on_save=None):
        super().__init__(parent)

        self.controller = controller
        self.venda_data = venda_data
        self.venda_id = venda_data[0]
        self.on_save = on_save  # <- salva o callback aqui

        # 📌 2. Adicione este código para aplicar o ícone da janela principal
        try:
            # Acessa o objeto PhotoImage (parent.icon_tk) que deve estar na janela principal
            self.iconphoto(False, parent.icon_tk) 
        except Exception:
            # Ignora se falhar, o ícone principal não é crucial para o funcionamento
            pass 

        # Busca itens da venda no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT itens_vendidos FROM vendas WHERE id=?", (self.venda_id,))
        result = cursor.fetchone() # É mais seguro pegar o resultado antes
        if result:
            itens_str = result[0]
            # ... (lógica de ast.literal_eval/json) ...
            try:
                self.itens = json.loads(itens_str)
            except:
                self.itens = ast.literal_eval(itens_str)
        else:
            self.itens = []
            
        conn.close()

        self.itens = ast.literal_eval(itens_str)

        self.transient(parent)
        self.grab_set()
        self.title(f"Editar Venda {self.venda_id}")
        self.configure(bg=self.controller.bg_color1)
        self.geometry("500x500")

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.controller.white_color, padx=10, pady=10, relief="solid", bd=1)
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)

        tk.Label(main_frame, text=f"EDITAR VENDA #{self.venda_id}",
                 font=("Arial", 16, "bold"), bg=self.controller.white_color,
                 fg=self.controller.bg_color1).pack(pady=(0, 10))

        self.items_frame = tk.Frame(main_frame, bg=self.controller.white_color)
        self.items_frame.pack(fill="both", expand=True)

        self.render_items_table()

        self.total_label = tk.Label(main_frame, text="", font=("Arial", 12, "bold"),
                                    bg=self.controller.white_color, fg=self.controller.bg_color1)
        self.total_label.pack(pady=10)
        self.update_total()

        action_frame = tk.Frame(main_frame, bg=self.controller.white_color)
        action_frame.pack(pady=10)

        btn_salvar = tk.Button(action_frame, text="Salvar Alterações",
                               font=("Arial", 10), bg=self.controller.bg_color1, fg=self.controller.white_color,
                               command=self.save_changes, relief="flat")
        btn_salvar.pack(side="left", padx=10)

        btn_cancelar = tk.Button(action_frame, text="Cancelar",
                                 font=("Arial", 10), bg="#F44336", fg=self.controller.white_color,
                                 command=self.destroy, relief="flat")
        btn_cancelar.pack(side="left", padx=10)

    def render_items_table(self):
        """Renderiza tabela de itens com botões de editar e excluir"""
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        headers = ["ID", "Item", "Qtd", "Subtotal", "", ""]
        for col, text in enumerate(headers):
            tk.Label(self.items_frame, text=text, font=("Arial", 14, "bold"),
                     bg=self.controller.white_color).grid(row=0, column=col, padx=5, pady=5, sticky="nsew")

        for i, item in enumerate(self.itens):
            bg = "#F9F9F9" if i % 2 == 0 else self.controller.white_color
            tk.Label(self.items_frame, text=f"{i+1}", font=("Arial", 10, "bold"),
                     bg=bg, relief="flat").grid(row=i+1, column=0, padx=5)
            tk.Label(self.items_frame, text=item['nome'], font=("Arial", 10),
                     bg=bg, relief="flat").grid(row=i+1, column=1, sticky="w")
            tk.Label(self.items_frame, text=f"{item['quantidade']:.3f}", font=("Arial", 10),
                     bg=bg, relief="flat").grid(row=i+1, column=2)
            tk.Label(self.items_frame, text=f"R$ {item['subtotal']:.2f}", font=("Arial", 10),
                     bg=bg, relief="flat").grid(row=i+1, column=3)

            btn_edit = tk.Button(self.items_frame, text="Editar", command=lambda idx=i: self.edit_item(idx),
                                 bg=self.controller.bg_color2,fg=self.controller.black_color, relief="flat")
            btn_edit.grid(row=i+1, column=4, padx=5)
            #btn_edit.configure(bg=bg)

            btn_delete = tk.Button(self.items_frame, text="Excluir", command=lambda idx=i: self.delete_item(idx), 
                                   bg="#F44336", fg=self.controller.white_color, relief="flat")
            btn_delete.grid(row=i+1, column=5, padx=5)
            #btn_delete.configure(bg=bg)


    # Dentro do EdicaoVendaDialog
    def edit_item(self, idx):
        """Abre o EditItemDialog no mesmo estilo do EdicaoVendaDialog"""
        EditItemDialog(
            parent=self,
            controller=self.controller,
            idx=idx,
            item=self.itens[idx],
            on_save=lambda: [self.render_items_table(), self.update_total()]  # Atualiza tabela e total ao salvar
        )

    def delete_item(self, idx):
        if messagebox.askyesno("Remover Item", f"Deseja remover '{self.itens[idx]['nome']}' desta venda?"):
            self.itens.pop(idx)
            self.render_items_table()
            self.update_total()

    def update_total(self):
        total = sum(item['subtotal'] for item in self.itens)
        self.total_label.config(text=f"TOTAL: R$ {total:.2f}")
        
    def save_changes(self):

        if not self.itens:
            messagebox.showwarning("Nenhum Item", "A venda precisa ter pelo menos um item para ser salva.")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE vendas SET itens_vendidos=?, total=? WHERE id=?",
                (json.dumps(self.itens), sum(item['subtotal'] for item in self.itens), self.venda_id)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Venda atualizada com sucesso!")
            self.controller.update_daily_sales_report()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar a venda: {e}")

        if self.on_save:
            self.on_save()
# -------------------- Dialog de Edição de Item --------------------

class EditItemDialog(tk.Toplevel):
    def __init__(self, parent, controller, idx, item, on_save=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.idx = idx
        self.item = item
        self.on_save = on_save
        self.title(f"Editar Item - {item['nome']}")
        self.geometry("800x650")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=self.controller.bg_color1)

        # 📌 CORREÇÃO: Use self.winfo_toplevel() para obter a janela raiz (FrutariaApp) 
        # que contém a imagem do ícone (icon_tk).
        try:
            # Obtém a janela de nível superior (o root da aplicação)
            root_app = self.winfo_toplevel() 
            # Verifica se o root_app tem o ícone e aplica na dialog
            if hasattr(root_app, 'icon_tk'):
                self.iconphoto(False, root_app.icon_tk) 
        except Exception:
            # Ignora se falhar
            pass
        # Buscar preço padrão do produto no banco, se não estiver no item
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT preco, unidade FROM produtos WHERE nome=?", (item['nome'],))
        produto = cursor.fetchone()
        conn.close()

        preco_padrao = produto[0] if produto else 0
        unidade = produto[1] if produto else "un"

        self.item.setdefault('preco', preco_padrao)
        self.item.setdefault('unidade', unidade)

        self.create_widgets()

    def create_widgets(self):
        # --- Frame principal ---
        main_frame = tk.Frame(self, bg=self.controller.white_color, padx=15, pady=15, relief="solid", bd=1)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Título ---
        tk.Label(main_frame, text=f"EDITAR ITEM: {self.item['nome']}",
                 font=("Arial", 16, "bold"), bg=self.controller.white_color,
                 fg=self.controller.bg_color1).pack(pady=(0, 15))

        # --- Formulário ---
        form_frame = tk.Frame(main_frame, bg=self.controller.white_color)
        form_frame.pack(pady=10, fill="x")

        # Quantidade
        tk.Label(form_frame, text="Quantidade:", font=("Arial", 12),
                 bg=self.controller.white_color, anchor="w").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.qty_entry = tk.Entry(form_frame, font=("Arial", 12), width=10)
        self.qty_entry.insert(0, f"{self.item.get('quantidade', 1):.3f}".replace('.', ','))
        self.qty_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        # Preço
        tk.Label(form_frame, text=f"Preço ({self.item['unidade']}):", font=("Arial", 12),
                 bg=self.controller.white_color, anchor="w").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.price_entry = tk.Entry(form_frame, font=("Arial", 12), width=10)
        self.price_entry.insert(0, f"{self.item.get('preco', 0):.2f}".replace('.', ','))
        self.price_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        # Subtotal (dinâmico)
        self.subtotal_label = tk.Label(form_frame, text=f"Subtotal: R$ {self.item.get('subtotal', 0):.2f}",
                                       font=("Arial", 12, "bold"), bg=self.controller.white_color, anchor="w")
        self.subtotal_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=10, padx=5)

        # Atualiza subtotal enquanto digita
        self.qty_entry.bind("<KeyRelease>", self.update_subtotal)
        self.price_entry.bind("<KeyRelease>", self.update_subtotal)

        # --- Botões de ação ---
        action_frame = tk.Frame(main_frame, bg=self.controller.white_color)
        action_frame.pack(pady=15)

        tk.Button(action_frame, text="Salvar", bg=self.controller.bg_color1, fg=self.controller.white_color, width=12,
                  command=self.save_item, relief="flat").pack(side="left", padx=10)
        tk.Button(action_frame, text="Cancelar", bg="#F44336", fg="white", width=12,
                  command=self.destroy, relief="flat").pack(side="left", padx=10)

        # Bind enter / escape
        self.qty_entry.bind("<Return>", lambda e: self.save_item())
        self.price_entry.bind("<Return>", lambda e: self.save_item())
        self.bind("<Escape>", lambda e: self.destroy())

    def update_subtotal(self, event=None):
        try:
            qty = float(self.qty_entry.get().replace(',', '.'))
            preco = float(self.price_entry.get().replace(',', '.'))
            subtotal = qty * preco
            self.subtotal_label.config(text=f"Subtotal: R$ {subtotal:.2f}")
        except ValueError:
            self.subtotal_label.config(text="Subtotal: -")

    def save_item(self):
        try:
            qty = float(self.qty_entry.get().replace(',', '.'))
            preco = float(self.price_entry.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Quantidade e preço devem ser números válidos.")
            return

        if qty <= 0 or preco <= 0:
            messagebox.showerror("Erro", "Quantidade e preço devem ser maiores que zero.")
            return

        # Atualiza item apenas para esta venda
        self.item['quantidade'] = qty
        self.item['preco'] = preco
        self.item['subtotal'] = qty * preco

        if self.on_save:
            self.on_save()  # Atualiza tabela / total no EdicaoVendaDialog

        self.destroy()

# Tela de abriri e fechar caixa
class OpenCloseCaixaDialog(tk.Toplevel):
    def __init__(self, parent, title, label_text, callback, confirm_text="Confirmar"):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.confirmed = False
        self.value = None

        theme, card, body = build_dialog_shell(
            self,
            parent,
            title,
            subtitle=label_text,
            size=(560, 420),
            controller=parent,
        )
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        field = tk.Frame(body, bg=theme["surface"])
        field.pack(fill="x", pady=(6, 18))
        make_form_label(field, "Valor", theme).pack(anchor="w")
        self.valor_entry = make_entry(field, theme, justify="center")
        self.valor_entry.pack(fill="x", ipady=10, pady=(6, 0))
        self.valor_entry.focus_set()

        action = tk.Frame(body, bg=theme["surface"])
        action.pack(fill="x")
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)

        btn_confirm = tk.Button(action, text=confirm_text, command=self.on_confirm)
        style_button(btn_confirm, "primary", theme).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        btn_cancel = tk.Button(action, text="Cancelar", command=self.on_cancel)
        style_button(btn_cancel, "secondary", theme).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.valor_entry.bind("<Return>", lambda _e: self.on_confirm())
        self.wait_window()

    def on_confirm(self):
        try:
            valor = float(self.valor_entry.get().replace(',', '.'))
            if valor < 0:
                messagebox.showerror("Erro", "O valor não pode ser negativo.", parent=self)
                return
            self.value = valor
            self.confirmed = True
            self.destroy()
            self.callback(valor)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor numérico válido.", parent=self)

    def on_cancel(self):
        self.confirmed = False
        self.value = None
        self.destroy()

class OpenCloseCaixaDialog(tk.Toplevel):
    def __init__(
        self,
        parent,
        title,
        label_text,
        callback,
        confirm_text="Confirmar",
        close_summary=None,
    ):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.confirmed = False
        self.value = None
        self.close_summary = close_summary or {}
        self.metrics_vars = {}
        self.metric_entries = {}

        theme, card, body = build_dialog_shell(
            self,
            parent,
            title,
            subtitle=label_text,
            size=(820, 650) if self.close_summary else (560, 420),
            controller=parent,
        )
        self.theme = theme
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        if self.close_summary:
            self._build_close_summary_layout(body, theme)
        else:
            field = tk.Frame(body, bg=theme["surface"])
            field.pack(fill="x", pady=(6, 18))
            make_form_label(field, "Valor", theme).pack(anchor="w")
            self.valor_entry = make_entry(field, theme, justify="center")
            self.valor_entry.pack(fill="x", ipady=10, pady=(6, 0))
            self.valor_entry.focus_set()
            self.valor_entry.bind("<Return>", lambda _e: self.on_confirm())

        action = tk.Frame(body, bg=theme["surface"])
        action.pack(fill="x", pady=(16, 0))
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)

        btn_confirm = tk.Button(action, text=confirm_text, command=self.on_confirm)
        style_button(btn_confirm, "primary", theme).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )

        btn_cancel = tk.Button(action, text="Cancelar", command=self.on_cancel)
        style_button(btn_cancel, "secondary", theme).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.wait_window()

    def _format_currency(self, value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _build_close_summary_layout(self, body, theme):
        summary = self.close_summary
        pagamentos = summary.get("pagamentos", {})
        valor_abertura = float(summary.get("valor_abertura", 0.0))
        total_vendas = float(summary.get("total_vendas", 0.0))

        top_grid = tk.Frame(body, bg=theme["surface"])
        top_grid.pack(fill="x", pady=(4, 14))
        for col in range(3):
            top_grid.columnconfigure(col, weight=1)

        cards = [
            ("Troco Inicial", valor_abertura, "#EEF7F0", theme["primary"]),
            ("Vendas do Dia", total_vendas, "#FFF6EA", "#B85C00"),
            ("Previsto no Fechamento", valor_abertura + total_vendas, "#EDF4FF", "#1E5AA7"),
        ]
        for idx, (title, value, bg, fg) in enumerate(cards):
            item = tk.Frame(top_grid, bg=bg, padx=14, pady=12)
            item.grid(row=0, column=idx, sticky="ew", padx=(0, 8) if idx < 2 else 0)
            tk.Label(
                item,
                text=title.upper(),
                font=("Segoe UI Semibold", 9),
                bg=bg,
                fg=fg,
            ).pack(anchor="w")
            tk.Label(
                item,
                text=self._format_currency(value),
                font=("Segoe UI Black", 14),
                bg=bg,
                fg=fg,
            ).pack(anchor="w", pady=(8, 0))

        content = tk.Frame(body, bg=theme["surface"])
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=4)
        content.columnconfigure(1, weight=2)

        inputs = tk.Frame(content, bg=theme["surface"])
        inputs.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        inputs.columnconfigure(0, weight=1)

        resumo = tk.Frame(content, bg=theme["surface_alt"], padx=16, pady=16)
        resumo.grid(row=0, column=1, sticky="nsew")
        resumo.columnconfigure(0, weight=1)

        maquininha_total = (
            float(pagamentos.get("CARTAO_CREDITO", 0.0))
            + float(pagamentos.get("CARTAO_DEBITO", 0.0))
            + float(pagamentos.get("QR_CODE", 0.0))
            + float(pagamentos.get("PIX", 0.0))
        )

        fields = [
            ("Dinheiro em Caixa", "DINHEIRO", valor_abertura + float(pagamentos.get("DINHEIRO", 0.0))),
            ("Total Efetivado da Maquininha", "MAQUININHA", maquininha_total),
        ]

        # Modelo anterior com varias insercoes individuais por metodo de pagamento.
        # Mantido comentado para reativacao futura, se necessario.
        #
        # fields = [
        #     ("Dinheiro em Caixa", "DINHEIRO", valor_abertura + float(pagamentos.get("DINHEIRO", 0.0))),
        #     ("Cartao de Credito", "CARTAO_CREDITO", float(pagamentos.get("CARTAO_CREDITO", 0.0))),
        #     ("Cartao de Debito", "CARTAO_DEBITO", float(pagamentos.get("CARTAO_DEBITO", 0.0))),
        #     ("QR Code", "QR_CODE", float(pagamentos.get("QR_CODE", 0.0))),
        #     ("PIX", "PIX", float(pagamentos.get("PIX", 0.0))),
        # ]

        for idx, (label, key, default_value) in enumerate(fields):
            card_bg = "#F8FBF5" if idx == 0 else "#FFF8EE"
            accent = theme["primary"] if idx == 0 else theme["accent"]
            field = tk.Frame(
                inputs,
                bg=card_bg,
                padx=18,
                pady=16,
                highlightthickness=1,
                highlightbackground=theme["border"],
            )
            field.grid(
                row=idx,
                column=0,
                sticky="ew",
                pady=(0, 12 if idx < len(fields) - 1 else 0),
            )
            field.columnconfigure(0, weight=1)
            tk.Label(
                field,
                text=label.upper(),
                font=("Segoe UI Semibold", 10),
                bg=card_bg,
                fg=accent,
            ).grid(row=0, column=0, sticky="w")
            tk.Label(
                field,
                text="Informe o valor conferido no fechamento.",
                font=("Segoe UI", 9),
                bg=card_bg,
                fg=theme["text_muted"],
            ).grid(row=1, column=0, sticky="w", pady=(4, 10))
            entry = make_entry(field, theme, justify="right")
            entry.configure(font=("Segoe UI Black", 18))
            entry.grid(row=2, column=0, sticky="ew", ipady=10)
            entry.insert(0, f"{default_value:.2f}".replace(".", ","))
            entry.bind("<KeyRelease>", lambda _e: self._update_close_totals())
            self.metric_entries[key] = entry

        resumo_items = [
            ("Total Conferido", "total_conferido", theme["text"]),
            ("Lucro do Dia", "lucro_dia", theme["primary"]),
            ("Diferença", "diferenca", theme["danger"]),
        ]
        for idx, (label, key, color) in enumerate(resumo_items):
            line = tk.Frame(resumo, bg=theme["surface_alt"])
            line.grid(row=idx, column=0, sticky="ew", pady=(0, 12 if idx < 2 else 0))
            line.columnconfigure(0, weight=1)
            tk.Label(
                line,
                text=label.upper(),
                font=("Segoe UI Semibold", 9),
                bg=theme["surface_alt"],
                fg=theme["text_muted"],
            ).grid(row=0, column=0, sticky="w")
            self.metrics_vars[key] = tk.StringVar(value=self._format_currency(0.0))
            tk.Label(
                line,
                textvariable=self.metrics_vars[key],
                font=("Segoe UI Black", 15),
                bg=theme["surface_alt"],
                fg=color,
            ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self._update_close_totals()
        if "DINHEIRO" in self.metric_entries:
            self.metric_entries["DINHEIRO"].focus_set()

    def _entry_value(self, key):
        entry = self.metric_entries.get(key)
        if entry is None:
            return 0.0
        text = entry.get().strip().replace(",", ".")
        if not text:
            return 0.0
        return float(text)

    def _calculate_close_result(self):
        pagamentos = {
            "DINHEIRO": self._entry_value("DINHEIRO"),
            "MAQUININHA": self._entry_value("MAQUININHA"),
            "CARTAO_CREDITO": 0.0,
            "CARTAO_DEBITO": 0.0,
            "QR_CODE": 0.0,
            "PIX": 0.0,
        }
        total_conferido = sum(pagamentos.values())
        valor_abertura = float(self.close_summary.get("valor_abertura", 0.0))
        total_vendas = float(self.close_summary.get("total_vendas", 0.0))
        lucro_dia = total_conferido - valor_abertura
        diferenca = total_conferido - (valor_abertura + total_vendas)
        return pagamentos, total_conferido, lucro_dia, diferenca

    def _update_close_totals(self):
        try:
            _, total_conferido, lucro_dia, diferenca = self._calculate_close_result()
        except ValueError:
            if self.metrics_vars:
                self.metrics_vars["total_conferido"].set("Valor inválido")
                self.metrics_vars["lucro_dia"].set("Valor inválido")
                self.metrics_vars["diferenca"].set("Valor inválido")
            return

        self.metrics_vars["total_conferido"].set(self._format_currency(total_conferido))
        self.metrics_vars["lucro_dia"].set(self._format_currency(lucro_dia))
        if abs(diferenca) < 0.01:
            self.metrics_vars["diferenca"].set("Caixa batido")
        else:
            self.metrics_vars["diferenca"].set(self._format_currency(diferenca))

    def on_confirm(self):
        try:
            if self.close_summary:
                pagamentos, total_conferido, lucro_dia, diferenca = self._calculate_close_result()
                if any(valor < 0 for valor in pagamentos.values()):
                    messagebox.showerror(
                        "Erro",
                        "Os valores informados não podem ser negativos.",
                        parent=self,
                    )
                    return
                self.value = {
                    "pagamentos": pagamentos,
                    "total_conferido": total_conferido,
                    "lucro_dia": lucro_dia,
                    "diferenca": diferenca,
                }
                self.confirmed = True
                self.destroy()
                self.callback(self.value)
                return

            valor = float(self.valor_entry.get().replace(",", "."))
            if valor < 0:
                messagebox.showerror("Erro", "O valor não pode ser negativo.", parent=self)
                return
            self.value = valor
            self.confirmed = True
            self.destroy()
            self.callback(valor)
        except ValueError:
            messagebox.showerror(
                "Erro",
                "Por favor, insira um valor numerico valido.",
                parent=self,
            )

    def on_cancel(self):
        self.confirmed = False
        self.value = None
        self.destroy()


class ImprimirDialog(tk.Toplevel):
    def __init__(self, parent, note_text, tipo_nota):
        super().__init__(parent)
        self.parent = parent
        self.note_text = note_text
        self.tipo_nota = tipo_nota
        theme, card, body = build_dialog_shell(
            self,
            parent,
            f"Nota {tipo_nota.capitalize()}",
            subtitle="Confira o conteudo antes de imprimir o comprovante.",
            size=(940, 720),
            controller=parent,
        )
        self.theme = theme

        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        preview_frame = tk.Frame(body, bg=theme["surface"])
        preview_frame.grid(row=0, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        text_widget = tk.Text(
            preview_frame,
            font=("Consolas", 10),
            bg="#FCFDF8",
            fg=theme["text"],
            relief="flat",
            padx=16,
            pady=16,
            wrap="none",
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        text_widget.insert("1.0", self.note_text)
        text_widget.config(state=tk.DISABLED)

        scrollbar_y = ttk.Scrollbar(preview_frame, orient="vertical", command=text_widget.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=text_widget.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        btn_frame = tk.Frame(body, bg=theme["surface"])
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        btn_print = tk.Button(btn_frame, text="Imprimir", command=self.handle_print)
        style_button(btn_print, "primary", theme).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        btn_close = tk.Button(btn_frame, text="Fechar", command=self.destroy)
        style_button(btn_close, "secondary", theme).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.minsize(860, 620)
        self.wait_window()

    def handle_print(self):
        if self.tipo_nota == "simplificada":
            self.parent.imprimir_nota_simplificada()
        elif self.tipo_nota == "completa":
            self.parent.imprimir_nota_completa()
        self.destroy()

class EmpresaInfoDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        theme, card, body = build_dialog_shell(
            self,
            parent,
            "Informações da Empresa",
            subtitle="Mantenha os dados institucionais atualizados para relatórios e documentos.",
            size=(760, 560),
            controller=parent,
        )
        self.theme = theme
        self.entries = {}
        self._build_form(body)
        self.load_info()

    def _build_form(self, body):
        grid = tk.Frame(body, bg=self.theme["surface"])
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(1, weight=1)

        labels = ["Nome Fantasia", "Razão Social", "CNPJ", "Endereço", "Cidade", "Estado", "CEP", "Telefone", "E-mail"]
        for i, text in enumerate(labels):
            make_form_label(grid, f"{text}:", self.theme).grid(row=i, column=0, sticky="w", pady=6, padx=(0, 10))
            entry = make_entry(grid, self.theme)
            entry.grid(row=i, column=1, sticky="ew", pady=6)
            self.entries[text.lower().replace('?', 'a').replace('?', 'o').replace('?', 'c').replace(' ', '_')] = entry

        action = tk.Frame(body, bg=self.theme["surface"])
        action.pack(fill="x", pady=(18, 0))
        btn_save = tk.Button(action, text="Salvar", command=self.save_info)
        style_button(btn_save, "primary", self.theme).pack(anchor="e")

    def load_info(self):
        info = get_company_info()
        if info:
            mapping = {
                'nome_fantasia': 'nome_fantasia',
                'razao_social': 'razao_social',
                'cnpj': 'cnpj',
                'endereco': 'endereco',
                'cidade': 'cidade',
                'estado': 'estado',
                'cep': 'cep',
                'telefone': 'telefone',
                'email': 'email',
            }
            for key, info_key in mapping.items():
                entry = self.entries.get(key)
                if entry and info.get(info_key) is not None:
                    entry.delete(0, tk.END)
                    entry.insert(0, info[info_key])

    def save_info(self):
        data = {
            "nome_fantasia": self.entries["nome_fantasia"].get(),
            "razao_social": self.entries["razao_social"].get(),
            "cnpj": self.entries["cnpj"].get(),
            "endereco": self.entries["endereco"].get(),
            "cidade": self.entries["cidade"].get(),
            "estado": self.entries["estado"].get(),
            "cep": self.entries["cep"].get(),
            "telefone": self.entries["telefone"].get(),
            "email": self.entries["email"].get(),
        }
        if save_company_info(**data):
            messagebox.showinfo("Sucesso", "Informações da empresa salvas com sucesso!", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Erro", "Falha ao salvar informações da empresa.", parent=self)

class FinalizarVendaDialog(tk.Toplevel):
    def __init__(self, parent, total_venda, callback_finalizar):
        super().__init__(parent)
        self.parent = parent
        self.total_venda = total_venda
        self.callback_finalizar = callback_finalizar
        self.metodo_pagamento = tk.StringVar(self, value="CARTAO_CREDITO")
        self.valor_pago_var = tk.StringVar(self, value=f"{self.total_venda:.2f}".replace('.', ','))
        self.theme, _, body = build_dialog_shell(
            self,
            parent,
            "Finalizar Venda",
            subtitle=None,
            size=(760, 500),
            controller=parent,
        )
        self._build_layout(body)
        self.on_metodo_change()
        self.wait_window()

    def _build_layout(self, body):
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=0)
        body.rowconfigure(1, weight=0)
        body.rowconfigure(2, weight=0)

        metodo_container = tk.Frame(body, bg=self.theme["surface_alt"], padx=14, pady=14)
        metodo_container.grid(row=0, column=0, sticky="ew")
        tk.Label(metodo_container, text="Forma de pagamento", font=("Segoe UI Semibold", 14), bg=self.theme["surface_alt"], fg=self.theme["text"]).pack(anchor="w")

        opcoes = [
            ("Cartao de Credito", "CARTAO_CREDITO"),
            ("Cartao de Debito", "CARTAO_DEBITO"),
            ("PIX", "PIX"),
            ("QR Code", "QR_CODE"),
            ("Dinheiro", "DINHEIRO"),
        ]
        for texto, valor in opcoes:
            tk.Radiobutton(
                metodo_container,
                text=texto,
                variable=self.metodo_pagamento,
                value=valor,
                command=self.on_metodo_change,
                font=("Segoe UI", 11),
                bg=self.theme["surface_alt"],
                activebackground=self.theme["surface_alt"],
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=6)

        resumo = tk.Frame(body, bg=self.theme["surface"], padx=18, pady=18)
        resumo.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        tk.Label(resumo, text="Total da venda", font=("Segoe UI", 12), bg=self.theme["surface"], fg=self.theme["text_muted"]).pack(anchor="w")
        tk.Label(resumo, text=f"R$ {self.total_venda:.2f}".replace('.', ','), font=("Segoe UI Black", 24), bg=self.theme["surface"], fg=self.theme["danger"]).pack(anchor="w", pady=(6, 20))

        self.dinheiro_frame = tk.Frame(resumo, bg=self.theme["surface"])
        self.dinheiro_frame.pack(fill="x")
        make_form_label(self.dinheiro_frame, "Valor recebido (R$)", self.theme).pack(anchor="w")
        self.valor_pago_entry = make_entry(self.dinheiro_frame, self.theme, textvariable=self.valor_pago_var, justify="right")
        self.valor_pago_entry.pack(fill="x", ipady=8, pady=(6, 10))

        self.btn_calcular = tk.Button(self.dinheiro_frame, text="Calcular troco", command=self.calcular_e_mostrar_troco)
        style_button(self.btn_calcular, "primary", self.theme).pack(fill="x")

        self.troco_label = tk.Label(self.dinheiro_frame, text="TROCO: R$ 0,00", font=("Segoe UI Semibold", 11), fg="#1D4ED8", bg=self.theme["surface"])
        self.troco_label.pack(anchor="w", pady=(12, 0))

        action = tk.Frame(body, bg=self.theme["surface"])
        action.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)

        btn_cancel = tk.Button(action, text="Cancelar", command=self.destroy)
        style_button(btn_cancel, "secondary", self.theme).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        btn_finish = tk.Button(action, text="Finalizar venda", command=self.processar_pagamento)
        style_button(btn_finish, "success", self.theme).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def on_metodo_change(self):
        metodo = self.metodo_pagamento.get()
        if metodo == "DINHEIRO":
            self.dinheiro_frame.pack(fill="x")
            self.valor_pago_entry.focus_set()
            self.valor_pago_var.set(f"{self.total_venda:.2f}".replace('.', ','))
            self.troco_label.config(text="TROCO: R$ 0,00", fg="#1D4ED8")
        else:
            self.dinheiro_frame.pack_forget()

    def calcular_e_mostrar_troco(self):
        try:
            valor_pago = float(self.valor_pago_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Valor pago inválido.", parent=self)
            return

        troco = calcular_troco(self.total_venda, valor_pago)
        if troco == 0.0 and valor_pago < self.total_venda:
            self.troco_label.config(text="Valor insuficiente", fg=self.theme["danger"])
        else:
            self.troco_label.config(text=f"TROCO: R$ {troco:.2f}".replace('.', ','), fg="#1D4ED8")

    def processar_pagamento(self):
        metodo = self.metodo_pagamento.get()
        valor_pago = self.total_venda
        troco = 0.0

        if metodo == "DINHEIRO":
            try:
                valor_pago = float(self.valor_pago_var.get().replace(',', '.'))
                troco = calcular_troco(self.total_venda, valor_pago)
            except ValueError:
                messagebox.showerror("Erro", "Valor pago inválido.", parent=self)
                return

            if valor_pago < self.total_venda:
                messagebox.showwarning("Atenção", "Valor pago insuficiente!", parent=self)
                return

            self.callback_finalizar(metodo, valor_pago, troco)
            self.destroy()
            return

        if metodo in ["CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "QR_CODE"]:
            self.callback_finalizar(metodo, self.total_venda, 0.0)
            self.destroy()
            return

        messagebox.showwarning("Atenção", f"Método de pagamento '{metodo}' inválido ou não suportado.", parent=self)


class CadastroProdutoDialog(tk.Toplevel):
    def __init__(self, parent, controller, product_data=None):
        super().__init__(parent)
        self.controller = controller
        self.product_data = product_data
        self.is_editing = product_data is not None
        title = "Editar Produto" if self.is_editing else "Cadastrar Produto"
        subtitle = (
            "Atualize as informacoes do item no cadastro."
            if self.is_editing
            else "Preencha os dados principais para incluir um novo item no estoque."
        )
        self.theme, self.card, self.body = build_dialog_shell(
            self,
            parent,
            title,
            subtitle=subtitle,
            size=(860, 550),
            controller=controller,
        )
        self.create_form_widgets()

    def create_form_widgets(self):
        form_frame = tk.Frame(self.body, bg=self.theme["surface"])
        form_frame.pack(fill="both", expand=True)
        for column in range(4):
            form_frame.columnconfigure(column, weight=1)

        make_form_label(form_frame, "Nome do produto", self.theme).grid(row=0, column=0, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 6))
        make_form_label(form_frame, "Código de barras", self.theme).grid(row=0, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=(0, 6))
        self.produto_nome_entry = make_entry(form_frame, self.theme)
        self.produto_nome_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 10), ipady=8, pady=(0, 14))
        self.cod_barras_entry = make_entry(form_frame, self.theme)
        self.cod_barras_entry.grid(row=1, column=2, columnspan=2, sticky="ew", padx=(10, 0), ipady=8, pady=(0, 14))

        make_form_label(form_frame, "Preco (R$)", self.theme).grid(row=2, column=0, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 6))
        make_form_label(form_frame, "Estoque", self.theme).grid(row=2, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=(0, 6))
        self.produto_preco_entry = make_entry(form_frame, self.theme)
        self.produto_preco_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 10), ipady=8, pady=(0, 14))
        self.produto_estoque_entry = make_entry(form_frame, self.theme)
        self.produto_estoque_entry.grid(row=3, column=2, columnspan=2, sticky="ew", padx=(10, 0), ipady=8, pady=(0, 14))

        make_form_label(form_frame, "Unidade", self.theme).grid(row=4, column=0, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 6))
        make_form_label(form_frame, "SKU", self.theme).grid(row=4, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=(0, 6))
        self.produto_unidade_entry = ttk.Combobox(form_frame, values=["kg", "un"], state="readonly", font=("Segoe UI", 11))
        self.produto_unidade_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=(0, 10), ipady=6)
        self.produto_unidade_entry.set("un")
        self.sku_entry = make_entry(form_frame, self.theme)
        self.sku_entry.grid(row=5, column=2, columnspan=2, sticky="ew", padx=(10, 0), ipady=8)

        if self.is_editing:
            data = self.product_data
            self.produto_nome_entry.insert(0, data[1])
            self.produto_preco_entry.insert(0, f"{data[2]:.2f}".replace(".", ","))
            self.produto_estoque_entry.insert(0, f"{data[3]:.2f}".replace(".", ","))
            self.produto_unidade_entry.set(data[4])
            self.cod_barras_entry.insert(0, str(data[5]) if data[5] is not None else "")
            self.sku_entry.insert(0, str(data[6]) if data[6] is not None else "")

        action_frame = tk.Frame(self.body, bg=self.theme["surface"])
        action_frame.pack(fill="x", pady=(22, 0))
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        btn_text = "Salvar Alteracoes" if self.is_editing else "Adicionar Produto"
        btn_add_produto = tk.Button(action_frame, text=btn_text, command=self.salvar_e_fechar)
        style_button(btn_add_produto, "primary", self.theme).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        btn_cancelar = tk.Button(action_frame, text="Cancelar", command=self.destroy)
        style_button(btn_cancelar, "danger", self.theme).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def salvar_e_fechar(self):
        try:
            produto_data = {
                "nome": self.produto_nome_entry.get(),
                "preco": float(self.produto_preco_entry.get().replace(",", ".")),
                "estoque": float(self.produto_estoque_entry.get().replace(",", ".")),
                "unidade": self.produto_unidade_entry.get(),
                "cod_barras": self.cod_barras_entry.get(),
                "sku": self.sku_entry.get(),
            }
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Os campos Preco e Estoque devem ser numeros validos.", parent=self)
            return

        success = False
        if self.is_editing:
            produto_id = self.product_data[0]
            success = self.controller.atualizar_produto_via_dialog(produto_id, produto_data)
        else:
            success = self.controller.salvar_produto_via_dialog(produto_data)

        if success:
            self.destroy()


class CadastroFuncionarioDialog(tk.Toplevel):
    def __init__(self, parent, controller, employee_data=None):
        super().__init__(parent)
        self.controller = controller
        self.employee_data = employee_data
        self.is_editing = employee_data is not None
        self.compact_mode = parent.winfo_screenwidth() <= 1180 or parent.winfo_screenheight() <= 800
        title = "Editar Funcionario" if self.is_editing else "Cadastrar Funcionario"
        subtitle = (
            "Ajuste credenciais, cargo e dados operacionais do colaborador."
            if self.is_editing
            else "Cadastre um novo operador para acesso ao sistema."
        )
        dialog_width = min(860, max(parent.winfo_screenwidth() - 90, 620))
        dialog_height = min(550, max(parent.winfo_screenheight() - 120, 420))
        self.theme, self.card, self.body = build_dialog_shell(
            self,
            parent,
            title,
            subtitle=subtitle,
            size=(dialog_width, dialog_height),
            controller=controller,
        )
        self.create_form_widgets()

    def create_form_widgets(self):
        form_frame = tk.Frame(self.body, bg=self.theme["surface"])
        form_frame.pack(fill="both", expand=True)
        total_columns = 2 if self.compact_mode else 4
        for column in range(total_columns):
            form_frame.columnconfigure(column, weight=1)

        entry_pad_y = 6 if self.compact_mode else 8
        action_gap = 6 if self.compact_mode else 8
        label_gap = (0, 4) if self.compact_mode else (0, 6)
        cargo_font = ("Segoe UI", 10 if self.compact_mode else 11)

        make_form_label(form_frame, "Nome completo", self.theme).grid(row=0, column=0, columnspan=total_columns, sticky="w", pady=label_gap)
        self.funcionario_nome_entry = make_entry(form_frame, self.theme)
        self.funcionario_nome_entry.grid(row=1, column=0, columnspan=total_columns, sticky="ew", ipady=entry_pad_y, pady=(0, 12 if self.compact_mode else 14))

        make_form_label(form_frame, "Usuário", self.theme).grid(row=2, column=0, columnspan=1, sticky="w", padx=(0, 8), pady=label_gap)
        make_form_label(form_frame, "Cargo", self.theme).grid(row=2, column=1, columnspan=1, sticky="w", padx=(8, 0), pady=label_gap)
        self.funcionario_usuario_entry = make_entry(form_frame, self.theme)
        self.funcionario_usuario_entry.grid(row=3, column=0, columnspan=1, sticky="ew", padx=(0, 8), ipady=entry_pad_y, pady=(0, 12 if self.compact_mode else 14))
        self.funcionario_cargo_entry = ttk.Combobox(form_frame, values=["Caixa", "Gerente"], state="readonly", font=cargo_font)
        self.funcionario_cargo_entry.grid(row=3, column=1, columnspan=1, sticky="ew", padx=(8, 0), ipady=entry_pad_y - 1, pady=(0, 12 if self.compact_mode else 14))
        self.funcionario_cargo_entry.set("Caixa")

        senha_label = "Nova senha" if self.is_editing else "Senha"
        make_form_label(form_frame, senha_label, self.theme).grid(row=4, column=0, columnspan=1, sticky="w", padx=(0, 8), pady=label_gap)
        self.funcionario_senha_entry = make_entry(form_frame, self.theme, show="*")
        self.funcionario_senha_entry.grid(row=5, column=0, columnspan=1, sticky="ew", padx=(0, 8), ipady=entry_pad_y)
        if self.is_editing:
            tk.Label(
                form_frame,
                text="Deixe em branco para manter a senha atual.",
                font=("Segoe UI", 8 if self.compact_mode else 9),
                bg=self.theme["surface"],
                fg=self.theme["text_muted"],
                wraplength=220 if self.compact_mode else 260,
                justify="left",
            ).grid(row=5, column=1, columnspan=1, sticky="w", padx=(8, 0))

        if self.is_editing:
            data = self.employee_data
            self.funcionario_nome_entry.insert(0, data[1])
            self.funcionario_usuario_entry.insert(0, data[2])
            self.funcionario_cargo_entry.set(data[4])

        action_frame = tk.Frame(self.body, bg=self.theme["surface"])
        action_frame.pack(fill="x", pady=(16 if self.compact_mode else 22, 0))
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        btn_text = "Salvar Alterações" if self.is_editing else "Adicionar Funcionário"
        btn_add_funcionario = tk.Button(action_frame, text=btn_text, command=self.salvar_e_fechar)
        style_button(btn_add_funcionario, "primary", self.theme).grid(row=0, column=0, padx=(0, action_gap), sticky="ew")
        btn_cancelar = tk.Button(action_frame, text="Cancelar", command=self.destroy)
        style_button(btn_cancelar, "danger", self.theme).grid(row=0, column=1, padx=(action_gap, 0), sticky="ew")

    def salvar_e_fechar(self):
        funcionario_data = {
            "nome": self.funcionario_nome_entry.get(),
            "usuario": self.funcionario_usuario_entry.get(),
            "senha": self.funcionario_senha_entry.get(),
            "cargo": self.funcionario_cargo_entry.get(),
        }

        success = False
        if self.is_editing:
            employee_id = self.employee_data[0]
            success = self.controller.atualizar_funcionario_via_dialog(employee_id, funcionario_data)
        else:
            success = self.controller.salvar_funcionario_via_dialog(funcionario_data)

        if success:
            self.destroy()


class EdicaoCarrinhoDialog(tk.Toplevel):
    def __init__(self, parent, controller, item_data, item_index):
        super().__init__(parent)
        self.controller = controller
        self.item_data = item_data
        self.item_index = item_index
        self.theme, self.card, self.body = build_dialog_shell(
            self,
            parent,
            "Editar Item do Carrinho",
            subtitle="Ajuste a quantidade do item selecionado sem sair da venda em andamento.",
            size=(600, 500),
            controller=controller,
        )
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.body, bg=self.theme["surface"])
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)

        info_card = tk.Frame(main_frame, bg=self.theme["surface_alt"], padx=16, pady=14)
        info_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        tk.Label(info_card, text="Produto", font=("Segoe UI", 9), bg=self.theme["surface_alt"], fg=self.theme["text_muted"]).pack(anchor="w")
        tk.Label(info_card, text=self.item_data["nome"], font=("Segoe UI Semibold", 13), bg=self.theme["surface_alt"], fg=self.theme["text"]).pack(anchor="w", pady=(4, 0))

        unidade_display = self.item_data.get("unidade", "un")
        if unidade_display == "unidade":
            unidade_display = "un"

        make_form_label(main_frame, f"Nova quantidade ({unidade_display})", self.theme).grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.new_qty_entry = make_entry(main_frame, self.theme)
        self.new_qty_entry.insert(0, f"{self.item_data['quantidade']:.3f}".replace(".", ","))
        self.new_qty_entry.grid(row=2, column=0, sticky="ew", ipady=8)
        self.new_qty_entry.bind("<Return>", lambda event: self.save_changes())

        action_frame = tk.Frame(main_frame, bg=self.theme["surface"])
        action_frame.grid(row=3, column=0, sticky="ew", pady=(22, 0))
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        btn_salvar = tk.Button(action_frame, text="Salvar Alteraões", command=self.save_changes)
        style_button(btn_salvar, "primary", self.theme).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        btn_cancelar = tk.Button(action_frame, text="Cancelar", command=self.destroy)
        style_button(btn_cancelar, "danger", self.theme).grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def save_changes(self):
        try:
            new_qty = float(self.new_qty_entry.get().replace(",", "."))
            if new_qty <= 0:
                messagebox.showerror("Erro", "Quantidade deve ser maior que zero.", parent=self)
                return

            target_cart = getattr(self.controller, "carrinho_itens", None)
            if target_cart is None:
                target_cart = getattr(self.controller, "carrinho", None)
            if target_cart is None:
                raise AttributeError("Controlador sem carrinho ativo.")

            target_cart[self.item_index]["quantidade"] = new_qty
            target_cart[self.item_index]["subtotal"] = new_qty * self.item_data["preco"]
            self.controller.atualizar_carrinho_treeview()
            self.controller.atualizar_total()
            messagebox.showinfo("Sucesso", "Item atualizado no carrinho.", parent=self)
            self.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida. Use apenas numeros.", parent=self)


class AdicionarItemDialog(tk.Toplevel):
    STABLE_SAMPLES_REQUIRED = 5
    STABLE_DELTA = 0.003
    WEIGHT_TIMEOUT_SECONDS = 8.0

    def __init__(self, parent, callback, callback_adicionar, balanca_instance=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.callback_adicionar = callback_adicionar
        self.balanca = balanca_instance
        self.theme, self.card, self.body = build_dialog_shell(
            self,
            parent,
            None,
            subtitle=None,
            size=(800, 600),
            controller=parent,
        )
        self.monitorando_balanca = True
        self.balanca_ativa = False
        self.produto_selecionado = None
        self._ultimo_peso = None
        self._stable_count = 0
        self._stable_weight = None
        self._kg_started_at = None
        self._timed_out = False
        self._clock = __import__("time").monotonic
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        self.produto_entry.focus_set()
        self.loop_leitura_balanca()

    def _build_ui(self):
        self.body.columnconfigure(0, weight=7)
        self.body.columnconfigure(1, weight=5)
        self.body.rowconfigure(1, weight=1)

        left = tk.Frame(self.body, bg=self.theme["surface"])
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)

        right = tk.Frame(self.body, bg=self.theme["surface"])
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.columnconfigure(0, weight=1)

        top_hint = tk.Frame(left, bg="#EDF7EF", padx=16, pady=14)
        top_hint.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(top_hint, text="Lançamento rápido", font=("Segoe UI Semibold", 13), bg="#EDF7EF", fg=self.theme["text"]).pack(anchor="w")
        tk.Label(top_hint, text="Digite nome, SKU ou código e confirme o item sem sair da operação.", font=("Segoe UI", 10), bg="#EDF7EF", fg=self.theme["text_muted"], wraplength=360, justify="left").pack(anchor="w", pady=(4, 0))

        make_form_label(left, "Produto", self.theme).grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.produto_var = tk.StringVar()
        self.produto_entry = ttk.Combobox(left, textvariable=self.produto_var, font=("Segoe UI", 12))
        self.produto_entry.grid(row=2, column=0, sticky="ew", ipady=6, pady=(0, 14))
        self.produto_entry.bind('<<ComboboxSelected>>', self.verificar_tipo_produto)
        self.produto_entry.bind('<KeyRelease>', self.filtrar_produtos)
        self.produto_entry.bind('<Return>', self._on_produto_submit)
        self.produto_entry.bind('<KP_Enter>', self._on_produto_submit)

        quantity_card = tk.Frame(left, bg=self.theme["surface_alt"], padx=18, pady=18)
        quantity_card.grid(row=3, column=0, sticky="ew")
        quantity_card.columnconfigure(0, weight=1)
        tk.Label(quantity_card, text="Quantidade / peso", font=("Segoe UI Semibold", 11), bg=self.theme["surface_alt"], fg=self.theme["text"]).grid(row=0, column=0, sticky="w")
        tk.Label(quantity_card, text="Para produtos por KG, o peso só é liberado quando estabiliza.", font=("Segoe UI", 9), bg=self.theme["surface_alt"], fg=self.theme["text_muted"], wraplength=340, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 12))
        self.quantidade_var = tk.StringVar(value="1")
        self.quantidade_entry = make_entry(quantity_card, self.theme, textvariable=self.quantidade_var, justify="center")
        self.quantidade_entry.grid(row=2, column=0, sticky="ew", ipady=14)
        self.quantidade_entry.configure(font=("Segoe UI Black", 22))


        metrics_card = tk.Frame(right, bg="#FFF7ED", padx=18, pady=18)
        metrics_card.grid(row=0, column=0, sticky="ew")
        metrics_card.columnconfigure(0, weight=1)
        tk.Label(metrics_card, text="Status da balança", font=("Segoe UI Semibold", 13), bg="#FFF7ED", fg=self.theme["text"]).grid(row=0, column=0, sticky="w")
        self.status_conexao = tk.Label(metrics_card, text="Conexão: verificando...", font=("Segoe UI Semibold", 10), bg="#FFF7ED", fg=self.theme["text_muted"])
        self.status_conexao.grid(row=1, column=0, sticky="w", pady=(10, 6))
        self.status_balanca = tk.Label(metrics_card, text="Peso: aguardando produto por KG...", font=("Segoe UI", 10), bg="#FFF7ED", fg=self.theme["text_muted"], wraplength=240, justify="left")
        self.status_balanca.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.status_estabilidade = tk.Label(metrics_card, text="Estabilidade: não iniciada", font=("Segoe UI", 10), bg="#FFF7ED", fg=self.theme["text_muted"], wraplength=240, justify="left")
        self.status_estabilidade.grid(row=3, column=0, sticky="w")

        weight_card = tk.Frame(right, bg="#EEF3FF", padx=18, pady=18)
        weight_card.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        weight_card.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        tk.Label(weight_card, text="Peso atual", font=("Segoe UI Semibold", 11), bg="#EEF3FF", fg=self.theme["text"]).grid(row=0, column=0, sticky="w")
        self.weight_display = tk.Label(weight_card, text="0,000 kg", font=("Segoe UI Black", 28), bg="#EEF3FF", fg="#1E5AA7")
        self.weight_display.grid(row=1, column=0, sticky="w", pady=(8, 16))
        tk.Label(weight_card, text="Fluxo recomendado", font=("Segoe UI Semibold", 11), bg="#EEF3FF", fg=self.theme["text"]).grid(row=2, column=0, sticky="w")
        for idx, step in enumerate([
            "1. Busque e selecione o produto.",
            "2. Se for KG, aguarde a leitura estabilizar.",
            "3. Pressione Enter para concluir.",
        ], start=3):
            tk.Label(weight_card, text=step, font=("Segoe UI", 10), bg="#EEF3FF", fg=self.theme["text_muted"], wraplength=250, justify="left").grid(row=idx, column=0, sticky="w", pady=(6 if idx == 3 else 4, 0))

        action_bar = tk.Frame(self.body, bg=self.theme["surface"])
        action_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        action_bar.columnconfigure(0, weight=1)
        action_bar.columnconfigure(1, weight=1)
        btn_cancel = tk.Button(action_bar, text="Cancelar", command=self.ao_fechar)
        style_button(btn_cancel, "secondary", self.theme).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        btn_add = tk.Button(action_bar, text="Adicionar (Enter)", command=self.confirmar)
        style_button(btn_add, "success", self.theme).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.bind('<Return>', lambda _e: self.confirmar())
        self.bind('<Escape>', lambda _e: self.ao_fechar())

    def _resolver_produto_digitado(self, texto):
        texto = str(texto or "").strip()
        if not texto:
            return None

        produto = get_product_by_code(texto)
        if produto:
            return produto

        nome_base = texto.split(" - ")[0].strip()
        return get_product_by_name(nome_base)

    def _on_produto_submit(self, _event=None):
        produto = self._resolver_produto_digitado(self.produto_var.get())
        if produto:
            self.produto_selecionado = produto
            self.produto_var.set(produto[1])
            self.produto_entry['values'] = [produto[1]]
            self.verificar_tipo_produto()
            self.quantidade_entry.focus_set()
        return "break"

    def filtrar_produtos(self, event):
        busca = self.produto_var.get().strip()
        if len(busca) <= 1:
            return

        produto_exato = self._resolver_produto_digitado(busca)
        if produto_exato:
            self.produto_selecionado = produto_exato
            self.produto_entry['values'] = [produto_exato[1]]
            return

        self.produto_entry['values'] = filter_products_for_combobox(busca.upper())

    def _reset_weight_tracking(self):
        self._ultimo_peso = None
        self._stable_count = 0
        self._stable_weight = None
        self._kg_started_at = self._clock() if self.balanca_ativa else None
        self._timed_out = False

    def verificar_tipo_produto(self, event=None):
        try:
            texto = self.produto_var.get().strip()
            if not texto:
                return
            self.produto_selecionado = self._resolver_produto_digitado(texto)
            if not self.produto_selecionado:
                return
            self.produto_var.set(self.produto_selecionado[1])
            unidade = self.produto_selecionado[4].upper()
            if unidade == 'KG':
                self.balanca_ativa = True
                self.quantidade_entry.config(state='normal')
                self.quantidade_entry.delete(0, tk.END)
                self.status_balanca.config(text="Peso: aguardando leitura da balança...", fg="#0B6D36")
                self.status_estabilidade.config(text="Estabilidade: coletando amostras...", fg="#A16207")
                self._reset_weight_tracking()
            else:
                self.balanca_ativa = False
                self.quantidade_var.set("1")
                self.weight_display.config(text="manual")
                self.status_balanca.config(text="Produto unitário. Quantidade manual liberada.", fg="#1E5AA7")
                self.status_estabilidade.config(text="Estabilidade: não se aplica", fg=self.theme["text_muted"])
        except Exception as e:
            print(f"Erro ao verificar produto: {e}")

    def _atualizar_status_conexao(self, status):
        porta = status.get("port") or "serial"
        if status.get("connected"):
            self.status_conexao.config(text=f"Conexão: online | {porta}", fg="#0B6D36")
        else:
            erro = str(status.get("last_error") or "sem resposta")
            erro_upper = erro.upper()
            if "COULD NOT OPEN PORT" in erro_upper or "ACCESS IS DENIED" in erro_upper:
                erro_curto = f"{porta} indisponível"
            elif "FILENOTFOUNDERROR" in erro_upper:
                erro_curto = "porta não encontrada"
            elif "NENHUMA PORTA SERIAL DISPONIVEL" in erro_upper:
                erro_curto = "nenhuma porta serial"
            elif len(erro) > 42:
                erro_curto = erro[:42].rstrip() + "..."
            else:
                erro_curto = erro
            self.status_conexao.config(text=f"Conexão: offline | {erro_curto}", fg="#B91C1C")

    def _processar_estabilidade(self, peso):
        if self._ultimo_peso is None or abs(peso - self._ultimo_peso) <= self.STABLE_DELTA:
            self._stable_count += 1
        else:
            self._stable_count = 1
        self._ultimo_peso = peso
        self._stable_weight = peso
        if self._stable_count >= self.STABLE_SAMPLES_REQUIRED and peso > 0.005:
            self.status_estabilidade.config(text=f"Estabilidade: peso confirmado em {peso:.3f} kg", fg="#0B6D36")
            return True
        self.status_estabilidade.config(text=f"Estabilidade: {self._stable_count}/{self.STABLE_SAMPLES_REQUIRED} leituras semelhantes", fg="#A16207")
        return False

    def loop_leitura_balanca(self):
        if not self.monitorando_balanca:
            return
        status = self.balanca.obter_status() if self.balanca else {
            "connected": False,
            "weight": 0.0,
            "last_read_age": None,
            "last_error": "Balança indisponível",
        }
        self._atualizar_status_conexao(status)

        if self.balanca_ativa and self.balanca:
            peso = status.get("weight", 0.0)
            self.quantidade_entry.delete(0, tk.END)
            self.quantidade_entry.insert(0, f"{peso:.3f}".replace('.', ','))
            self.weight_display.config(text=f"{peso:.3f} kg".replace('.', ','))
            if self._kg_started_at and self._clock() - self._kg_started_at > self.WEIGHT_TIMEOUT_SECONDS and peso <= 0.005:
                self._timed_out = True
                self.status_balanca.config(text="Peso: timeout de leitura. Confira a conexão ou reposicione o item.", fg="#B91C1C")
                self.status_estabilidade.config(text="Estabilidade: aguardando nova leitura válida", fg="#B91C1C")
            else:
                if peso <= 0.005:
                    self.status_balanca.config(text="Peso: aguardando item na balança...", fg=self.theme["text_muted"])
                    self.status_estabilidade.config(text="Estabilidade: aguardando peso mínimo", fg=self.theme["text_muted"])
                    self._stable_count = 0
                else:
                    self._timed_out = False
                    estavel = self._processar_estabilidade(peso)
                    if estavel:
                        self.status_balanca.config(text=f"Peso: {peso:.3f} kg pronto para adicionar".replace('.', ','), fg="#0B6D36")
                    else:
                        self.status_balanca.config(text=f"Peso: {peso:.3f} kg em estabilização...".replace('.', ','), fg="#A16207")
        elif self.produto_selecionado:
            self.status_estabilidade.config(text="Estabilidade: não se aplica", fg=self.theme["text_muted"])

        self.after(150, self.loop_leitura_balanca)

    def _peso_estavel_para_confirmar(self, quantidade):
        if not self.balanca_ativa:
            return True
        return (
            quantidade > 0.005
            and self._stable_weight is not None
            and abs(quantidade - self._stable_weight) <= self.STABLE_DELTA
            and self._stable_count >= self.STABLE_SAMPLES_REQUIRED
            and not self._timed_out
        )

    def confirmar(self):
        if not self.produto_selecionado:
            self.verificar_tipo_produto()
            if not self.produto_selecionado:
                messagebox.showwarning("Atencao", "Selecione um produto válido.", parent=self)
                return
        try:
            quantidade = float(self.quantidade_entry.get().replace(',', '.') or '0')
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida. Digite apenas numeros.", parent=self)
            return
        if quantidade <= 0:
            messagebox.showwarning("Erro", "Quantidade inválida.", parent=self)
            return
        if self.balanca_ativa and not self._peso_estavel_para_confirmar(quantidade):
            messagebox.showwarning("Peso ainda não estabilizado", "Aguarde o peso ficar estável antes de adicionar o item.", parent=self)
            return
        preco_unitario = self.produto_selecionado[2]
        subtotal = preco_unitario * quantidade
        self.callback_adicionar(self.produto_selecionado, quantidade, subtotal)
        self.ao_fechar()

    def ao_fechar(self):
        self.monitorando_balanca = False
        self.balanca_ativa = False
        if hasattr(self.parent, "ativar_monitor_balanca"):
            self.parent.ativar_monitor_balanca()
        self.grab_release()
        self.destroy()


class FinalizarVendaDialog(tk.Toplevel):
    PAYMENT_OPTIONS = [
        ("Cartão de Crédito", "CARTAO_CREDITO", None),
        ("Cartão de Débito", "CARTAO_DEBITO", None),
        ("PIX", "PIX", None),
        ("QR Code", "QR_CODE", None),
        ("Dinheiro", "DINHEIRO", None),
    ]

    def __init__(self, parent, total_venda, callback_finalizar):
        super().__init__(parent)
        self.parent = parent
        self.total_venda = total_venda
        self.callback_finalizar = callback_finalizar
        self.metodo_pagamento = tk.StringVar(self, value="CARTAO_CREDITO")
        self.valor_pago_var = tk.StringVar(self, value=f"{self.total_venda:.2f}".replace('.', ','))
        self.option_cards = []
        self.option_labels = []
        self.option_index = 0

        self.theme, _, body = build_dialog_shell(
            self,
            parent,
            None,
            subtitle=None,
            size=(760, 560),
            controller=parent,
        )
        self._build_layout(body)
        self._bind_keys()
        self.on_metodo_change()
        self._highlight_selected_option()
        self.wait_window()

    def _build_layout(self, body):
        body.columnconfigure(0, weight=7)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=0)

        metodo_container = tk.Frame(body, bg=self.theme["surface_alt"], padx=14, pady=14)
        metodo_container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        metodo_container.columnconfigure(0, weight=1)
        tk.Label(metodo_container, text="Forma de pagamento", font=("Segoe UI Semibold", 14), bg=self.theme["surface_alt"], fg=self.theme["text"]).grid(row=0, column=0, sticky="w")
        tk.Label(metodo_container, text="Use as setas para navegar e Enter para confirmar.", font=("Segoe UI", 9), bg=self.theme["surface_alt"], fg=self.theme["text_muted"], wraplength=430, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 10))

        options_grid = tk.Frame(metodo_container, bg=self.theme["surface_alt"])
        options_grid.grid(row=2, column=0, sticky="ew")
        options_grid.columnconfigure(0, weight=1)

        for idx, (titulo, valor, descricao) in enumerate(self.PAYMENT_OPTIONS):
            card = tk.Frame(options_grid, bg="#FFFFFF", padx=10, pady=7, cursor="hand2", highlightthickness=2, highlightbackground=self.theme["border"])
            card.grid(row=idx, column=0, sticky="ew", pady=2)
            card.columnconfigure(0, weight=0)
            card.columnconfigure(1, weight=1)
            card.columnconfigure(2, weight=0)

            index_lbl = tk.Label(card, text=f"{idx + 1:02d}", font=("Segoe UI Semibold", 9), width=3, bg="#FFFFFF", fg=self.theme["text_muted"])
            index_lbl.grid(row=0, column=0, sticky="w", padx=(0, 10))

            title_lbl = tk.Label(card, text=titulo, font=("Segoe UI Semibold", 10), bg="#FFFFFF", fg=self.theme["text"])
            title_lbl.grid(row=0, column=1, sticky="w")

            desc_lbl = tk.Label(card, text=descricao, font=("Segoe UI", 8), bg="#FFFFFF", fg=self.theme["text_muted"], justify="right")
            desc_lbl.grid(row=0, column=2, sticky="e")

            for widget in (card, index_lbl, title_lbl, desc_lbl):
                widget.bind("<Button-1>", lambda _e, index=idx: self._select_option(index, confirm=False))
                widget.bind("<Double-Button-1>", lambda _e, index=idx: self._select_option(index, confirm=True))

            self.option_cards.append(card)
            self.option_labels.append((index_lbl, title_lbl, desc_lbl))

        resumo = tk.Frame(body, bg=self.theme["surface"], padx=14, pady=14, highlightthickness=1, highlightbackground=self.theme["border"])
        resumo.grid(row=0, column=1, sticky="nsew")
        resumo.columnconfigure(0, weight=1)

        tk.Label(resumo, text="Resumo da venda", font=("Segoe UI", 11), bg=self.theme["surface"], fg=self.theme["text_muted"]).grid(row=0, column=0, sticky="w")
        tk.Label(resumo, text=f"R$ {self.total_venda:.2f}".replace('.', ','), font=("Segoe UI Black", 24), bg=self.theme["surface"], fg=self.theme["danger"]).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.selection_label = tk.Label(resumo, text="Selecionado: Cartão de Crédito", font=("Segoe UI Semibold", 10), bg=self.theme["surface"], fg=self.theme["text"])
        self.selection_label.grid(row=2, column=0, sticky="w", pady=(0, 12))

        self.dinheiro_frame = tk.Frame(resumo, bg=self.theme["surface"])
        self.dinheiro_frame.grid(row=3, column=0, sticky="ew")
        self.dinheiro_frame.columnconfigure(0, weight=1)
        make_form_label(self.dinheiro_frame, "Valor recebido (R$)", self.theme).grid(row=0, column=0, sticky="w")
        self.valor_pago_entry = make_entry(self.dinheiro_frame, self.theme, textvariable=self.valor_pago_var, justify="right")
        self.valor_pago_entry.grid(row=1, column=0, sticky="ew", ipady=6, pady=(4, 8))

        self.btn_calcular = tk.Button(self.dinheiro_frame, text="Calcular troco", command=self.calcular_e_mostrar_troco)
        style_button(self.btn_calcular, "primary", self.theme).grid(row=2, column=0, sticky="ew")

        self.troco_label = tk.Label(self.dinheiro_frame, text="TROCO: R$ 0,00", font=("Segoe UI Semibold", 11), fg="#1D4ED8", bg=self.theme["surface"])
        self.troco_label.grid(row=3, column=0, sticky="w", pady=(10, 0))

        action = tk.Frame(body, bg=self.theme["surface"])
        action.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)
        btn_cancel = tk.Button(action, text="Cancelar", command=self.destroy)
        style_button(btn_cancel, "secondary", self.theme).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_finish = tk.Button(action, text="Finalizar venda", command=self.processar_pagamento)
        style_button(self.btn_finish, "success", self.theme).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _bind_keys(self):
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self.processar_pagamento())
        self.bind("<Up>", lambda _e: self._move_selection(-1))
        self.bind("<Down>", lambda _e: self._move_selection(1))
        self.bind("<Left>", lambda _e: self._move_selection(-1))
        self.bind("<Right>", lambda _e: self._move_selection(1))

    def _move_selection(self, delta):
        total = len(self.PAYMENT_OPTIONS)
        new_index = self.option_index + delta
        if new_index < 0:
            new_index = 0
        if new_index >= total:
            new_index = total - 1
        self._select_option(new_index, confirm=False)

    def _select_option(self, index, confirm=False):
        self.option_index = index
        _, valor, _ = self.PAYMENT_OPTIONS[index]
        self.metodo_pagamento.set(valor)
        self._highlight_selected_option()
        self.on_metodo_change()
        if confirm:
            self.processar_pagamento()

    def _highlight_selected_option(self):
        for idx, card in enumerate(self.option_cards):
            selected = idx == self.option_index
            bg = "#EAF7EC" if selected else "#FFFFFF"
            border = self.theme["primary"] if selected else self.theme["border"]
            fg = self.theme["primary"] if selected else self.theme["text"]
            muted = "#2F6F4F" if selected else self.theme["text_muted"]
            card.configure(bg=bg, highlightbackground=border)
            labels = self.option_labels[idx]
            labels[0].configure(bg=bg, fg=muted)
            labels[1].configure(bg=bg, fg=fg)
            labels[2].configure(bg=bg, fg=muted)
        titulo = self.PAYMENT_OPTIONS[self.option_index][0]
        self.selection_label.config(text=f"Selecionado: {titulo}")

    def on_metodo_change(self):
        metodo = self.metodo_pagamento.get()
        if metodo == "DINHEIRO":
            self.dinheiro_frame.grid(row=3, column=0, sticky="ew")
            self.valor_pago_entry.focus_set()
            self.valor_pago_var.set(f"{self.total_venda:.2f}".replace('.', ','))
            self.troco_label.config(text="TROCO: R$ 0,00", fg="#1D4ED8")
        else:
            self.dinheiro_frame.grid_remove()
            self.btn_finish.focus_set()

    def calcular_e_mostrar_troco(self):
        try:
            valor_pago = float(self.valor_pago_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Valor pago inválido.", parent=self)
            return

        troco = calcular_troco(self.total_venda, valor_pago)
        if troco == 0.0 and valor_pago < self.total_venda:
            self.troco_label.config(text="Valor insuficiente", fg=self.theme["danger"])
        else:
            self.troco_label.config(text=f"TROCO: R$ {troco:.2f}".replace('.', ','), fg="#1D4ED8")

    def processar_pagamento(self):
        metodo = self.metodo_pagamento.get()
        valor_pago = self.total_venda
        troco = 0.0

        if metodo == "DINHEIRO":
            try:
                valor_pago = float(self.valor_pago_var.get().replace(',', '.'))
                troco = calcular_troco(self.total_venda, valor_pago)
            except ValueError:
                messagebox.showerror("Erro", "Valor pago inválido.", parent=self)
                return

            if valor_pago < self.total_venda:
                messagebox.showwarning("Atencao", "Valor pago insuficiente!", parent=self)
                return

            self.callback_finalizar(metodo, valor_pago, troco)
            self.destroy()
            return

        if metodo in ["CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "QR_CODE"]:
            self.callback_finalizar(metodo, self.total_venda, 0.0)
            self.destroy()
            return

        messagebox.showwarning("Atenção", f"Método de pagamento '{metodo}' inválido ou não suportado.", parent=self)
