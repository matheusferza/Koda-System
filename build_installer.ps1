$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseScript = Join-Path $projectRoot "build_release.ps1"
$issFile = Join-Path $projectRoot "KODA_SYSTEM.iss"
$installerOutput = Join-Path $projectRoot "installer"
$compilerOutput = Join-Path $env:TEMP "KodaSystemInstallerBuild"
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "ISCC.exe não encontrado. Instale o Inno Setup 6 antes de gerar o instalador."
}

if (-not (Test-Path $releaseScript)) {
    throw "Script de build não encontrado: $releaseScript"
}

Write-Host "Gerando pasta de distribuição..."
powershell -ExecutionPolicy Bypass -File $releaseScript

if (-not (Test-Path $installerOutput)) {
    New-Item -ItemType Directory -Path $installerOutput | Out-Null
}
if (Test-Path $compilerOutput) {
    Remove-Item $compilerOutput -Recurse -Force
}
New-Item -ItemType Directory -Path $compilerOutput | Out-Null

Write-Host "Compilando instalador..."
& $iscc "/O$compilerOutput" $issFile
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao compilar o instalador."
}

Copy-Item -Path (Join-Path $compilerOutput "KODA_SYSTEM_Instalador.exe") -Destination $installerOutput -Force

Write-Host "Instalador gerado em $installerOutput"
