# 👨‍💻 Instruções para Desenvolvedores - SGR Desktop

## 📋 Visão Geral

Este documento explica como configurar e executar o projeto **SGR Desktop** em modo de desenvolvimento. O sistema é composto por:

- **Backend Flask** (Python) - Servidor proxy na porta 5000
- **Frontend Electron** (HTML/CSS/JS) - Aplicação desktop

---

## 🔧 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### Obrigatórios

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - Verificar instalação: `python --version`

2. **Node.js 18+**
   - Download: https://nodejs.org/
   - Verificar instalação: `node --version` e `npm --version`

3. **Git**
   - Download: https://git-scm.com/downloads
   - Verificar instalação: `git --version`

### Opcionais (mas recomendados)

4. **PostgreSQL** (se precisar testar conexão com banco)
   - Download: https://www.postgresql.org/download/

5. **Editor de Código**
   - VS Code: https://code.visualstudio.com/
   - PyCharm: https://www.jetbrains.com/pycharm/

---

## 🚀 Setup Inicial (Primeira Vez)

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd SGR-Desktop
```

### 2. Configurar Backend

```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual Python
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo de configuração
copy config.env.example config.env
# (Linux/Mac: cp config.env.example config.env)

# Editar config.env com suas configurações
# Abra o arquivo e configure:
# - API_EXTERNA_URL (URL da API externa)
# - API_TIMEOUT (timeout em segundos)
```

**Arquivo `config.env`:**
```env
API_EXTERNA_URL=https://meu-back-restaurante.92x7nhce4t8m6.us-east-1.cs.amazonlightsail.com/
API_TIMEOUT=30
```

### 3. Configurar Frontend

```bash
# Voltar para a raiz do projeto
cd ..

# Navegar para o diretório frontend
cd frontend

# Instalar dependências npm
npm install
```

---

## ▶️ Como Executar em Modo Desenvolvimento

### Método 1: Script Automatizado (Recomendado)

**Windows:**
```bash
# Na raiz do projeto (SGR-Desktop)
cd SGR-Desktop
.\iniciar_sistema.bat
```

**O que o script faz:**
1. Verifica se o ambiente virtual existe
2. Para processos Python antigos
3. Inicia o servidor Flask em background
4. Aguarda 5 segundos para Flask inicializar
5. Verifica se Flask está rodando
6. Inicia a aplicação Electron

**Resultado:**
- Flask rodando em `http://localhost:5000`
- Electron abre automaticamente com a aplicação

---

### Método 2: Manual (Terminais Separados)

#### Terminal 1 - Backend (Flask)

```bash
# Navegar para backend
cd SGR-Desktop\backend

# Ativar ambiente virtual
venv\Scripts\activate

# Iniciar servidor Flask
python app.py
```

**Você verá:**
```
======================================================================
[INICIO] FLASK PROXY REST
======================================================================
[OK] Flask iniciando com API Externa conectada
[SERVIDOR] Iniciando servidor Flask...
   Host: 0.0.0.0
   Porta: 5000
   URL Local: http://localhost:5000
======================================================================

 * Running on http://0.0.0.0:5000
```

#### Terminal 2 - Frontend (Electron)

```bash
# Navegar para frontend
cd SGR-Desktop\frontend

# Iniciar Electron
npm start
```

**Você verá:**
- Aplicação Electron abrindo automaticamente
- Janela com tela de login

---

### Método 3: Apenas Backend (Para Testar APIs)

```bash
# No diretório backend
cd SGR-Desktop\backend
.\iniciar_completo.bat
```

**O que faz:**
- Cria venv se não existir
- Instala dependências automaticamente
- Testa conexão com banco (opcional)
- Inicia Flask

**Útil para:**
- Testar endpoints da API
- Debug do backend
- Desenvolvimento sem frontend

---

## 📁 Estrutura do Projeto

```
SGR-Desktop/
├── backend/                    # Servidor Flask
│   ├── app.py                  # Ponto de entrada do servidor
│   ├── config.env              # Configurações (não versionado)
│   ├── config.env.example      # Template de configuração
│   ├── requirements.txt        # Dependências Python
│   ├── venv/                   # Ambiente virtual (não versionado)
│   └── app/
│       ├── __init__.py         # Factory do Flask
│       ├── config.py           # Carregamento de config
│       ├── proxy.py            # Lógica de proxy HTTP
│       ├── routes/             # Blueprints (rotas)
│       │   ├── analytics.py    # Métricas e análises
│       │   ├── avaliacoes.py   # Sistema de avaliações
│       │   ├── cardapio.py     # CRUD de cardápio
│       │   ├── pedidos.py      # Gestão de pedidos
│       │   └── system.py       # Login e sistema
│       ├── services/            # Serviços auxiliares
│       │   └── diagnostics.py # Diagnóstico de conectividade
│       └── utils/              # Utilitários
│           └── status.py       # Funções de status
│
├── frontend/                   # Aplicação Electron
│   ├── main.js                 # Processo principal Electron
│   ├── index.html              # Shell principal (SPA)
│   ├── package.json            # Configuração npm
│   ├── paginas/                # Páginas HTML
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── cardapio.html
│   │   ├── pedidos.html
│   │   ├── vendas.html
│   │   └── avaliacoes.html
│   ├── js/                     # Scripts JavaScript
│   │   ├── login.js
│   │   ├── dashboard.js
│   │   ├── cardapio.js
│   │   ├── pedidos.js
│   │   ├── vendas.js
│   │   └── avaliacoes.js
│   └── css/                    # Estilos CSS
│       ├── base.css
│       ├── login.css
│       ├── dashboard.css
│       ├── cardapio.css
│       ├── pedidos.css
│       ├── vendas.css
│       └── avaliacoes.css
│
├── iniciar_sistema.bat         # Script de inicialização completa
└── README.md                   # Documentação principal
```

---

## 🔍 Verificando se Está Funcionando

### 1. Verificar Backend (Flask)

Abra no navegador ou use curl:
```bash
# Health check
curl http://localhost:5000/api/health

# Ou abra no navegador:
# http://localhost:5000/api/health
```

**Resposta esperada:**
```json
{
  "status": "success",
  "message": "API Flask (Proxy) está funcionando!",
  "api_externa_status": "active",
  "api_externa_url": "http://3.90.155.156:8080",
  "timestamp": "2024-12-XX..."
}
```

### 2. Verificar Frontend (Electron)

- A aplicação Electron deve abrir automaticamente
- Tela de login deve aparecer
- Console do Electron (F12) não deve mostrar erros

### 3. Testar Login

**Credenciais de teste:**
- Email: `gourmet@teste.com` (ou conforme sua API)
- Senha: (consulte administrador)

**Fluxo:**
1. Preencher email e senha
2. Clicar em "Entrar"
3. Deve redirecionar para dashboard

---

## 🛠️ Comandos Úteis

### Backend

```bash
# Ativar ambiente virtual
cd backend
venv\Scripts\activate

# Instalar nova dependência
pip install nome-do-pacote
pip freeze > requirements.txt  # Atualizar requirements.txt

# Ver logs do Flask
# Os logs aparecem no terminal onde o Flask está rodando

# Parar Flask
# Pressione Ctrl+C no terminal do Flask
```

### Frontend

```bash
# Instalar nova dependência
cd frontend
npm install nome-do-pacote

# Limpar node_modules e reinstalar
rmdir /s /q node_modules  # Windows
npm install

# Abrir DevTools no Electron
# Pressione F12 na aplicação

# Ver logs do Electron
# Os logs aparecem no terminal onde o Electron está rodando
```

---

## 🐛 Troubleshooting

### Problema: "Ambiente virtual não encontrado"

**Solução:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

### Problema: "Porta 5000 já está em uso"

**Solução:**
```bash
# Windows - Verificar processo na porta 5000
netstat -ano | findstr :5000

# Matar processo (substitua <PID> pelo número encontrado)
taskkill /F /PID <PID>

# Ou simplesmente reinicie o computador
```

---

### Problema: "npm start não funciona"

**Solução:**
```bash
cd frontend
npm install
npm start
```

**Se ainda não funcionar:**
```bash
# Limpar cache do npm
npm cache clean --force
rmdir /s /q node_modules
npm install
```

---

### Problema: "Flask inicia mas Electron não conecta"

**Verificações:**
1. Flask está rodando em `0.0.0.0:5000` (não apenas `127.0.0.1`)
2. Firewall não está bloqueando
3. CORS está habilitado no Flask (verificar `app/__init__.py`)

**Teste manual:**
```bash
# Testar endpoint do Flask
curl http://localhost:5000/api/health
```

---

### Problema: "Erro ao fazer login"

**Verificações:**
1. API externa está acessível
2. URL no `config.env` está correta
3. Credenciais estão corretas
4. Cookies estão sendo salvos (verificar logs do Flask)

**Logs úteis:**
- Backend: Verificar console do Flask
- Frontend: Abrir DevTools (F12) e ver Console

---

### Problema: "Mudanças no código não aparecem"

**Solução:**
1. **Backend:** Reinicie o Flask (Ctrl+C e execute novamente)
2. **Frontend:** Recarregue a página no Electron (Ctrl+R ou F5)
3. **HTML/CSS/JS:** Pode precisar fechar e abrir o Electron novamente

**Hot Reload:**
- Não está implementado
- Requer restart manual

---

## 📝 Fluxo de Desenvolvimento

### 1. Fazer Alterações

**Backend (Python):**
- Edite arquivos em `backend/app/`
- Salve o arquivo
- Reinicie Flask (Ctrl+C e execute novamente)

**Frontend (JavaScript/HTML/CSS):**
- Edite arquivos em `frontend/`
- Salve o arquivo
- Recarregue no Electron (F5 ou Ctrl+R)

### 2. Testar Alterações

1. Execute o sistema (`.\iniciar_sistema.bat`)
2. Teste a funcionalidade alterada
3. Verifique logs no console
4. Use DevTools (F12) para debug do frontend

### 3. Debug

**Backend:**
- Logs aparecem no terminal do Flask
- Prefixos: `[PROXY]`, `[CARDAPIO]`, `[PEDIDOS]`, etc.
- Use `print()` para debug

**Frontend:**
- Abra DevTools (F12)
- Console mostra logs JavaScript
- Network tab mostra requisições HTTP
- Application tab mostra localStorage

---

## 🔄 Atualizar Dependências

### Backend

```bash
cd backend
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

### Frontend

```bash
cd frontend
npm update
```

---

## 🧪 Testar Endpoints da API

### Usando curl

```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/restaurantes/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"teste@teste.com\",\"senha\":\"senha123\"}"

# Listar cardápio
curl http://localhost:5000/api/cardapio/1
```

### Usando Postman ou Insomnia

1. Importar coleção de endpoints
2. Configurar base URL: `http://localhost:5000/api`
3. Testar endpoints individualmente

---

## 📚 Documentação Adicional

- **README.md** - Visão geral do projeto
- **COMPILACAO_FINAL.md** - Como compilar para produção
- **INSTRUCOES_CLIENTE.md** - Instruções para clientes finais
- **INSTRUCOES_COMPILACAO.md** - Compilação rápida

---

## 🎯 Checklist de Setup

Antes de começar a desenvolver, verifique:

- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado
- [ ] Git instalado
- [ ] Repositório clonado
- [ ] Ambiente virtual criado (`backend/venv/`)
- [ ] Dependências Python instaladas
- [ ] Dependências npm instaladas
- [ ] Arquivo `config.env` criado e configurado
- [ ] Flask inicia sem erros
- [ ] Electron inicia sem erros
- [ ] Login funciona

---

## 💡 Dicas para Desenvolvedores

### 1. Organização do Código

- **Backend:** Cada funcionalidade em seu próprio blueprint
- **Frontend:** Cada página tem seu próprio JS e CSS
- **Nomenclatura:** Use nomes descritivos em português

### 2. Logs e Debug

- Use `print()` no backend para debug
- Use `console.log()` no frontend
- Logs sempre com prefixos: `[MODULO] Mensagem`

### 3. Versionamento

- Commite frequentemente
- Mensagens de commit descritivas
- Não commite `config.env` ou `venv/`

### 4. Performance

- Backend: Sessão HTTP reutilizada
- Frontend: Carregamento dinâmico de páginas
- Evite requisições desnecessárias

### 5. Segurança

- Nunca commite senhas ou tokens
- Use `config.env` para dados sensíveis
- Valide dados no backend e frontend

---

## 🚨 Problemas Comuns e Soluções

### Erro: "ModuleNotFoundError"

**Causa:** Dependência não instalada

**Solução:**
```bash
cd backend
venv\Scripts\activate
pip install nome-do-modulo
```

---

### Erro: "Cannot find module"

**Causa:** Dependência npm não instalada

**Solução:**
```bash
cd frontend
npm install
```

---

### Erro: "Connection refused"

**Causa:** Flask não está rodando ou porta errada

**Solução:**
1. Verificar se Flask está rodando
2. Verificar porta (deve ser 5000)
3. Verificar firewall

---

### Erro: "Sessão expirada"

**Causa:** Cookie JSESSIONID expirado

**Solução:**
1. Fazer logout
2. Fazer login novamente
3. Verificar se API externa está acessível

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs (backend e frontend)
2. Consulte a documentação
3. Verifique se todos os pré-requisitos estão instalados
4. Tente reiniciar o sistema

---

## 🎉 Pronto para Desenvolver!

Agora você tem tudo configurado. Para começar:

```bash
cd SGR-Desktop
.\iniciar_sistema.bat
```

**Boa sorte com o desenvolvimento! 🚀**

---

**Última atualização:** Dezembro 2024  
**Versão do documento:** 1.0

