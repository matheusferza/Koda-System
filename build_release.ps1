$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$distRoot = Join-Path $projectRoot "deploy"
$specFile = Join-Path $projectRoot "KODA_SYSTEM.spec"
$seedDb = Join-Path $projectRoot "frutaria_base.db"
$templateCsv = Join-Path $projectRoot "template_importacao_produtos.csv"
$appFolderName = "KODA_SYSTEM"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pythonExe) {
    throw "Python nao encontrado. Crie uma .venv no projeto ou tenha 'python' disponivel no PATH."
}

Write-Host "Limpando builds anteriores..."
foreach ($folder in @("build", "dist", "deploy")) {
    $target = Join-Path $projectRoot $folder
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force
    }
}

if (Test-Path $seedDb) {
    Remove-Item $seedDb -Force
}

Write-Host "Gerando template de importacao..."
@"
acao;nome;preco;estoque;unidade;sku;cod_barras
novo;EXEMPLO PRODUTO;4.95;20;un;;
atualizar;EXEMPLO PRODUTO;5.45;25;un;;
"@ | Set-Content -Path $templateCsv -Encoding UTF8

Write-Host "Gerando banco base limpo para distribuicao..."
$seedScript = @'
from database import setup_database, verify_and_add_initial_users

seed_db = r"__SEED_DB__"
setup_database(seed_db)
verify_and_add_initial_users(seed_db)
print(seed_db)
'@
$seedScript.Replace("__SEED_DB__", $seedDb) | & $pythonExe -
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o banco base de distribuicao."
}

Write-Host "Gerando executavel KODA_SYSTEM..."
& $pythonExe -m PyInstaller --noconfirm $specFile
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o executavel com PyInstaller."
}

New-Item -ItemType Directory -Path $distRoot | Out-Null
Copy-Item -Path (Join-Path $projectRoot "dist\\$appFolderName") -Destination $distRoot -Recurse -Force

$readmePath = Join-Path $distRoot "COMO_INSTALAR.txt"
@"
KODA SYSTEM - DISTRIBUICAO

1. Copie a pasta KODA_SYSTEM inteira para o outro computador.
2. Execute KODA_SYSTEM.exe dentro da pasta.
3. Nao remova os arquivos internos, imagens ou DLLs.

Observacoes:
- O banco frutaria.db sera criado automaticamente na primeira abertura do app.
- A distribuicao leva um banco base limpo com apenas os usuarios iniciais:
  gerente1 / 1234
  caixa1 / 1234
- Para impressao Bematech, instale o driver da impressora no computador de destino.
- Para a balanca, conecte a porta USB/serial antes de abrir o app.
"@ | Set-Content -Path $readmePath -Encoding UTF8

Write-Host "Build concluido em $distRoot"
