# 🍽️ SGR Desktop - Sistema de Gerenciamento de Restaurantes

## 📋 Sobre o Projeto

O **SGR Desktop** é um sistema completo de gerenciamento para restaurantes, desenvolvido com interface desktop moderna e funcionalidades robustas para controle de vendas, pedidos, cardápio, avaliações e muito mais.

### ✨ Principais Funcionalidades

- 📊 **Dashboard Inteligente** - Análise de vendas e produtos em tempo real
- 💰 **Gestão de Vendas** - Controle completo de faturamento e relatórios
- 🍕 **Cardápio Dinâmico** - Gerenciamento de itens do menu
- ⭐ **Sistema de Avaliações** - Feedback dos clientes
- 📦 **Gestão de Pedidos** - Acompanhamento do status em tempo real
- 🔐 **Autenticação Segura** - Sistema de login integrado

---

## 🏗️ Arquitetura do Projeto

```
SGR-Desktop/
├── backend/          # API Flask + PostgreSQL
├── frontend/         # Interface Electron + HTML/CSS/JS
├── iniciar_sistema.bat  # Script de inicialização
README.md         # Este arquivo
```

### 🔧 Tecnologias Utilizadas

**Backend:**
- Python 3.11
- Flask 2.3.3
- PostgreSQL
- psycopg2 (driver de banco de dados)

**Frontend:**
- Electron (aplicação desktop)
- HTML5 + CSS3
- JavaScript ES6+
- Chart.js (gráficos)

---

## 🚀 Como Fazer Funcionar na Sua Casa

### 📥 Pré-requisitos

Antes de começar, você precisa ter instalado:

1. **Python 3.11+** - [Download aqui](https://www.python.org/downloads/)
2. **PostgreSQL 14+** - [Download aqui](https://www.postgresql.org/download/)
3. **Node.js 18+** (apenas para desenvolvimento) - [Download aqui](https://nodejs.org/)
4. **Git** (opcional) - [Download aqui](https://git-scm.com/downloads)

### 🔽 Passo 1: Clonar o Repositório

```bash
# Abra o terminal/CMD e navegue até a pasta desejada
cd C:\Users\SeuUsuario\Desktop

# Clone o repositório
git clone https://github.com/seu-usuario/SGR-Desktop.git

# Entre na pasta do projeto
cd SGR-Desktop
```

### 🔧 Passo 2: Configurar o Backend

```bash
# Entre na pasta do backend
cd backend

# Crie um ambiente virtual Python (OPCIONAL mas RECOMENDADO)
python -m venv venv

# Ative o ambiente virtual
# No Windows (CMD):
venv\Scripts\activate

# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 🗄️ Passo 3: Configurar o Banco de Dados PostgreSQL

1. **Instale o PostgreSQL** se ainda não tiver
2. **Crie um banco de dados:**

```bash
# Abra o terminal do PostgreSQL (pgAdmin ou psql)
psql -U postgres
```

```sql
-- Crie o banco de dados
CREATE DATABASE sgr_restaurante;

-- Crie um usuário (opcional)
CREATE USER sgr_user WITH PASSWORD 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON DATABASE sgr_restaurante TO sgr_user;
```

3. **Configure a conexão no arquivo `backend/config.env`:**

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sgr_restaurante
DB_USER=postgres
DB_PASSWORD=sua_senha
```

### ⚙️ Passo 4: Inicializar o Backend

```bash
# Certifique-se de estar na pasta backend
cd backend

# Se estiver usando ambiente virtual, ative-o primeiro

# Execute o servidor Flask
python app.py
```

Você verá algo como:
```
 * Running on http://127.0.0.1:5000
```

✅ **Backend rodando!** Deixe essa janela aberta.

### 🖥️ Passo 5: Iniciar o Sistema Desktop

1. **Abra uma NOVA janela de terminal** (deixe o backend rodando na anterior)

2. **Execute o script de inicialização:**

```bash
# Na pasta raiz do projeto (SGR-Desktop)
.\iniciar_sistema.bat
```

OU, se preferir manualmente:

```bash
# Instale as dependências do frontend (apenas primeira vez)
cd frontend
npm install

# Inicie o Electron
npm start
```

### 🎉 Pronto!

O sistema deve abrir em uma janela desktop. Faça login e comece a usar!

**Credenciais padrão:**
- Email: `admin@restaurante.com`
- Senha: `admin123`
*(Altere após primeiro acesso)*

---

## 📁 Estrutura Detalhada dos Diretórios

### 🗂️ `backend/` - Servidor Flask

**Arquivos importantes:**
- `app.py` - API principal com todos os endpoints
- `database_config.py` - Configuração de conexão com PostgreSQL
- `config.env` - Variáveis de ambiente (senhas, host, etc.)
- `requirements.txt` - Dependências Python
- `iniciar_servidor.bat` - Script rápido para iniciar backend

**Endpoints principais:**
- `/api/login` - Autenticação
- `/api/pedidos/restaurante/<id>` - Listar pedidos
- `/api/cardapio/<id>` - Gerenciar cardápio
- `/api/avaliacoes/<id>` - Avaliações dos clientes
- `/api/dashboard/<id>` - Dados para gráficos

### 🎨 `frontend/` - Interface Electron

```
frontend/
├── index.html          # Página principal (SPA)
├── main.js             # Processo principal do Electron
├── package.json        # Dependências Node.js
├── paginas/            # HTML de cada seção
│   ├── dashboard.html
│   ├── vendas.html
│   ├── cardapio.html
│   ├── avaliacoes.html
│   └── pedidos.html
├── js/                 # JavaScript de cada página
│   ├── dashboard.js
│   ├── vendas.js
│   ├── cardapio.js
│   ├── avaliacoes.js
│   └── pedidos.js
└── css/                # Estilos CSS
    ├── base.css        # Estilos globais
    ├── dashboard.css   # Específico para dashboard
    └── ...
```

---

## 📄 Documentação Detalhada

### 📘 Páginas do Sistema

#### 1. **Dashboard** (`frontend/paginas/dashboard.html`)
**Funcionalidade:** Painel principal com gráficos e KPIs  
**JavaScript:** `frontend/js/dashboard.js`  
**Importância:** Visualização consolidada de vendas, produtos mais vendidos e tendências.

**Funcionalidades:**
- Gráficos interativos (Chart.js)
- Alternância entre "Vendas" e "Produtos"
- Períodos: Semanal, Mensal, Anual
- Cards de resumo com valores principais

#### 2. **Gestão de Vendas** (`frontend/paginas/vendas.html`)
**Funcionalidade:** Relatórios detalhados de vendas  
**JavaScript:** `frontend/js/vendas.js`  
**Importância:** Análise de faturamento, ticket médio e vendas por período.

**Funcionalidades:**
- Filtros por período
- Exportação de relatórios
- Gráfico de barras de faturamento
- Top produtos mais vendidos

#### 3. **Cardápio Dinâmico** (`frontend/paginas/cardapio.html`)
**Funcionalidade:** Gerenciamento de itens do menu  
**JavaScript:** `frontend/js/cardapio.js`  
**Importância:** CRUD completo de pratos, bebidas e acompanhamentos.

**Funcionalidades:**
- Adicionar, editar, excluir itens
- Upload de imagens
- Gerenciamento de categorias
- Atualização de preços

#### 4. **Sistema de Avaliações** (`frontend/paginas/avaliacoes.html`)
**Funcionalidade:** Feedback dos clientes  
**JavaScript:** `frontend/js/avaliacoes.js`  
**Importância:** Monitora satisfação e permite resposta às avaliações.

**Funcionalidades:**
- Visualização de estrelas
- Média de avaliações
- Filtro por nota
- Resposta a comentários

#### 5. **Gestão de Pedidos** (`frontend/paginas/pedidos.html`)
**Funcionalidade:** Controle de pedidos em tempo real  
**JavaScript:** `frontend/js/pedidos.js`  
**Importância:** Acompanhamento de status, detalhes e atualização de pedidos.

**Funcionalidades:**
- Lista de pedidos com status
- Modal de detalhes
- Atualização de status (Pendente → Em Preparo → Pronto → Entregue)
- Filtros por status e data
- KPIs de pedidos

---

## 🛠️ Troubleshooting (Solução de Problemas)

### ❌ Problema: "ModuleNotFoundError: No module named 'flask'"

**Solução:**
```bash
cd backend
pip install -r requirements.txt
```

### ❌ Problema: "Error connecting to database"

**Solução:**
1. Verifique se o PostgreSQL está rodando
2. Confira o arquivo `backend/config.env`
3. Teste a conexão:
```bash
psql -U postgres -d sgr_restaurante
```

### ❌ Problema: "Cannot find module 'electron'"

**Solução:**
```bash
cd frontend
npm install
```

### ❌ Problema: Erro 500 ao carregar pedidos

**Solução:** Verifique se o banco de dados está configurado corretamente. O sistema funciona com dados de teste se não houver dados reais.

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação em `backend/README_BACKEND.md`
2. Consulte os arquivos de exemplo
3. Abra uma issue no GitHub

---

## 📝 Licença

Este projeto é de uso livre para fins educacionais e comerciais.

---

## 🎨 Esquema de Cores

O sistema utiliza:
- **Verde primário:** `#2CB480` - Elementos de destaque
- **Verde hover:** `#24A06B` - Estados de hover
- **Azul:** `#3B82F6` - Reserado para gráficos

Mais detalhes em: `CHANGELOG_CORES.md`

---

**Desenvolvido com ❤️ para facilitar a gestão de restaurantes.**
