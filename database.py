#Database
import sqlite3
import random
import string
from datetime import datetime
import hashlib
import ast
from utils import DB_PATH

SKU_START = 2001
EAN_PREFIX = "78900000"

# --- FUNÇÃO FUNDAMENTAL DE CONEXÃO ---
def get_db_connection(db_path=None):
    """Retorna uma conexao com o banco de dados."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password):
    """Cria um hash seguro para a senha."""
    salt = "sEnsE@P@55wOrd_frutaria" # Um "salt" fixo para este exemplo
    return hashlib.sha256(str.encode(password + salt)).hexdigest()

def check_password(password, hashed_password):
    """Verifica se a senha digitada corresponde ao hash armazenado."""
    return hash_password(password) == hashed_password

def setup_database(db_path=None):
    """Configura o banco de dados e cria as tabelas e colunas necessárias."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL,
            estoque REAL NOT NULL,
            unidade TEXT NOT NULL,
            cod_barras TEXT,
            sku TEXT UNIQUE
        )
    ''')

    # Tabela de Funcionários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            cargo TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    
    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_funcionario INTEGER NOT NULL,
            data_venda TEXT NOT NULL,
            total REAL NOT NULL,
            itens_vendidos TEXT NOT NULL,
            metodo_pagamento TEXT NOT NULL DEFAULT 'DINHEIRO', 
            valor_pago REAL NOT NULL DEFAULT 0.0,
            troco REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (id_funcionario) REFERENCES funcionarios(id)
        )
    ''')

    # 📌 ALTER TABLE (CORREÇÃO PARA TABELAS EXISTENTES)
    # Adiciona as colunas se elas ainda não existirem
    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN metodo_pagamento TEXT NOT NULL DEFAULT 'DINHEHEIRO'")
    except sqlite3.OperationalError:
        pass # Coluna já existe

    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN valor_pago REAL NOT NULL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass # Coluna já existe
        
    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN troco REAL NOT NULL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass # Coluna já existe

    # Tabela de Caixa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TEXT NOT NULL,
            data_fechamento TEXT,
            valor_abertura REAL NOT NULL,
            valor_fechamento REAL,
            total_vendas REAL,
            status TEXT NOT NULL CHECK(status IN ('aberto', 'fechado'))
        )
    ''')

    # --- ATUALIZAÇÃO DA TABELA EMPRESA ---
    # 1. Tenta criar a tabela com TODOS os campos novos se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY CHECK (id = 1), -- Garante linha única
            nome_fantasia TEXT,
            razao_social TEXT,
            cnpj TEXT,
            endereco TEXT,
            bairro TEXT,
            cidade TEXT,        -- Novo campo
            estado TEXT,        -- Novo campo
            cep TEXT,           -- Novo campo
            telefone TEXT,
            email TEXT,         -- Novo campo
            logo_path TEXT
        )
    ''')

    # --- MIGRAÇÃO AUTOMÁTICA (Para BD existentes) ---
    # Se o banco já existia sem os novos campos, tentamos adicioná-los.
    # Usamos try/except porque se a coluna já existir, o SQLite dará erro.
    new_columns = ['bairro', 'cidade', 'estado', 'cep', 'email']
    for col in new_columns:
        try:
            cursor.execute(f"ALTER TABLE empresa ADD COLUMN {col} TEXT")
            print(f"Coluna '{col}' adicionada à tabela 'empresa'.")
        except sqlite3.OperationalError:
            # Ignora o erro se a coluna já existir
            pass

    conn.commit()
    conn.close()

def add_multiple_products(products_list):
    """
    Insere uma lista de produtos no banco de dados usando inserção em lote (batch insertion).
    products_list deve ser uma lista de tuplas: 
    [(nome, preco, estoque, unidade, cod_barras, sku), ...]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # A query de INSERT INTO deve ter o número exato de placeholders (?)
    # que correspondem às colunas.
    # Colunas: nome, preco, estoque, unidade, cod_barras, sku
    insert_query = """
        INSERT INTO produtos (nome, preco, estoque, unidade, cod_barras, sku) 
        VALUES (?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Usa executemany para inserir todos os produtos de uma vez
        cursor.executemany(insert_query, products_list)
        conn.commit()
        print(f"SUCESSO: {len(products_list)} produtos inseridos/atualizados em massa.")
    except Exception as e:
        conn.rollback()
        print(f"ERRO ao tentar inserir produtos em massa: {e}")
        # Se um produto for UNIQUE (nome/sku) e já existir, ele pode falhar.
        print("Tente limpar a lista de produtos com nomes duplicados e tente novamente.")
    finally:
        conn.close()

# --- Funções de Produtos ---

def _normalize_digits(value):
    if value is None:
        return ""
    return "".join(ch for ch in str(value).strip() if ch.isdigit())


def is_valid_sku(sku):
    return len(_normalize_digits(sku)) == 4


def calculate_ean13_check_digit(base12):
    digits = _normalize_digits(base12)
    if len(digits) != 12:
        raise ValueError("Base EAN-13 deve ter 12 digitos.")
    total = 0
    for idx, digit in enumerate(digits):
        total += int(digit) * (1 if idx % 2 == 0 else 3)
    return str((10 - (total % 10)) % 10)


def generate_ean13_from_sku(sku):
    sku_digits = _normalize_digits(sku).zfill(4)
    base12 = f"{EAN_PREFIX}{sku_digits}"
    return f"{base12}{calculate_ean13_check_digit(base12)}"


def is_valid_ean13(code):
    digits = _normalize_digits(code)
    if len(digits) != 13:
        return False
    return digits[-1] == calculate_ean13_check_digit(digits[:12])


def get_next_available_sku(cursor, start=SKU_START):
    cursor.execute("SELECT sku FROM produtos WHERE sku IS NOT NULL AND TRIM(sku) <> ''")
    used = set()
    for (sku,) in cursor.fetchall():
        digits = _normalize_digits(sku)
        if len(digits) == 4:
            used.add(int(digits))

    candidate = start
    while candidate in used:
        candidate += 1
    return f"{candidate:04d}"


def ensure_product_codes(produto_id=None, sku=None, cod_barras=None, cursor=None):
    own_connection = cursor is None
    conn = None
    if own_connection:
        conn = get_db_connection()
        cursor = conn.cursor()

    sku_digits = _normalize_digits(sku)
    barcode_digits = _normalize_digits(cod_barras)

    if not is_valid_sku(sku_digits):
        sku_digits = get_next_available_sku(cursor)
    else:
        sku_digits = sku_digits.zfill(4)
        query = "SELECT id FROM produtos WHERE sku=?"
        params = [sku_digits]
        if produto_id is not None:
            query += " AND id<>?"
            params.append(produto_id)
        cursor.execute(query, tuple(params))
        if cursor.fetchone():
            sku_digits = get_next_available_sku(cursor)

    if not is_valid_ean13(barcode_digits):
        barcode_digits = generate_ean13_from_sku(sku_digits)
    else:
        query = "SELECT id FROM produtos WHERE cod_barras=?"
        params = [barcode_digits]
        if produto_id is not None:
            query += " AND id<>?"
            params.append(produto_id)
        cursor.execute(query, tuple(params))
        if cursor.fetchone():
            barcode_digits = generate_ean13_from_sku(sku_digits)

    if own_connection:
        conn.close()
    return sku_digits, barcode_digits


def assign_missing_product_codes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sku, cod_barras FROM produtos ORDER BY id")
    produtos = cursor.fetchall()

    atualizados = 0
    for produto_id, sku, cod_barras in produtos:
        new_sku, new_cod_barras = ensure_product_codes(
            produto_id=produto_id,
            sku=sku,
            cod_barras=cod_barras,
            cursor=cursor,
        )
        if _normalize_digits(sku) != new_sku or _normalize_digits(cod_barras) != new_cod_barras:
            cursor.execute(
                "UPDATE produtos SET sku=?, cod_barras=? WHERE id=?",
                (new_sku, new_cod_barras, produto_id),
            )
            atualizados += 1

    conn.commit()
    conn.close()
    return atualizados


def add_product(nome, preco, quantidade, unidade, sku, cod_barras):
    """Adiciona um novo produto ao banco de dados, verificando duplicidade de SKU e Cód. Barras."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sku, cod_barras = ensure_product_codes(
            sku=sku, cod_barras=cod_barras, cursor=cursor
        )
        normalized_name = str(nome or "").strip().upper()
        cursor.execute(
            "SELECT id, nome FROM produtos WHERE UPPER(TRIM(nome)) = ? OR sku = ? OR cod_barras = ?",
            (normalized_name, sku, cod_barras),
        )
        duplicate = cursor.fetchone()
        if duplicate:
            raise ValueError(
                f"Erro: Já existe um produto cadastrado com este nome, SKU ou código de barras ({duplicate[1]})."
            )
        cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, sku, cod_barras) VALUES (?, ?, ?, ?, ?, ?)", (nome, preco, quantidade, unidade, sku, cod_barras))
        conn.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: produtos.sku" in str(e):
            raise ValueError("Erro: Já existe um produto com este SKU.")
        elif "UNIQUE constraint failed: produtos.cod_barras" in str(e):
            raise ValueError("Erro: Já existe um produto com este Código de Barras.")
        else:
            raise e
    finally:
        conn.close()

def get_all_products():
    """Busca todos os produtos do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, estoque, unidade, sku, cod_barras FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def get_product_by_id(product_id):
    """Retorna os dados de um produto a partir de seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id=?", (product_id,))
    produto = cursor.fetchone()
    conn.close()
    return produto

def get_product_by_name(nome):
    """Retorna um produto pelo nome."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE nome=?", (nome,))
    produto = cursor.fetchone()
    conn.close()
    return produto

def get_product_by_name_balaca(nome):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Selecionamos todas as colunas necessárias
    cursor.execute("SELECT id, nome, preco, estoque, unidade, cod_barras, sku FROM produtos WHERE nome = ?", (nome,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "nome": row[1],
            "preco": row[2],
            "estoque": row[3],
            "unidade": row[4], # 📌 Importante para a balança
            "cod_barras": row[5],
            "sku": row[6]
        }
    return None

def update_product(produto_id, nome, preco, quantidade, unidade, sku, cod_barras):
    """Atualiza os dados de um produto."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sku, cod_barras = ensure_product_codes(
        produto_id=produto_id, sku=sku, cod_barras=cod_barras, cursor=cursor
    )
    normalized_name = str(nome or "").strip().upper()
    cursor.execute(
        "SELECT id, nome FROM produtos WHERE (UPPER(TRIM(nome)) = ? OR sku = ? OR cod_barras = ?) AND id <> ?",
        (normalized_name, sku, cod_barras, produto_id),
    )
    duplicate = cursor.fetchone()
    if duplicate:
        conn.close()
        raise ValueError(
            f"Erro: Já existe um produto cadastrado com este nome, SKU ou código de barras ({duplicate[1]})."
        )
    cursor.execute("UPDATE produtos SET nome=?, preco=?, estoque=?, unidade=?, sku=?, cod_barras=? WHERE id=?", (nome, preco, quantidade, unidade, sku, cod_barras, produto_id))
    conn.commit()
    conn.close()

def get_product_by_sku(sku):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE sku=?", (sku,))
    produto = cursor.fetchone()
    conn.close()
    return produto

def get_product_by_barcode(cod_barras):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE cod_barras=?", (cod_barras,))
    produto = cursor.fetchone()
    conn.close()
    return produto

def get_product_by_code(code):
    """Retorna um produto buscando pelo Código de Barras ou SKU."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE cod_barras=?", (code,))
    produto = cursor.fetchone()
    if produto:
        conn.close()
        return produto
    cursor.execute("SELECT * FROM produtos WHERE sku=?", (code,))
    produto = cursor.fetchone()
    conn.close()
    return produto

def delete_product_db(produto_id):
    """Exclui um produto do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
    conn.commit()
    conn.close()

def update_product_stock(nome, quantidade_vendida):
    """Atualiza a quantidade de um produto após uma venda."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade_vendida, nome))
    conn.commit()
    conn.close()

def filter_products_for_combobox(query):
    """Retorna uma lista de nomes de produtos que correspondem à query."""     
    produtos = get_all_products()
    query_lower = query.lower()
    resultados_busca = [
        p[1] for p in produtos 
        if query_lower in p[1].lower() 
        or (p[5] and query_lower in p[5].lower()) 
        or (p[6] and query_lower in p[6].lower()) 
    ]
    return resultados_busca

# --- Funções de Funcionários ---

def add_employee(nome, usuario, cargo, senha):
    """Adiciona um novo funcionário ao banco de dados."""
    hashed_senha = hash_password(senha)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO funcionarios (nome, usuario, cargo, senha) VALUES (?, ?, ?, ?)", (nome, usuario, cargo, hashed_senha))
    conn.commit()
    conn.close()

def get_all_employees():
    """Retorna todos os funcionários do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, usuario, cargo FROM funcionarios")
    funcionarios = cursor.fetchall()
    conn.close()
    return funcionarios

def get_employee_by_username_and_password(usuario, senha):
    """Verifica se o funcionário e a senha estão corretos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, cargo, senha FROM funcionarios WHERE usuario=?", (usuario,))
    funcionario = cursor.fetchone()
    conn.close()
    if funcionario and check_password(senha, funcionario[2]):
        return (funcionario[0], funcionario[1]) # Retorna nome e cargo
    return None

def is_manager(usuario, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cargo, senha FROM funcionarios WHERE usuario=?", (usuario,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == 'Gerente' and check_password(password, result[1]):
        return True
    return False

def delete_employee_db(funcionario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM funcionarios WHERE id=?", (funcionario_id,))
    conn.commit()
    conn.close()

def update_employee_db(employee_id, nome, usuario, cargo, nova_senha=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if nova_senha:
        hashed_senha = hash_password(nova_senha)
        cursor.execute("UPDATE funcionarios SET nome=?, usuario=?, cargo=?, senha=? WHERE id=?", 
                       (nome, usuario, cargo, hashed_senha, employee_id))
    else:
        cursor.execute("UPDATE funcionarios SET nome=?, usuario=?, cargo=? WHERE id=?", 
                       (nome, usuario, cargo, employee_id))
    conn.commit()
    conn.close()

def get_employee_by_id(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, usuario, senha, cargo FROM funcionarios WHERE id=?", (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    return employee

def verify_and_add_initial_users(db_path=None):
    """Verifica se os usuários iniciais já existem e os adiciona se necessário."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    usuarios_iniciais = (
        ("Gerente Master", "gerente1", "Gerente", "1234"),
        ("Caixa Principal", "caixa1", "Caixa", "1234"),
    )

    for nome, usuario, cargo, senha in usuarios_iniciais:
        cursor.execute("SELECT 1 FROM funcionarios WHERE usuario=?", (usuario,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO funcionarios (nome, usuario, cargo, senha) VALUES (?, ?, ?, ?)",
                (nome, usuario, cargo, hash_password(senha)),
            )

    conn.commit()
    conn.close()

# --- Funções de Vendas ---

def add_sale(id_funcionario, total, itens_vendidos, metodo_pagamento, valor_pago, troco):
    """
    Registra uma nova venda com detalhes de pagamento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO vendas 
            (id_funcionario, data_venda, total, itens_vendidos, metodo_pagamento, valor_pago, troco) 
        VALUES 
            (?, ?, ?, ?, ?, ?, ?)
    """, (id_funcionario, data_venda, total, itens_vendidos, metodo_pagamento, valor_pago, troco))

    sale_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sale_id

def get_daily_sales():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM vendas WHERE data_venda LIKE ?", (hoje + '%',))
    vendas = cursor.fetchall()
    conn.close()
    return vendas

def update_sale_db(sale_id, new_total, new_itens):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE vendas SET total=?, itens_vendidos=? WHERE id=?", (new_total, str(new_itens), sale_id))
    conn.commit()
    conn.close()

def delete_sale_db(sale_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas WHERE id=?", (sale_id,))
    conn.commit()
    conn.close()

def get_sale_by_id(sale_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendas WHERE id=?", (sale_id,))
    venda = cursor.fetchone()
    conn.close()
    return venda

def get_daily_sales_total():
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(total) FROM vendas WHERE data_venda LIKE ?", (f"{data_hoje}%",))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0.0


def get_daily_sales_payment_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT metodo_pagamento, COALESCE(SUM(total), 0)
        FROM vendas
        WHERE data_venda LIKE ?
        GROUP BY metodo_pagamento
        """,
        (f"{data_hoje}%",),
    )
    rows = cursor.fetchall()
    conn.close()

    summary = {
        "DINHEIRO": 0.0,
        "CARTAO_CREDITO": 0.0,
        "CARTAO_DEBITO": 0.0,
        "QR_CODE": 0.0,
        "PIX": 0.0,
    }
    for metodo, total in rows:
        if metodo in summary:
            summary[metodo] = float(total or 0.0)
    return summary

# --- Funções de Caixa ---

def open_cash_register_db(initial_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO caixa (data_abertura, valor_abertura, status) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), initial_value, 'aberto'))
    conn.commit()
    conn.close()
    
def close_cash_register_db(cash_register_id, final_value, total_sales):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE caixa
        SET data_fechamento=?, valor_fechamento=?, total_vendas=?, status=?
        WHERE id=?
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), final_value, total_sales, 'fechado', cash_register_id))
    conn.commit()
    conn.close()

def get_cash_register_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, valor_abertura, data_abertura FROM caixa WHERE status='aberto' ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"status": "aberto", "id": result[0], "valor_abertura": result[1], "data_abertura": result[2]}
    else:
        return {"status": "fechado"}

def get_open_cash_register_initial_value():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor_abertura FROM caixa WHERE status='aberto' ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0

# --- Funções da Empresa (ATUALIZADAS) ---

def get_company_info():
    """Retorna os dados da empresa (única linha), incluindo os novos campos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Seleciona todas as colunas novas também
    cursor.execute("SELECT nome_fantasia, razao_social, cnpj, endereco, bairro, cidade, estado, cep, telefone, email, logo_path FROM empresa WHERE id=1")
    data = cursor.fetchone()
    conn.close()
    
    if data:
        return {
            "nome_fantasia": data[0],
            "razao_social": data[1],
            "cnpj": data[2],
            "endereco": data[3],
            "bairro": data[4],
            "cidade": data[5],
            "estado": data[6],
            "cep": data[7],
            "telefone": data[8],
            "email": data[9],
            "logo_path": data[10]
        }
    return None

def save_company_info(nome_fantasia, razao_social, cnpj, endereco, bairro, cidade, estado, cep, telefone, email, logo_path):
    """Salva ou atualiza TODOS os dados da empresa usando INSERT OR REPLACE."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # A sintaxe INSERT OR REPLACE é perfeita aqui. Se o ID 1 já existe, ele substitui tudo.
    cursor.execute("""
        INSERT OR REPLACE INTO empresa (id, nome_fantasia, razao_social, cnpj, endereco, bairro, cidade, estado, cep, telefone, email, logo_path)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome_fantasia, razao_social, cnpj, endereco, bairro, cidade, estado, cep, telefone, email, logo_path))
    
    conn.commit()
    conn.close()
    return True # Retorna True para indicar sucesso

def delete_company_info():
    """Remove os dados da empresa (reseta)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empresa WHERE id=1")
    conn.commit()
    conn.close()
