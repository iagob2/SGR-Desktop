@echo off
echo ========================================
echo   EMPACOTANDO FLASK EM EXECUTAVEL
echo ========================================
echo.

REM Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Ambiente virtual não encontrado!
    echo 💡 Execute primeiro: python -m venv venv
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo 🐍 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar se PyInstaller está instalado
echo 📦 Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller não encontrado!
    echo 💡 Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Erro ao instalar PyInstaller
        pause
        exit /b 1
    )
)

REM Limpar builds anteriores
echo 🧹 Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "flask_server.spec" (
    echo ✅ Arquivo .spec encontrado
) else (
    echo ❌ Arquivo flask_server.spec não encontrado!
    echo 💡 Certifique-se de que o arquivo .spec existe
    pause
    exit /b 1
)

REM Gerar executável
echo 🔨 Gerando executável...
pyinstaller flask_server.spec --clean --noconfirm

if errorlevel 1 (
    echo ❌ Erro ao gerar executável
    pause
    exit /b 1
)

REM Verificar se o executável foi gerado
if exist "dist\flask_server.exe" (
    echo.
    echo ========================================
    echo   ✅ EXECUTAVEL GERADO COM SUCESSO!
    echo ========================================
    echo.
    echo 📁 Executável está em: dist\flask_server.exe
    echo.
    echo 🚀 Próximos passos:
    echo    1. Teste o executável: dist\flask_server.exe
    echo    2. Copie o executável para o diretório do Electron
    echo    3. Atualize o main.js do Electron para usar o .exe
    echo.
) else (
    echo ❌ Executável não foi gerado!
    echo 💡 Verifique os logs acima para erros
    pause
    exit /b 1
)

pause