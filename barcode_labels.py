import csv
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from branding import APP_NAME, POWERED_BY_LABEL
from database import EAN_PREFIX, get_all_products, is_valid_ean13
from theme import APP_THEME
from utils import ensure_runtime_dir, get_app_logo_path


EAN_L = {
    "0": "0001101",
    "1": "0011001",
    "2": "0010011",
    "3": "0111101",
    "4": "0100011",
    "5": "0110001",
    "6": "0101111",
    "7": "0111011",
    "8": "0110111",
    "9": "0001011",
}
EAN_G = {
    "0": "0100111",
    "1": "0110011",
    "2": "0011011",
    "3": "0100001",
    "4": "0011101",
    "5": "0111001",
    "6": "0000101",
    "7": "0010001",
    "8": "0001001",
    "9": "0010111",
}
EAN_R = {
    "0": "1110010",
    "1": "1100110",
    "2": "1101100",
    "3": "1000010",
    "4": "1011100",
    "5": "1001110",
    "6": "1010000",
    "7": "1000100",
    "8": "1001000",
    "9": "1110100",
}
EAN_PARIDADES = {
    "0": "LLLLLL",
    "1": "LLGLGG",
    "2": "LLGGLG",
    "3": "LLGGGL",
    "4": "LGLLGG",
    "5": "LGGLLG",
    "6": "LGGGLL",
    "7": "LGLGLG",
    "8": "LGLGGL",
    "9": "LGGLGL",
}


def somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def slug(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "produto"))
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto[:70] or "produto"


def moeda(valor):
    try:
        return f"R$ {float(valor):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return ""


def normalizar_produto(produto):
    return {
        "id": produto[0],
        "nome": produto[1],
        "preco": produto[2],
        "estoque": produto[3],
        "unidade": produto[4],
        "sku": produto[5],
        "codigo_barras": somente_digitos(produto[6]),
    }


def listar_produtos_com_codigo_interno(produtos=None):
    produtos = get_all_products() if produtos is None else produtos
    internos = []
    invalidos = []
    prefixo_interno = EAN_PREFIX

    for produto in produtos:
        item = normalizar_produto(produto)
        codigo = item["codigo_barras"]
        if not is_valid_ean13(codigo):
            invalidos.append(item)
            continue
        if codigo.startswith(prefixo_interno):
            internos.append(item)

    internos.sort(key=lambda item: (str(item["nome"] or "").lower(), str(item["sku"] or "")))
    return internos, invalidos


def desenho_etiqueta(produto, largura, altura):
    nome = str(produto.get("nome", "")).strip()
    codigo = produto["codigo_barras"]
    sku = str(produto.get("sku", "")).strip()
    unidade = str(produto.get("unidade", "")).strip()
    preco = moeda(produto.get("preco"))

    desenho = Drawing(largura, altura)
    desenho.add(String(8, altura - 15, nome[:34], fontName="Helvetica-Bold", fontSize=11))
    subtitulo = f"{preco} / {unidade}" if preco and unidade else f"{preco}{unidade}"
    desenho.add(String(8, altura - 29, subtitulo[:32], fontName="Helvetica", fontSize=8.5))
    desenho.add(String(largura - 64, altura - 29, f"SKU {sku}", fontName="Helvetica", fontSize=8.5))

    barcode = createBarcodeDrawing(
        "EAN13",
        value=codigo,
        barHeight=31 * mm,
        barWidth=0.38 * mm,
        humanReadable=True,
    )
    barcode.translate((largura - barcode.width) / 2, 16)
    desenho.add(barcode, name="barcode")
    desenho.add(String((largura - 72) / 2, 5, codigo, fontName="Helvetica", fontSize=7.5))
    return desenho


def bits_ean13(codigo):
    paridade = EAN_PARIDADES[codigo[0]]
    esquerda = "".join((EAN_L if modo == "L" else EAN_G)[digito] for modo, digito in zip(paridade, codigo[1:7]))
    direita = "".join(EAN_R[digito] for digito in codigo[7:])
    return "101" + esquerda + "01010" + direita + "101"


def fonte(tamanho, bold=False):
    arquivo = "arialbd.ttf" if bold else "arial.ttf"
    caminho = Path(r"C:\Windows\Fonts") / arquivo
    try:
        return ImageFont.truetype(str(caminho), tamanho)
    except OSError:
        return ImageFont.load_default()


def texto_centralizado(draw, xy, texto, font, fill):
    x, y, largura = xy
    bbox = draw.textbbox((0, 0), texto, font=font)
    draw.text((x + (largura - (bbox[2] - bbox[0])) / 2, y), texto, fill=fill, font=font)


def salvar_png_etiqueta(produto, destino):
    largura, altura = 760, 470
    img = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(img)
    nome = str(produto.get("nome", "")).strip()
    codigo = produto["codigo_barras"]
    info = f"{moeda(produto.get('preco'))} / {str(produto.get('unidade', '')).strip()}   SKU {str(produto.get('sku', '')).strip()}"

    draw.rectangle((0, 0, largura - 1, altura - 1), outline=(200, 200, 200), width=2)
    texto_centralizado(draw, (24, 20, largura - 48), nome[:34], fonte(34, bold=True), (0, 0, 0))
    texto_centralizado(draw, (24, 62, largura - 48), info, fonte(24), (30, 30, 30))

    bits = bits_ean13(codigo)
    modulo = 5
    barcode_w = len(bits) * modulo
    x0 = (largura - barcode_w) // 2
    y0 = 120
    bar_h = 245
    guard_indices = set(range(3)) | set(range(45, 50)) | set(range(92, 95))

    for i, bit in enumerate(bits):
        if bit == "1":
            h = bar_h + 24 if i in guard_indices else bar_h
            x = x0 + i * modulo
            draw.rectangle((x, y0, x + modulo - 1, y0 + h), fill=(0, 0, 0))

    texto_centralizado(draw, (24, 395, largura - 48), codigo, fonte(22), (0, 0, 0))
    texto_centralizado(draw, (24, 425, largura - 48), "EAN-13 gerado pelo sistema", fonte(20), (65, 65, 65))
    img.save(destino, "PNG")


def gerar_pngs(produtos, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    for produto in produtos:
        nome_arquivo = f"{slug(produto.get('nome'))}_{produto['codigo_barras']}.png"
        salvar_png_etiqueta(produto, pasta / nome_arquivo)


def cor(nome):
    return colors.HexColor(APP_THEME[nome])


def texto_ajustado(pdf, texto, x, y, max_width, fonte_nome, fonte_tamanho, min_size=7):
    texto = str(texto or "")
    size = fonte_tamanho
    while size > min_size and pdf.stringWidth(texto, fonte_nome, size) > max_width:
        size -= 0.5
    pdf.setFont(fonte_nome, size)
    pdf.drawString(x, y, texto)
    return size


def desenhar_logo(pdf, x, y, tamanho):
    try:
        logo = ImageReader(get_app_logo_path())
        pdf.drawImage(logo, x, y, width=tamanho, height=tamanho, preserveAspectRatio=True, mask="auto")
    except Exception:
        pdf.setFillColor(cor("accent"))
        pdf.circle(x + tamanho / 2, y + tamanho / 2, tamanho / 2, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(x + tamanho / 2, y + tamanho / 2 - 6, "KS")


def desenhar_capa(pdf, total_produtos):
    largura_pagina, altura_pagina = A4
    pdf.setFillColor(cor("bg"))
    pdf.rect(0, 0, largura_pagina, altura_pagina, fill=1, stroke=0)
    pdf.setFillColor(cor("nav"))
    pdf.rect(0, altura_pagina - 6.6 * cm, largura_pagina, 6.6 * cm, fill=1, stroke=0)
    pdf.setFillColor(cor("primary"))
    pdf.rect(0, altura_pagina - 6.9 * cm, largura_pagina, 0.35 * cm, fill=1, stroke=0)
    pdf.setFillColor(cor("accent"))
    pdf.rect(0, altura_pagina - 7.25 * cm, largura_pagina, 0.35 * cm, fill=1, stroke=0)

    desenhar_logo(pdf, 1.4 * cm, altura_pagina - 5.3 * cm, 2.2 * cm)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(4.1 * cm, altura_pagina - 3.55 * cm, APP_NAME)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(4.1 * cm, altura_pagina - 4.0 * cm, "Catalogo operacional para frente de caixa")

    pdf.setFillColor(cor("text"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(1.45 * cm, altura_pagina - 9.0 * cm, "Codigos de barras")
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(1.45 * cm, altura_pagina - 10.15 * cm, "dos produtos internos")

    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 11)
    pdf.drawString(1.5 * cm, altura_pagina - 11.35 * cm, "Use no caixa para itens sem codigo fisico na embalagem.")

    card_x = 1.5 * cm
    card_y = altura_pagina - 17.0 * cm
    card_w = largura_pagina - 3.0 * cm
    card_h = 3.25 * cm
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(cor("border"))
    pdf.roundRect(card_x, card_y, card_w, card_h, 8, fill=1, stroke=1)
    pdf.setFillColor(cor("accent"))
    pdf.roundRect(card_x + 0.45 * cm, card_y + 0.55 * cm, 2.2 * cm, 2.15 * cm, 6, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(card_x + 1.55 * cm, card_y + 1.28 * cm, str(total_produtos))
    pdf.setFillColor(cor("text"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(card_x + 3.1 * cm, card_y + 1.9 * cm, "etiquetas prontas para leitura")
    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 9.5)
    pdf.drawString(card_x + 3.1 * cm, card_y + 1.35 * cm, "EAN-13 gerado pelo sistema, com nome, unidade e SKU.")

    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(1.5 * cm, 1.45 * cm, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    pdf.drawRightString(largura_pagina - 1.5 * cm, 1.45 * cm, POWERED_BY_LABEL)
    pdf.showPage()


def desenhar_cabecalho(pdf, pagina, total_produtos):
    largura_pagina, altura_pagina = A4
    pdf.setFillColor(cor("nav"))
    pdf.rect(0, altura_pagina - 2.15 * cm, largura_pagina, 2.15 * cm, fill=1, stroke=0)
    pdf.setFillColor(cor("primary"))
    pdf.rect(0, altura_pagina - 2.23 * cm, largura_pagina, 0.08 * cm, fill=1, stroke=0)
    pdf.setFillColor(cor("accent"))
    pdf.rect(0, altura_pagina - 2.35 * cm, largura_pagina, 0.12 * cm, fill=1, stroke=0)
    desenhar_logo(pdf, 1.05 * cm, altura_pagina - 1.75 * cm, 1.15 * cm)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2.55 * cm, altura_pagina - 1.1 * cm, "Catalogo de codigos de barras")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(2.55 * cm, altura_pagina - 1.52 * cm, f"{total_produtos} produtos internos para leitura no caixa")
    pdf.setFillColor(cor("accent_soft"))
    pdf.roundRect(largura_pagina - 3.2 * cm, altura_pagina - 1.55 * cm, 2.15 * cm, 0.65 * cm, 6, fill=1, stroke=0)
    pdf.setFillColor(cor("nav"))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawCentredString(largura_pagina - 2.125 * cm, altura_pagina - 1.32 * cm, f"PAG. {pagina}")


def desenhar_rodape(pdf):
    largura_pagina, _ = A4
    pdf.setStrokeColor(cor("border"))
    pdf.line(1.05 * cm, 1.05 * cm, largura_pagina - 1.05 * cm, 1.05 * cm)
    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(1.05 * cm, 0.62 * cm, APP_NAME)
    pdf.drawRightString(largura_pagina - 1.05 * cm, 0.62 * cm, "Mantenha as barras limpas e sem plastico reflexivo.")


def desenhar_card_produto(pdf, produto, x, y, largura, altura, indice):
    nome = str(produto.get("nome", "")).strip()
    codigo = produto["codigo_barras"]
    sku = str(produto.get("sku", "")).strip()
    unidade = str(produto.get("unidade", "")).strip().upper()

    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(cor("border"))
    pdf.roundRect(x, y, largura, altura, 7, fill=1, stroke=1)

    pdf.setFillColor(cor("surface_alt"))
    pdf.roundRect(x + 0.15 * cm, y + altura - 1.08 * cm, largura - 0.3 * cm, 0.9 * cm, 5, fill=1, stroke=0)
    pdf.setFillColor(cor("primary"))
    pdf.roundRect(x + 0.32 * cm, y + altura - 0.86 * cm, 0.95 * cm, 0.46 * cm, 4, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawCentredString(x + 0.795 * cm, y + altura - 0.72 * cm, f"{indice:02d}")

    pdf.setFillColor(cor("text"))
    texto_ajustado(pdf, nome[:42], x + 1.43 * cm, y + altura - 0.78 * cm, largura - 3.2 * cm, "Helvetica-Bold", 10.5)

    pdf.setFillColor(cor("accent"))
    pdf.roundRect(x + largura - 1.82 * cm, y + altura - 0.86 * cm, 1.43 * cm, 0.46 * cm, 4, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawCentredString(x + largura - 1.105 * cm, y + altura - 0.72 * cm, unidade or "UN")

    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(x + 0.38 * cm, y + altura - 1.47 * cm, "SKU")
    pdf.drawString(x + 2.55 * cm, y + altura - 1.47 * cm, "CODIGO")
    pdf.setFillColor(cor("text"))
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(x + 0.38 * cm, y + altura - 1.88 * cm, sku)
    pdf.drawString(x + 2.55 * cm, y + altura - 1.88 * cm, codigo)

    barcode = createBarcodeDrawing(
        "EAN13",
        value=codigo,
        barHeight=28.5 * mm,
        barWidth=0.38 * mm,
        humanReadable=True,
    )
    barcode_x = x + (largura - barcode.width) / 2
    barcode_y = y + 0.55 * cm
    renderPDF.draw(barcode, pdf, barcode_x, barcode_y)

    pdf.setFillColor(cor("text_muted"))
    pdf.setFont("Helvetica", 7.2)
    pdf.drawCentredString(x + largura / 2, y + 0.22 * cm, codigo)


def gerar_pdf(produtos, destino):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(destino), pagesize=A4)
    largura_pagina, altura_pagina = A4

    desenhar_capa(pdf, len(produtos))

    margem_x = 1.05 * cm
    margem_topo = 2.75 * cm
    margem_base = 1.35 * cm
    colunas = 2
    linhas = 4
    gap_x = 0.55 * cm
    gap_y = 0.48 * cm
    largura = (largura_pagina - 2 * margem_x - gap_x) / colunas
    altura = (altura_pagina - margem_topo - margem_base - (linhas - 1) * gap_y) / linhas

    pagina = 1
    desenhar_cabecalho(pdf, pagina, len(produtos))
    desenhar_rodape(pdf)
    for idx, produto in enumerate(produtos):
        pos = idx % (colunas * linhas)
        if idx and pos == 0:
            pdf.showPage()
            pagina += 1
            desenhar_cabecalho(pdf, pagina, len(produtos))
            desenhar_rodape(pdf)

        coluna = pos % colunas
        linha = pos // colunas
        x = margem_x + coluna * (largura + gap_x)
        y = altura_pagina - margem_topo - (linha + 1) * altura - linha * gap_y
        desenhar_card_produto(pdf, produto, x, y, largura, altura, idx + 1)

    pdf.save()


def gerar_resumo(produtos, destino):
    destino = Path(destino)
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.writer(arquivo, delimiter=";")
        writer.writerow(["nome", "unidade", "sku", "codigo_barras"])
        for produto in produtos:
            writer.writerow([
                produto.get("nome", ""),
                produto.get("unidade", ""),
                produto.get("sku", ""),
                produto.get("codigo_barras", ""),
            ])


def gerar_catalogo_codigos_barras(destino_pdf=None, gerar_imagens=True):
    produtos, invalidos = listar_produtos_com_codigo_interno()
    if not produtos:
        raise ValueError("Nenhum produto com código interno EAN-13 foi encontrado.")

    base_dir = Path(ensure_runtime_dir("output/etiquetas_codigos_barras"))
    pdf_path = Path(destino_pdf) if destino_pdf else base_dir / "catalogo_codigos_barras_produtos_internos.pdf"
    imagens_dir = base_dir / "imagens_png"
    csv_path = base_dir / "produtos_internos_gerados.csv"

    gerar_pdf(produtos, pdf_path)
    if gerar_imagens:
        gerar_pngs(produtos, imagens_dir)
    gerar_resumo(produtos, csv_path)

    return {
        "pdf": str(pdf_path),
        "imagens_dir": str(imagens_dir),
        "csv": str(csv_path),
        "total": len(produtos),
        "invalidos": len(invalidos),
    }
