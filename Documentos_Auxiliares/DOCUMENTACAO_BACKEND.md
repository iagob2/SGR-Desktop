# 📘 Documentação Detalhada do Backend - SGR Desktop

> **📖 Sobre este documento:** Esta documentação fornece uma explicação técnica detalhada do backend do SGR Desktop, incluindo arquitetura, implementação, fluxos de dados e detalhes técnicos de baixo nível. Ideal para desenvolvedores que precisam entender, manter ou estender o sistema.

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Estrutura de Diretórios](#estrutura-de-diretórios)
4. [Componentes Principais](#componentes-principais)
5. [Fluxos de Dados](#fluxos-de-dados)
6. [Sistema de Proxy](#sistema-de-proxy)
7. [Gerenciamento de Sessão](#gerenciamento-de-sessão)
8. [Rotas e Endpoints](#rotas-e-endpoints)
9. [Tratamento de Erros](#tratamento-de-erros)
10. [Diagnósticos e Monitoramento](#diagnósticos-e-monitoramento)

---

## 🎯 Visão Geral

O backend do SGR Desktop é um **proxy REST inteligente** construído com Flask (Python) que atua como intermediário entre o frontend Electron e a API externa Java (Spring Boot). Sua função principal é:

- **Proxy de Requisições**: Encaminhar requisições do frontend para a API externa
- **Conversão de Formatos**: Converter respostas HTML da API Java para JSON estruturado
- **Gerenciamento de Sessão**: Manter cookies de autenticação (JSESSIONID) entre requisições
- **Cálculos Analíticos**: Processar dados de pedidos localmente para gerar métricas
- **Diagnóstico Automático**: Verificar conectividade e saúde da API externa

### Fluxo de Comunicação
```
Frontend (Electron) → Flask (localhost:5000) → API Externa (nuvem:8080) → PostgreSQL
```

---

## 🏗️ Arquitetura

### Padrão Arquitetural
O backend utiliza o padrão **Blueprint** do Flask para modularização:

```
app/
├── __init__.py          # Factory Pattern - Criação do app Flask
├── config.py            # Configurações centralizadas
├── proxy.py             # Core do sistema de proxy
├── routes/              # Blueprints (módulos de rotas)
│   ├── system.py        # Autenticação, perfil, health check
│   ├── cardapio.py      # CRUD de cardápio
│   ├── pedidos.py       # Gestão de pedidos
│   ├── analytics.py     # Métricas e análises
│   └── avaliacoes.py    # Avaliações de restaurante/pratos
├── services/            # Serviços auxiliares
│   └── diagnostics.py   # Verificação de conectividade
└── utils/               # Funções utilitárias
    └── status.py        # Validação de status de pedidos
```

### Princípios de Design
1. **Separação de Responsabilidades**: Cada módulo tem uma função específica
2. **Reutilização**: Funções comuns centralizadas em `proxy.py` e `utils/`
3. **Resiliência**: Tratamento robusto de erros e fallbacks
4. **Logging Detalhado**: Logs extensivos para debugging

---

## 📁 Estrutura de Diretórios

### `backend/app.py`
**Função**: Ponto de entrada do servidor Flask

**Responsabilidades**:
- Exibir banner de inicialização
- Verificar conectividade com API externa antes de iniciar
- Configurar encoding UTF-8 para Windows
- Iniciar servidor Flask em `0.0.0.0:5000`

**Fluxo de Inicialização**:
```python
1. print_startup_banner() → Exibe informações do servidor
2. verificar_conectividade_api() → Testa conexão com API externa
3. app.run() → Inicia servidor Flask
```

### `backend/app/__init__.py`
**Função**: Factory Pattern para criação do app Flask

**Componentes**:
- `create_app()`: Função factory que cria e configura o Flask
- `register_blueprints()`: Registra todos os módulos de rotas
- Configuração de CORS para permitir requisições do frontend
- Exportação da instância `app` para uso em `app.py`

**Fluxo de Criação**:
```python
1. Flask(__name__) → Cria instância Flask
2. CORS(flask_app) → Habilita CORS
3. Configura variáveis de ambiente
4. register_blueprints() → Registra rotas
5. Retorna app configurado
```

### `backend/app/config.py`
**Função**: Gerenciamento centralizado de configurações

**Processamento**:
1. Carrega variáveis de `config.env` via `python-dotenv`
2. Sanitiza `API_EXTERNA_URL`:
   - Remove comentários inline (`#`, ` <--`)
   - Garante barra final (`/`)
   - Remove espaços em branco
3. Extrai componentes da URL:
   - Protocolo (http/https)
   - Host/IP
   - Porta
4. Define timeout padrão (30s)

**Variáveis Exportadas**:
- `API_EXTERNA_BASE_URL`: URL completa da API
- `API_EXTERNA_PROTOCOL`: Protocolo (http/https)
- `API_EXTERNA_HOST`: Host/IP
- `API_EXTERNA_PORT`: Porta
- `API_TIMEOUT`: Timeout em segundos

---

## 🔧 Componentes Principais

### 1. Sistema de Proxy (`app/proxy.py`)

#### `api_session` (requests.Session)
**Função**: Sessão HTTP persistente que mantém cookies entre requisições

**Características**:
- Reutiliza conexões TCP (performance)
- Mantém cookies automaticamente
- Headers padrão configurados
- Timeout global definido

**Uso**:
```python
api_session.request(method, url, json=data, timeout=API_TIMEOUT)
```

#### `session_cookies_store` (Dict)
**Função**: Armazenamento adicional de cookies por `restaurante_id`

**Estrutura**:
```python
{
    restaurante_id: "JSESSIONID=valor",
    'latest': "JSESSIONID=valor"  # Último cookie usado
}
```

**Funções de Gerenciamento**:
- `get_session_cookie(restaurante_id)`: Obtém cookie específico
- `set_session_cookie(cookie_value, restaurante_id)`: Armazena cookie
- `clear_session_cookie(restaurante_id)`: Limpa cookie

#### `proxy_request(method, endpoint, data, params)`
**Função**: Função central que faz proxy de requisições

**Fluxo Detalhado**:

1. **Mapeamento de Endpoint**:
   ```python
   endpoint_api = mapear_endpoint_flask_para_api(endpoint)
   # Ex: /api/cardapio/add → itens
   ```

2. **Construção da URL**:
   ```python
   url = f'{API_EXTERNA_BASE_URL}{endpoint_api}'
   ```

3. **Preparação de Headers**:
   ```python
   headers = {
       'Accept': 'text/html,application/json,...',
       'User-Agent': 'SGR-Desktop-Flask-Proxy/1.0',
       'Origin': 'http://localhost:5000'
   }
   ```

4. **Gerenciamento de Cookies (Detalhes Técnicos)**:

**4.1. Detecção de Duplicatas**:
```python
jsessionid_count = sum(1 for name in api_session.cookies.keys() if name == 'JSESSIONID')
if jsessionid_count > 1:
    print(f"[COOKIE] AVISO: Encontrados {jsessionid_count} cookies JSESSIONID - limpando duplicatas...")
    jsessionid_val = api_session.cookies.get('JSESSIONID')
    cookies_backup = {name: value for name, value in api_session.cookies.items() if name != 'JSESSIONID'}
    api_session.cookies.clear()
    for name, value in cookies_backup.items():
        api_session.cookies.set(name, value)
    if jsessionid_val:
        api_session.cookies.set('JSESSIONID', jsessionid_val)
```
- **Problema**: Múltiplos cookies `JSESSIONID` causam conflito na API
- **Solução**: Remove duplicatas, mantém apenas o primeiro
- **Backup**: Salva outros cookies antes de limpar
- **Logs**: Registra ação para debugging

**4.2. Logging de Cookies**:
```python
if len(api_session.cookies) > 0:
    cookie_list = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
    print(f"[COOKIE] Sessao tem {len(api_session.cookies)} cookie(s): {', '.join(cookie_list)}")
```
- **Segurança**: Trunca valores para 20 caracteres (não expõe cookie completo)
- **Debugging**: Mostra primeiros 3 cookies para diagnóstico
- **Formato**: `name=value...` para legibilidade

**4.3. Processamento de Cookies Recebidos**:

**4.3.1. Extração de Set-Cookie Headers**:
```python
set_cookie_headers = (
    response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
)
if not set_cookie_headers and 'Set-Cookie' in response.headers:
    set_cookie_headers = [response.headers.get('Set-Cookie')]
```
- **Compatibilidade**: Suporta múltiplos formatos de header
- **Fallback**: Se `get_list` não disponível, usa `get` direto
- **Múltiplos Cookies**: Suporta múltiplos `Set-Cookie` headers

**4.3.2. Identificação de JSESSIONID**:
```python
for cookie_header in set_cookie_headers:
    cookie_value = cookie_header.split(';')[0].strip()  # Remove atributos (Path, Domain, etc.)
    if cookie_value.startswith('JSESSIONID='):
        jsessionid_value = cookie_value
```
- **Parsing**: Extrai apenas valor do cookie (remove atributos como `Path`, `Domain`, `Secure`)
- **Identificação**: Verifica se começa com `JSESSIONID=`
- **Armazenamento**: Salva valor completo para uso futuro

**4.3.3. Remoção de Cookie Antigo**:
```python
if 'JSESSIONID' in api_session.cookies:
    cookies_backup = {}
    for name, value in api_session.cookies.items():
        if name != 'JSESSIONID':
            cookies_backup[name] = value
    api_session.cookies.clear()
    for name, value in cookies_backup.items():
        api_session.cookies.set(name, value)
    print("[COOKIE] JSESSIONID antigo removido para evitar duplicata")
```
- **Limpeza**: Remove cookie antigo antes de adicionar novo
- **Preservação**: Mantém outros cookies (não relacionados a JSESSIONID)
- **Prevenção**: Evita acumulação de cookies JSESSIONID inválidos

**4.3.4. Armazenamento em Múltiplos Locais**:
```python
api_session.cookies.set('JSESSIONID', cookie_val)  # Sessão HTTP (para próxima requisição)
session_cookies_store['latest'] = jsessionid_value  # Store global (último usado)
if restaurante_id:
    session_cookies_store[restaurante_id] = jsessionid_value  # Store por restaurante
```
- **Sessão HTTP**: Cookie usado automaticamente em próximas requisições
- **Store Global**: Armazena último cookie usado (para recuperação)
- **Store por Restaurante**: Isola cookies por restaurante (multi-tenant)

5. **Envio da Requisição**:
   ```python
   response = api_session.request(
       method=method,
       url=url,
       json=data,
       params=params,
       headers=headers,
       timeout=API_TIMEOUT,
       allow_redirects=True
   )
   ```
- **Sessão Reutilizada**: `api_session` mantém conexões TCP abertas (performance)
- **Cookies Automáticos**: Cookies da sessão são enviados automaticamente
- **Redirects**: Segue redirecionamentos HTTP (301, 302, etc.)
- **Timeout**: Abandona requisição após `API_TIMEOUT` segundos

6. **Processamento de Resposta (Detalhes Técnicos)**:

**6.1. Detecção de Tipo de Conteúdo**:
```python
content_type = response.headers.get('Content-Type', '').lower()
if 'application/json' in content_type:
    # Processa JSON diretamente
elif 'text/html' in content_type or response.text.strip().startswith('<!DOCTYPE'):
    # Processa HTML via parse_html_response()
```
- **JSON**: Retorna diretamente (sem parsing)
- **HTML**: Converte para JSON via `parse_html_response()`
- **Detecção**: Usa `Content-Type` header ou análise de conteúdo

**6.2. Tratamento de Erros HTTP**:
```python
if response.status_code >= 400:
    error_data = {
        'status': 'error',
        'message': f'Erro HTTP {response.status_code}',
        'status_code': response.status_code,
    }
    if response.status_code == 403 and API_EXTERNA_HOST in ['localhost', '127.0.0.1']:
        error_data['diagnostico'] = {
            'tipo_erro': 'servidor_nao_encontrado',
            'sugestao': 'Use API_EXTERNA_URL=http://3.90.155.156:8080 no config.env'
        }
```
- **4xx**: Erros do cliente (validação, autenticação, etc.)
- **5xx**: Erros do servidor (interno, indisponível, etc.)
- **Diagnóstico**: Sugestões específicas baseadas no erro

7. **Conversão de Resposta**:
   - **JSON**: Retorna diretamente
   - **HTML**: Chama `parse_html_response()`
   - **Erro**: Formata mensagem de erro estruturada

8. **Tratamento de Erros**:
   - `Timeout`: Retorna 504 com diagnóstico
   - `ConnectionError`: Retorna 503 com sugestões
   - `RequestException`: Retorna 502 com detalhes

#### `parse_html_response(html_content, endpoint)`
**Função**: Converte respostas HTML da API Java para JSON estruturado

**Algoritmo de Parsing Detalhado**:

**1. Verificação de Dependências**:
```python
if not BS4_AVAILABLE:
    return {
        'status': 'success',
        'message': 'Resposta HTML recebida (beautifulsoup4 nao instalado)',
        'raw_html': html_content[:500],
    }
```
- Se `beautifulsoup4` não estiver instalado, retorna HTML bruto
- Limita a 500 caracteres para evitar respostas muito grandes

**2. Parsing de Login** (`restaurantes/login`):

**2.1. Extração de Nome do Restaurante**:
```python
success_pattern = re.compile(
    r'Login bem-sucedido.*?Bem-vindo\(a\),\s*(.+?)\.', re.IGNORECASE
)
match = success_pattern.search(html_content)
```
- Usa regex para encontrar mensagem de sucesso no HTML
- Extrai nome entre "Bem-vindo(a)," e o ponto final

**2.2. Extração de `restaurante_id` (Múltiplas Estratégias)**:

**Estratégia 1: Scripts JavaScript**:
```python
for script in scripts:
    # Busca padrão: restaurante_id = 123
    id_match = re.search(
        r'restaurante[_\s]*id\s*[=:]\s*(\d+)', script.string, re.IGNORECASE
    )
    # Busca padrão JSON: {'restaurante_id': 123}
    json_match = re.search(
        r'\{[^}]*restaurante[_\s]*id[^}]*\}', script.string, re.IGNORECASE | re.DOTALL
    )
```
- Procura em todos os `<script>` tags
- Aceita múltiplos formatos: `restaurante_id = 123`, `restauranteId: 123`, `{"restaurante_id": 123}`
- Converte aspas simples para duplas antes de fazer parse JSON

**Estratégia 2: Inputs Hidden**:
```python
hidden_inputs = soup.find_all('input', {'type': 'hidden'})
for inp in hidden_inputs:
    if 'restaurante' in inp.get('name', '').lower() and 'id' in inp.get('name', '').lower():
        restaurante_id = int(inp.get('value', 0))
```
- Busca inputs hidden com `name` contendo "restaurante" e "id"
- Extrai valor numérico do atributo `value`

**Estratégia 3: Data-Attributes**:
```python
elements = soup.find_all(attrs={'data-restaurante-id': True})
restaurante_id = int(elements[0].get('data-restaurante-id'))
```
- Busca elementos HTML com atributo `data-restaurante-id`
- Útil quando a API usa data-attributes para passar dados

**Estratégia 4: URLs em Links**:
```python
links = soup.find_all('a', href=True)
for link in links:
    href = link.get('href', '')
    id_match = re.search(r'[?&](?:id|restaurante_id)=(\d+)', href, re.IGNORECASE)
    if id_match:
        restaurante_id = int(id_match.group(1))
```
- Extrai ID de query parameters em links
- Aceita formatos: `?id=123`, `&restaurante_id=123`

**2.3. Formato de Resposta**:
```python
result = {
    'status': 'success',
    'message': 'Login realizado com sucesso',
    'data': {
        'restaurante_id': restaurante_id,
        'restaurante_nome': restaurante_nome
    }
}
```

**3. Parsing de Listagem de Itens** (`itens`, `cardapio`):

**3.1. Localização da Tabela**:
```python
tabela = soup.find('table', id='tabelaItens')
if not tabela:
    tabela = soup.find('table')  # Fallback: primeira tabela encontrada
```
- Prioriza tabela com ID específico
- Fallback para primeira tabela se ID não encontrado

**3.2. Extração de Dados das Linhas**:
```python
rows = tabela.find_all('tr')
for row in rows:
    cells = row.find_all(['td', 'th'])
    if len(cells) >= 3:
        item = {
            'id': int(cells[0].get_text(strip=True)) if cells[0].get_text(strip=True).isdigit() else None,
            'nome': cells[1].get_text(strip=True),
            'preco': float(cells[2].get_text(strip=True).replace('R$', '').replace(',', '.').strip()),
            'categoria': cells[3].get_text(strip=True) if len(cells) > 3 else 'OUTROS',
            'restaurante_id': int(cells[4].get_text(strip=True)) if len(cells) > 4 and cells[4].get_text(strip=True).isdigit() else None,
            'imagemUrl': cells[5].find('a').get('href', '') if len(cells) > 5 and cells[5].find('a') else ''
        }
```
- Processa cada linha (`<tr>`) da tabela
- Extrai texto de cada célula (`<td>` ou `<th>`)
- Normaliza preço: remove "R$", substitui vírgula por ponto
- Trata erros individualmente por linha (continua processamento)

**3.3. Validação**:
```python
if item.get('nome') and item.get('id'):
    items.append(item)
```
- Só adiciona item se tiver `nome` e `id` válidos
- Ignora linhas de cabeçalho ou inválidas

**4. Parsing Genérico** (Fallback):

**4.1. Extração de JSON de Scripts**:
```python
scripts = soup.find_all('script')
for script in scripts:
    json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
    if json_match:
        parsed = json.loads(json_match.group())
        if isinstance(parsed, dict) and 'status' in parsed:
            return parsed
```
- Procura objetos JSON em scripts
- Valida se é dicionário com chave `status`

**4.2. Extração de Data-Attributes**:
```python
elements_with_data = soup.find_all(
    attrs=lambda attrs: attrs and any(k.startswith('data-') for k in attrs.keys())
)
for elem in elements_with_data:
    for key, value in elem.attrs.items():
        if key.startswith('data-'):
            data_key = key.replace('data-', '').replace('-', '_')
            data[data_key] = value
```
- Converte `data-restaurante-id` → `restaurante_id`
- Converte hífens para underscores

**4.3. Detecção de Erros**:
```python
text_content = main_content.get_text(strip=True)
if any(palavra in text_content.lower() for palavra in ['erro', 'error', 'falha', 'inválido', 'incorreto']):
    return {
        'status': 'error',
        'message': 'Erro no login. Verifique suas credenciais.',
    }
```
- Analisa texto extraído do HTML
- Detecta palavras-chave de erro
- Retorna resposta de erro estruturada

**5. Tratamento de Exceções**:
```python
except Exception as exc:
    print(f"[AVISO] Erro ao parsear HTML: {exc}")
    import traceback
    print(f"[DEBUG] Traceback: {traceback.format_exc()}")
    return {
        'status': 'success',
        'message': 'Resposta HTML recebida (não parseado)',
        'raw_html': html_content[:500],
    }
```
- Captura todas as exceções
- Loga traceback completo para debugging
- Retorna HTML bruto em caso de erro (não quebra o fluxo)

**Dependências**:
- `beautifulsoup4`: Biblioteca de parsing HTML (recomendado)
- `re`: Módulo de regex padrão do Python
- `json`: Módulo JSON padrão do Python
- Fallback: Retorna HTML bruto se BS4 não disponível

#### `mapear_endpoint_flask_para_api(flask_endpoint)`
**Função**: Mapeia endpoints do Flask para endpoints da API externa

**Mapeamentos**:
- `/api/cardapio/add` → `itens`
- `/api/cardapio/edit/{id}` → `itens/{id}`
- `/api/cardapio/{restaurante_id}` → `itens` (com params)
- Outros endpoints: mantém como está

---

### 2. Rotas do Sistema (`app/routes/system.py`)

#### `POST /api/restaurantes/login`
**Função**: Autenticação de restaurante

**Fluxo**:
1. Valida dados recebidos (email, senha)
2. Chama `proxy_request('POST', 'restaurantes/login', data)`
3. Processa resposta:
   - Se sucesso: extrai `restaurante_id` e associa cookie
   - Se erro: retorna mensagem formatada
4. Tratamento de erros específicos:
   - 502: URL inválida no config.env
   - 504: Timeout
   - 503: Conexão recusada
   - 401/403: Credenciais inválidas

**Associação de Cookie**:
```python
if restaurante_id and jsessionid:
    cookie_string = f"JSESSIONID={jsessionid}"
    set_session_cookie(cookie_string, restaurante_id)
```

#### `GET /api/restaurantes/perfil`
**Função**: Busca informações do restaurante logado

**Processamento**:
- Chama `proxy_request('GET', 'restaurantes/perfil')`
- Normaliza estrutura de resposta:
  - Procura `restaurante_id` em múltiplos locais
  - Procura `restaurante_nome` em múltiplos locais
  - Garante formato padronizado

#### `GET /api/health`
**Função**: Health check do proxy Flask

**Retorno**:
```json
{
  "status": "success",
  "message": "API Flask (Proxy) está funcionando!",
  "api_externa_status": "active|inactive",
  "api_externa_url": "http://...",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### 3. Rotas de Cardápio (`app/routes/cardapio.py`)

#### `GET /api/cardapio/{restaurante_id}`
**Função**: Lista todos os itens do cardápio

**Processamento**:
1. Chama `proxy_request('GET', f'cardapio/{restaurante_id}')`
2. Normaliza resposta:
   - Se lista: retorna diretamente
   - Se dict com `data`: extrai array
   - Se dict com `itens`: extrai array
3. Retorna formato padronizado:
   ```json
   {
     "status": "success",
     "data": [...]
   }
   ```

#### `POST /api/cardapio/add`
**Função**: Adiciona novo item ao cardápio

**Validação**:
- Campos obrigatórios: `nome`, `preco`, `Categoria`, `restaurante_id`
- `nome`: deve ser string não vazia
- `preco`: deve ser número > 0

**Transformação de Dados**:
```python
dados_para_api = {
    'nome': dados['nome'].strip(),
    'descricao': dados.get('descricao', '').strip() or '',
    'preco': float(dados['preco']),
    'Categoria': dados['Categoria'].strip(),
    'restaurante': {'id': int(dados['restaurante_id'])},
    'imagemUrl': dados.get('imagemUrl', '').strip() or ''
}
```

**Fallback para Form-URLEncoded**:
- Se retornar 400 com erro de formato
- Tenta novamente como `application/x-www-form-urlencoded`
- Converte estrutura aninhada para formato plano

#### `PUT /api/cardapio/edit/{item_id}`
**Função**: Edita item existente

**Processamento**:
- Mapeia para endpoint `itens/{item_id}`
- Envia dados atualizados
- Retorna resposta formatada

#### `DELETE /api/cardapio/delete/{item_id}`
**Função**: Remove item do cardápio

**Processamento**:
- Chama `proxy_request('DELETE', f'itens/{item_id}')`
- Aceita status 200 ou 204 como sucesso

---

### 4. Rotas de Pedidos (`app/routes/pedidos.py`)

#### `GET /api/pedidos/restaurante/{restaurante_id}`
**Função**: Lista pedidos de um restaurante

**Filtros Suportados**:
- `?status=pendente`: Filtra por status
- `?data_inicio=2024-01-01`: Filtra por data inicial
- `?data_fim=2024-01-31`: Filtra por data final

**Processamento**:
1. Busca todos os pedidos via `proxy_request('GET', 'pedidos/restaurante')`
2. Filtra por `restaurante_id`:
   - Verifica `pedido.restaurante.id` ou `pedido.restaurante_id`
3. Aplica filtros adicionais:
   - Status: compara normalizado (uppercase)
   - Data: parse ISO e compara
4. Normaliza estrutura:
   - Garante `restaurante_id` presente
   - Unifica `criadoEm` / `criado_em`
   - Garante `itens` como array
5. Ordena por data (mais recente primeiro)

**Fallback com Dados Mock**:
- Se API externa falhar, retorna dados de teste
- Útil para desenvolvimento e demonstrações

#### `GET /api/pedidos/restaurante/{restaurante_id}/concluidos`
**Função**: Lista apenas pedidos concluídos/finalizados

**Processamento**:
- Similar ao endpoint anterior
- Filtra usando `is_status_concluido()`:
  - Aceita: FINALIZADO, CONCLUIDO, CONCLUÍDO, ENTREGUE
  - Rejeita: PENDENTE, EM_PREPARO, PRONTO, CANCELADO

#### `PUT /api/pedidos/{pedido_id}/status`
**Função**: Atualiza status de um pedido

**Mapeamento de Status**:
```python
{
    'pendente': 'PENDENTE',
    'em_preparo': 'EM_PREPARO',
    'pronto': 'PRONTO',
    'concluido': 'FINALIZADO',
    'finalizado': 'FINALIZADO',
    'entregue': 'ENTREGUE',
    'cancelado': 'CANCELADO'
}
```

**Endpoint da API Externa**:
- Usa `/pedidos/{pedido_id}/status-restaurante?status={status}`
- Específico para restaurantes (diferente do endpoint de clientes)

#### `GET /api/pedidos/{pedido_id}`
**Função**: Busca detalhes de um pedido específico

**Processamento**:
1. Busca todos os pedidos
2. Filtra por `pedido_id`
3. Calcula `valor_total` se ausente:
   - Soma `quantidade * preco` de cada item
4. Formata itens:
   - Extrai nome, preço, quantidade
   - Calcula subtotal
   - Inclui observações
5. Formata cliente:
   - Extrai nome, telefone, etc.

---

### 5. Rotas de Analytics (`app/routes/analytics.py`)

#### `GET /api/top-produtos/{restaurante_id}/{periodo}`
**Função**: Top 3 produtos mais vendidos

**Períodos Suportados**:
- `semanal`: Últimos 7 dias
- `mensal`: Últimos 30 dias
- `anual`: Últimos 365 dias

**Algoritmo**:
1. Busca todos os pedidos concluídos
2. Filtra por `restaurante_id` e período
3. Agrega por produto:
   ```python
   produtos_vendidos[produto_id] = {
       'quantidade': soma_quantidades,
       'valor_total': soma_valores,
       'nome': nome_produto,
       'preco_unitario': preco
   }
   ```
4. Ordena por quantidade (descendente)
5. Retorna top 3

#### `GET /api/vendas/{restaurante_id}/{periodo}`
**Função**: Dados de vendas agrupados por período

**Agrupamento**:
- **Semanal**: Últimas 4 semanas
- **Mensal**: Últimos 6 meses
- **Anual**: Últimos 5 anos

**Retorno**:
```json
{
  "status": "success",
  "data": {
    "periodo": "mensal",
    "labels": ["Jan", "Fev", "Mar", ...],
    "vendas": [1000.00, 1500.00, ...],
    "produtos": [50, 75, ...]
  }
}
```

#### `GET /api/dashboard/{restaurante_id}`
**Função**: Dashboard completo com todas as métricas

**Métricas Calculadas**:

1. **Cards (KPIs)**:
   - `total_vendas`: Soma de todos os pedidos concluídos
   - `quantidade_produtos`: Total de itens vendidos
   - `ticket_medio_diario`: `total_vendas / quantidade_pedidos`
   - `evolucao_percentual`: `((vendas_hoje - vendas_ontem) / vendas_ontem) * 100`

2. **Gráficos**:
   - `valor_diario`: Vendas dos últimos 7 dias
   - `produtos_diarios`: Produtos vendidos dos últimos 7 dias

**Processamento**:
1. Busca pedidos concluídos via endpoint interno
2. Itera sobre pedidos:
   - Calcula valor total (soma de itens ou usa `valor_total`)
   - Conta quantidade de itens
   - Agrupa por data
3. Calcula métricas agregadas
4. Formata para exibição

---

### 6. Rotas de Avaliações (`app/routes/avaliacoes.py`)

#### `GET /api/avaliacoes/{restaurante_id}`
**Função**: Lista avaliações do restaurante

**Processamento**:
- Chama `proxy_request('GET', f'avaliacoes/{restaurante_id}')`
- Retorna lista ou objeto formatado

#### `GET /api/avaliacoes/pratos/{restaurante_id}`
**Função**: Lista avaliações específicas de pratos

**Processamento Complexo**:
1. Busca todas as avaliações de pratos
2. Busca todos os itens do restaurante
3. Filtra avaliações:
   - Verifica se prato pertence ao restaurante
   - Compara `prato.restaurante.id` ou `prato.restaurante_id`
   - Ou verifica se `prato.id` está na lista de itens do restaurante
4. Calcula média de notas
5. Retorna com resumo:
   ```json
   {
     "status": "success",
     "data": {
       "avaliacoes": [...],
       "resumo": {
         "media_notas": 4.5,
         "total_avaliacoes": 10
       }
     }
   }
   ```

#### `POST /api/avaliacoes-prato`
**Função**: Cria avaliação de prato

**Validação**:
- `nota`: Obrigatório
- `prato.id`: Obrigatório

---

### 7. Utilitários (`app/utils/status.py`)

#### `is_status_concluido(status)`
**Função**: Verifica se status indica pedido concluído

**Status Aceitos**:
- FINALIZADO, FINALIZADA, FINALIZADOS, FINALIZADAS
- CONCLUIDO, CONCLUÍDO, CONCLUIDA, CONCLUÍDA, etc.
- ENTREGUE, ENTREGUES

**Uso**: Filtragem de pedidos para cálculos analíticos

---

### 8. Serviços (`app/services/diagnostics.py`)

#### `verificar_conectividade_api()`
**Função**: Diagnóstico completo da API externa

**Testes Realizados**:

1. **Teste HTTP**:
   - GET na URL base
   - Timeout de 5 segundos
   - Verifica status 200

2. **Teste de Socket**:
   - Tenta conectar diretamente na porta
   - Timeout de 3 segundos
   - Verifica se porta está aberta

**Logs Detalhados**:
- URL, protocolo, host, porta, timeout
- Resultado de cada teste
- Sugestões de correção se falhar

**Retorno**: `True` se conectável, `False` caso contrário

---

## 🔄 Fluxos de Dados

### Fluxo de Login
```
1. Frontend → POST /api/restaurantes/login
2. Flask → proxy_request('POST', 'restaurantes/login')
3. API Externa → Valida credenciais
4. API Externa → Retorna HTML com JSESSIONID
5. Flask → parse_html_response() extrai restaurante_id
6. Flask → set_session_cookie() armazena cookie
7. Flask → Retorna JSON formatado
8. Frontend → Armazena restaurante_id no localStorage
```

### Fluxo de Listagem de Cardápio
```
1. Frontend → GET /api/cardapio/{restaurante_id}
2. Flask → proxy_request('GET', 'cardapio/{restaurante_id}')
3. API Externa → Retorna HTML com tabela
4. Flask → parse_html_response() extrai itens da tabela
5. Flask → Retorna JSON com array de itens
6. Frontend → Renderiza cardápio
```

### Fluxo de Atualização de Status
```
1. Frontend → PUT /api/pedidos/{id}/status
2. Flask → Mapeia status (ex: 'concluido' → 'FINALIZADO')
3. Flask → proxy_request('PUT', 'pedidos/{id}/status-restaurante')
4. API Externa → Atualiza status no banco
5. API Externa → Retorna confirmação
6. Flask → Retorna JSON formatado
7. Frontend → Atualiza interface
```

### Fluxo de Cálculo de Analytics
```
1. Frontend → GET /api/dashboard/{restaurante_id}
2. Flask → GET /api/pedidos/restaurante/{id}/concluidos (interno)
3. Flask → Filtra pedidos concluídos
4. Flask → Calcula métricas:
   - Soma valores
   - Conta produtos
   - Agrupa por data
   - Calcula evolução
5. Flask → Retorna JSON com cards e gráficos
6. Frontend → Renderiza dashboard
```

---

## 🛡️ Tratamento de Erros

### Níveis de Tratamento

1. **Nível de Proxy** (`proxy_request`):
   - Timeout → 504 com diagnóstico
   - ConnectionError → 503 com sugestões
   - RequestException → 502 com detalhes
   - Exceções genéricas → 500

2. **Nível de Rota**:
   - Validação de dados → 400
   - Erros da API externa → Propaga status code
   - Exceções não tratadas → 500 com traceback

3. **Nível de Parsing**:
   - HTML inválido → Retorna raw HTML
   - Dados ausentes → Valores padrão
   - Erros de parsing → Logs detalhados

### Mensagens de Erro Estruturadas
```json
{
  "status": "error",
  "message": "Mensagem amigável",
  "diagnostico": {
    "tipo_erro": "timeout|connection_error|url_parse_error",
    "url_testada": "...",
    "sugestoes": [...]
  }
}
```

---

## 📊 Diagnósticos e Monitoramento

### Logs Estruturados
Todos os logs seguem padrão:
```
[COMPONENTE] Mensagem
   Detalhes adicionais
```

**Componentes**:
- `[PROXY]`: Requisições proxy
- `[CARDAPIO]`: Operações de cardápio
- `[PEDIDOS]`: Operações de pedidos
- `[LOGIN]`: Autenticação
- `[COOKIE]`: Gerenciamento de cookies
- `[PARSE]`: Parsing de HTML
- `[ERRO]`: Erros gerais
- `[DEBUG]`: Informações de debug

### Health Check
- Endpoint `/api/health` verifica status do proxy
- Testa conectividade com API externa
- Retorna timestamp e status

---

## 🔐 Segurança

### Gerenciamento de Cookies
- Cookies armazenados apenas em memória (não em disco)
- Limpeza automática de duplicatas
- Associação com `restaurante_id` para isolamento

### Validação de Dados
- Validação de tipos (string, number, etc.)
- Sanitização de inputs (strip, etc.)
- Validação de campos obrigatórios

### CORS
- Configurado para permitir requisições do frontend
- Origin: `http://localhost:5000`

---

## 🚀 Performance

### Otimizações
1. **Sessão HTTP Reutilizada**: `requests.Session` mantém conexões abertas
2. **Parsing Condicional**: Só parseia HTML quando necessário
3. **Cache de Cookies**: Evita buscar cookies repetidamente
4. **Agregação Local**: Cálculos analíticos feitos no backend (menos requisições)

### Limitações
- Timeout padrão: 30 segundos
- Sem cache de respostas (sempre busca da API)
- Parsing HTML pode ser lento para grandes respostas

---

## 📝 Notas de Implementação

### Dependências Críticas
- `beautifulsoup4`: Recomendado para parsing HTML robusto
- `requests`: Biblioteca HTTP
- `flask`: Framework web
- `flask-cors`: CORS middleware

### Compatibilidade
- Python 3.11+
- Windows (encoding UTF-8 configurado)
- Linux/Mac (compatível)

### Configuração
- Arquivo `config.env` necessário
- Variável `API_EXTERNA_URL` obrigatória
- Timeout configurável via `API_TIMEOUT`

---

## 🔄 Manutenção e Extensibilidade

### Adicionar Nova Rota
1. Criar função no blueprint apropriado
2. Usar `proxy_request()` para comunicação
3. Adicionar tratamento de erros
4. Adicionar logs detalhados
5. Registrar no `__init__.py` (já feito via blueprint)

### Adicionar Novo Parser
1. Adicionar caso em `parse_html_response()`
2. Identificar padrão HTML específico
3. Extrair dados estruturados
4. Retornar formato padronizado

### Debugging
- Logs detalhados em cada etapa
- Traceback completo em erros
- Diagnóstico automático de conectividade
- Health check endpoint

---

**Fim da Documentação do Backend**

