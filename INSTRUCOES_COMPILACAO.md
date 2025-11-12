# 🚀 Instruções Completas de Compilação - SGR Desktop

## 📋 Sumário

Este documento explica o processo completo de compilação do SGR Desktop, desde a criação do pacote do Flask até a geração do executável final do Electron, incluindo soluções para problemas comuns.

---

## 🎯 Objetivo

Gerar um executável `.exe` standalone que inclui:
- ✅ Backend Flask empacotado como executável
- ✅ Frontend Electron empacotado como aplicação desktop
- ✅ Tudo funcionando sem necessidade de Python ou Node.js instalados

---

## ⚡ Execução Rápida (Resumo)

Se você já conhece o processo, pode usar o método rápido:

### Método Rápido (Recomendado)

```powershell
# 1. Abra o PowerShell como Administrador
# 2. Navegue até a pasta do projeto
cd D:\git\Desktop

# 3. Execute o script de build
.\build.bat
```

**Isso realizará automaticamente:**
1. ✅ Empacotamento do Flask em executável
2. ✅ Cópia do executável para `resources/`
3. ✅ Limpeza do cache do electron-builder
4. ✅ Build do Electron
5. ✅ Verificação se o executável foi gerado

**Resultado:** `SGR-Desktop\frontend\dist\win-unpacked\SGR-Desktop.exe`

---

## 📋 Pré-requisitos Detalhados

Antes de começar, certifique-se de ter instalado:

- ✅ **Python 3.11+** (para criar o executável do Flask)
- ✅ **Node.js 18+** (para criar o executável do Electron)
- ✅ **npm 9+** (gerenciador de pacotes do Node.js)
- ✅ **Git** (para clonar o repositório)
- ✅ **Windows 10/11** (sistema operacional)

**Verificar versões instaladas:**
```bash
python --version    # Deve ser 3.11 ou superior
node --version      # Deve ser 18 ou superior
npm --version       # Deve ser 9 ou superior
```

---

## 🔧 Processo Completo de Compilação

### 📊 Fluxo do Processo de Build

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROCESSO DE BUILD                            │
└─────────────────────────────────────────────────────────────────┘

1. BACKEND (Flask)
   │
   ├── Criar ambiente virtual Python
   ├── Instalar dependências (Flask, PyInstaller, etc.)
   ├── Configurar config.env
   │
   └── Gerar executável do Flask
       │
       └── PyInstaller → flask_server.exe
           │
           └── backend/dist/flask_server.exe ✅

2. FRONTEND (Electron)
   │
   ├── Copiar flask_server.exe para resources/
   │   │
   │   └── frontend/resources/flask_server.exe ✅
   │
   ├── Instalar dependências do Electron
   ├── Limpar cache do electron-builder
   │
   └── Gerar executável do Electron
       │
       └── Electron Builder → SGR-Desktop.exe
           │
           └── frontend/dist/win-unpacked/SGR-Desktop.exe ✅
           │
           └── resources/flask_server.exe (incluído no pacote) ✅

3. RESULTADO FINAL
   │
   └── Aplicação standalone pronta para distribuição
       │
       ├── SGR-Desktop.exe (aplicação principal)
       └── flask_server.exe (backend empacotado)
```

---

### Passo 1: Preparar o Ambiente Backend (Flask)

#### 1.1. Navegar até a pasta backend

```bash
cd SGR-Desktop\backend
```

#### 1.2. Criar ambiente virtual (se não existir)

```bash
python -m venv venv
```

#### 1.3. Ativar ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

#### 1.4. Instalar dependências do Flask

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- Flask 2.3.3
- Flask-CORS 4.0.0
- requests 2.31.0
- python-dotenv 1.0.0
- beautifulsoup4 4.12.2
- lxml 4.9.3
- pyinstaller 6.16.0

#### 1.5. Configurar arquivo de configuração

```bash
copy config.env.example config.env
```

Edite o arquivo `config.env` com as configurações corretas:
- `API_EXTERNA_URL`: URL da API externa
- `API_TIMEOUT`: Timeout para requisições

---

### Passo 2: Criar Executável do Flask (PyInstaller)

#### 2.1. Verificar se PyInstaller está instalado

```bash
python -c "import PyInstaller"
```

Se não estiver instalado:
```bash
pip install pyinstaller
```

#### 2.2. Entender o arquivo de configuração do PyInstaller

O arquivo `flask_server.spec` contém a configuração completa do PyInstaller:

**Estrutura do arquivo `flask_server.spec`:**

```python
# flask_server.spec
# Configuração do PyInstaller para empacotar o Flask

# Análise do código Python
a = Analysis(
    ['app.py'],  # Arquivo principal do Flask
    pathex=[],   # Caminhos adicionais para módulos
    binaries=[], # Binários externos (se houver)
    datas=[
        ('config.env', '.'),  # Incluir arquivo de configuração
        ('config.env.example', '.'),  # Incluir exemplo (opcional)
    ],
    hiddenimports=[
        # Módulos que o PyInstaller não detecta automaticamente
        'app',
        'app.config',
        'app.proxy',
        'app.routes.analytics',
        'app.routes.avaliacoes',
        'app.routes.cardapio',
        'app.routes.pedidos',
        'app.routes.system',
        'app.services.diagnostics',
        'app.utils.status',
        # Bibliotecas Flask
        'flask',
        'flask_cors',
        'requests',
        'beautifulsoup4',
        'bs4',
        'lxml',
        'dotenv',
        # ... outros módulos necessários
    ],
    excludes=[
        # Pacotes que não são necessários (para reduzir tamanho)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'pytest',
        'pytest-mock',
        'pytest-cov',
    ],
)

# Criar arquivo ZIP com código Python
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Criar executável final
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='flask_server',  # Nome do executável
    debug=False,           # Modo debug desabilitado
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,              # Comprimir com UPX (reduz tamanho)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # Mostrar console para logs do Flask
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # Ícone do executável (opcional)
)
```

**Explicação das configurações:**

- **`datas`:** Arquivos que devem ser incluídos no executável (como `config.env`)
- **`hiddenimports`:** Módulos que o PyInstaller não detecta automaticamente
- **`excludes`:** Pacotes que não são necessários (para reduzir o tamanho do executável)
- **`console=True`:** Mostra console para logs do Flask (útil para debug)
- **`upx=True`:** Comprime o executável com UPX (reduz tamanho)

**Tamanho esperado do executável:**
- Com UPX: ~20-30 MB
- Sem UPX: ~40-50 MB

#### 2.3. Gerar executável do Flask

**Opção A: Usando script automatizado (Recomendado)**

```bash
cd SGR-Desktop\backend
.\build_flask.bat
```

**Opção B: Manualmente**

```bash
cd SGR-Desktop\backend
venv\Scripts\activate
pyinstaller flask_server.spec --clean --noconfirm
```

#### 2.4. Verificar se o executável foi gerado

```bash
Test-Path "SGR-Desktop\backend\dist\flask_server.exe"
```

Se retornar `True`, o executável foi gerado com sucesso! ✅

**Localização:** `SGR-Desktop\backend\dist\flask_server.exe`

---

### Passo 3: Preparar o Ambiente Frontend (Electron)

#### 3.1. Navegar até a pasta frontend

```bash
cd SGR-Desktop\frontend
```

#### 3.2. Instalar dependências do Electron

```bash
npm install
```

**Dependências principais:**
- electron 28.0.0
- electron-builder 24.0.0

#### 3.3. Entender a configuração do package.json

O arquivo `package.json` contém a configuração completa do Electron Builder:

**Estrutura da configuração de build:**

```json
{
  "build": {
    "appId": "com.sgrdesktop.app",
    "productName": "SGR-Desktop",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!**/node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}",
      "!**/node_modules/*/{test,__tests__,tests,powered-test,example,examples}",
      "!**/node_modules/*.d.ts",
      "!**/node_modules/.bin",
      "!**/*.{iml,o,hprof,orig,pyc,pyo,rbc,swp,csproj,sln,xproj}",
      "!.editorconfig",
      "!**/._*",
      "!**/{.DS_Store,.git,.hg,.svn,CVS,RCS,SCCS,.gitignore,.gitattributes}",
      "!**/{__pycache__,thumbs.db,.flowconfig,.idea,.vs,.nyc_output}",
      "!**/{appveyor.yml,.travis.yml,circle.yml}",
      "!**/{npm-debug.log,yarn.lock,.yarn-integrity,.yarn-metadata.json}",
      "!../backend/**"  // Excluir diretório backend
    ],
    "extraResources": [
      {
        "from": "resources/flask_server.exe",
        "to": "flask_server.exe"
      }
    ],
    "win": {
      "target": "dir",
      "icon": "assets/icon.ico",
      "sign": null,
      "signAndEditExecutable": false,
      "signDlls": false
    }
  }
}
```

**Explicação das configurações:**

- **`appId`:** Identificador único da aplicação
- **`productName`:** Nome do produto (aparece no executável)
- **`directories.output`:** Diretório de saída do build
- **`files`:** Lista de arquivos a incluir/excluir do pacote
- **`extraResources`:** Recursos adicionais (como `flask_server.exe`) que serão incluídos fora do `.asar`
- **`win.target`:** Tipo de build (`dir` = pasta descompactada, `nsis` = instalador)
- **`win.sign`:** Configuração de code signing (`null` = desabilitado)
- **`win.signAndEditExecutable`:** Não assinar executáveis
- **`win.signDlls`:** Não assinar DLLs

**Por que `extraResources` e não `files`?**

- **`extraResources`:** Arquivos são colocados em `resources/` (fora do `.asar`)
- **`files`:** Arquivos são incluídos no `.asar` (arquivo compactado)
- **Razão:** `flask_server.exe` precisa estar fora do `.asar` para ser executado como processo separado

#### 3.4. Como o main.js encontra o executável do Flask

O arquivo `main.js` do Electron contém lógica para encontrar o executável do Flask:

**Modo Desenvolvimento:**
- Usa Python do ambiente virtual: `backend/venv/Scripts/python.exe`
- Executa: `python.exe app.py`

**Modo Produção (Empacotado):**
- Procura `flask_server.exe` em múltiplos caminhos:
  1. `process.resourcesPath/flask_server.exe` (caminho padrão quando empacotado)
  2. `__dirname/../resources/flask_server.exe` (caminho alternativo)
  3. `__dirname/../backend/dist/flask_server.exe` (fallback)
  4. `process.cwd()/resources/flask_server.exe` (caminho relativo ao diretório de trabalho)

**Código do main.js:**
```javascript
function startFlask() {
    const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
    
    if (isDev) {
        // Modo desenvolvimento: usar Python do venv
        const flaskPath = path.join(__dirname, '..', 'backend', 'app.py');
        const pythonPath = path.join(__dirname, '..', 'backend', 'venv', 'Scripts', 'python.exe');
        flaskProcess = spawn(pythonPath, [flaskPath], {
            cwd: path.join(__dirname, '..', 'backend'),
            stdio: ['pipe', 'pipe', 'pipe']
        });
    } else {
        // Modo produção: usar executável do Flask
        const possiblePaths = [
            path.join(process.resourcesPath, 'flask_server.exe'),
            path.join(__dirname, '..', 'resources', 'flask_server.exe'),
            path.join(__dirname, '..', 'backend', 'dist', 'flask_server.exe'),
            path.join(process.cwd(), 'resources', 'flask_server.exe'),
        ];
        
        let finalPath = null;
        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(possiblePath)) {
                finalPath = possiblePath;
                break;
            }
        }
        
        if (!finalPath) {
            console.error('❌ Executável do Flask não encontrado');
            return null;
        }
        
        flaskProcess = spawn(finalPath, [], {
            cwd: path.dirname(finalPath),
            stdio: ['pipe', 'pipe', 'pipe']
        });
    }
}
```

**Por que múltiplos caminhos?**
- Garante compatibilidade em diferentes cenários
- Funciona tanto em desenvolvimento quanto em produção
- Funciona mesmo se o executável estiver em locais diferentes

**Configurações importantes:**
- ✅ `target: "dir"` - Gera pasta descompactada (não requer code signing)
- ✅ `sign: null` - Desabilita code signing (evita erros de symlinks)
- ✅ `signAndEditExecutable: false` - Não assina executáveis
- ✅ `signDlls: false` - Não assina DLLs
- ✅ `extraResources` - Inclui `flask_server.exe` no pacote (fora do `.asar`)

---

### Passo 4: Copiar Executável do Flask para Recursos do Electron

#### 4.1. Criar diretório de recursos (se não existir)

```bash
mkdir SGR-Desktop\frontend\resources
```

#### 4.2. Copiar executável do Flask

```bash
copy SGR-Desktop\backend\dist\flask_server.exe SGR-Desktop\frontend\resources\flask_server.exe
```

**Localização:** `SGR-Desktop\frontend\resources\flask_server.exe`

---

### Passo 5: Limpar Cache do Electron Builder

#### 5.1. Abrir PowerShell como Administrador

- Pressione `Win + X`
- Selecione "Windows PowerShell (Admin)" ou "Terminal (Admin)"
- Ou clique com botão direito no PowerShell e selecione "Executar como administrador"

#### 5.2. Limpar cache do winCodeSign

```powershell
Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
```

**Por que limpar o cache?**
- O cache pode conter arquivos com symbolic links corrompidos
- O Windows não consegue criar symbolic links sem privilégios administrativos
- Limpar o cache evita erros durante o build

---

### Passo 6: Compilar Aplicação Electron

#### 6.1. Usar script automatizado (Recomendado)

**Opção A: Script batch completo (build.bat)**

```bash
cd D:\git\Desktop
.\build.bat
```

Este script realiza automaticamente:
1. ✅ Empacota Flask em executável
2. ✅ Verifica se o executável foi gerado
3. ✅ Copia executável para `resources/`
4. ✅ Navega para pasta frontend
5. ✅ Limpa arquivos antigos
6. ✅ Instala dependências do Electron
7. ✅ Limpa cache do electron-builder
8. ✅ Executa build do Electron

**Opção B: Script PowerShell (build_sem_code_signing_v2.ps1)**

```powershell
cd D:\git\Desktop\SGR-Desktop\frontend
.\build_sem_code_signing_v2.ps1
```

Este script:
1. ✅ Limpa cache do electron-builder
2. ✅ Configura variáveis de ambiente para desabilitar code signing
3. ✅ Executa build do Electron
4. ✅ Verifica se o executável foi gerado

#### 6.2. Build manual (se scripts não funcionarem)

```powershell
# 1. Limpar cache
Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force

# 2. Navegar até pasta frontend
cd D:\git\Desktop\SGR-Desktop\frontend

# 3. Configurar variáveis de ambiente
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
$env:CSC_LINK = ""
$env:WIN_CSC_LINK = ""

# 4. Executar build
npm run build
```

---

### Passo 7: Verificar se o Build Funcionou

#### 7.1. Verificar se o executável foi gerado

```powershell
Test-Path "D:\git\Desktop\SGR-Desktop\frontend\dist\win-unpacked\SGR-Desktop.exe"
```

Se retornar `True`, o build foi bem-sucedido! ✅

#### 7.2. Estrutura do build gerado

```
SGR-Desktop/frontend/dist/
└── win-unpacked/
    ├── SGR-Desktop.exe          # Executável principal
    ├── resources/
    │   └── flask_server.exe     # Executável do Flask
    └── ... (outros arquivos do Electron)
```

#### 7.3. Testar o executável

1. Navegue até `SGR-Desktop\frontend\dist\win-unpacked\`
2. Execute `SGR-Desktop.exe`
3. Verifique se o aplicativo inicia corretamente
4. Verifique se o Flask está funcionando (console deve aparecer)

---

## ❌ Problema Principal: Erro de Symlinks

### ⚠️ O Erro Mais Comum

**Este é o erro mais frequente durante o build do SGR Desktop no Windows.**

### Descrição do Problema

O electron-builder está tentando baixar e extrair o `winCodeSign`, que contém symbolic links que o Windows não consegue criar sem privilégios administrativos.

**Erro apresentado:**
```
ERROR: Cannot create symbolic link : O cliente não tem o privilégio necessário.
```

**Quando acontece:**
- Durante o build do Electron
- Quando o electron-builder tenta baixar o `winCodeSign`
- Ao extrair arquivos com symbolic links

### Causa Raiz

1. **Symlinks no Windows**: O Windows requer privilégios administrativos para criar symbolic links
2. **winCodeSign**: O electron-builder baixa automaticamente o `winCodeSign` para code signing, mesmo quando não é necessário
3. **Cache Corrompido**: O cache do electron-builder pode conter arquivos com symlinks que não podem ser extraídos

### Solução Definitiva

**Passo 1: Desabilitar Code Signing no package.json**

```json
{
  "build": {
    "win": {
      "target": "dir",
      "icon": "assets/icon.ico",
      "sign": null,
      "signAndEditExecutable": false,
      "signDlls": false
    }
  }
}
```

**Passo 2: Limpar Cache do Electron Builder**

```powershell
# Execute como Administrador
Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
```

**Passo 3: Usar Target `dir` (Não Requer Code Signing)**

```json
{
  "win": {
    "target": "dir"  // Gera pasta descompactada (não requer code signing)
  }
}
```

**Passo 4: Executar Build**

```powershell
# Execute como Administrador
cd D:\git\Desktop
.\build.bat
```

### ⚠️ Nota Importante

**O erro de symlinks pode aparecer, mas o build ainda pode funcionar!**

- Verifique se o executável foi gerado mesmo com avisos
- Se `SGR-Desktop.exe` existir em `dist/win-unpacked/`, o build foi bem-sucedido
- Os avisos de symlinks podem ser ignorados se o executável foi gerado

---

## ❌ Outros Problemas Comuns e Soluções

### Problema 1: Caminho Incorreto do Flask

**Erro apresentado:**
```
file source doesn't exist  from=D:\git\Desktop\SGR-Desktop\frontend\backend\dist\flask_server.exe
```

**Causa:**
- O `package.json` estava procurando o executável do Flask em um caminho relativo incorreto
- O caminho estava como `frontend/backend/dist/` em vez de `backend/dist/`

**Solução:**
1. **Copiar executável do Flask para `resources/`:**
   ```bash
   copy SGR-Desktop\backend\dist\flask_server.exe SGR-Desktop\frontend\resources\flask_server.exe
   ```
2. **Atualizar `package.json`:**
   ```json
   {
     "extraResources": [
       {
         "from": "resources/flask_server.exe",
         "to": "flask_server.exe"
       }
     ]
   }
   ```
3. **Verificar se o arquivo existe:**
   ```powershell
   Test-Path "SGR-Desktop\frontend\resources\flask_server.exe"
   ```

---

### Problema 2: Propriedade `arch` Inválida

**Erro apresentado:**
```
Invalid configuration object. electron-builder 24.13.3 has been initialized using a configuration object that does not match the API schema.
- configuration.win has an unknown property 'arch'.
```

**Causa:**
- A propriedade `arch` não é válida dentro do objeto `win` no electron-builder 24.13.3

**Solução:**
- Remover propriedade `arch` de dentro de `win` no `package.json`
- A arquitetura é detectada automaticamente pelo electron-builder

**Configuração correta:**
```json
{
  "win": {
    "target": "dir",
    "icon": "assets/icon.ico"
  }
}
```

---

### Problema 3: Encoding no Script PowerShell

**Erro apresentado:**
```
A cadeia de caracteres não tem o terminador: ".
```

**Causa:**
- Emojis e caracteres especiais no script PowerShell causavam problemas de encoding

**Solução:**
- Use o script alternativo `build_sem_code_signing_v2.ps1` que não tem emojis
- Ou remova emojis do script original

---

### Problema 5: Executável não foi gerado

**Causa:**
- Build falhou antes de gerar o executável
- Erro de symlinks impediu o build
- Cache corrompido do electron-builder
- Problemas de permissão
- Arquivo `flask_server.exe` não encontrado em `resources/`

**Solução:**
1. **Verifique se o Flask foi gerado:**
   ```powershell
   Test-Path "SGR-Desktop\backend\dist\flask_server.exe"
   ```
2. **Verifique se o Flask foi copiado:**
   ```powershell
   Test-Path "SGR-Desktop\frontend\resources\flask_server.exe"
   ```
3. **Execute o PowerShell como Administrador**
4. **Limpe o cache manualmente:**
   ```powershell
   Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
   ```
5. **Verifique os logs do build para mais detalhes**

---

### Problema 6: PyInstaller não encontrado

**Erro apresentado:**
```
❌ PyInstaller não encontrado!
```

**Solução:**
1. **Ative o ambiente virtual:**
   ```bash
   cd SGR-Desktop\backend
   venv\Scripts\activate
   ```
2. **Instale PyInstaller:**
   ```bash
   pip install pyinstaller
   ```
3. **Ou instale todas as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Problema 7: Ambiente virtual não encontrado

**Erro apresentado:**
```
❌ Ambiente virtual não encontrado!
```

**Solução:**
1. **Crie o ambiente virtual:**
   ```bash
   cd SGR-Desktop\backend
   python -m venv venv
   ```
2. **Ative o ambiente virtual:**
   ```bash
   venv\Scripts\activate
   ```
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Problema 8: Electron Builder não encontrado

**Erro apresentado:**
```
electron-builder not found
```

**Solução:**
1. **Navegue até a pasta frontend:**
   ```bash
   cd SGR-Desktop\frontend
   ```
2. **Instale electron-builder:**
   ```bash
   npm install --save-dev electron-builder
   ```
3. **Ou instale todas as dependências:**
   ```bash
   npm install
   ```

---

## 🔍 Verificação Completa do Build

### Checklist de Verificação

- ✅ Ambiente virtual do Python criado e ativado
- ✅ Dependências do Flask instaladas
- ✅ Arquivo `config.env` configurado
- ✅ Executável do Flask gerado (`backend/dist/flask_server.exe`)
- ✅ Executável do Flask copiado para `frontend/resources/`
- ✅ Dependências do Electron instaladas
- ✅ Cache do electron-builder limpo
- ✅ Executável do Electron gerado (`frontend/dist/win-unpacked/SGR-Desktop.exe`)
- ✅ Aplicação testada e funcionando

---

## 📦 Estrutura Final do Build

```
SGR-Desktop/
├── backend/
│   ├── dist/
│   │   └── flask_server.exe        # Executável do Flask (gerado pelo PyInstaller)
│   ├── build_flask.bat             # Script para gerar executável do Flask
│   └── flask_server.spec           # Configuração do PyInstaller
├── frontend/
│   ├── resources/
│   │   └── flask_server.exe        # Copiado do backend/dist/ (incluído no pacote)
│   ├── dist/
│   │   └── win-unpacked/
│   │       ├── SGR-Desktop.exe     # Executável final do Electron
│   │       └── resources/
│   │           └── flask_server.exe # Executável do Flask (incluído no pacote)
│   ├── build_sem_code_signing_v2.ps1 # Script PowerShell para build
│   └── package.json                # Configuração do Electron Builder
└── build.bat                       # Script principal de build
```

---

## 🚀 Execução Rápida (Resumo)

### Método 1: Script Automatizado (Recomendado)

```bash
# 1. Abra o PowerShell como Administrador
# 2. Navegue até a pasta do projeto
cd D:\git\Desktop

# 3. Execute o script de build
.\build.bat
```

### Método 2: Script PowerShell

```powershell
# 1. Abra o PowerShell como Administrador
# 2. Limpe o cache
Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force

# 3. Navegue até a pasta frontend
cd D:\git\Desktop\SGR-Desktop\frontend

# 4. Execute o script
.\build_sem_code_signing_v2.ps1
```

### Método 3: Manual (Passo a Passo)

```bash
# 1. Gerar executável do Flask
cd SGR-Desktop\backend
.\build_flask.bat

# 2. Copiar executável para resources
copy dist\flask_server.exe ..\frontend\resources\flask_server.exe

# 3. Limpar cache (como Administrador)
Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force

# 4. Compilar Electron
cd ..\frontend
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npm run build
```

---

## 📝 Notas Importantes

### 1. Privilégios Administrativos

- **Importante:** Execute o PowerShell como Administrador para limpar o cache corretamente
- **Por quê:** O Windows requer privilégios administrativos para remover arquivos com symlinks

### 2. Code Signing

- **Desenvolvimento:** Code signing não é necessário
- **Produção:** Para distribuição, será necessário configurar code signing adequadamente
- **Solução atual:** Code signing está desabilitado para evitar erros de symlinks

### 3. Target `dir` vs `nsis`

- **`dir`:** Gera pasta descompactada (não requer code signing)
- **`nsis`:** Gera instalador (requer code signing)
- **Solução atual:** Usando `dir` para evitar necessidade de code signing

### 4. Cache do Electron Builder

- **Problema:** Cache pode conter arquivos com symlinks corrompidos
- **Solução:** Limpar cache antes de cada build (se necessário)
- **Localização:** `%LOCALAPPDATA%\electron-builder\Cache\winCodeSign`

### 5. Executável do Flask

- **Geração:** PyInstaller gera `flask_server.exe` em `backend/dist/`
- **Cópia:** Script `build.bat` copia para `frontend/resources/`
- **Empacotamento:** Electron Builder inclui em `extraResources`

---

## 🎉 Resultado Final

Após o build bem-sucedido, você terá:

- ✅ **Executável do Flask** (`backend/dist/flask_server.exe`)
- ✅ **Executável do Electron** (`frontend/dist/win-unpacked/SGR-Desktop.exe`)
- ✅ **Aplicação standalone** (não requer Python ou Node.js instalados)
- ✅ **Pronto para distribuição** (para desenvolvimento/testes)

---

## 📚 Documentação Adicional

Para mais detalhes, consulte:

- 📘 [`SGR-Desktop/frontend/COMO_EXECUTAR_BUILD.md`](./SGR-Desktop/frontend/COMO_EXECUTAR_BUILD.md) — guia passo a passo para executar o build
- 📋 [`Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md`](./Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md) — documentação técnica completa do backend
- 🎨 [`Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md`](./Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md) — documentação técnica completa do frontend

---

## 🔄 Próximos Passos

1. ✅ **Testar o executável gerado**
   - Execute `SGR-Desktop.exe`
   - Verifique se o aplicativo inicia corretamente
   - Verifique se o Flask está funcionando

2. ✅ **Distribuir para clientes**
   - Copie a pasta `win-unpacked/` completa
   - Ou crie um instalador usando `nsis` (requer code signing)

3. ✅ **Configurar code signing (produção)**
   - Obtenha um certificado de code signing
   - Configure no `package.json`
   - Gere instalador usando `nsis`

---

**Última atualização:** Dezembro 2024
**Versão:** 1.0.0
