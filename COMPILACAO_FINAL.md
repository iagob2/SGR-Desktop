# 📦 Guia de Compilação e Distribuição Final - SGR Desktop

Este guia detalha como compilar seu aplicativo Electron SGR Desktop em um executável final para distribuição aos clientes.

---

## 🎯 Objetivo

Gerar um arquivo executável (.exe para Windows, .dmg para macOS) que seus clientes possam instalar e usar sem precisar de Python, Node.js ou qualquer dependência adicional.

---

## 📋 Pré-requisitos

Antes de começar, você precisa ter:

1. ✅ **Node.js instalado** (versão 16 ou superior)
2. ✅ **npm ou yarn** (gerenciador de pacotes)
3. ✅ **Python instalado** (para rodar o backend durante a compilação)
4. ✅ **PostgreSQL rodando** (para os dados de teste)

---

## 🛠️ Passo 1: Instalar electron-builder

O `electron-builder` é a ferramenta que vai gerar o executável final.

```bash
# Navegue até a pasta frontend
cd SGR-Desktop/frontend

# Instale o electron-builder como dependência de desenvolvimento
npm install --save-dev electron-builder
```

---

## 🛠️ Passo 2: Configurar o package.json

Adicione a configuração do electron-builder no seu `package.json`:

```json
{
  "name": "sgr-desktop",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "dist": "electron-builder --publish=never"
  },
  "build": {
    "appId": "com.sabore.desktop",
    "productName": "SGR Desktop",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!**/*.md",
      "!.git",
      "!.gitignore",
      "!node_modules",
      "!dist",
      "!*.bat"
    ],
    "win": {
      "target": [
        {
          "target": "nsis",
          "arch": ["x64", "ia32"]
        }
      ],
      "icon": "assets/icon.ico"
    },
    "mac": {
      "target": [
        {
          "target": "dmg",
          "arch": ["x64", "arm64"]
        }
      ],
      "icon": "assets/icon.icns"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  }
}
```

---

## 🛠️ Passo 3: Criar Ícones para o Aplicativo

Você precisa criar ícones para o aplicativo:

### Windows (.ico)
- Crie ou baixe um arquivo de ícone
- Coloque em: `SGR-Desktop/frontend/assets/icon.ico`
- Tamanho recomendado: 256x256 pixels

### macOS (.icns)
- Coloque em: `SGR-Desktop/frontend/assets/icon.icns`
- Tamanho recomendado: 512x512 pixels

**💡 Dica:** Use um editor de imagens ou gerador online de ícones:
- https://www.favicon-generator.org/
- https://convertio.co/pt/ico-icns/

---

## 🛠️ Passo 4: Criar Script de Compilação

Crie um arquivo `build.bat` (Windows) ou `build.sh` (Linux/Mac) na pasta raiz do projeto:

### build.bat (Windows)
```batch
@echo off
echo ========================================
echo   COMPILANDO SGR DESKTOP
echo ========================================
echo.

REM Navegar para a pasta frontend
cd frontend

echo [1/3] Limpando arquivos antigos...
if exist dist rmdir /s /q dist
if exist "dist-win" rmdir /s /q dist-win

echo [2/3] Instalando dependências...
call npm install

echo [3/3] Compilando aplicativo...
call npm run build

echo.
echo ========================================
echo   COMPILAÇÃO CONCLUÍDA!
echo ========================================
echo.
echo O executável está em: frontend\dist\
echo.
pause
```

### build.sh (Linux/Mac)
```bash
#!/bin/bash
echo "========================================"
echo "  COMPILANDO SGR DESKTOP"
echo "========================================"
echo ""

cd frontend

echo "[1/3] Limpando arquivos antigos..."
rm -rf dist

echo "[2/3] Instalando dependências..."
npm install

echo "[3/3] Compilando aplicativo..."
npm run build

echo ""
echo "========================================"
echo "  COMPILAÇÃO CONCLUÍDA!"
echo "========================================"
echo ""
echo "O executável está em: frontend/dist/"
echo ""
```

---

## 🛠️ Passo 5: Compilar o Aplicativo

### No Windows:
```bash
# Execute o arquivo build.bat
.\build.bat

# OU execute diretamente
cd frontend
npm run build
```

### No Linux/Mac:
```bash
# Dê permissão de execução
chmod +x build.sh

# Execute
./build.sh

# OU execute diretamente
cd frontend
npm run build
```

---

## 📁 O que vai ser gerado?

Após a compilação, você terá:

```
SGR-Desktop/frontend/dist/
├── SGR Desktop Setup 1.0.0.exe  ← Arquivo de instalação (Windows)
└── win-unpacked/                 ← Pasta com o app descompactado (para testar)
```

### Arquivos gerados:

#### Windows (.exe)
- `SGR Desktop Setup 1.0.0.exe` - Instalador do aplicativo
- Tamanho aproximado: 80-150 MB
- Pode ser distribuído para seus clientes

#### macOS (.dmg)
- `SGR Desktop-1.0.0.dmg` - Disco virtual para instalação
- Tamanho aproximado: 90-160 MB
- Pode ser distribuído para seus clientes

---

## 🧪 Passo 6: Testar o Executável

### Windows
1. Navegue até: `SGR-Desktop/frontend/dist/`
2. Execute o arquivo `SGR Desktop Setup 1.0.0.exe`
3. Siga o assistente de instalação
4. O aplicativo será instalado e você pode abrir do menu Iniciar

### macOS
1. Abra o arquivo `.dmg`
2. Arraste o aplicativo para a pasta Applications
3. Abra o aplicativo

---

## 🚀 Passo 7: Distribuir para Clientes

### Opção 1: Distribuição Manual
1. Copie o arquivo `.exe` (Windows) ou `.dmg` (Mac)
2. Envie via email, pendrive, ou plataforma de download
3. O cliente instala executando o arquivo

### Opção 2: Distribuição Online
1. Faça upload do arquivo em um servidor (Google Drive, Dropbox, AWS S3)
2. Envie o link de download para o cliente
3. O cliente baixa e instala

---

## 📝 Checklist de Compilação

Antes de compilar, verifique:

- [ ] Todas as dependências do `package.json` estão instaladas
- [ ] Ícones (icon.ico/icon.icns) estão na pasta `assets/`
- [ ] Backend Flask está funcionando corretamente
- [ ] Todas as funcionalidades foram testadas
- [ ] Versão do aplicativo está correta no `package.json`

---

## 🔧 Resolução de Problemas Comuns

### Erro: "electron-builder not found"
```bash
npm install --save-dev electron-builder
```

### Erro: "Icon not found"
- Certifique-se de que os ícones estão em `frontend/assets/`
- Nome dos arquivos: `icon.ico` (Windows) e `icon.icns` (Mac)

### Erro: "Python not found" durante compilação
- O Python precisa estar instalado e no PATH
- Ou desabilite a verificação do Flask durante a compilação

### Executável muito grande
- Remova node_modules antes de compilar
- Use `electron-builder --dir` para gerar apenas pasta (não instalador)

---

## 📊 Tamanho do Executável

| Plataforma | Tamanho Aproximado |
|------------|-------------------|
| Windows (.exe) | 80-150 MB |
| macOS (.dmg) | 90-160 MB |
| Linux (.AppImage) | 70-140 MB |

**💡 Dica:** O tamanho é grande porque inclui:
- Node.js (runtime)
- Electron (framework)
- Todas as dependências do projeto
- Backend Python (se incluído)

---

## 🎉 Finalização

Após a compilação bem-sucedida:

1. ✅ Teste o executável em uma máquina limpa (sem Python/Node instalado)
2. ✅ Verifique se todas as funcionalidades funcionam
3. ✅ Distribua para seus clientes
4. ✅ Crie um arquivo README com instruções de instalação

---

## 📚 Arquivos de Referência

- **Documentação Electron Builder**: https://www.electron.build/
- **Guia de Otimização**: https://www.electron.build/configuration/configuration

---

## 🏆 Produto Final

Você terá um arquivo executável que:

✅ **Não precisa** de instalação de Python
✅ **Não precisa** de instalação de Node.js
✅ **Não precisa** de configuração manual
✅ **Funciona** em qualquer computador Windows/Mac
✅ **Inclui** tudo o que é necessário para rodar

**É isso que seus clientes vão receber!** 🎉

---

## 📞 Suporte

Se tiver problemas durante a compilação, verifique:
1. Logs de erro no console
2. Documentação do electron-builder
3. Issues conhecidas no GitHub do Electron

---

**Última atualização:** Dezembro 2024  
**Versão do guia:** 1.0.0
