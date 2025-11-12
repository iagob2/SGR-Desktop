@echo off
echo ========================================
echo   COMPILANDO SGR DESKTOP
echo ========================================
echo.

REM Passo 1: Empacotar Flask
echo [1/8] Empacotando Flask em executável...
cd SGR-Desktop\backend
call build_flask.bat
if errorlevel 1 (
    echo ❌ Erro ao empacotar Flask
    pause
    exit /b 1
)
cd ..\..

REM Passo 2: Verificar se o executável do Flask foi gerado
echo [2/8] Verificando executável do Flask...
if not exist "SGR-Desktop\backend\dist\flask_server.exe" (
    echo ❌ Executável do Flask não encontrado!
    echo 💡 Verifique se o build do Flask foi concluído com sucesso
    pause
    exit /b 1
)
echo ✅ Executável do Flask encontrado

REM Passo 3: Copiar executável do Flask para recursos do Electron
echo [3/8] Copiando executável do Flask para recursos do Electron...
if not exist "SGR-Desktop\frontend\resources" mkdir "SGR-Desktop\frontend\resources"
copy /Y "SGR-Desktop\backend\dist\flask_server.exe" "SGR-Desktop\frontend\resources\flask_server.exe"
if errorlevel 1 (
    echo ❌ Erro ao copiar executável do Flask
    pause
    exit /b 1
)
echo ✅ Executável do Flask copiado

REM Passo 4: Navegar para a pasta frontend
echo [4/8] Navegando para pasta frontend...
cd SGR-Desktop\frontend

REM Passo 5: Limpar arquivos antigos
echo [5/8] Limpando arquivos antigos...
if exist dist rmdir /s /q dist
if exist "dist-win" rmdir /s /q dist-win
echo ✅ Arquivos antigos removidos
echo.

REM Passo 6: Instalar dependências do Electron
echo [6/8] Instalando dependências do Electron...
call npm install
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✅ Dependências instaladas
echo.

REM Passo 7: Limpar cache do electron-builder (winCodeSign)
echo [7/8] Limpando cache do electron-builder...
echo 💡 Removendo cache problemático do winCodeSign...
REM Tentar remover cache usando PowerShell (mais eficiente)
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path '%LOCALAPPDATA%\electron-builder\Cache\winCodeSign') { Remove-Item -Path '%LOCALAPPDATA%\electron-builder\Cache\winCodeSign' -Recurse -Force -ErrorAction SilentlyContinue; Write-Host 'Cache removido' } else { Write-Host 'Cache não encontrado' }" 2>nul
REM Verificar se ainda existe (fallback)
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" (
    echo ⚠️  Cache ainda existe - tentando remover manualmente...
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" 2>nul
    if errorlevel 1 (
        echo ⚠️  Não foi possível remover cache (pode precisar de privilégios administrativos)
        echo 💡 Isso não impedirá o build, mas pode gerar avisos...
    ) else (
        echo ✅ Cache removido com sucesso
    )
) else (
    echo ✅ Cache limpo (não existe ou foi removido)
)
echo.

REM Passo 8: Compilar aplicativo
echo [8/8] Compilando aplicativo para Windows...
echo 💡 Usando script PowerShell para build sem code signing...
echo.
REM Tentar usar script PowerShell (mais robusto)
if exist "build_sem_code_signing.ps1" (
    echo 💡 Executando script PowerShell para build...
    powershell -NoProfile -ExecutionPolicy Bypass -File "build_sem_code_signing.ps1"
    set BUILD_EXIT_CODE=%errorlevel%
) else if exist "build_sem_code_signing_v2.ps1" (
    echo 💡 Executando script PowerShell alternativo para build...
    powershell -NoProfile -ExecutionPolicy Bypass -File "build_sem_code_signing_v2.ps1"
    set BUILD_EXIT_CODE=%errorlevel%
) else (
    echo ⚠️  Script PowerShell não encontrado, usando método alternativo...
    echo 💡 Desabilitando code signing completamente...
    set CSC_IDENTITY_AUTO_DISCOVERY=false
    set CSC_LINK=
    set WIN_CSC_LINK=
    set CSC_KEY_PASSWORD=
    set CSC_NAME=
    set SKIP_NOTARIZATION=true
    echo.
    echo 🔨 Iniciando build do Electron...
    call npm run build
    set BUILD_EXIT_CODE=%errorlevel%
)
echo.
REM Verificar se o executável foi gerado (importante: verificar resultado real)
echo 🔍 Verificando se o executável foi gerado...
if exist "dist\win-unpacked\SGR-Desktop.exe" (
    echo ✅ Executável gerado com sucesso!
    echo 📁 Executável está em: dist\win-unpacked\SGR-Desktop.exe
    echo.
    echo 💡 Se houve avisos sobre symlinks, eles foram ignorados
    echo 💡 O executável está pronto para uso!
    set BUILD_SUCCESS=1
) else (
    echo ❌ Executável não foi gerado
    echo.
    echo 💡 Possíveis causas:
    echo    1. Erro de symlinks no cache do winCodeSign
    echo    2. Cache corrompido do electron-builder
    echo    3. Problemas de permissão
    echo    4. Arquivo flask_server.exe não encontrado em resources/
    echo.
    echo 💡 Soluções:
    echo    1. Execute o PowerShell como Administrador e execute:
    echo       cd SGR-Desktop\frontend
    echo       .\build_sem_code_signing.ps1
    echo    2. Ou limpe o cache manualmente:
    echo       Remove-Item -Path '%LOCALAPPDATA%\electron-builder\Cache\winCodeSign' -Recurse -Force
    echo    3. Verifique se flask_server.exe existe em: frontend\resources\
    echo.
    set BUILD_SUCCESS=0
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!
echo ========================================
echo.
echo 📁 O executável está em: SGR-Desktop\frontend\dist\
echo.
echo 🚀 Próximos passos:
echo    1. Teste o arquivo .exe gerado
echo    2. Distribua para seus clientes
echo    3. Parabéns! 🎉
echo.
pause