# Script PowerShell para build sem code signing (Versao 2 - Mais Robusta)
# Limpa cache do electron-builder e executa build

# Definir codificacao UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BUILD SEM CODE SIGNING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Passo 1: Limpar cache do electron-builder
Write-Host "[1/3] Limpando cache do electron-builder..." -ForegroundColor Yellow

$cachePath = "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign"

if (Test-Path $cachePath) {
    Write-Host "  Cache encontrado: $cachePath" -ForegroundColor Gray
    try {
        # Tentar remover arquivos individuais primeiro
        $items = Get-ChildItem -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
        $itemCount = ($items | Measure-Object).Count
        Write-Host "  Removendo $itemCount itens..." -ForegroundColor Gray
        
        foreach ($item in $items) {
            try {
                Remove-Item -Path $item.FullName -Force -ErrorAction SilentlyContinue
            } catch {
                # Ignorar erros de symlinks
            }
        }
        
        # Tentar remover diretorio
        Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Cache removido com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "  [AVISO] Nao foi possivel remover todo o cache: $_" -ForegroundColor Yellow
        Write-Host "  Continuando mesmo assim..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] Cache nao encontrado (ja esta limpo)" -ForegroundColor Green
}

Write-Host ""

# Passo 2: Configurar variaveis de ambiente
Write-Host "[2/3] Configurando variaveis de ambiente..." -ForegroundColor Yellow

$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
$env:CSC_LINK = ""
$env:WIN_CSC_LINK = ""
$env:CSC_KEY_PASSWORD = ""
$env:CSC_NAME = ""
$env:SKIP_NOTARIZATION = "true"

Write-Host "  [OK] Code signing desabilitado" -ForegroundColor Green
Write-Host ""

# Passo 3: Executar build
Write-Host "[3/3] Executando build do Electron..." -ForegroundColor Yellow
Write-Host "  Comando: npm run build" -ForegroundColor Gray
Write-Host ""

npm run build

$buildExitCode = $LASTEXITCODE
Write-Host ""

# Verificar resultado
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICACAO DO BUILD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$exePath = "dist\win-unpacked\SGR-Desktop.exe"

if (Test-Path $exePath) {
    Write-Host "[SUCCESS] Executavel gerado com sucesso!" -ForegroundColor Green
    Write-Host "  Caminho: $exePath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD CONCLUIDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[ERROR] Executavel nao foi gerado" -ForegroundColor Red
    Write-Host "  Caminho esperado: $exePath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Possiveis causas:" -ForegroundColor Yellow
    Write-Host "  1. Erro de symlinks no cache do winCodeSign" -ForegroundColor Gray
    Write-Host "  2. Cache corrompido do electron-builder" -ForegroundColor Gray
    Write-Host "  3. Problemas de permissao" -ForegroundColor Gray
    Write-Host "  4. Arquivo flask_server.exe nao encontrado em resources/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Solucoes:" -ForegroundColor Yellow
    Write-Host "  1. Execute o PowerShell como Administrador" -ForegroundColor Gray
    Write-Host "  2. Limpe o cache manualmente:" -ForegroundColor Gray
    Write-Host "     Remove-Item -Path '$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign' -Recurse -Force" -ForegroundColor White
    Write-Host "  3. Verifique se flask_server.exe existe em: frontend\resources\" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

