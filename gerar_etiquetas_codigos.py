import csv
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas


OUT_DIR = Path("output") / "etiquetas_codigos_barras"


def localizar_relatorio_estoque():
    downloads = Path.home() / "Downloads"
    candidatos = []
    if downloads.exists():
        candidatos.extend(downloads.glob("relatorio_estoque_*.csv"))
        arquivo_padrao = downloads / "relatorio_estoque.csv"
        if arquivo_padrao.exists():
            candidatos.append(arquivo_padrao)
    if not candidatos:
        return None
    return max(candidatos, key=lambda caminho: caminho.stat().st_mtime)


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def digito_ean13(primeiros_12):
    total = 0
    for i, digito in enumerate(primeiros_12):
        total += int(digito) * (1 if i % 2 == 0 else 3)
    return str((10 - (total % 10)) % 10)


def ean13_valido(codigo):
    codigo = somente_digitos(codigo)
    return len(codigo) == 13 and digito_ean13(codigo[:12]) == codigo[-1]


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto[:70] or "produto"


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


def moeda(valor):
    try:
        return f"R$ {float(valor):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return ""


def carregar_produtos(csv_path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as arquivo:
        produtos = list(csv.DictReader(arquivo, delimiter=";"))

    internos = []
    invalidos = []
    for produto in produtos:
        codigo = somente_digitos(produto.get("codigo_barras"))
        if not ean13_valido(codigo):
            invalidos.append(produto)
            continue

        produto["codigo_barras"] = codigo
        if codigo.startswith("78900000"):
            internos.append(produto)

    internos.sort(key=lambda item: (item.get("nome") or "", item.get("sku") or ""))
    return internos, invalidos


def desenho_etiqueta(produto, largura, altura):
    nome = produto.get("nome", "").strip()
    codigo = produto["codigo_barras"]
    sku = produto.get("sku", "").strip()
    unidade = produto.get("unidade", "").strip()
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
    barcode_x = (largura - barcode.width) / 2
    barcode_y = 16
    desenho.add(barcode, name="barcode")
    barcode.translate(barcode_x, barcode_y)

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

    nome_font = fonte(34, bold=True)
    info_font = fonte(24)
    codigo_font = fonte(22)
    produto_font = fonte(20)

    nome = produto.get("nome", "").strip()
    codigo = produto["codigo_barras"]
    info = f"{moeda(produto.get('preco'))} / {produto.get('unidade', '').strip()}   SKU {produto.get('sku', '').strip()}"

    draw.rectangle((0, 0, largura - 1, altura - 1), outline=(200, 200, 200), width=2)
    texto_centralizado(draw, (24, 20, largura - 48), nome[:34], nome_font, (0, 0, 0))
    texto_centralizado(draw, (24, 62, largura - 48), info, info_font, (30, 30, 30))

    bits = bits_ean13(codigo)
    modulo = 5
    quiet = 12 * modulo
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

    draw.rectangle((x0 - quiet, y0, x0 - 1, y0 + bar_h + 24), fill="white")
    draw.rectangle((x0 + barcode_w, y0, x0 + barcode_w + quiet - 1, y0 + bar_h + 24), fill="white")

    texto_centralizado(draw, (24, 395, largura - 48), codigo, codigo_font, (0, 0, 0))
    texto_centralizado(draw, (24, 425, largura - 48), "EAN-13 gerado pelo sistema", produto_font, (65, 65, 65))
    img.save(destino, "PNG")


def gerar_pngs(produtos, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    for produto in produtos:
        nome_arquivo = f"{slug(produto.get('nome', 'produto'))}_{produto['codigo_barras']}.png"
        salvar_png_etiqueta(produto, pasta / nome_arquivo)


def gerar_pdf(produtos, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(destino), pagesize=A4)
    largura_pagina, altura_pagina = A4

    margem_x = 1.2 * cm
    margem_y = 1.3 * cm
    titulo_h = 1.2 * cm
    colunas = 2
    linhas = 4
    gap_x = 0.7 * cm
    gap_y = 0.7 * cm
    largura = (largura_pagina - 2 * margem_x - gap_x) / colunas
    altura = (altura_pagina - 2 * margem_y - titulo_h - (linhas - 1) * gap_y) / linhas

    def cabecalho(pagina):
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margem_x, altura_pagina - margem_y, "Catalogo de codigos de barras - produtos internos")
        pdf.setFont("Helvetica", 8)
        pdf.drawRightString(
            largura_pagina - margem_x,
            altura_pagina - margem_y,
            f"Pagina {pagina}",
        )
        pdf.setStrokeColor(colors.lightgrey)
        pdf.line(margem_x, altura_pagina - margem_y - 0.25 * cm, largura_pagina - margem_x, altura_pagina - margem_y - 0.25 * cm)

    pagina = 1
    cabecalho(pagina)

    for idx, produto in enumerate(produtos):
        pos = idx % (colunas * linhas)
        if idx and pos == 0:
            pdf.showPage()
            pagina += 1
            cabecalho(pagina)

        coluna = pos % colunas
        linha = pos // colunas
        x = margem_x + coluna * (largura + gap_x)
        y = altura_pagina - margem_y - titulo_h - (linha + 1) * altura - linha * gap_y

        pdf.setStrokeColor(colors.HexColor("#BDBDBD"))
        pdf.roundRect(x, y, largura, altura, 4, stroke=1, fill=0)
        desenho = desenho_etiqueta(produto, largura - 10, altura - 8)
        renderPDF.draw(desenho, pdf, x + 5, y + 4)

    pdf.save()


def gerar_resumo(produtos, invalidos, destino):
    with destino.open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.writer(arquivo, delimiter=";")
        writer.writerow(["nome", "preco", "unidade", "sku", "codigo_barras"])
        for produto in produtos:
            writer.writerow([
                produto.get("nome", ""),
                produto.get("preco", ""),
                produto.get("unidade", ""),
                produto.get("sku", ""),
                produto.get("codigo_barras", ""),
            ])

    if invalidos:
        inv_path = destino.with_name("codigos_invalidos_ignorados.csv")
        with inv_path.open("w", encoding="utf-8", newline="") as arquivo:
            campos = invalidos[0].keys()
            writer = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
            writer.writeheader()
            writer.writerows(invalidos)


def main():
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = localizar_relatorio_estoque()
        if csv_path is None:
            raise SystemExit(
                "Informe o CSV de estoque como argumento ou salve um arquivo "
                "'relatorio_estoque_*.csv' na pasta Downloads."
            )
    produtos, invalidos = carregar_produtos(csv_path)
    if not produtos:
        raise SystemExit("Nenhum codigo interno EAN-13 com prefixo 78900000 foi encontrado.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gerar_pngs(produtos, OUT_DIR / "imagens_png")
    gerar_pdf(produtos, OUT_DIR / "catalogo_codigos_barras_produtos_internos.pdf")
    gerar_resumo(produtos, invalidos, OUT_DIR / "produtos_internos_gerados.csv")

    print(f"Produtos internos: {len(produtos)}")
    print(f"Codigos invalidos ignorados: {len(invalidos)}")
    print(f"Saida: {(OUT_DIR).resolve()}")


if __name__ == "__main__":
    main()
