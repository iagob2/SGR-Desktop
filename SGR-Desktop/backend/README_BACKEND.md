# 🔧 Backend Flask - SGR Desktop

## 📋 Visão Geral

Backend desenvolvido em **Flask (Python)** que fornece APIs REST para o sistema de gerenciamento de restaurantes. Conecta-se ao banco de dados **PostgreSQL** e oferece endpoints para:

- Autenticação de usuários
- Gestão de pedidos
- Consulta de vendas e relatórios
- CRUD de cardápio
- Sistema de avaliações
- Dados para dashboards

---

## 🗄️ Estrutura do Banco de Dados

### Tabelas Principais

```sql
restaurante        -- Informações do restaurante
clientes          -- Dados dos clientes
pedido           -- Pedidos realizados
item_pedido      -- Itens de cada pedido
item_restaurante -- Cardápio do restaurante
avaliacao        -- Avaliações dos clientes
```

---

## ⚙️ Configuração

### 1. Instalar Dependências

```bash
# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

**Dependências:**
- Flask 2.3.3
- psycopg2 2.9.11
- flask-cors 6.0.1
- python-dotenv 1.1.1

### 2. Configurar Banco de Dados

Edite o arquivo `config.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sgr_restaurante
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
```

### 3. Executar o Servidor

```bash
python app.py
```

O servidor será iniciado em: `http://localhost:5000`

---

## 🔌 Endpoints da API

### Autenticação

```
POST /api/login
```

**Request:**
```json
{
  "email": "admin@restaurante.com",
  "senha": "admin123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "restaurante_id": 1,
    "nome": "Restaurante Sabore"
  }
}
```

### Pedidos

#### Listar Pedidos de um Restaurante
```
GET /api/pedidos/restaurante/<int:restaurante_id>
```

**Parâmetros opcionais (query):**
- `status` - Filtrar por status (pendente, em_preparo, pronto, entregue, cancelado)
- `data_inicio` - Data inicial (YYYY-MM-DD)
- `data_fim` - Data final (YYYY-MM-DD)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 103,
      "valor_total": 139.30,
      "status": "FINALIZADO",
      "data_pedido": "2025-10-23T18:30:00",
      "cliente": {
        "nome": "Bruno Costa",
        "telefone": "(11) 99999-1234"
      }
    }
  ],
  "count": 5
}
```

#### Detalhes de um Pedido
```
GET /api/pedidos/<int:pedido_id>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "pedido": {
      "id": 103,
      "status": "FINALIZADO",
      "data_pedido": "2025-10-23T18:30:00",
      "observacoes": "Sem cebola",
      "valor_total": 139.30,
      "cliente": {
        "nome": "Bruno Costa",
        "telefone": "(11) 99999-1234",
        "email": "bruno@email.com"
      }
    },
    "itens": [
      {
        "nome": "Pizza Quatro Queijos",
        "quantidade": 1,
        "preco": 80.00,
        "subtotal": 80.00,
        "observacoes": "Extra queijo",
        "descricao": "Pizza com queijos especiais"
      }
    ]
  }
}
```

#### Atualizar Status de Pedido
```
PUT /api/pedidos/<int:pedido_id>/status
```

**Request:**
```json
{
  "status": "em_preparo"
}
```

**Status válidos:**
- `pendente`
- `em_preparo`
- `pronto`
- `entregue`
- `cancelado`

### Dashboard

```
GET /api/dashboard/<int:restaurante_id>/resumo?periodo=semanal
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "vendas_totais": 15234.50,
    "pedidos_totais": 247,
    "ticket_medio": 61.68,
    "vendas_diarias": {...},
    "produtos_diarios": {...}
  }
}
```

### Cardápio

```
GET /api/cardapio/<int:restaurante_id>
POST /api/cardapio/item
PUT /api/cardapio/item/<int:item_id>
DELETE /api/cardapio/item/<int:item_id>
```

### Avaliações

```
GET /api/avaliacoes/<int:restaurante_id>
GET /api/avaliacoes/<int:restaurante_id>/resumo
```

---

## 🎨 Esquema de Cores

O backend não tem interface visual, mas os dados retornados são consumidos pela interface verde (`#2CB480`).

---

## 🛠️ Desenvolvimento

### Estrutura do Código

```python
# app.py
├── Configuração Flask
├── Conexão com PostgreSQL
├── Endpoints de Login
├── Endpoints de Pedidos
├── Endpoints de Dashboard
├── Endpoints de Cardápio
├── Endpoints de Avaliações
└── Dados de teste (mock data)
```

### Adicionar Novo Endpoint

```python
@app.route('/api/nova-rota/<int:id>', methods=['GET'])
def nova_rota(id):
    try:
        # Buscar dados
        query = "SELECT * FROM tabela WHERE id = %s"
        results = execute_query(query, (id,))
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

### Logs e Debug

Desabilite o modo debug em produção:

```python
# app.py (linha final)
app.run(debug=False, host='0.0.0.0', port=5000)
```

---

## 📊 Dados de Teste

O backend inclui dados de teste (mock) que são retornados quando não há dados reais no banco. Isso permite testar o sistema sem configuração completa do PostgreSQL.

**IDs de teste:**
- Pedidos: 99, 100, 101, 102, 103

---

## 🔒 Segurança

- ✅ Validação de sessão via localStorage
- ✅ Prepared statements (SQL injection protection)
- ✅ CORS configurado
- ✅ Tratamento de exceções
- ⚠️ Configure senhas fortes no `config.env`

---

## 📝 Logs

O sistema gera logs no console do Flask. Para ver todos os logs:

```bash
python app.py
```

**Logs importantes:**
- `🔍 Buscando detalhes para o Pedido ID: X`
- `⚠️ Pedido X não encontrado no banco. Retornando dados de teste.`
- `✅ Detalhes do pedido X carregados.`

---

## 🚨 Troubleshooting

### Erro: "could not connect to server"

**Solução:**
1. Verifique se PostgreSQL está rodando
2. Confira as credenciais em `config.env`
3. Teste a conexão manualmente

### Erro: "column does not exist"

**Solução:**
Verifique se todas as tabelas estão criadas no banco. Execute as migrations necessárias.

### Erro: "ModuleNotFoundError"

**Solução:**
```bash
pip install -r requirements.txt
```

---

## 📞 Suporte

- Consulte os comentários no código (`app.py`)
- Veja os arquivos de exemplo
- Verifique os logs do Flask

---

**Desenvolvido para facilitar a gestão de restaurantes.**