@echo off
echo 🚀 Iniciando servidor Flask SGR-Desktop...
echo.
echo 📍 Diretório: %CD%
echo.

REM Tentar diferentes comandos Python
echo 🔍 Procurando Python...

REM Tentar python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python encontrado!
    echo 🚀 Iniciando servidor...
    python app.py
    goto :end
)

REM Tentar python3
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python3 encontrado!
    echo 🚀 Iniciando servidor...
    python3 app.py
    goto :end
)

REM Tentar py
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Py encontrado!
    echo 🚀 Iniciando servidor...
    py app.py
    goto :end
)

echo ❌ Python não encontrado!
echo.
echo 💡 Instale o Python de uma das seguintes formas:
echo    1. https://www.python.org/downloads/
echo    2. Microsoft Store
echo    3. Anaconda/Miniconda
echo.
echo 🔧 Ou configure o PATH do Python no Windows
echo.

:end
pause
