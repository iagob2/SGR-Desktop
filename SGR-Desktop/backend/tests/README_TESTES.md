# 🧪 Guia de Testes - Backend SGR Desktop

## 📋 Visão Geral

Este diretório contém a suíte de testes automatizados para o backend Flask do SGR Desktop. Os testes seguem o princípio **FIRST** (Fast, Independent, Repeatable, Self-validating, Timely) e cobrem diferentes níveis de teste.

---

## 🏗️ Estrutura de Testes

```
tests/
├── __init__.py                    # Inicialização do módulo de testes
├── conftest.py                    # Fixtures compartilhadas e configurações
├── test_unit_utils.py            # Testes unitários de utilitários
├── test_unit_parsing.py           # Testes unitários de parsing HTML/JSON
├── test_unit_analytics.py         # Testes unitários de cálculos analíticos
├── test_integration_proxy.py      # Testes de integração do proxy
├── test_integration_flask.py      # Testes de integração dos endpoints Flask
└── README_TESTES.md               # Este arquivo
```

---

## 🧪 Tipos de Testes

### 1. Testes de Unidade (Unit Tests)

**Foco:** Testar funções isoladas e puras (Caixa-Branca)

#### `test_unit_utils.py`
- **Teste:** `is_status_concluido()`
- **Objetivo:** Verificar se a função identifica corretamente status de pedidos concluídos
- **Cenários:**
  - Status concluídos válidos (FINALIZADO, CONCLUIDO, ENTREGUE)
  - Variações de maiúsculas/minúsculas
  - Status não concluídos (PENDENTE, EM_PREPARO)
  - Valores inválidos (None, vazio)

#### `test_unit_parsing.py`
- **Teste:** `parse_html_response()`
- **Objetivo:** Verificar conversão de HTML da API Java para JSON
- **Cenários:**
  - Parsing de login (extração de restaurante_id)
  - Parsing de tabela de itens
  - Tratamento de HTML inválido
  - Fallback quando BS4 não disponível

#### `test_unit_analytics.py`
- **Teste:** Cálculos de métricas e KPIs
- **Objetivo:** Verificar cálculos analíticos (ticket médio, top produtos, evolução)
- **Cenários:**
  - Cálculo de ticket médio
  - Ordenação de top produtos
  - Filtro por período
  - Cálculo de evolução percentual

### 2. Testes de Integração (Integration Tests)

**Foco:** Testar interação entre componentes

#### `test_integration_proxy.py`
- **Teste:** `proxy_request()`
- **Objetivo:** Verificar comunicação Flask ↔️ API Externa
- **Cenários:**
  - Proxy retorna JSON quando API retorna JSON
  - Proxy converte HTML para JSON
  - Manutenção de cookies JSESSIONID
  - Tratamento de timeout
  - Tratamento de erro de conexão

#### `test_integration_flask.py`
- **Teste:** Endpoints Flask
- **Objetivo:** Verificar endpoints HTTP
- **Cenários:**
  - Health check (`/api/health`)
  - Validação de login
  - Estrutura de resposta JSON

---

## 🚀 Como Executar os Testes

### Instalação de Dependências

```bash
# No diretório backend
cd SGR-Desktop/backend

# Ativar ambiente virtual
venv\Scripts\activate

# Instalar pytest e dependências de teste
pip install pytest pytest-mock pytest-cov
```

### Executar Todos os Testes

```bash
# Executar todos os testes
pytest

# Executar com output detalhado
pytest -v

# Executar com cobertura de código
pytest --cov=app --cov-report=html
```

### Executar Testes Específicos

```bash
# Executar apenas testes unitários
pytest tests/test_unit_*.py

# Executar apenas testes de integração
pytest tests/test_integration_*.py

# Executar teste específico
pytest tests/test_unit_utils.py::TestIsStatusConcluido::test_status_finalizado_deve_retornar_true
```

### Executar com Marcadores

```bash
# Executar apenas testes marcados como "unit"
pytest -m unit

# Executar apenas testes marcados como "integration"
pytest -m integration
```

---

## 📊 Cobertura de Código

### Gerar Relatório de Cobertura

```bash
# Gerar relatório HTML
pytest --cov=app --cov-report=html

# Abrir relatório
# Arquivo gerado em: htmlcov/index.html
```

### Meta de Cobertura

- **Testes Unitários:** ≥ 80% de cobertura
- **Funções Críticas:** 100% de cobertura (parsing, cálculos, validações)

---

## 🔧 Fixtures Disponíveis

### `test_config`
- Configura variáveis de ambiente para testes
- Mock da URL da API externa

### `sample_pedidos`
- Retorna lista de pedidos simulados
- Útil para testes de cálculos analíticos

### `sample_html_login`
- Retorna HTML simulado de resposta de login
- Útil para testes de parsing

### `client`
- Cliente de teste Flask
- Permite fazer requisições HTTP simuladas

---

## 📝 Adicionar Novos Testes

### Estrutura de um Teste

```python
"""
🧪 TESTE: Descrição do que está sendo testado

Foco: Tipo de teste (Unit/Integration/System)
"""

import pytest

class TestNomeDaFuncao:
    """
    Teste: Nome descritivo do teste
    
    Objetivo: O que o teste verifica
    """
    
    def test_cenario_especifico(self):
        """Teste: Descrição do cenário específico"""
        # Arrange (preparar dados)
        entrada = "dados de teste"
        
        # Act (executar função)
        resultado = funcao_sob_teste(entrada)
        
        # Assert (verificar resultado)
        assert resultado == "valor esperado"
```

### Convenções

- **Nomes de arquivos:** `test_<tipo>_<modulo>.py`
- **Nomes de classes:** `Test<NomeDaFuncao>`
- **Nomes de métodos:** `test_<cenario>`
- **Docstrings:** Sempre documentar objetivo do teste

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'app'"

**Solução:** Certifique-se de estar no diretório `backend/` e que o ambiente virtual está ativado.

### Erro: "pytest not found"

**Solução:** Instale pytest: `pip install pytest`

### Testes falhando por timeout

**Solução:** Aumente o timeout nos fixtures ou mocks da API externa.

---

## 📚 Recursos

- **Documentação pytest:** https://docs.pytest.org/
- **Documentação Flask Testing:** https://flask.palletsprojects.com/en/latest/testing/
- **Princípios FIRST:** https://www.agilealliance.org/glossary/first/

---

**Última atualização:** Dezembro 2024

