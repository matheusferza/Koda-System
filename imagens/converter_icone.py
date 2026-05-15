from PIL import Image

# Substitua pelo caminho completo da sua imagem PNG
caminho_png = "C:\\Users\\mfgm5\\OneDrive\\Documentos\\App_frutaria_3.0\\APP_FRUTAS.png"

# O nome do arquivo ICO que será criado
caminho_ico = "C:\\Users\\mfgm5\\OneDrive\\Documentos\\App_frutaria_3.0\\APP_FRUTAS.ico"

# Abrir a imagem
img = Image.open(caminho_png)

# Converter e salvar no formato ICO
img.save(caminho_ico, format='ICO')

print(f"Arquivo .ico criado com sucesso em: {caminho_ico}")
