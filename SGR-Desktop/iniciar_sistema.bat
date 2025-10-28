@echo off
echo 🚀 Iniciando Sistema SGR-Desktop...
echo.

REM Verificar se o ambiente virtual existe
if not exist "backend\venv\Scripts\python.exe" (
    echo ❌ Ambiente virtual não encontrado!
    echo 💡 Execute primeiro: cd backend && python -m venv venv
    pause
    exit /b 1
)

REM Parar processos Python existentes
echo 🛑 Parando processos Python existentes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

REM Aguardar um pouco
timeout /t 2 /nobreak >nul

REM Iniciar servidor Flask
echo 🐍 Iniciando servidor Flask...
cd backend
start /B venv\Scripts\python.exe app.py

REM Aguardar servidor inicializar
echo ⏳ Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

REM Verificar se servidor está rodando
echo 🔍 Verificando se servidor está rodando...
curl -s http://localhost:5000/api/dashboard/15 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Servidor Flask rodando em http://localhost:5000
) else (
    echo ⚠️  Servidor pode não estar rodando ainda...
)

REM Voltar para diretório frontend
cd ..\frontend

REM Iniciar aplicação Electron
echo 🖥️  Iniciando aplicação Electron...
npm start

pause
