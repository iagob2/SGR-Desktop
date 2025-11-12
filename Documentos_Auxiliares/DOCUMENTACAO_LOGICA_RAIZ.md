# 📁 Documentação Detalhada da Lógica do Diretório Raiz (SGR-Desktop)

> **📖 Sobre este documento:** Esta documentação explica a organização geral do projeto SGR Desktop, incluindo scripts de inicialização, orquestração entre backend e frontend, fluxos de execução e pontos de entrada do sistema. Ideal para entender como o sistema é iniciado e coordenado.

## 📂 Visão Geral do Diretório Raiz

O diretório raiz `SGR-Desktop/` é o **ponto de entrada** e **orquestrador** de todo o sistema. Ele contém:

- **Scripts de inicialização** que coordenam backend e frontend
- **Documentação** centralizada do projeto
- **Estrutura de diretórios** que organiza backend e frontend
- **Configurações** compartilhadas

**Arquitetura Geral:**
```
SGR-Desktop/
├── backend/          # Servidor Flask (Proxy)
├── frontend/         # Aplicação Electron (UI)
├── scripts/          # Scripts de automação
└── docs/             # Documentação
```

---

## 🏗️ Estrutura de Diretórios

### 📁 `backend/` - Servidor Flask

**Responsabilidade:** Proxy inteligente entre frontend e API externa Java.

**Conteúdo:**
- `app.py` - Ponto de entrada do servidor
- `app/` - Módulo principal da aplicação
- `config.env` - Configurações (não versionado)
- `requirements.txt` - Dependências Python
- `venv/` - Ambiente virtual Python

**Documentação:** Ver `DOCUMENTACAO_BACKEND.md` (em `Documentos_Auxiliares/`)

---

### 📁 `frontend/` - Aplicação Electron

**Responsabilidade:** Interface desktop do usuário.

**Conteúdo:**
- `main.js` - Processo principal do Electron
- `index.html` - Shell principal (SPA)
- `paginas/` - Páginas HTML da aplicação
- `js/` - Scripts JavaScript por página
- `css/` - Estilos CSS por página
- `package.json` - Configuração npm/Electron

**Documentação:** Ver `DOCUMENTACAO_FRONTEND.md` (em `Documentos_Auxiliares/`)

---

## 🚀 Scripts de Inicialização

### 📄 `iniciar_sistema.bat` - Script Principal de Inicialização

**Localização:** `SGR-Desktop/iniciar_sistema.bat`

**Responsabilidade:** Inicia backend e frontend em sequência.

**Fluxo de Execução:**

```
1. Verifica se venv existe
   ↓
2. Para processos Python existentes
   ↓
3. Inicia servidor Flask (em background)
   ↓
4. Aguarda 5 segundos
   ↓
5. Verifica se servidor está rodando (curl /api/health)
   ↓
6. Inicia aplicação Electron (npm start)
```

**Detalhes do Script:**

**1. Verificação de Ambiente Virtual:**
```batch
if not exist "backend\venv\Scripts\python.exe" (
    echo ❌ Ambiente virtual não encontrado!
    echo 💡 Execute primeiro: cd backend && python -m venv venv
    pause
    exit /b 1
)
```

**2. Parar Processos Antigos:**
```batch
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul
```
- Mata processos Python que possam estar rodando
- Aguarda 2 segundos para garantir que processos foram finalizados

**3. Iniciar Flask:**
```batch
cd backend
start /B venv\Scripts\python.exe app.py
```
- `start /B` - Inicia em background (não bloqueia)
- Usa Python do venv
- Executa `app.py`

**4. Verificação de Saúde:**
```batch
timeout /t 5 /nobreak >nul
curl -s http://localhost:5000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Servidor Flask rodando
) else (
    echo ⚠️  Servidor pode não estar rodando ainda...
)
```
- Aguarda 5 segundos para Flask inicializar
- Testa endpoint `/api/health`
- Informa status ao usuário

**5. Iniciar Electron:**
```batch
cd ..\frontend
npm start
```
- Muda para diretório frontend
- Executa `npm start` (definido em `package.json`)
- Bloqueia até Electron fechar

**Uso:**
```batch
# Na raiz do projeto
.\iniciar_sistema.bat
```

**Saída Esperada:**
```
🚀 Iniciando Sistema SGR-Desktop...
🛑 Parando processos Python existentes...
🐍 Iniciando servidor Flask...
⏳ Aguardando servidor inicializar...
🔍 Verificando se servidor está rodando...
✅ Servidor Flask rodando em http://localhost:5000
🖥️  Iniciando aplicação Electron...
```

---

### 📄 `backend/iniciar_completo.bat` - Script de Inicialização do Backend

**Localização:** `SGR-Desktop/backend/iniciar_completo.bat`

**Responsabilidade:** Inicia apenas o backend, com setup completo.

**Funcionalidades:**

1. **Verificação de Diretório:**
   ```batch
   if not exist "app.py" (
       echo ❌ Arquivo app.py não encontrado!
       exit /b 1
   )
   ```

2. **Criação de Ambiente Virtual (se não existir):**
   ```batch
   if not exist "venv" (
       echo 🔧 Criando ambiente virtual...
       py -m venv venv
   )
   ```

3. **Ativação do Ambiente Virtual:**
   ```batch
   call venv\Scripts\activate.bat
   ```

4. **Instalação de Dependências (se necessário):**
   ```batch
   pip show flask >nul 2>&1
   if %errorlevel% neq 0 (
       pip install flask flask-cors psycopg2-binary python-dotenv requests
   )
   ```
   - Verifica se Flask está instalado
   - Se não, instala todas as dependências

5. **Teste de Conexão com Banco (opcional):**
   ```batch
   python -c "import psycopg2; conn = psycopg2.connect(...)"
   ```
   - Tenta conectar ao PostgreSQL
   - Se falhar, apenas avisa (não bloqueia)

6. **Inicialização do Servidor:**
   ```batch
   python app.py
   ```

**Uso:**
```batch
# No diretório backend
cd backend
.\iniciar_completo.bat
```

**Diferenças do `iniciar_sistema.bat`:**
- Este script é **focado apenas no backend**
- Faz **setup completo** (cria venv, instala deps)
- **Bloqueia** até servidor ser finalizado (Ctrl+C)
- Útil para desenvolvimento/debug do backend isoladamente

---

## 📚 Documentação

### 📄 `README.md` - Documentação Principal

**Localização:** `SGR-Desktop/README.md`

**Conteúdo:**
- Visão geral do projeto
- Estrutura de diretórios
- Guia de instalação
- Guia de execução
- Tecnologias utilizadas
- Troubleshooting

**Propósito:** Primeiro ponto de contato para novos desenvolvedores.

---

### 📄 `DOCUMENTACAO_BACKEND.md` - Documentação Técnica Detalhada do Backend

**Localização:** `Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md`

**Conteúdo:**
- Arquitetura do backend (Flask, Blueprints, Proxy)
- Rotas e endpoints detalhados
- Sistema de proxy (parsing HTML/JSON)
- Gerenciamento de sessão e cookies
- Tratamento de erros e diagnósticos
- Fluxos de dados completos
- Detalhes técnicos de implementação

**Propósito:** Referência técnica completa e detalhada do backend, incluindo detalhes de baixo nível de implementação.

---

### 📄 `DOCUMENTACAO_FRONTEND.md` - Documentação Técnica Detalhada do Frontend

**Localização:** `Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md`

**Conteúdo:**
- Arquitetura do frontend (Electron, SPA)
- Sistema de navegação dinâmica
- Gerenciamento de estado (localStorage)
- Componentes UI e estilização
- Integração com backend
- Detalhes técnicos de implementação
- Execução de scripts dinâmicos

**Propósito:** Referência técnica completa e detalhada do frontend, incluindo detalhes de baixo nível de implementação.

---

### 📄 `DOCUMENTACAO_LOGICA_RAIZ.md` - Este Documento

**Localização:** `Documentos_Auxiliares/DOCUMENTACAO_LOGICA_RAIZ.md`

**Conteúdo:**
- Estrutura do diretório raiz
- Scripts de inicialização e orquestração
- Fluxos de inicialização do sistema
- Configurações compartilhadas
- Pontos de entrada do sistema
- Troubleshooting e manutenção

**Propósito:** Entendimento da organização geral do projeto e orquestração entre backend e frontend.

---

## 🔄 Fluxos de Inicialização

### 🚀 Fluxo Completo (Backend + Frontend)

```
1. Usuário executa iniciar_sistema.bat
   ↓
2. Script verifica ambiente virtual
   ↓
3. Para processos Python antigos
   ↓
4. Inicia Flask em background
   ↓
5. Aguarda 5 segundos
   ↓
6. Verifica saúde do servidor (curl /api/health)
   ↓
7. Inicia Electron (npm start)
   ↓
8. Electron carrega main.js
   ↓
9. main.js inicia Flask novamente (processo filho)
   ↓
10. main.js cria janela e carrega login.html
    ↓
11. Sistema pronto para uso
```

**Nota:** O Flask é iniciado **duas vezes**:
- Uma vez pelo `iniciar_sistema.bat` (para desenvolvimento)
- Uma vez pelo `main.js` do Electron (para produção)

**Razão:** 
- Em desenvolvimento, pode querer rodar Flask separadamente
- Em produção, Electron gerencia Flask automaticamente

---

### 🐍 Fluxo Apenas Backend

```
1. Usuário executa backend/iniciar_completo.bat
   ↓
2. Script verifica se está no diretório correto
   ↓
3. Cria venv se não existir
   ↓
4. Ativa venv
   ↓
5. Instala dependências se necessário
   ↓
6. Testa conexão com banco (opcional)
   ↓
7. Inicia Flask (bloqueia)
   ↓
8. Servidor rodando em http://localhost:5000
```

**Uso:** Desenvolvimento/debug do backend isoladamente.

---

### 🖥️ Fluxo Apenas Frontend

```
1. Usuário executa npm start no diretório frontend
   ↓
2. package.json executa script "start"
   ↓
3. Electron inicia
   ↓
4. main.js inicia Flask como processo filho
   ↓
5. Aguarda Flask inicializar (3 segundos)
   ↓
6. Cria janela e carrega login.html
```

**Uso:** Desenvolvimento/debug do frontend (assumindo backend já rodando ou iniciado automaticamente).

---

## 🔧 Configurações Compartilhadas

### 📄 `.gitignore` (se existir)

**Conteúdo típico:**
```
# Python
__pycache__/
*.py[cod]
venv/
*.env

# Node
node_modules/
dist/

# Electron
*.log
```

**Propósito:** Excluir arquivos gerados e sensíveis do versionamento.

---

### 📄 `package.json` (se existir na raiz)

**Conteúdo típico:**
```json
{
  "name": "sgr-desktop",
  "scripts": {
    "start": "cd frontend && npm start",
    "backend": "cd backend && python app.py"
  }
}
```

**Propósito:** Scripts npm para facilitar execução.

---

## 🎯 Pontos de Entrada do Sistema

### 1. **Desenvolvimento Completo**
```batch
# Na raiz
.\iniciar_sistema.bat
```
- Inicia backend e frontend
- Melhor para desenvolvimento geral

### 2. **Apenas Backend**
```batch
# No diretório backend
cd backend
.\iniciar_completo.bat
```
- Apenas servidor Flask
- Útil para testar APIs

### 3. **Apenas Frontend**
```batch
# No diretório frontend
cd frontend
npm start
```
- Apenas aplicação Electron
- Flask iniciado automaticamente pelo Electron

### 4. **Backend Manual**
```batch
# No diretório backend
cd backend
venv\Scripts\activate
python app.py
```
- Controle total sobre Flask
- Útil para debug avançado

---

## 🔄 Orquestração do Sistema

### 📊 Diagrama de Dependências

```
iniciar_sistema.bat
    ├── Backend (Flask)
    │   ├── app.py
    │   ├── app/__init__.py
    │   ├── app/proxy.py
    │   └── app/routes/*
    │
    └── Frontend (Electron)
        ├── main.js
        │   └── Inicia Flask (processo filho)
        ├── index.html
        │   └── Carrega páginas dinamicamente
        └── js/*.js
            └── Faz requisições para Flask
```

### 🔗 Fluxo de Comunicação

```
Electron (Frontend)
    ↓ HTTP (localhost:5000)
Flask (Backend/Proxy)
    ↓ HTTP (API Externa)
API Java (Spring Boot)
    ↓ JDBC
PostgreSQL (Banco de Dados)
```

**Camadas:**
1. **UI Layer:** Electron + HTML/CSS/JS
2. **Proxy Layer:** Flask (conversão HTML→JSON, sessão)
3. **API Layer:** Spring Boot (lógica de negócio)
4. **Data Layer:** PostgreSQL (persistência)

---

## 🛠️ Scripts de Build e Distribuição

### 📄 `build.bat` (se existir)

**Responsabilidade:** Empacota aplicação para distribuição.

**Fluxo típico:**
```
1. Limpa builds antigos
2. Instala dependências do frontend
3. Executa npm run build
4. Gera instalador .exe
5. Cria pasta win-unpacked/
```

**Saída:**
- `frontend/dist/SGR Desktop Setup <versão>.exe`
- `frontend/dist/win-unpacked/`

---

## 📝 Convenções e Padrões

### 📁 Estrutura de Diretórios

- **Backend:** `backend/`
- **Frontend:** `frontend/`
- **Scripts:** Na raiz ou em subdiretórios específicos
- **Documentação:** Na raiz, com prefixo `DOCUMENTACAO_*`

### 📄 Nomenclatura de Arquivos

- **Scripts Batch:** `iniciar_*.bat`, `build.bat`
- **Documentação:** 
  - `README.md` - Documentação principal (raiz)
  - `DOCUMENTACAO_BACKEND.md` - Documentação técnica do backend (em `Documentos_Auxiliares/`)
  - `DOCUMENTACAO_FRONTEND.md` - Documentação técnica do frontend (em `Documentos_Auxiliares/`)
  - `DOCUMENTACAO_LOGICA_RAIZ.md` - Este documento (em `Documentos_Auxiliares/`)
- **Configuração:** `config.env`, `package.json`, `requirements.txt`
- **Instruções:** `INSTRUCOES_COMPILACAO.md`, `INSTRUCOES_CLIENTE.md`, `INSTRUCOES_DESENVOLVIMENTO.md`

### 🔤 Convenções de Código

- **Backend:** Python (PEP 8)
- **Frontend:** JavaScript (ES6+)
- **Comentários:** Em português
- **Logs:** Prefixos `[MODULO]` em maiúsculas

---

## 🐛 Troubleshooting

### Problema: Script não inicia Flask

**Causas possíveis:**
- Ambiente virtual não existe
- Python não está no PATH
- Porta 5000 já está em uso

**Soluções:**
```batch
# Criar venv
cd backend
python -m venv venv

# Verificar processos na porta 5000
netstat -ano | findstr :5000

# Matar processo
taskkill /F /PID <PID>
```

---

### Problema: Electron não inicia

**Causas possíveis:**
- Node.js não instalado
- Dependências não instaladas
- Porta já em uso

**Soluções:**
```batch
# Instalar dependências
cd frontend
npm install

# Verificar Node.js
node --version
npm --version
```

---

### Problema: Flask inicia mas Electron não conecta

**Causas possíveis:**
- Flask não está em `0.0.0.0:5000`
- Firewall bloqueando
- CORS não configurado

**Soluções:**
- Verificar `app.py` - deve usar `host='0.0.0.0'`
- Verificar `app/__init__.py` - CORS deve estar habilitado
- Testar manualmente: `curl http://localhost:5000/api/health`

---

## 🔒 Segurança

### Arquivos Sensíveis

**NÃO versionar:**
- `backend/config.env` - Contém URLs e configurações
- `backend/venv/` - Ambiente virtual (grande, específico do sistema)
- `frontend/node_modules/` - Dependências (grande)
- `frontend/dist/` - Builds gerados

**Versionar:**
- `backend/config.env.example` - Template de configuração
- `backend/requirements.txt` - Lista de dependências
- `frontend/package.json` - Configuração npm

---

## 📊 Métricas e Monitoramento

### Logs do Sistema

**Backend:**
- Logs no console (stdout/stderr)
- Prefixos: `[PROXY]`, `[CARDAPIO]`, `[PEDIDOS]`, etc.

**Frontend:**
- Logs no DevTools (F12)
- Console do navegador Electron

**Scripts:**
- Output direto no console
- Emojis para facilitar leitura (🚀, ✅, ❌, ⚠️)

---

## 🚀 Performance

### Otimizações

1. **Inicialização:**
   - Flask inicia em background
   - Electron aguarda Flask estar pronto
   - Timeouts configuráveis

2. **Desenvolvimento:**
   - Hot reload não implementado (requer restart manual)
   - Logs detalhados para debug

3. **Produção:**
   - Build otimizado do Electron
   - Flask com debug desabilitado

---

## 🔄 Manutenção

### Atualizar Dependências

**Backend:**
```batch
cd backend
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

**Frontend:**
```batch
cd frontend
npm update
```

### Limpar Cache

**Backend:**
```batch
# Limpar __pycache__
cd backend
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
```

**Frontend:**
```batch
# Limpar node_modules e reinstalar
cd frontend
rmdir /s /q node_modules
npm install
```

---

## 📚 Recursos Adicionais

### Documentação Externa

- **Flask:** https://flask.palletsprojects.com/
- **Electron:** https://www.electronjs.org/
- **Chart.js:** https://www.chartjs.org/
- **Tailwind CSS:** https://tailwindcss.com/

### Arquivos de Referência

- **Documentação Técnica:**
  - `Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md` - Documentação técnica detalhada do backend
  - `Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md` - Documentação técnica detalhada do frontend
  - `Documentos_Auxiliares/DOCUMENTACAO_LOGICA_RAIZ.md` - Este documento (organização geral)
- **Documentação de Instruções:**
  - `README.md` - Visão geral do projeto (raiz)
  - `INSTRUCOES_DESENVOLVIMENTO.md` - Instruções para desenvolvedores
  - `INSTRUCOES_COMPILACAO.md` - Instruções de compilação
  - `INSTRUCOES_CLIENTE.md` - Instruções para clientes finais
- **Documentação Específica:**
  - `backend/README.md` - Documentação específica do backend (se existir)
  - `frontend/README.md` - Documentação específica do frontend (se existir)

---

## 🎯 Próximos Passos

### Para Desenvolvedores

1. **Ler documentação:**
   - Começar por `README.md` (raiz do projeto)
   - Depois `DOCUMENTACAO_BACKEND.md` (em `Documentos_Auxiliares/`)
   - Depois `DOCUMENTACAO_FRONTEND.md` (em `Documentos_Auxiliares/`)
   - Este documento (`DOCUMENTACAO_LOGICA_RAIZ.md`) para entender organização geral

2. **Configurar ambiente:**
   - Instalar Python 3.11+
   - Instalar Node.js 18+
   - Criar venv e instalar dependências

3. **Executar sistema:**
   - Usar `iniciar_sistema.bat`
   - Ou executar backend e frontend separadamente

4. **Explorar código:**
   - Começar por `backend/app.py`
   - Depois `frontend/main.js`
   - Depois `frontend/index.html`

---

## 🔍 Pontos Críticos

1. **Ordem de Inicialização:**
   - Flask deve iniciar antes do Electron
   - Electron aguarda Flask estar pronto

2. **Portas:**
   - Flask: `5000` (configurável em `app.py`)
   - API Externa: `8080` (configurável em `config.env`)

3. **Paths:**
   - Scripts assumem estrutura de diretórios específica
   - Caminhos relativos devem ser mantidos

4. **Ambiente:**
   - Windows (scripts `.bat`)
   - Python 3.11+
   - Node.js 18+

5. **Dependências:**
   - Backend: `requirements.txt`
   - Frontend: `package.json`

---

**Fim da Documentação do Diretório Raiz**

