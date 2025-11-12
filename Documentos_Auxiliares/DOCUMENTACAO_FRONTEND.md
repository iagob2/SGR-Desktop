# 🎨 Documentação Detalhada do Frontend - SGR Desktop

> **📖 Sobre este documento:** Esta documentação fornece uma explicação técnica detalhada do frontend do SGR Desktop, incluindo arquitetura Electron, sistema de navegação SPA, gerenciamento de estado, integração com backend e detalhes técnicos de implementação. Ideal para desenvolvedores que precisam entender, manter ou estender o sistema.

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura Electron](#arquitetura-electron)
3. [Estrutura de Diretórios](#estrutura-de-diretórios)
4. [Sistema de Navegação](#sistema-de-navegação)
5. [Gerenciamento de Estado](#gerenciamento-de-estado)
6. [Módulos da Aplicação](#módulos-da-aplicação)
7. [Fluxos de Dados](#fluxos-de-dados)
8. [Autenticação e Segurança](#autenticação-e-segurança)
9. [UI/UX e Estilização](#uiux-e-estilização)
10. [Integração com Backend](#integração-com-backend)

---

## 🎯 Visão Geral

O frontend do SGR Desktop é uma **aplicação desktop multiplataforma** construída com Electron que fornece uma interface moderna e responsiva para gestão de restaurantes. Suas características principais são:

- **Aplicação Desktop Nativa**: Usa Electron para criar aplicação desktop
- **Interface SPA (Single Page Application)**: Navegação dinâmica sem recarregar página
- **Design Moderno**: UI responsiva com Tailwind CSS e CSS customizado
- **Gráficos Interativos**: Visualizações com Chart.js
- **Autenticação Persistente**: localStorage para manter sessão
- **Integração com Flask**: Comunicação via REST API

### Stack Tecnológica
- **Electron 28.x**: Framework para aplicações desktop
- **HTML5/CSS3**: Estrutura e estilização
- **JavaScript (ES6+)**: Lógica da aplicação
- **Chart.js**: Gráficos e visualizações
- **Tailwind CSS**: Framework CSS utilitário
- **Fetch API**: Comunicação HTTP

---

## 🏗️ Arquitetura Electron

### Processos Electron

#### Processo Principal (`main.js`)
**Responsabilidades**:
- Criar e gerenciar janelas do aplicativo
- Iniciar servidor Flask em background
- Gerenciar lifecycle da aplicação
- Configurar menus e atalhos
- Capturar e logar erros não tratados

**Fluxo de Inicialização Detalhado**:

**1. Inicialização do Electron**:
```javascript
app.whenReady().then(() => {
    startFlask();  // Inicia Flask em processo separado
    setTimeout(() => {
        createWindow();  // Aguarda 3 segundos para Flask inicializar
    }, 3000);
});
```
- **`app.whenReady()`**: Aguarda Electron estar totalmente inicializado
- **`startFlask()`**: Inicia servidor Flask em processo filho
- **`setTimeout(3000ms)`**: Delay para garantir que Flask esteja rodando
- **`createWindow()`**: Cria janela principal do aplicativo

**2. Função `startFlask()` - Detalhes Técnicos**:

**2.1. Localização de Arquivos**:
```javascript
const flaskPath = path.join(__dirname, '..', 'backend', 'app.py');
const pythonPath = path.join(__dirname, '..', 'backend', 'venv', 'Scripts', 'python.exe');
```
- **Caminhos Relativos**: Usa `path.join()` para compatibilidade cross-platform
- **Python Virtual**: Usa Python do ambiente virtual (não Python global)
- **Windows**: `Scripts\python.exe` (Linux/Mac: `bin/python`)

**2.2. Spawn do Processo Flask**:
```javascript
flaskProcess = spawn(pythonPath, [flaskPath], {
    cwd: path.join(__dirname, '..', 'backend'),  // Diretório de trabalho
    stdio: ['pipe', 'pipe', 'pipe']  // stdin, stdout, stderr
});
```
- **`spawn()`**: Cria processo filho (não bloqueia thread principal)
- **`cwd`**: Define diretório de trabalho (importante para imports)
- **`stdio`**: Captura stdout/stderr para logs

**2.3. Captura de Logs**:
```javascript
flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);  // Logs do Flask
});

flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask Error: ${data}`);  // Erros do Flask
});
```
- **`stdout.on('data')`**: Captura logs normais do Flask
- **`stderr.on('data')`**: Captura erros do Flask
- **Console**: Redireciona logs para console do Electron

**2.4. Tratamento de Eventos**:
```javascript
flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
});

flaskProcess.on('error', (err) => {
    console.error('Failed to start Flask:', err);
});
```
- **`close`**: Detecta quando processo Flask termina
- **`error`**: Detecta erros ao iniciar processo (ex: Python não encontrado)
- **Code**: Código de saída do processo (0 = sucesso)

**3. Função `createWindow()` - Detalhes Técnicos**:

**3.1. Configuração da Janela**:
```javascript
mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
        nodeIntegration: false,  // Segurança: sem acesso ao Node.js
        contextIsolation: true,  // Isolamento de contexto
        enableRemoteModule: false,  // Desabilita módulo remoto
        webSecurity: false,  // Permite carregamento local (desenvolvimento)
        allowRunningInsecureContent: true  // Permite conteúdo local
    },
    show: false  // Não mostrar até estar pronto
});
```
- **Dimensões**: 1400x900 pixels (tamanho padrão)
- **Mínimas**: 1200x800 pixels (tamanho mínimo)
- **`nodeIntegration: false`**: Previne acesso direto ao Node.js (segurança)
- **`contextIsolation: true`**: Isola contexto do renderizador (segurança)
- **`webSecurity: false`**: Necessário para carregar arquivos locais (file://)
- **`show: false`**: Oculta janela até estar totalmente carregada

**3.2. Carregamento de Página**:
```javascript
mainWindow.loadFile(path.join(__dirname, 'paginas', 'login.html'));
```
- **`loadFile()`**: Carrega arquivo HTML local (não precisa de servidor HTTP)
- **Caminho**: `paginas/login.html` (relativo ao diretório do frontend)
- **Protocolo**: Usa protocolo `file://` (nativo do Electron)

**3.3. Eventos da Janela**:
```javascript
mainWindow.once('ready-to-show', () => {
    mainWindow.show();  // Mostra janela quando pronta
});

mainWindow.on('closed', () => {
    mainWindow = null;  // Limpa referência quando fechada
});
```
- **`ready-to-show`**: Dispara quando página está carregada (uma vez)
- **`show()`**: Mostra janela (evita flash de conteúdo não carregado)
- **`closed`**: Dispara quando janela é fechada
- **`null`**: Limpa referência para permitir garbage collection

**4. Função `stopFlask()` - Detalhes Técnicos**:

```javascript
function stopFlask() {
    if (flaskProcess) {
        flaskProcess.kill();  // Mata processo Flask
        flaskProcess = null;  // Limpa referência
    }
}
```
- **`kill()`**: Envia sinal SIGTERM para processo Flask
- **Cleanup**: Limpa referência do processo
- **Uso**: Chamado quando aplicativo fecha (`before-quit`)

**5. Tratamento de Erros**:

```javascript
process.on('uncaughtException', (error) => {
    console.error('Erro não capturado:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Promise rejeitada não tratada:', reason);
});
```
- **`uncaughtException`**: Captura erros não tratados no processo principal
- **`unhandledRejection`**: Captura Promises rejeitadas não tratadas
- **Logging**: Registra erros para debugging
- **Prevenção**: Evita crash do aplicativo

#### Processo de Renderização (HTML/JS)
**Responsabilidades**:
- Renderizar interface do usuário
- Gerenciar navegação entre páginas
- Fazer requisições HTTP para backend
- Gerenciar estado local (localStorage)

**Isolamento**:
- `nodeIntegration: false` → Sem acesso direto ao Node.js
- `contextIsolation: true` → Isolamento de contexto
- `webSecurity: false` → Permite carregamento local (desenvolvimento)

### Comunicação entre Processos
- **IPC (Inter-Process Communication)**: Não utilizado (comunicação via HTTP)
- **HTTP REST**: Frontend → Flask (localhost:5000) → API Externa

---

## 📁 Estrutura de Diretórios

```
frontend/
├── main.js              # Processo principal Electron
├── index.html           # Shell principal (SPA container)
├── package.json         # Dependências e scripts
├── paginas/             # Páginas HTML modulares
│   ├── login.html       # Tela de login
│   ├── dashboard.html   # Dashboard principal
│   ├── vendas.html      # Gestão de vendas
│   ├── cardapio.html    # CRUD de cardápio
│   ├── pedidos.html     # Gestão de pedidos
│   └── avaliacoes.html  # Avaliações
├── js/                  # Scripts JavaScript
│   ├── login.js         # Lógica de autenticação
│   ├── dashboard.js     # Lógica do dashboard
│   ├── vendas.js        # Lógica de vendas
│   ├── cardapio.js      # Lógica de cardápio
│   ├── pedidos.js       # Lógica de pedidos
│   └── avaliacoes.js    # Lógica de avaliações
└── css/                 # Estilos CSS
    ├── base.css         # Estilos globais
    ├── login.css        # Estilos de login
    ├── dashboard.css    # Estilos do dashboard
    ├── vendas.css       # Estilos de vendas
    ├── cardapio.css     # Estilos de cardápio
    ├── pedidos.css      # Estilos de pedidos
    └── avaliacoes.css   # Estilos de avaliações
```

---

## 🔄 Sistema de Navegação

### Arquitetura SPA

O `index.html` atua como **shell principal** que:
1. Carrega sidebar de navegação
2. Gerencia área de conteúdo dinâmico (`#pageContent`)
3. Carrega páginas HTML via AJAX
4. Executa scripts das páginas dinamicamente

### Função `loadPage(pageName)`

**Fluxo Detalhado**:

1. **Verificação de Autenticação**:
   ```javascript
   const authenticated = localStorage.getItem('authenticated');
   const restauranteId = localStorage.getItem('restaurante_id');
   if (authenticated !== 'true' || !restauranteId) {
       window.location.href = 'paginas/login.html';
       return;
   }
   ```

2. **Atualização de Navegação**:
   - Remove classe `active` de todos os itens
   - Adiciona `active` ao item clicado

3. **Limpeza de Scripts**:
   - Remove scripts de módulos anteriores para evitar conflitos
   - Preserva bibliotecas (Chart.js, Tailwind, etc.)

4. **Carregamento de Página**:
   ```javascript
   const pageHTML = await loadHTMLFile(`paginas/${pageName}.html`);
   pageContent.innerHTML = pageHTML;
   ```

5. **Execução de Scripts**:
   - Função `executeScriptsFromHTML()` processa scripts sequencialmente
   - Scripts externos: aguarda `onload` antes de continuar
   - Scripts inline: executa imediatamente

6. **Inicialização do Módulo**:
   ```javascript
   setTimeout(() => {
       if (typeof inicializarDashboard === 'function') {
           inicializarDashboard();
       }
   }, 500);
   ```

### Função `loadHTMLFile(url)`

**Implementação**:
- Usa `XMLHttpRequest` (compatível com `file://`)
- Suporta status 0 (protocolo file://)
- Retorna Promise com conteúdo HTML

### Função `executeScriptsFromHTML(htmlContent, callback)`

**Processamento Sequencial (Detalhes Técnicos)**:

**1. Extração de Scripts**:
```javascript
const tempDiv = document.createElement('div');
tempDiv.innerHTML = htmlContent;
const scripts = Array.from(tempDiv.getElementsByTagName('script'));
```
- **`createElement('div')`**: Cria elemento temporário (não adicionado ao DOM)
- **`innerHTML`**: Parseia HTML e extrai elementos
- **`getElementsByTagName('script')`**: Encontra todos os scripts
- **`Array.from()`**: Converte NodeList para Array (permite métodos de array)

**2. Processamento Sequencial (Algoritmo Detalhado)**:

**2.1. Função Recursiva**:
```javascript
function processNextScript() {
    if (currentIndex >= scripts.length) {
        // Todos os scripts foram processados
        if (callback) callback(scriptsExecuted);
        return;
    }
    
    const script = scripts[currentIndex];
    currentIndex++;
    
    if (script.src) {
        // Script externo
        loadExternalScript(script.src, processNextScript);
    } else {
        // Script inline
        executeInlineScript(script.textContent, processNextScript);
    }
}
```
- **Recursão**: Processa um script por vez
- **Contador**: `currentIndex` rastreia posição atual
- **Callback**: Chama próximo script após conclusão

**2.2. Carregamento de Script Externo**:
```javascript
function loadExternalScript(src, callback) {
    const scriptEl = document.createElement('script');
    scriptEl.src = src;
    scriptEl.onload = () => {
        scriptsExecuted++;
        callback();  // Processa próximo script
    };
    scriptEl.onerror = () => {
        console.error(`Erro ao carregar script: ${src}`);
        callback();  // Continua mesmo com erro
    };
    document.head.appendChild(scriptEl);
}
```
- **`createElement('script')`**: Cria elemento script
- **`src`**: Define origem do script
- **`onload`**: Aguarda script carregar antes de continuar
- **`onerror`**: Trata erros de carregamento (continua processamento)
- **`appendChild`**: Adiciona ao DOM (dispara carregamento)

**2.3. Execução de Script Inline**:
```javascript
function executeInlineScript(code, callback) {
    try {
        // Cria script temporário e executa
        const scriptEl = document.createElement('script');
        scriptEl.textContent = code;
        document.head.appendChild(scriptEl);
        document.head.removeChild(scriptEl);  // Remove após execução
        scriptsExecuted++;
    } catch (error) {
        console.error('Erro ao executar script inline:', error);
    } finally {
        callback();  // Sempre continua para próximo script
    }
}
```
- **`textContent`**: Define código do script
- **`appendChild`**: Adiciona ao DOM (dispara execução)
- **`removeChild`**: Remove após execução (limpeza)
- **Try/Catch**: Captura erros de execução (não quebra fluxo)

**3. Por que Sequencial? (Justificativa Técnica)**:

**3.1. Race Conditions**:
- **Problema**: Scripts executados em paralelo podem acessar variáveis antes de inicialização
- **Solução**: Execução sequencial garante ordem definida

**3.2. Dependências entre Scripts**:
- **Problema**: Script B pode depender de Script A
- **Solução**: Execução sequencial garante que Script A execute antes de Script B

**3.3. Inicialização de Módulos**:
- **Problema**: Funções globais podem não estar disponíveis
- **Solução**: Aguarda script anterior completar antes de executar próximo

**4. Limpeza de Scripts Anteriores**:

```javascript
// Remove scripts de módulos anteriores
const existingScripts = document.head.querySelectorAll('script[data-module]');
existingScripts.forEach(script => script.remove());
```
- **`querySelectorAll`**: Encontra scripts de módulos anteriores
- **`data-module`**: Atributo para identificar scripts de módulos
- **`remove()`**: Remove scripts antigos (evita conflitos)
- **Preservação**: Mantém bibliotecas (Chart.js, Tailwind, etc.)

**5. Callback de Conclusão**:

```javascript
processNextScript();  // Inicia processamento

// Callback é chamado quando todos os scripts executaram
if (callback) callback(scriptsExecuted);
```
- **Callback**: Notifica quando todos os scripts executaram
- **Contador**: Passa número de scripts executados
- **Inicialização**: Permite chamar funções de inicialização após carregamento

---

## 💾 Gerenciamento de Estado

### localStorage

**Chaves Utilizadas**:
- `authenticated`: `'true'` se usuário autenticado
- `restaurante_id`: ID do restaurante logado
- `restaurante_nome`: Nome do restaurante

**Operações**:
```javascript
// Salvar
localStorage.setItem('restaurante_id', id);
localStorage.setItem('authenticated', 'true');

// Ler
const id = localStorage.getItem('restaurante_id');

// Limpar (logout)
localStorage.removeItem('authenticated');
localStorage.removeItem('restaurante_id');
localStorage.removeItem('restaurante_nome');
```

### Variáveis Globais por Módulo

Cada módulo define variáveis globais para estado:
```javascript
// dashboard.js
window.restauranteIdString = localStorage.getItem('restaurante_id');

// vendas.js
window.restauranteIdStringVendas = localStorage.getItem('restaurante_id');

// cardapio.js
window.restauranteIdStringCardapio = localStorage.getItem('restaurante_id');
```

**Por que Variáveis Globais?**
- Acessíveis em qualquer escopo do módulo
- Persistem entre recarregamentos de página (via localStorage)
- Evitam requisições repetidas

---

## 📦 Módulos da Aplicação

### 1. Módulo de Login (`js/login.js`)

#### Função `handleLogin(email, senha)`

**Fluxo**:
1. **Requisição de Login**:
   ```javascript
   const response = await fetch(`${API_BASE_URL}/restaurantes/login`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ email, senha })
   });
   ```

2. **Processamento de Resposta**:
   - Se `status === 'success'`:
     - Extrai `restaurante_id` e `restaurante_nome`
     - Se `restaurante_id` ausente: busca via `/restaurantes/perfil`
     - Salva no localStorage
     - Redireciona para `index.html`

3. **Tratamento de Erros**:
   - Exibe mensagem de erro
   - Remove loading state
   - Mantém usuário na tela de login

#### Validação de Formulário
- Validação em tempo real via `validateInput()`
- Classes CSS `valid`/`invalid` para feedback visual
- Validação antes de submit (campos obrigatórios)

#### Estados de UI
- **Loading**: Botão desabilitado, spinner visível, texto "Entrando..."
- **Erro**: Mensagem vermelha exibida por 5 segundos
- **Sucesso**: Redirecionamento automático

---

### 2. Módulo de Dashboard (`js/dashboard.js`)

#### Função `carregarDashboard()`

**Fluxo**:
1. **Requisição de Dados**:
   ```javascript
   const response = await fetch(
       `http://localhost:5000/api/dashboard/${restauranteId}`
   );
   ```

2. **Processamento de Resposta**:
   - Extrai `cards` (KPIs) e `graficos` (dados para Chart.js)
   - Atualiza elementos DOM com valores
   - Inicializa gráficos

3. **Tratamento de Erros de Autenticação**:
   - Se status 401/403: limpa localStorage, redireciona para login
   - Detecta mensagens de erro de sessão

#### Função `atualizarCards(dados)`

**KPIs Atualizados**:
- `total_vendas`: Formata como moeda brasileira
- `quantidade_produtos`: Número inteiro
- `ticket_medio_diario`: Formata como moeda
- `evolucao_percentual`: Formata com sinal (+/-) e cor

#### Função `inicializarGraficos(dados)`

**Gráficos Criados**:
1. **Gráfico de Vendas Diárias**:
   - Tipo: Line Chart (Chart.js)
   - Dados: `graficos.valor_diario`
   - Cores: Gradiente azul

2. **Gráfico de Produtos Vendidos**:
   - Tipo: Bar Chart (Chart.js)
   - Dados: `graficos.produtos_diarios`
   - Cores: Gradiente verde

**Configuração Chart.js**:
```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: dados.labels,
        datasets: [{
            data: dados.data,
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
    }
});
```

#### Função `inicializarDashboard()`

**Ordem de Execução**:
1. Verifica se elementos DOM existem
2. Chama `carregarDashboard()`
3. Configura event listeners
4. Inicializa tabs (se houver)

---

### 3. Módulo de Vendas (`js/vendas.js`)

#### Função `carregarVendas(periodo)`

**Períodos Suportados**:
- `semanal`, `mensal`, `anual`

**Fluxo**:
1. Requisição: `GET /api/vendas/{restaurante_id}/{periodo}`
2. Processamento: Extrai `labels`, `vendas`, `produtos`
3. Atualização: Atualiza gráficos e tabelas

#### Função `carregarTopProdutos(periodo)`

**Fluxo**:
1. Requisição: `GET /api/top-produtos/{restaurante_id}/{periodo}`
2. Processamento: Extrai top 3 produtos
3. Renderização: Cria cards com posição, nome, quantidade, valor

---

### 4. Módulo de Cardápio (`js/cardapio.js`)

#### Função `carregarCardapio()`

**Fluxo**:
1. Requisição: `GET /api/cardapio/{restaurante_id}`
2. Processamento: Recebe array de itens
3. Renderização: Cria cards para cada item com:
   - Imagem (se disponível)
   - Nome
   - Categoria
   - Preço formatado
   - Botões de editar/excluir

#### Função `adicionarItem(dados)`

**Fluxo**:
1. Validação: Verifica campos obrigatórios
2. Requisição: `POST /api/cardapio/add`
3. Processamento: Se sucesso, recarrega lista
4. Feedback: Exibe mensagem de sucesso/erro

#### Função `editarItem(itemId, dados)`

**Fluxo**:
1. Preenche formulário com dados existentes
2. Modal de edição aberto
3. Requisição: `PUT /api/cardapio/edit/{itemId}`
4. Atualização: Atualiza item na lista

#### Função `deletarItem(itemId)`

**Fluxo**:
1. Confirmação do usuário
2. Requisição: `DELETE /api/cardapio/delete/{itemId}`
3. Remoção: Remove item da lista visualmente

---

### 5. Módulo de Pedidos (`js/pedidos.js`)

#### Estrutura de Objeto

```javascript
const PedidosApp = {
    config: {
        restaurante_id: null,
        api_base: 'http://localhost:5000/api'
    },
    init: function() { ... },
    carregarPedidos: function() { ... },
    atualizarStatus: function(pedidoId, novoStatus) { ... },
    filtrarPorStatus: function(status) { ... }
};
```

#### Função `PedidosApp.init()`

**Inicialização**:
1. Obtém `restaurante_id` do localStorage
2. Configura event listeners
3. Carrega pedidos iniciais
4. Configura filtros

#### Função `PedidosApp.carregarPedidos()`

**Fluxo**:
1. Requisição: `GET /api/pedidos/restaurante/{restaurante_id}`
2. Processamento: Filtra e ordena pedidos
3. Renderização: Cria cards para cada pedido com:
   - ID do pedido
   - Status (com badge colorido)
   - Data/hora
   - Valor total
   - Cliente
   - Botões de ação

#### Função `PedidosApp.atualizarStatus(pedidoId, novoStatus)`

**Fluxo**:
1. Confirmação do usuário
2. Requisição: `PUT /api/pedidos/{pedidoId}/status`
3. Atualização: Atualiza status visualmente
4. Feedback: Exibe mensagem de sucesso/erro

#### Filtros
- **Por Status**: Pendente, Em Preparo, Pronto, Entregue, Cancelado
- **Por Data**: Filtro de data inicial/final
- **Busca**: Filtro por ID ou nome do cliente

---

### 6. Módulo de Avaliações (`js/avaliacoes.js`)

#### Função `carregarAvaliacoes()`

**Fluxo**:
1. Requisição: `GET /api/avaliacoes/{restaurante_id}`
2. Processamento: Calcula média de notas
3. Renderização: Lista avaliações com:
   - Nota (estrelas)
   - Comentário
   - Data
   - Cliente (se disponível)

#### Função `carregarAvaliacoesPratos()`

**Fluxo**:
1. Requisição: `GET /api/avaliacoes/pratos/{restaurante_id}`
2. Processamento: Agrupa por prato
3. Renderização: Cards por prato com:
   - Nome do prato
   - Média de notas
   - Total de avaliações
   - Lista de avaliações individuais

#### Visualização de Estrelas
```javascript
function renderizarEstrelas(nota) {
    const estrelas = '⭐'.repeat(Math.floor(nota));
    const meiaEstrela = nota % 1 >= 0.5 ? '⭐' : '';
    return estrelas + meiaEstrela;
}
```

---

## 🔐 Autenticação e Segurança

### Verificação de Autenticação

#### No `index.html`
```javascript
// Verificação inicial
const authenticated = localStorage.getItem('authenticated');
if (authenticated !== 'true') {
    window.location.href = 'paginas/login.html';
}

// Verificação periódica (a cada 5 segundos)
setInterval(verificarAutenticacao, 5000);

// Verificação ao clicar (5% de chance)
document.addEventListener('click', function(event) {
    if (Math.random() < 0.05) {
        verificarAutenticacao();
    }
});
```

#### Em Cada Módulo
```javascript
// Verificação antes de carregar dados
const restauranteId = localStorage.getItem('restaurante_id');
if (!restauranteId) {
    window.location.href = 'paginas/login.html';
    return;
}
```

### Tratamento de Erros de Autenticação

#### Detecção de 401/403
```javascript
if (response.status === 401 || response.status === 403) {
    const errorMsg = data.message || '';
    const isAuthError = errorMsg.toLowerCase().includes('sessão') ||
                       errorMsg.toLowerCase().includes('expirada');
    
    if (isAuthError) {
        localStorage.removeItem('authenticated');
        localStorage.removeItem('restaurante_id');
        window.location.href = 'paginas/login.html';
    }
}
```

### Logout

#### Função `logout()`
```javascript
function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        localStorage.removeItem('authenticated');
        localStorage.removeItem('restaurante_id');
        localStorage.removeItem('restaurante_nome');
        window.location.href = 'paginas/login.html';
    }
}
```

---

## 🎨 UI/UX e Estilização

### Estrutura de Layout

#### Sidebar (`index.html`)
- Logo no topo
- Menu de navegação (Dashboard, Vendas, Cardápio, etc.)
- Link de logout no rodapé
- Classes CSS: `sidebar`, `nav-item`, `active`

#### Área de Conteúdo
- Container principal: `main-content`
- Área dinâmica: `#pageContent`
- Mensagens de status: `#statusMessage`

### Framework CSS

#### Tailwind CSS
- Framework utilitário via CDN
- Classes como `bg-blue-500`, `text-white`, `rounded-lg`
- Responsividade: `md:`, `lg:`, etc.

#### CSS Customizado
- Arquivos modulares por página
- Variáveis CSS para cores e espaçamentos
- Animações e transições

### Componentes Reutilizáveis

#### Cards
```html
<div class="card">
    <div class="card-header">Título</div>
    <div class="card-body">Conteúdo</div>
</div>
```

#### Botões
```html
<button class="btn btn-primary">Ação</button>
<button class="btn btn-danger">Excluir</button>
```

#### Modais
```html
<div class="modal" id="modalId">
    <div class="modal-content">
        <!-- Conteúdo -->
    </div>
</div>
```

### Gráficos (Chart.js)

#### Configuração Padrão
```javascript
{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
    },
    scales: {
        y: { beginAtZero: true }
    }
}
```

---

## 🔌 Integração com Backend

### Configuração da API

#### URL Base
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

### Padrão de Requisições

#### GET
```javascript
const response = await fetch(`${API_BASE_URL}/endpoint/${id}`);
const data = await response.json();
```

#### POST
```javascript
const response = await fetch(`${API_BASE_URL}/endpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
});
const data = await response.json();
```

#### PUT
```javascript
const response = await fetch(`${API_BASE_URL}/endpoint/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
});
```

#### DELETE
```javascript
const response = await fetch(`${API_BASE_URL}/endpoint/${id}`, {
    method: 'DELETE'
});
```

### Tratamento de Respostas

#### Formato Esperado
```json
{
  "status": "success|error",
  "message": "Mensagem opcional",
  "data": { ... }
}
```

#### Processamento
```javascript
if (data.status === 'success') {
    // Processar dados
    atualizarUI(data.data);
} else {
    // Exibir erro
    mostrarErro(data.message);
}
```

### Tratamento de Erros

#### Erros de Rede
```javascript
try {
    const response = await fetch(url);
} catch (error) {
    console.error('Erro de conexão:', error);
    mostrarErro('Erro de conexão com o servidor');
}
```

#### Erros HTTP
```javascript
if (!response.ok) {
    const errorData = await response.json();
    mostrarErro(errorData.message || 'Erro desconhecido');
}
```

---

## 🚀 Performance

### Otimizações

1. **Carregamento Lazy**: Páginas carregadas apenas quando necessário
2. **Cache de Dados**: localStorage para evitar requisições repetidas
3. **Debounce**: Em campos de busca/filtro
4. **Throttle**: Em eventos de scroll/resize

### Limitações

- Sem cache de requisições HTTP (sempre busca do backend)
- Gráficos recriados a cada carregamento (não reutilizados)
- Sem virtualização de listas longas

---

## 🐛 Debugging

### Console Logs
```javascript
console.log('✅ Operação bem-sucedida');
console.error('❌ Erro:', error);
console.warn('⚠️ Aviso:', message);
```

### DevTools
- Acessível via F12 (se habilitado)
- Inspeção de elementos
- Network tab para requisições
- Console para logs

### Mensagens de Status
```javascript
function showStatus(message, type) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.style.display = 'block';
    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 3000);
}
```

---

## 📝 Notas de Implementação

### Dependências
- Electron: Framework desktop
- Chart.js: Gráficos (via CDN)
- Tailwind CSS: Framework CSS (via CDN)

### Compatibilidade
- Windows 10+
- macOS 10.13+
- Linux (distribuições modernas)

### Build e Distribuição
- `npm start`: Modo desenvolvimento
- `npm run build`: Build para produção (Electron Builder)
- Saída: `dist/` com instalador `.exe`

---

**Fim da Documentação do Frontend**

