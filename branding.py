from datetime import datetime


APP_NAME = "KODA SYSTEM"
APP_NAME_MULTILINE = "KODA\nSYSTEM"
APP_VERSION = "3.0.0"
APP_SUBTITLE = "Operacao, estoque e gestao."
APP_DESCRIPTION = (
    "Controle de caixa, estoque e equipe com foco em velocidade, "
    "estabilidade e apresentacao profissional."
)
APP_ABOUT_HEADING = "Plataforma de operacao para mercados, mercearias e lojas de bairro."
APP_ABOUT_HIGHLIGHTS = (
    "Frente de caixa com foco em agilidade no atendimento.",
    "Gestao de estoque, produtos, equipe e dados da empresa.",
    "Relatorios operacionais e historico de vendas para acompanhamento diario.",
    "Geracao de etiquetas e catalogos com codigo de barras interno EAN-13.",
)
COPYRIGHT_HOLDER = "MJBS COMPANY"
COPYRIGHT_LABEL = f"Copyright (c) {datetime.now().year} {COPYRIGHT_HOLDER}"
POWERED_BY_LABEL = f"Desenvolvido por {COPYRIGHT_HOLDER}"
APP_PUBLISHER = COPYRIGHT_HOLDER
APP_EXECUTABLE_NAME = "KODA_SYSTEM"
APP_INSTALLER_NAME = "KODA_SYSTEM_Instalador"
ASSET_BASENAME = "KODA_SYSTEM"
REPORT_HEADER = f"{APP_NAME} - RELATORIO GERENCIAL DE VENDAS"
REPORT_FOOTER = f"Gerado por {APP_NAME} | {COPYRIGHT_HOLDER}"

LOGIN_HIGHLIGHTS = (
    "Caixa agil para operacao diaria",
    "Gestao de estoque com leitura de itens",
    "Historico de vendas e relatorios claros",
    "Interface mais limpa para equipes e gerencia",
    "Base pronta para crescimento do negocio",
)

PAGE_TITLES = {
    "caixa": "Frente de Caixa",
    "gerencia": "Painel Gerencial",
    "produtos_view": "Produtos",
    "funcionarios_view": "Funcionarios",
    "relatorios_view": "Relatorios do Dia",
    "relatorios_gerais_view": "Historico de Vendas",
    "empresa_view": "Dados da Empresa",
}


def format_window_title(section=None):
    if section:
        return f"{APP_NAME} | {section}"
    return APP_NAME


def get_page_title(page_name):
    return PAGE_TITLES.get(page_name, str(page_name).replace("_", " ").title())
