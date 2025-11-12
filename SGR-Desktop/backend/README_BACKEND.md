# 🔧 Backend Flask - SGR Desktop

## 📋 Visão Geral

Backend desenvolvido em **Flask (Python)** que funciona como um proxy entre o cliente Electron e a API Java na nuvem. A arquitetura agora está modularizada:

```
Electron -> Flask (localhost:5000) -> API Externa (nuvem:8080) -> PostgreSQL
```

Principais responsabilidades:

- Proxy de autenticação, pedidos, cardápio, avaliações e dashboards
- Tratamento e parse de respostas HTML/JSON vindas da API externa
- Cálculos analíticos locais (top produtos, vendas, métricas do dashboard)
- Manutenção de sessão/cookies com tratamento de duplicidade

---

## 🗂️ Estrutura de Pastas

```
backend/
├── app.py                   # Entry point (banner, health check, run server)
├── app/                     # Pacote principal
│   ├── __init__.py          # Flask app, CORS, registro de blueprints
│   ├── config.py            # Carregamento e sanitização de variáveis de ambiente
│   ├── proxy.py             # Sessão requests, proxy_request, parse HTML, cookies
│   ├── routes/              # Blueprints por domínio
│   │   ├── analytics.py     # Top produtos, vendas por período, dashboard
│   │   ├── avaliacoes.py    # Avaliações de restaurante e pratos
│   │   ├── cardapio.py      # CRUD do cardápio (proxy itens)
│   │   ├── pedidos.py       # Listagem, filtro, detalhes e status de pedidos
│   │   └── system.py        # Login, perfil, health check
│   ├── services/
│   │   └── diagnostics.py   # Diagnóstico de conectividade com API externa
│   └── utils/
│       └── status.py        # Funções auxiliares (ex.: is_status_concluido)
├── config.env               # Variáveis de ambiente (URL da API, timeout, etc.)
├── requirements.txt         # Dependências Python
└── README_BACKEND.md        # Este documento
```

---

## ⚙️ Configuração

### 1. Instalar Dependências

```bash
# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

Dependências principais:

- Flask 3.x
- flask-cors 6.x
- requests 2.x
- python-dotenv 1.x
- beautifulsoup4 4.x (opcional, mas recomendado para parse de HTML)

### 2. Configurar Variáveis

Edite `config.env`:

```env
API_EXTERNA_URL=http://3.90.155.156:8080    # URL da API Java
API_TIMEOUT=30                              # Timeout em segundos
```

Alertas:

- Remova comentários na mesma linha das variáveis (o parser sanitiza, mas o ideal é deixar limpo).
- Outras variáveis (DB_HOST, DB_USER etc.) podem ser ignoradas: a comunicação com o PostgreSQL acontece na API Java.

### 3. Executar o Servidor

```bash
python app.py
```

Ou, usando o script do projeto:

```bash
python iniciar_completo.bat
```

O servidor Flask sobe em `http://localhost:5000`.

---

## 🔌 Endpoints (Blueprints)

### Cardápio (`app/routes/cardapio.py`)

- `GET /api/cardapio/<int:restaurante_id>`
- `POST /api/cardapio/add`
- `PUT /api/cardapio/edit/<int:item_id>`
- `DELETE /api/cardapio/delete/<int:item_id>`

Todos os endpoints usam `proxy_request` e respeitam os cookies/sessão do restaurante.

### Pedidos (`app/routes/pedidos.py`)

- `GET /api/pedidos/restaurante/<int:restaurante_id>`
  - Filtros: `status`, `data_inicio`, `data_fim`
- `GET /api/pedidos/restaurante/<int:restaurante_id>/concluidos`
- `GET /api/pedidos/<int:pedido_id>`
- `PUT /api/pedidos/<int:pedido_id>/status`

Inclui dados mock para testes quando a API externa não retorna pedidos.

### Analytics (`app/routes/analytics.py`)

- `GET /api/top-produtos/<int:restaurante_id>/<periodo>`
- `GET /api/vendas/<int:restaurante_id>/<periodo>`
- `GET /api/dashboard/<int:restaurante_id>`

Períodos aceitos: `semanal`, `mensal`, `anual`. Os cálculos são feitos localmente com base nos pedidos concluídos.

### Avaliações (`app/routes/avaliacoes.py`)

- `GET /api/avaliacoes/<int:restaurante_id>`
- `GET /api/avaliacoes/pratos/<int:restaurante_id>`
- `POST /api/avaliacoes-prato`

Filtra avaliações de pratos cruzando os itens do restaurante.

### Sistema (`app/routes/system.py`)

- `POST /api/restaurantes/login`
- `GET /api/restaurantes/perfil`
- `GET /api/restaurantes/<int:restaurante_id>`
- `GET /api/health`

Responsável por autenticação, perfil e checagem de saúde.

---

## 🔄 Fluxo de Proxy

1. Frontend chama endpoint Flask (`/api/...`).
2. `proxy_request` mapeia para endpoint da API Java.
3. Sessão compartilhada (`requests.Session`) mantém cookies; duplicatas são tratadas.
4. Resposta é parseada independente do `Content-Type` (JSON > HTML > texto).
5. Login: resposta é normalizada para o formato esperado pelo Electron.

---

## 🧪 Dados de Teste

Quando a API externa não retorna dados (ex.: pedidos), o backend entrega mocks para garantir que o frontend funcione durante desenvolvimento.

---

## 🔒 Segurança & Diagnóstico

- Sessões persistidas com limpeza de cookies duplicados (`proxy.py`).
- Diagnóstico detalhado para:
  - Timeout (`status: 504`)
  - Conexão recusada (`status: 503`)
  - URL inválida (instruções para `config.env`)
  - Erros 401/403 com fallback `form-urlencoded`
- `services/diagnostics.py` fornece `verificar_conectividade_api()` com testes de HTTP e TCP.

---

## 🛠️ Desenvolvimento

### Adicionando um novo endpoint

Crie um Blueprint em `app/routes/<dominio>.py`:

```python
from flask import Blueprint, jsonify, request

from ..proxy import proxy_request

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/api/inventario', methods=['GET'])
def listar_inventario():
    status_code, response = proxy_request('GET', 'inventario')
    return jsonify(response), status_code
```

Registre o Blueprint em `app/__init__.py`:

```python
from .routes.inventario import inventario_bp

def register_blueprints(flask_app):
    flask_app.register_blueprint(inventario_bp)
```

---

## 📝 Logs

- `proxy_request` imprime detalhes da requisição (método, URL, cookies, body).
- `parse_html_response` informa os caminhos usados no parse.
- `diagnostics.verificar_conectividade_api` mostra passo a passo de conectividade.

---

## 🚨 Troubleshooting

| Problema                       | Solução                                                                 |
|--------------------------------|-------------------------------------------------------------------------|
| `502 url_parse_error`          | Remover comentários inline na linha `API_EXTERNA_URL` do `config.env`. |
| `503 connection_error`         | Verificar se API Java está ativa e acessível na porta configurada.      |
| `504 timeout`                  | API externa demora a responder; checar rede ou aumentar `API_TIMEOUT`.  |
| `403 servidor_nao_encontrado`  | API configurada como `localhost` mas não está rodando.                 |
| `ModuleNotFoundError`          | Rodar `pip install -r requirements.txt`.                                |

---

## 📞 Suporte

- Revise logs no terminal.
- Garanta que o `config.env` está configurado corretamente.
- Para novos módulos, mantenha a separação em blueprints e utilize `proxy_request`.

---

**Desenvolvido para facilitar a manutenção e evolução do SGR Desktop, com uma arquitetura modular e diagnósticos aprimorados.**

