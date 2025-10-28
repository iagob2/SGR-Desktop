@echo off
echo ========================================
echo   COMPILANDO SGR DESKTOP
echo ========================================
echo.

REM Navegar para a pasta frontend
cd frontend

echo [1/4] Limpando arquivos antigos...
if exist dist rmdir /s /q dist
if exist "dist-win" rmdir /s /q dist-win
echo ✅ Arquivos antigos removidos
echo.

echo [2/4] Instalando dependências do Electron...
call npm install
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✅ Dependências instaladas
echo.

echo [3/4] Instalando electron-builder (se necessário)...
call npm install --save-dev electron-builder
if errorlevel 1 (
    echo ⚠️  electron-builder já instalado ou erro na instalação
)
echo ✅ electron-builder pronto
echo.

echo [4/4] Compilando aplicativo para Windows...
call npm run build
if errorlevel 1 (
    echo ❌ Erro ao compilar
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!
echo ========================================
echo.
echo 📁 O executável está em: frontend\dist\
echo.
echo 🚀 Próximos passos:
echo    1. Teste o arquivo .exe gerado
echo    2. Distribua para seus clientes
echo    3. Parabéns! 🎉
echo.
pause
