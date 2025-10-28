# 🎨 Frontend Electron - SGR Desktop

## 📋 Visão Geral

Interface desktop desenvolvida com **Electron** que consome APIs Flask e fornece uma experiência de usuário moderna e responsiva para gerenciamento de restaurantes.

---

## 🏗️ Arquitetura

### Estrutura de Arquivos

```
frontend/
├── index.html              # Página principal (SPA)
├── main.js                 # Processo principal Electron
├── package.json            # Dependências Node.js
├── paginas/                # HTML de cada seção
│   ├── dashboard.html      # Dashboard com gráficos
│   ├── vendas.html         # Gestão de vendas
│   ├── cardapio.html       # CRUD de cardápio
│   ├── avaliacoes.html     # Sistema de avaliações
│   └── pedidos.html        # Gestão de pedidos
├── js/                     # JavaScript modular
│   ├── dashboard.js        # Lógica de gráficos
│   ├── vendas.js           # Relatórios de vendas
│   ├── cardapio.js         # Gerenciamento de itens
│   ├── avaliacoes.js       # Feedback dos clientes
│   └── pedidos.js          # Controle de pedidos
└── css/                    # Estilos modulares
    ├── base.css            # Estilos globais
    ├── dashboard.css       # Dashboard específico
    ├── vendas.css          # Vendas específico
    ├── cardapio.css        # Cardápio específico
    ├── avaliacoes.css      # Avaliações específico
    └── pedidos.css         # Pedidos específico
```

---

## 🎯 Páginas e Funcionalidades

### 📊 Dashboard (`paginas/dashboard.html`)

**JavaScript:** `js/dashboard.js`  
**Estilos:** `css/dashboard.css`  
**Importância:** ⭐⭐⭐⭐⭐ (Crítico)

**Funcionalidades:**
- **Gráficos interativos** usando Chart.js
- **Alternância de abas:** Vendas ↔ Produtos
- **Filtros temporais:** Semanal, Mensal, Anual
- **KPIs principais:** Vendas totais, pedidos, ticket médio
- **Visualização de tendências** em tempo real

**Como funciona:**
1. Carrega dados da API `/api/dashboard/<id>/resumo`
2. Processa dados para gráfico de linha
3. Alterna entre visualização de vendas e produtos
4. Atualiza conforme filtro temporal selecionado

---

### 💰 Gestão de Vendas (`paginas/vendas.html`)

**JavaScript:** `js/vendas.js`  
**Estilos:** `css/vendas.css`  
**Importância:** ⭐⭐⭐⭐ (Alto)

**Funcionalidades:**
- **Relatório de faturamento** por período
- **Gráfico de barras** de vendas diárias
- **Top produtos mais vendidos**
- **Exportação de relatórios** (planejado)
- **Filtros avançados:** Data inicial, data final

**Como funciona:**
1. Busca dados de `/api/relatorios/faturamento/<id>`
2. Renderiza gráfico de barras
3. Lista top produtos com valores
4. Permite exportação (futuro)

---

### 🍕 Cardápio Dinâmico (`paginas/cardapio.html`)

**JavaScript:** `js/cardapio.js`  
**Estilos:** `css/cardapio.css`  
**Importância:** ⭐⭐⭐⭐⭐ (Crítico)

**Funcionalidades:**
- **CRUD completo** de itens do menu
- **Upload de imagens** para pratos
- **Gerenciamento de categorias**
- **Atualização de preços** em tempo real
- **Preview de itens**

**Como funciona:**
1. Carrega itens de `/api/cardapio/<id>`
2. Permite adicionar, editar, excluir
3. Upload de imagens via API
4. Atualização instantânea da interface

---

### ⭐ Sistema de Avaliações (`paginas/avaliacoes.html`)

**JavaScript:** `js/avaliacoes.js`  
**Estilos:** `css/avaliacoes.css`  
**Importância:** ⭐⭐⭐ (Médio)

**Funcionalidades:**
- **Visualização de avaliações** em estrelas
- **Média de avaliações** e total
- **Filtro por nota** (1-5 estrelas)
- **Resposta a comentários** (futuro)
- **Estatísticas de satisfação**

**Como funciona:**
1. Busca avaliações de `/api/avaliacoes/<id>`
2. Calcula média e total
3. Renderiza cards com estrelas
4. Permite filtrar por nota

---

### 📦 Gestão de Pedidos (`paginas/pedidos.html`)

**JavaScript:** `js/pedidos.js`  
**Estilos:** `css/pedidos.css`  
**Importância:** ⭐⭐⭐⭐⭐ (Crítico)

**Funcionalidades:**
- **Lista de pedidos** em tempo real
- **Modal de detalhes** com itens completos
- **Atualização de status:** Pendente → Em Preparo → Pronto → Entregue
- **Filtros:** Por status e data
- **KPIs:** Total, pendentes, em preparo, entregues

**Como funciona:**
1. Carrega pedidos de `/api/pedidos/restaurante/<id>`
2. Exibe tabela com dados principais
3. Ao clicar, abre modal com detalhes de `/api/pedidos/<id>`
4. Permite atualizar status via PUT

**Fluxo de status:**
```
Pendente → Em Preparo → Pronto → Entregue
   ↓           ↓           ↓         ↓
[azul]    [amarelo]   [verde]   [verde escuro]
```

---

## 🎨 Sistema de Cores

### Esquema Padrão

- **Verde primário:** `#2CB480` - Menu, seleções, botões
- **Verde hover:** `#24A06B` - Estados de hover
- **Azul:** `#3B82F6` - Reservado para gráficos (depreciado, agora verde)
- **Textos:** `#111827` (principal), `#6B7280` (secundário)

### Variáveis CSS

Definidas em `css/base.css`:

```css
:root {
    --color-primary: #2CB480;
    --color-primary-hover: #24A06B;
    --color-blue: #3B82F6;
    --color-text-primary: #111827;
    --color-text-secondary: #6B7280;
}
```

---

## 🔧 Tecnologias

### Dependências Principais

**package.json:**
```json
{
  "electron": "^27.0.0",
  "chart.js": "^4.4.0"
}
```

### Bibliotecas Utilizadas

- **Electron** - Framework desktop
- **Chart.js** - Gráficos interativos
- **Fetch API** - Requisições HTTP
- **LocalStorage** - Persistência de sessão

---

## 🚀 Como Executar

### Desenvolvimento

```bash
cd frontend
npm install
npm start
```

### Produção

```bash
npm run build
npm run dist
```

---

## 🎯 Estados e Eventos

### Sistema de Navegação

```javascript
// Mudança de página
function loadPage(pageName) {
    // 1. Remove página atual
    document.querySelectorAll('.section').forEach(s => {
        s.classList.remove('active');
    });
    
    // 2. Carrega nova página
    fetch(`paginas/${pageName}.html`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('contentArea').innerHTML = html;
            // Executa scripts específicos da página
        });
}
```

### Persistência de Sessão

```javascript
// Login
localStorage.setItem('restaurante_id', restaurante_id);

// Uso em requisições
const restaurante_id = localStorage.getItem('restaurante_id');
fetch(`/api/pedidos/restaurante/${restaurante_id}`);
```

---

## 🐛 Debugging

### Logs no Console

```javascript
console.log('🔍 Debug info:', data);
console.error('❌ Erro:', error);
console.warn('⚠️ Aviso:', warning);
```

### DevTools

Abra com `F12` ou `Ctrl+Shift+I` durante desenvolvimento.

---

## 📱 Responsividade

O sistema é totalmente responsivo:

- **Desktop:** Layout completo
- **Tablet:** Adaptação de grids
- **Mobile:** Navegação empilhada

---

## 🔒 Segurança

- ✅ Validação de sessão via localStorage
- ✅ CORS configurado no backend
- ✅ Sanitização de inputs
- ⚠️ Certifique-se de HTTPS em produção

---

## 📊 Performance

### Otimizações

- **Lazy loading** de páginas
- **Cache** de elementos DOM
- **Debounce** em filtros
- **Event delegation** para listas

### Métricas

- Carregamento inicial: ~200ms
- Troca de página: ~100ms
- Requisições API: ~50-200ms

---

## 🛠️ Desenvolvimento

### Adicionar Nova Página

1. **Criar HTML:** `paginas/nova-pagina.html`
2. **Criar JS:** `js/nova-pagina.js`
3. **Criar CSS:** `css/nova-pagina.css`
4. **Adicionar no menu:** Edite `index.html`

### Adicionar Nova Funcionalidade

```javascript
// nova-funcionalidade.js
const NovaFuncionalidade = {
    config: { /* configurações */ },
    state: { /* estado */ },
    
    init() {
        // Inicialização
    },
    
    async buscarDados() {
        // Requisições API
    },
    
    renderizar() {
        // Atualização UI
    }
};

// Auto-inicialização
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => NovaFuncionalidade.init());
} else {
    NovaFuncionalidade.init();
}
```

---

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique o console do navegador (F12)
2. Consulte os comentários no código
3. Veja os exemplos de código

---

**Interface moderna e funcional para gestão de restaurantes.**