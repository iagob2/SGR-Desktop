# 🧪 Guia de Testes - Frontend SGR Desktop

## 📋 Visão Geral

Este diretório contém a suíte de testes automatizados para o frontend Electron do SGR Desktop. Os testes cobrem funções utilitárias, lógica de estado e integração com o backend.

---

## 🏗️ Estrutura de Testes

```
tests/
├── unit/
│   ├── test_formatacao.js          # Testes de formatação (moeda, data, etc.)
│   ├── test_validacao.js           # Testes de validação de formulários
│   └── test_estado.js              # Testes de gerenciamento de estado
├── integration/
│   ├── test_api_integration.js     # Testes de integração com Flask
│   └── test_navegacao.js            # Testes de navegação SPA
└── README_TESTES.md                 # Este arquivo
```

---

## 🧪 Tipos de Testes

### 1. Testes de Unidade (Unit Tests)

**Foco:** Testar funções puras e lógica isolada

#### Funções de Formatação
- Formatação de moeda (R$ 120,50)
- Formatação de data/hora
- Formatação de categoria

#### Validação de Formulários
- Validação de campos obrigatórios
- Validação de tipos (número, email)
- Validação de regras de negócio

#### Gerenciamento de Estado
- localStorage (salvar, ler, limpar)
- Variáveis globais por módulo

### 2. Testes de Integração (Integration Tests)

**Foco:** Testar interação Frontend ↔️ Backend

#### Integração com API Flask
- Conectividade (Electron consegue chamar Flask?)
- Contrato de API (respostas JSON esperadas)
- Tratamento de erros (500, timeout, etc.)

#### Navegação SPA
- Carregamento dinâmico de páginas
- Execução de scripts
- Preservação de estado entre navegações

---

## 🚀 Como Executar os Testes

### Instalação de Dependências

```bash
# No diretório frontend
cd SGR-Desktop/frontend

# Instalar dependências de teste
npm install --save-dev jest @testing-library/jest-dom
```

### Executar Todos os Testes

```bash
# Executar todos os testes
npm test

# Executar com coverage
npm test -- --coverage
```

---

## 📝 Exemplos de Testes

### Teste de Formatação

```javascript
// test_formatacao.js
describe('Formatação de Moeda', () => {
    test('deve formatar 120.5 para R$ 120,50', () => {
        const valor = 120.5;
        const formatado = formatarMoeda(valor);
        expect(formatado).toBe('R$ 120,50');
    });
});
```

### Teste de Validação

```javascript
// test_validacao.js
describe('Validação de Formulário', () => {
    test('deve validar campos obrigatórios', () => {
        const dados = { nome: '', preco: 0 };
        const valido = validarFormulario(dados);
        expect(valido).toBe(false);
    });
});
```

---

**Nota:** Testes do frontend podem ser executados com Jest ou framework similar.

---

**Última atualização:**  12/11/2025

