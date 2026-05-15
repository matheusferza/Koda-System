# KODA SYSTEM

Sistema desktop para operação de caixa, gestão de estoque, equipe, relatórios e geração de etiquetas com código de barras.

## Sobre o sistema

O `KODA SYSTEM` foi projetado para atender mercados, mercearias e operações de balcão que precisam de uma solução rápida, visualmente profissional e simples de operar no dia a dia.

Principais focos do produto:

- frente de caixa com fluxo ágil para atendimento
- gestão de produtos, estoque e equipe em uma interface única
- relatórios operacionais e histórico de vendas
- geração de etiquetas e catálogos com código de barras interno EAN-13
- base pronta para distribuição como executável e instalador

## Funcionalidades

- Login com perfis de acesso
- Frente de caixa com carrinho em tempo real
- Cadastro e edição de produtos
- Cadastro e gestão de funcionários
- Controle de abertura e fechamento de caixa
- Relatórios diários e históricos
- Geração de catálogo de etiquetas em PDF e PNG
- Importação e exportação de dados em CSV
- Identidade visual `KODA SYSTEM` com branding centralizado

## Tecnologias

- Python 3.13
- Tkinter e ttk
- SQLite
- Pillow
- ReportLab
- PySerial
- PyWin32
- PyInstaller

## Estrutura do projeto

```text
Koda_System/
|-- main.py
|-- gui.py
|-- interface_widgets.py
|-- dialogs.py
|-- database.py
|-- barcode_labels.py
|-- gerar_etiquetas_codigos.py
|-- branding.py
|-- theme.py
|-- utils.py
|-- build_release.ps1
|-- build_installer.ps1
|-- KODA_SYSTEM.spec
|-- KODA_SYSTEM.iss
|-- requirements.txt
|-- dados_empresa/
|-- imagens/
`-- .vscode/
```

## Como executar

1. Clone o repositório:

```powershell
git clone https://github.com/matheusferza/Koda-System.git
cd Koda-System
```

2. Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

4. Execute o sistema:

```powershell
python .\main.py
```

## Build e empacotamento

Para gerar a versão executável:

```powershell
.\build_release.ps1
```

Para gerar o instalador:

```powershell
.\build_installer.ps1
```

## Posicionamento do produto

O projeto foi estruturado para ser apresentado como um sistema comercial:

- visual renovado com a marca `KODA SYSTEM`
- rodapé institucional com `MJBS COMPANY`
- assets prontos para executável, instalador e documentação
- suporte a operação em notebooks e telas menores

## Desenvolvedor

Desenvolvido por `MJBS COMPANY`.

Repositório oficial:

- [matheusferza/Koda-System](https://github.com/matheusferza/Koda-System)
