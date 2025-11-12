# 🍽️ SGR Desktop — Sistema de Gestão de Restaurantes

O **SGR Desktop** é um ecossistema completo para gestão de restaurantes que combina:
- **Backend Flask (Python)**: proxy inteligente para a API Java oficial, com parsing de respostas HTML/JSON, manutenção de sessão, cálculos analíticos locais e diagnósticos automáticos.
- **Frontend Electron (HTML/CSS/JS)**: aplicação desktop multiplataforma focada em operadores, gestores e administradores, com interface moderna e responsiva.

Funcionalidades cobertas:
- Dashboard analítico com KPIs, evolução de vendas e top produtos
- Controle financeiro/Ponto de Venda (PDV)
- Gestão completa de cardápio (CRUD)
- Fila de pedidos e atualização de status em tempo real
- Avaliações de clientes e pratos com métricas e filtros
- Autenticação e controle de acesso com diagnóstico de sessão

---

## 📂 Estrutura Detalhada do Projeto

```
SGR-Desktop/
├── backend/                      # Backend Flask (proxy + agregação)
│   ├── app.py                    # Banner inicial + execução do servidor
│   ├── config.env                # Variáveis privadas (URL API externa, timeout...)
│   ├── config.env.example        # Exemplo seguro para versionamento
│   ├── iniciar_completo.bat      # Script para subir apenas o backend
│   ├── requirements.txt          # Dependências Python
│   ├── README_BACKEND.md         # Documentação detalhada do backend
│   └── app/
│       ├── __init__.py           # Criação do app Flask, CORS, registro de blueprints
│       ├── config.py             # Sanitização de `config.env` + exposição de constantes
│       ├── proxy.py              # requests.Session, cookies, parsing HTML↔JSON, roteamento
│       ├── routes/
│       │   ├── analytics.py      # Top produtos, vendas por período, dashboard consolidado
│       │   ├── avaliacoes.py     # Avaliações de restaurante/pratos
│       │   ├── cardapio.py       # CRUD de cardápio (proxy da API Java)
│       │   ├── pedidos.py        # Listagem, detalhes, status, dados mock
│       │   └── system.py         # Login, perfil do restaurante, health check
│       ├── services/
│       │   └── diagnostics.py    # Verificação ativa (HTTP + socket) da API externa
│       └── utils/
│           └── status.py         # Funções puras reutilizáveis (`is_status_concluido`)
│
├── frontend/                     # Aplicação Electron (UI)
│   ├── css/
│   │   ├── avaliacoes.css
│   │   ├── base.css
│   │   ├── cardapio.css
│   │   ├── dashboard.css
│   │   ├── login.css
│   │   ├── pedidos.css
│   │   └── vendas.css
│   ├── js/
│   │   ├── avaliacoes.js
│   │   ├── cardapio.js
│   │   ├── dashboard.js
│   │   ├── login.js
│   │   ├── pedidos.js
│   │   └── vendas.js
│   ├── paginas/
│   │   ├── avaliacoes.html
│   │   ├── cardapio.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── pedidos.html
│   │   └── vendas.html
│   ├── index.html                # Shell principal (SPA)
│   ├── main.js                   # Processo principal do Electron
│   ├── package.json / lock       # Scripts npm (start/build), dependências e builder
│   └── dist/                     # Saída do empacotamento (`SGR Desktop Setup*.exe`, `win-unpacked/`)
│
├── iniciar_sistema.bat           # Sobe backend + frontend em modo desenvolvimento
├── build.bat                     # Empacotamento final via Electron Builder
├── COMPILACAO_FINAL.md           # Guia completo de build/distribuição
├── INSTRUCOES_CLIENTE.md         # Manual de instalação e operação para clientes
├── INSTRUCOES_COMPILACAO.md      # Compilação rápida em três comandos
├── LICENSE                       # Licença MIT
└── README.md                     # Este documento (guia central)
```

---

## 🧭 Arquitetura em Alto Nível

### 🔧 Backend (Flask)

| Componente                     | Responsabilidade                                                                                |
|--------------------------------|--------------------------------------------------------------------------------------------------|
| `app.py`                       | Exibe banner, roda `verificar_conectividade_api()` e inicializa o Flask (`app.run`).           |
| `app/__init__.py`              | Cria a instância Flask, aplica CORS e registra todos os blueprints presentes em `routes/`.     |
| `app/config.py`                | Lê `config.env`, remove comentários inline, garante barra final e define constantes (`API_*`). |
| `app/proxy.py`                 | Função central `proxy_request`, manutenção da sessão `requests.Session`, parsing HTML<->JSON.  |
| `routes/analytics.py`          | Busca pedidos e calcula métricas localmente (top produtos, vendas por período, dashboard).     |
| `routes/avaliacoes.py`         | Faz proxy das avaliações (restaurante/pratos) e filtra por contexto.                           |
| `routes/cardapio.py`           | CRUD do cardápio (lista, adiciona, edita, exclui itens).                                       |
| `routes/pedidos.py`            | Listagem de pedidos, filtros, detalhes, status e fallback de dados mock.                       |
| `routes/system.py`             | Login, perfil do restaurante, health check e diagnósticos.                                     |
| `services/diagnostics.py`      | Testes HTTP + socket, logs com possíveis causas e orientações de correção.                     |
| `utils/status.py`              | Funções puras (`is_status_concluido`) reutilizadas em analytics/pedidos.                       |
| `README_BACKEND.md`            | Documentação aprofundada (fluxos, parsing, troubleshooting).                                   |

### 🎨 Frontend (Electron)

| Componente         | Responsabilidade                                                                               |
|--------------------|------------------------------------------------------------------------------------------------|
| `main.js`          | Processo principal do Electron (cria janela, define menus, trata lifecycle).                  |
| `index.html`       | Shell que carrega `paginas/*.html` via JavaScript e orquestra navegação.                      |
| `paginas/*.html`   | Estrutura visual de cada módulo (login, dashboard, vendas, cardápio, pedidos, avaliações).    |
| `js/*.js`          | Controladores: consumo da API via fetch, renderização de tabelas/gráficos, integração Chart.js.|
| `css/*.css`        | Estilos globais (`base.css`) e específicos por módulo (cores, layout, responsividade).         |
| `package.json`     | Scripts (`npm start`, `npm run build`), dependências e configuração do Electron Builder.       |
| `dist/`            | Saída do `npm run build` (instalador `.exe` e pasta `win-unpacked/`).                          |

### 🛠️ Scripts Essenciais

| Script                        | Função                                                                                             |
|-------------------------------|-----------------------------------------------------------------------------------------------------|
| `iniciar_sistema.bat`         | Mata processos Python antigos, ativa `backend/venv`, sobe Flask (`app.py`) e roda `npm start`.     |
| `backend/iniciar_completo.bat`| Automatiza criação/ativação da venv e execução do backend isoladamente.                            |
| `build.bat`                   | Limpa `frontend/dist`, instala dependências, garante `electron-builder`, executa `npm run build`.  |

---

## ⚡ Execução Rápida (Desenvolvimento)

```bash
# 1. Clonar repositório
git clone https://github.com/<usuario>/SGR-Desktop.git
cd SGR-Desktop

# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
copy config.env.example config.env
# Edite config.env com a URL/timeout corretos
python app.py                  # Servidor: http://localhost:5000

# 3. Frontend
cd ../frontend
npm install
npm start                      # Abre a aplicação Electron

# 4. Opcional: script completo
cd ..
.\iniciar_sistema.bat
```

---

## 🧠 Funcionalidades Principais

- Dashboard com KPIs, comparação semanal/mensal/anual e top produtos.
- Gestão de cardápio com cadastro, edição e remoção de itens.
- Controle de pedidos (listagem, filtros, detalhes, atualização de status).
- Análise de avaliações de clientes e pratos (notas, comentários, médias).
- Relatórios de vendas e consolidação de métricas no backend.
- Autenticação integrada com manutenção de cookies/sessão no proxy.
- Diagnóstico automático da API externa (timeout, URL inválida, conexão recusada).

---

## 🔧 Tecnologias Principais

| Camada            | Tecnologia / Biblioteca               | Observações                                      |
|-------------------|----------------------------------------|--------------------------------------------------|
| Backend            | Python 3.11+, Flask 3.x, Flask-CORS   | Proxy, CORS, marshaling HTML/JSON                |
|                    | Requests 2.x, python-dotenv 1.x       | Sessão HTTP persistida, saneamento de env        |
| Frontend           | Electron 28.x, Node.js 18.x, npm 9.x  | Aplicação desktop, scripts de build/distribuição |
| UI/Gráficos        | HTML5, CSS3 modular, Chart.js         | Layout responsivo, visualização analítica        |
| Empacotamento      | Electron Builder                      | Geração de instaladores (.exe, win-unpacked)     |

---

## 🧾 Documentação Complementar

### 📚 Documentação Técnica Detalhada

- 📘 [`Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md`](./Documentos_Auxiliares/DOCUMENTACAO_BACKEND.md) — documentação técnica completa do backend (arquitetura, rotas, parsing HTML/JSON, gerenciamento de sessão, detalhes de implementação).
- 🎨 [`Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md`](./Documentos_Auxiliares/DOCUMENTACAO_FRONTEND.md) — documentação técnica completa do frontend (arquitetura Electron, sistema SPA, gerenciamento de estado, detalhes de implementação).
- 📁 [`Documentos_Auxiliares/DOCUMENTACAO_LOGICA_RAIZ.md`](./Documentos_Auxiliares/DOCUMENTACAO_LOGICA_RAIZ.md) — organização geral do projeto (scripts de inicialização, orquestração, fluxos de execução).
- 📋 [`SGR-Desktop/backend/README_BACKEND.md`](./SGR-Desktop/backend/README_BACKEND.md) — documentação específica do backend.
- 📋 [`SGR-Desktop/frontend/README_FRONTEND.md`](./SGR-Desktop/frontend/README_FRONTEND.md) — documentação específica do frontend

### 📖 Instruções e Guias

- 👨‍💻 [`INSTRUCOES_DESENVOLVIMENTO.md`](./INSTRUCOES_DESENVOLVIMENTO.md) — instruções completas para desenvolvedores (setup, execução, troubleshooting).
- ⚒️ [`INSTRUCOES_COMPILACAO.md`](./INSTRUCOES_COMPILACAO.md) — compilação rápida em três comandos.
- 🧩 [`INSTRUCOES_CLIENTE.md`](./INSTRUCOES_CLIENTE.md) — instalação e primeiros passos para clientes finais.

### 🔧 Documentação de Build

- 📚 [`SGR-Desktop/DOCUMENTACAO_BUILD_COMPLETO.md`](./SGR-Desktop/DOCUMENTACAO_BUILD_COMPLETO.md) — documentação completa do processo de build (problemas, soluções, troubleshooting).
- 📋 [`SGR-Desktop/RESUMO_ERROS_SOLUCOES.md`](./SGR-Desktop/RESUMO_ERROS_SOLUCOES.md) — resumo executivo dos principais erros e soluções do build.
- 🚀 [`SGR-Desktop/frontend/COMO_EXECUTAR_BUILD.md`](./SGR-Desktop/frontend/COMO_EXECUTAR_BUILD.md) — guia passo a passo para executar o build.

---

## 📦 Empacotamento & Distribuição

1. Conferir se backend (Flask) e frontend (Electron) estão funcionando em modo dev.
2. Na raiz do projeto, executar:
   ```bash
   .\build.bat
   ```
   O script:
   - remove builds antigos,
   - instala dependências do frontend,
   - garante `electron-builder`,
   - roda `npm run build`.
3. Saída em `frontend/dist/`:
   ```
   SGR Desktop Setup <versão>.exe
   win-unpacked/
   ```
4. Testar o instalador em uma máquina limpa (ou VM) para validar login, dashboard e fluxos principais.

---

## 🧩 Troubleshooting

| Problema                                | Causa provável                                    | Ação recomendada                                                                  |
|-----------------------------------------|---------------------------------------------------|-----------------------------------------------------------------------------------|
| `url_parse_error` ao iniciar Flask      | `API_EXTERNA_URL` com comentários inline/whitespace | Limpar a linha no `config.env` ou copiar para nova linha sem comentários.         |
| Timeout (504) nas requisições           | API externa indisponível ou lenta                 | Verificar conectividade, aumentar `API_TIMEOUT` ou usar dados mock temporariamente.|
| `requests.exceptions.ConnectionError`   | Proxy Flask fora do ar ou porta ocupada           | Garantir `python app.py` ativo e porta 5000 livre.                                |
| `npm start` não abre a janela Electron  | Node.js desatualizado / dependências faltantes    | Atualizar Node ≥ 18.x e rodar `npm install`.                                      |
| `electron-builder not found`            | Dependência ausente no build                      | Executar `npm install --save-dev electron-builder`.                                |
| CRUDs falhando / sessão perdida         | Cookies expirados ou múltiplos `JSESSIONID`       | Relogar; o proxy limpa e renova cookies automaticamente.                          |
| **Erro de symlinks no build**          | **Windows não cria symlinks sem admin**           | **Ver [`SGR-Desktop/DOCUMENTACAO_BUILD_COMPLETO.md`](./SGR-Desktop/DOCUMENTACAO_BUILD_COMPLETO.md)** |
| **`configuration.win has unknown property 'arch'`** | **Propriedade inválida no package.json** | **Remover `arch` de dentro de `win` no `package.json`** |
| **Executável não gerado após build**   | **Cache corrompido ou falta de permissões**       | **Limpar cache como Administrador: `Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force`** |

---

## 🧪 Ambiente de Teste

O SGR Desktop possui uma suíte completa de testes automatizados que cobre diferentes níveis de teste, desde funções isoladas até fluxos completos do sistema.

### 📚 Documentação de Testes

- 🧪 [`SGR-Desktop/backend/tests/README_TESTES.md`](./SGR-Desktop/backend/tests/README_TESTES.md) — guia completo de testes do backend (unitários e integração)
- 🧪 [`SGR-Desktop/TESTES_SISTEMA.md`](./SGR-Desktop/TESTES_SISTEMA.md) — testes de sistema e fluxos funcionais completos
- 🧪 [`SGR-Desktop/frontend/tests/README_TESTES.md`](./SGR-Desktop/frontend/tests/README_TESTES.md) — guia de testes do frontend

### 🎯 Tipos de Testes Implementados

#### 1. Testes de Unidade (Unit Tests)
**Backend:**
- ✅ Funções de parsing HTML/JSON (`test_unit_parsing.py`)
- ✅ Cálculos analíticos e KPIs (`test_unit_analytics.py`)
- ✅ Utilitários (validação de status) (`test_unit_utils.py`)

**Frontend:**
- ✅ Formatação de dados (moeda, data, categoria)
- ✅ Validação de formulários
- ✅ Gerenciamento de estado (localStorage)

#### 2. Testes de Integração (Integration Tests)
- ✅ Proxy Flask ↔️ API Externa (`test_integration_proxy.py`)
- ✅ Endpoints Flask (`test_integration_flask.py`)
- ✅ Frontend ↔️ Backend (comunicação HTTP)

#### 3. Testes de Sistema (System Tests)
- ✅ Fluxo completo de autenticação
- ✅ Fluxo de venda (PDV)
- ✅ CRUD completo de cardápio
- ✅ Gestão de pedidos
- ✅ Dashboard analítico

#### 4. Testes de Aceitação (UAT)
- ✅ Tarefas do mundo real para gestores
- ✅ Tarefas do mundo real para operadores
- ✅ Validação com usuários finais

### 🚀 Como Executar os Testes

#### Backend (Python/pytest)

```bash
# No diretório backend
cd SGR-Desktop/backend

# Ativar ambiente virtual
venv\Scripts\activate

# Instalar dependências de teste
pip install pytest pytest-mock pytest-cov

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=app --cov-report=html
```

#### Frontend (JavaScript/Jest)

```bash
# No diretório frontend
cd SGR-Desktop/frontend

# Instalar dependências de teste
npm install --save-dev jest @testing-library/jest-dom

# Executar testes
npm test
```

### 📊 Cobertura de Código

- **Meta de Cobertura:** ≥ 80% para testes unitários
- **Funções Críticas:** 100% de cobertura (parsing, cálculos, validações)

### 🔍 Testes Não Funcionais

- **Performance:** Tempo de carregamento do dashboard (< 3s)
- **Segurança:** Controle de acesso e validação de sessão
- **Compatibilidade:** Windows (testado e validado)
- **Usabilidade:** Interface intuitiva para operadores

---

## 🧑‍💻 Autor e Licença

**Iago Correia**  
Fatec Praia Grande — Desenvolvimento de Software Multiplataforma  
📍 Praia Grande, SP  

Distribuído sob a licença **MIT** — consulte [LICENSE](./LICENSE) para detalhes.

---

**✨ SGR Desktop — Simplificando a gestão e potencializando resultados.**

