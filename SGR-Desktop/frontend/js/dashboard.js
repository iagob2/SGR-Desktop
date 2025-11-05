// dashboard.js - Funcionalidades específicas do Dashboard

// 🔥 CORREÇÃO CRÍTICA: Usar var para variáveis globais reutilizáveis (evita SyntaxError de redeclaração)
var chart = null;
var currentTab = 'vendas';
var API_BASE_URL = 'http://localhost:5000/api';

// Expor via window para acesso global
window.chart = chart;
window.currentTab = currentTab;
window.API_BASE_URL = API_BASE_URL;

// 🛑 CORREÇÃO CRÍTICA: Obter ID do localStorage sem fallback
window.restauranteIdString = localStorage.getItem('restaurante_id');
window.restaurante_id = parseInt(window.restauranteIdString, 10);


// Verificar se o ID é válido
if (!window.restaurante_id || isNaN(window.restaurante_id)) {
    console.error('❌ ERRO CRÍTICO: ID do restaurante inválido no dashboard!');
    console.error('❌ localStorage restaurante_id:', window.restauranteIdString);
    alert('Erro: Sessão inválida. Redirecionando para login...');
    window.location.href = 'paginas/login.html';
}

// ID já obtido e validado no topo do arquivo - usar variável restaurante_id diretamente

// Função para mostrar mensagens de status
function showStatus(message, type = 'success') {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    statusDiv.style.display = 'block';
    
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// Função para fazer requisições à API
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${window.API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        // Se for erro de conexão, mostrar mensagem mais específica
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('Erro de conexão: Verifique se o servidor está rodando em http://localhost:5000');
        }
        
        throw error;
    }
}

// Carregar métricas do dashboard
async function carregarDashboard() {
    try {
        showStatus('Carregando dados do dashboard...', 'loading');
        
        // Carregar dados completos do dashboard usando o novo endpoint centralizado
        const restauranteId = window.restaurante_id;
        
        console.log(`[DASHBOARD] Carregando dados para restaurante ${restauranteId}...`);
        const response = await fetch(`${window.API_BASE_URL}/dashboard/${restauranteId}`);
        
        // IMPORTANTE: Parsear JSON antes de verificar status
        // Se der erro no parse, pode ser resposta vazia ou HTML
        let dashboardData;
        try {
            dashboardData = await response.json();
        } catch (parseError) {
            console.error('[DASHBOARD] Erro ao parsear resposta:', parseError);
            // Se não conseguiu parsear, tentar ler como texto
            const textResponse = await response.text();
            console.error('[DASHBOARD] Resposta (texto):', textResponse.substring(0, 200));
            throw new Error('Resposta inválida da API');
        }
        
        console.log(`[DASHBOARD] Resposta recebida:`, {
            status: response.status,
            statusText: response.statusText,
            dataStatus: dashboardData.status,
            message: dashboardData.message
        });
        
        // Se status é 401/403 E a mensagem indica erro de sessão/login
        if (response.status === 401 || response.status === 403) {
            const errorMsg = dashboardData.message || '';
            const isAuthError = errorMsg.toLowerCase().includes('sessão') || 
                               errorMsg.toLowerCase().includes('expirada') ||
                               errorMsg.toLowerCase().includes('faça login') ||
                               errorMsg.toLowerCase().includes('login') ||
                               errorMsg.toLowerCase().includes('autentic') ||
                               errorMsg.toLowerCase().includes('credencial');
            
            if (isAuthError) {
                // Erro de autenticação confirmado - bloquear acesso
                console.error('❌ ERRO DE AUTENTICAÇÃO CONFIRMADO: Redirecionando para login...');
                console.error('   Status:', response.status);
                console.error('   Mensagem:', errorMsg);
                alert('Sua sessão expirou ou você não tem permissão. Redirecionando para login...');
                localStorage.removeItem('authenticated');
                localStorage.removeItem('restaurante_id');
                localStorage.removeItem('restaurante_nome');
                window.location.href = 'paginas/login.html';
                return;
            } else {
                // 401/403 mas não é erro de autenticação - pode ser endpoint protegido/inexistente
                console.warn(`⚠️ Status ${response.status} mas não parece ser erro de autenticação`);
                console.warn('   Mensagem:', errorMsg);
                console.warn('   Continuando com tratamento normal...');
                // Continuar - não redirecionar
            }
        }
        
        // Verificar se a resposta indica erro de login/credenciais
        if (dashboardData.status === 'error') {
            const errorMsg = dashboardData.message || '';
            if (errorMsg.toLowerCase().includes('sessão') || 
                errorMsg.toLowerCase().includes('expirada') ||
                errorMsg.toLowerCase().includes('login') || 
                errorMsg.toLowerCase().includes('credencial') || 
                errorMsg.toLowerCase().includes('autentic')) {
                // Erro de autenticação - bloquear acesso
                console.error('❌ ERRO DE AUTENTICAÇÃO NA RESPOSTA: Redirecionando para login...');
                alert('Erro de autenticação. Redirecionando para login...');
                localStorage.removeItem('authenticated');
                localStorage.removeItem('restaurante_id');
                localStorage.removeItem('restaurante_nome');
                window.location.href = 'paginas/login.html';
                return;
            }
        }
        
        if (dashboardData.status === 'success' && dashboardData.data) {
            const data = dashboardData.data;
            
            console.log('[DASHBOARD] Dados recebidos:', data);
            
            // Verificar se existem dados ou se estão vazios
            const hasCards = data.cards && Object.keys(data.cards).length > 0;
            const hasGraficos = data.graficos && Object.keys(data.graficos).length > 0;
            
            console.log('[DASHBOARD] Has cards:', hasCards);
            console.log('[DASHBOARD] Has graficos:', hasGraficos);
            
            if (!hasCards) {
                // Restaurante novo sem dados - mostrar zeros e mensagem
                console.log('[DASHBOARD] Sem cards, renderizando vazios');
                renderizarCardsVazios();
                showStatus('Carregado com sucesso. Restaurante ainda não possui vendas.', 'success');
            } else {
                console.log('[DASHBOARD] Renderizando cards com dados:', data.cards);
                renderizarCards(data.cards);
                showStatus('Dashboard carregado com sucesso!', 'success');
            }
            
            // CORREÇÃO: Sempre tentar renderizar gráficos, mesmo que pareçam vazios
            // O backend pode retornar arrays vazios mas ainda ter estrutura válida
            if (data.graficos && (data.graficos.valor_diario || data.graficos.produtos_diarios)) {
                console.log('[DASHBOARD] Atualizando graficos com dados:', data.graficos);
                // Verificar se há dados reais antes de renderizar
                const temDadosVendas = data.graficos.valor_diario && 
                    data.graficos.valor_diario.labels && 
                    data.graficos.valor_diario.labels.length > 0;
                const temDadosProdutos = data.graficos.produtos_diarios && 
                    data.graficos.produtos_diarios.labels && 
                    data.graficos.produtos_diarios.labels.length > 0;
                
                if (temDadosVendas || temDadosProdutos) {
                    // Garantir que o gráfico seja inicializado quando há dados
                    setTimeout(() => {
                        atualizarGraficos(data.graficos);
                    }, 100);
                } else {
                    console.log('[DASHBOARD] Graficos existem mas sem labels, renderizando vazios');
                    atualizarGraficosVazios();
                }
            } else {
                console.log('[DASHBOARD] Sem estrutura de graficos, renderizando vazios');
                atualizarGraficosVazios();
            }
            
        } else if (dashboardData.status === 'error') {
            // Erro da API mas não é de autenticação
            throw new Error(dashboardData.message || 'Erro ao carregar dados do dashboard');
        } else {
            // Resposta sem status - tratar como erro
            throw new Error('Resposta inválida da API');
        }
        
    } catch (error) {
        // Verificar se é erro de autenticação na mensagem
        if (error.message && (error.message.toLowerCase().includes('login') || 
                             error.message.toLowerCase().includes('credencial') ||
                             error.message.toLowerCase().includes('autentic'))) {
            console.error('❌ ERRO DE AUTENTICAÇÃO NO CATCH: Redirecionando para login...');
            alert('Erro de autenticação. Redirecionando para login...');
            localStorage.removeItem('authenticated');
            localStorage.removeItem('restaurante_id');
            localStorage.removeItem('restaurante_nome');
            window.location.href = 'paginas/login.html';
            return;
        }
        
        // Outro tipo de erro - mostrar mensagem mas NÃO usar dados mock
        console.error('Erro ao carregar dashboard:', error);
        showStatus(`Erro ao carregar dashboard: ${error.message}`, 'error');
        // NÃO usar dados mock - mostrar estado vazio
        renderizarCardsVazios();
        atualizarGraficosVazios();
        showStatus('Carregado (sem dados disponíveis)', 'warning');
    }
}

// Função para renderizar cards com dados reais
function renderizarCards(cards) {
    console.log('[DASHBOARD] renderizarCards chamado com:', cards);
    
    try {
        // Verificar se cada card existe antes de tentar acessá-lo
        if (cards.total_vendas) {
            const element = document.getElementById('faturamento-hoje');
            if (element) {
                const valor = cards.total_vendas.valor || 'R$ 0,00';
                element.textContent = valor;
                console.log('[DASHBOARD] Atualizado faturamento-hoje:', valor);
            } else {
                console.error('[DASHBOARD] Elemento faturamento-hoje não encontrado!');
            }
        } else {
            console.warn('[DASHBOARD] cards.total_vendas não existe');
        }
        
        if (cards.quantidade_produtos) {
            const element = document.getElementById('pedidos-hoje');
            if (element) {
                const valor = cards.quantidade_produtos.valor || '0';
                element.textContent = valor;
                console.log('[DASHBOARD] Atualizado pedidos-hoje:', valor);
            } else {
                console.error('[DASHBOARD] Elemento pedidos-hoje não encontrado!');
            }
        } else {
            console.warn('[DASHBOARD] cards.quantidade_produtos não existe');
        }
        
        if (cards.ticket_medio_diario) {
            const element = document.getElementById('total-restaurantes');
            if (element) {
                const valor = cards.ticket_medio_diario.valor || 'R$ 0,00';
                element.textContent = valor;
                console.log('[DASHBOARD] Atualizado total-restaurantes:', valor);
            } else {
                console.error('[DASHBOARD] Elemento total-restaurantes não encontrado!');
            }
        } else {
            console.warn('[DASHBOARD] cards.ticket_medio_diario não existe');
        }
        
        if (cards.evolucao_percentual) {
            const element = document.getElementById('pedidos-pendentes');
            if (element) {
                const valor = cards.evolucao_percentual.valor || '0%';
                element.textContent = valor;
                console.log('[DASHBOARD] Atualizado pedidos-pendentes:', valor);
            } else {
                console.error('[DASHBOARD] Elemento pedidos-pendentes não encontrado!');
            }
            
            // Atualizar indicadores de crescimento (todos os elementos .kpi-growth)
            const evolucaoElements = document.querySelectorAll('.kpi-growth');
            evolucaoElements.forEach(evolucaoElement => {
                if (evolucaoElement && cards.evolucao_percentual.valor_numerico !== undefined) {
                    evolucaoElement.innerHTML = `
                        <span>${cards.evolucao_percentual.valor_numerico >= 0 ? '↗' : '↘'}</span>
                        ${cards.evolucao_percentual.valor}
                    `;
                    evolucaoElement.className = `kpi-growth ${cards.evolucao_percentual.tipo || 'neutral'}`;
                }
            });
        } else {
            console.warn('[DASHBOARD] cards.evolucao_percentual não existe');
        }
        
        console.log('[DASHBOARD] Cards renderizados com sucesso');
        
    } catch (error) {
        console.error('[DASHBOARD] Erro ao renderizar cards:', error);
        renderizarCardsVazios();
    }
}

// Função para renderizar cards com valores zerados
function renderizarCardsVazios() {
    
    const elementos = [
        { id: 'faturamento-hoje', valor: 'R$ 0,00' },
        { id: 'pedidos-hoje', valor: '0' },
        { id: 'total-restaurantes', valor: 'R$ 0,00' },
        { id: 'pedidos-pendentes', valor: '0%' }
    ];
    
    elementos.forEach(({ id, valor }) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = valor;
        }
    });
    
    // Zerar indicador de crescimento
    const evolucaoElement = document.querySelector('.kpi-growth');
    if (evolucaoElement) {
        evolucaoElement.innerHTML = '<span>→</span> 0%';
        evolucaoElement.className = 'kpi-growth neutral';
    }
}

// 🔥 CORREÇÃO CRÍTICA: Função para gerenciar estado do gráfico (evita ciclo vicioso)
var isShowingEmptyMessage = false; // Flag para evitar loops

// Função para atualizar gráficos vazios
function atualizarGraficosVazios() {
    // Marcar que estamos mostrando mensagem vazia
    isShowingEmptyMessage = true;
    
    // Destruir qualquer gráfico existente
    if (chart) {
        chart.destroy();
        chart = null;
        window.chart = null;
    }
    
    const canvas = document.getElementById('mainChart');
    if (!canvas) {
        return;
    }
    
    // 🔥 CORREÇÃO: Substituir canvas por mensagem amigável SEMPRE que não há dados
    const container = canvas.parentNode;
    container.innerHTML = `
        <div class="flex items-center justify-center h-48 text-gray-500" id="emptyChartMessage">
            <div class="text-center">
                <span class="text-lg block mb-2">📊 Sem dados para exibir</span>
                <span class="text-sm text-gray-400">Este restaurante ainda não possui vendas registradas</span>
            </div>
        </div>`;
    
    // 🔥 MELHORIA: Desabilitar botões de aba quando não há dados
    document.querySelectorAll('.chart-tab').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
        btn.title = 'Sem dados para esta visualização';
    });
}

// Restaurar canvas quando há dados
function restaurarCanvas() {
    const container = document.querySelector('.chart-container');
    const emptyMessage = document.getElementById('emptyChartMessage');
    
    if (emptyMessage && container) {
        container.innerHTML = '<canvas id="mainChart"></canvas>';
        isShowingEmptyMessage = false;
        
        // Reabilitar botões de aba quando há dados
        document.querySelectorAll('.chart-tab').forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            btn.title = '';
        });
        
        return true;
    }
    
    return false;
}

// Função para atualizar gráficos com dados reais
function atualizarGraficos(dadosGraficos) {
    console.log('[DASHBOARD] atualizarGraficos chamado com:', dadosGraficos);
    
    // Verificar se os dados existem
    if (!dadosGraficos) {
        console.log('[DASHBOARD] Dados de gráficos não existem, renderizando vazios');
        atualizarGraficosVazios();
        return;
    }
    
    // Atualizar dados do gráfico de vendas
    if (dadosGraficos.valor_diario) {
        chartData.vendas.labels = dadosGraficos.valor_diario.labels || [];
        chartData.vendas.datasets[0].data = dadosGraficos.valor_diario.data || [];
        console.log('[DASHBOARD] Dados de vendas atualizados:', {
            labels: chartData.vendas.labels,
            data: chartData.vendas.datasets[0].data
        });
    }
    
    // Atualizar dados do gráfico de produtos
    if (dadosGraficos.produtos_diarios) {
        chartData.produtos.labels = dadosGraficos.produtos_diarios.labels || [];
        chartData.produtos.datasets[0].data = dadosGraficos.produtos_diarios.data || [];
        console.log('[DASHBOARD] Dados de produtos atualizados:', {
            labels: chartData.produtos.labels,
            data: chartData.produtos.datasets[0].data
        });
    }
    
    // Verificar se há dados significativos após atualização
    const vendasData = chartData.vendas.datasets[0].data || [];
    const produtosData = chartData.produtos.datasets[0].data || [];
    const vendasLabels = chartData.vendas.labels || [];
    const produtosLabels = chartData.produtos.labels || [];
    
    const hasVendasLabels = vendasLabels.length > 0;
    const hasProdutosLabels = produtosLabels.length > 0;
    // CORREÇÃO: Remover verificação de "some(value => value > 0)" para permitir gráficos zerados
    const hasVendasData = vendasData.length > 0; 
    const hasProdutosData = produtosData.length > 0;
    
    console.log('[DASHBOARD] Verificação de dados:', {
        hasVendasData,
        hasProdutosData,
        hasVendasLabels,
        hasProdutosLabels,
        vendasDataLength: vendasData.length,
        produtosDataLength: produtosData.length,
        vendasLabelsLength: vendasLabels.length,
        produtosLabelsLength: produtosLabels.length,
        vendasData: vendasData,
        produtosData: produtosData,
        vendasLabels: vendasLabels
    });
    
    // CORREÇÃO: Só esconder se NÃO TIVER LABELS (permite gráficos zerados)
    if (!hasVendasLabels && !hasProdutosLabels) {
        console.log('[DASHBOARD] Nenhum label encontrado, renderizando vazios');
        atualizarGraficosVazios();
        return;
    }
    
    // Se há dados significativos mas canvas foi substituído, restaurar
    let canvas = document.getElementById('mainChart');
    if (!canvas) {
        // Tentar restaurar o canvas se foi substituído por mensagem vazia
        if (isShowingEmptyMessage) {
            if (restaurarCanvas()) {
                canvas = document.getElementById('mainChart');
                isShowingEmptyMessage = false;
            }
        }
        
        // Se ainda não existe, criar o canvas
        if (!canvas) {
            const container = document.querySelector('.chart-container');
            if (container) {
                container.innerHTML = '<canvas id="mainChart"></canvas>';
                canvas = document.getElementById('mainChart');
                isShowingEmptyMessage = false;
            }
        }
    }
    
    if (!canvas) {
        console.error('[DASHBOARD] Não foi possível criar/obter o canvas');
        return;
    }
    
    // Se há gráfico existente, atualizar
    if (chart && typeof chart.update === 'function') {
        console.log('[DASHBOARD] Atualizando gráfico existente');
        try {
            // Atualizar o gráfico atual
            chart.data = chartData[currentTab];
            
            // Atualizar título baseado na aba atual
            const chartTitle = document.querySelector('.chart-title');
            if (chartTitle) {
                if (currentTab === 'vendas') {
                    chartTitle.textContent = 'Análise de Vendas';
                } else if (currentTab === 'produtos') {
                    chartTitle.textContent = 'Análise de Produtos';
                }
            }
            
            // Forçar atualização da escala Y
            if (chart.options && chart.options.scales && chart.options.scales.y) {
                chart.options.scales.y.ticks.callback = function(value) {
                    if (currentTab === 'vendas') {
                        return 'R$ ' + value.toLocaleString('pt-BR');
                    } else if (currentTab === 'produtos') {
                        return value.toLocaleString('pt-BR') + ' unidades';
                    }
                    return value.toLocaleString('pt-BR');
                };
            }
            
            chart.update('active');
            
            // Sincronizar com window
            window.chart = chart;
            window.currentTab = currentTab;
            console.log('[DASHBOARD] Gráfico atualizado com sucesso');
        } catch (error) {
            console.error('[DASHBOARD] Erro ao atualizar gráfico:', error);
            // Se der erro, recriar o gráfico
            chart = null;
            window.chart = null;
            initChart();
        }
    } else {
        // Se não há gráfico, inicializar agora com dados significativos
        console.log('[DASHBOARD] Inicializando novo gráfico com dados');
        // Forçar criação do gráfico mesmo se houver dados
        isShowingEmptyMessage = false;
        initChart();
    }
}



// Carregar restaurantes
async function carregarRestaurantes() {
    try {
        showStatus('Carregando restaurantes...', 'loading');
        
        const restaurantes = await apiRequest('/restaurantes');
        
        const restaurantesDiv = document.getElementById('restaurantesList');
        restaurantesDiv.innerHTML = `
            <div class="chart-section">
                <h3>Restaurantes Cadastrados (${restaurantes.length})</h3>
                <div style="display: grid; gap: 16px; margin-top: 20px;">
                    ${restaurantes.map(rest => `
                        <div style="background: #F9FAFB; padding: 16px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                            <h4>${rest.nome}</h4>
                            <p><strong>CNPJ:</strong> ${rest.cnpj}</p>
                            <p><strong>Email:</strong> ${rest.email}</p>
                            <p><strong>Cidade:</strong> ${rest.cidade || 'N/A'} - ${rest.estado || 'N/A'}</p>
                            ${rest.descricao ? `<p><strong>Descrição:</strong> ${rest.descricao}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        showStatus(`${restaurantes.length} restaurantes carregados!`, 'success');
        
    } catch (error) {
        showStatus(`Erro ao carregar restaurantes: ${error.message}`, 'error');
    }
}

// Carregar pedidos concluídos (para dashboard e vendas)
async function carregarPedidos() {
    try {
        showStatus('Carregando pedidos concluídos...', 'loading');
        
        // Usar o novo endpoint específico para pedidos concluídos
        const pedidos = await apiRequest(`/pedidos/restaurante/${window.restaurante_id}/concluidos`);
        
        const pedidosDiv = document.getElementById('pedidosList');
        if (!pedidosDiv) {
            console.warn('[DASHBOARD] Elemento pedidosList não encontrado');
            return;
        }
        
        if (pedidos.data && pedidos.data.length > 0) {
            pedidosDiv.innerHTML = `
                <div class="chart-section">
                    <h3>Pedidos Concluídos Recentes (${pedidos.data.length})</h3>
                    <div style="display: grid; gap: 16px; margin-top: 20px;">
                        ${pedidos.data.slice(0, 10).map(pedido => {
                            // Extrair nome do cliente de diferentes formatos possíveis
                            let clienteNome = 'N/A';
                            if (pedido.cliente && typeof pedido.cliente === 'object') {
                                clienteNome = pedido.cliente.nome || pedido.cliente.nomeCliente || 'N/A';
                            } else if (pedido.cliente_nome) {
                                clienteNome = pedido.cliente_nome;
                            }
                            
                            // Extrair data do pedido de diferentes formatos possíveis
                            let dataPedido = pedido.data_pedido || pedido.criadoEm || pedido.criado_em || new Date().toISOString();
                            
                            return `
                                <div style="background: #F9FAFB; padding: 16px; border-radius: 8px; border-left: 4px solid #10B981;">
                                    <h4>Pedido #${pedido.id}</h4>
                                    <p><strong>Status:</strong> ${pedido.status || 'N/A'}</p>
                                    <p><strong>Cliente:</strong> ${clienteNome}</p>
                                    <p><strong>Valor:</strong> R$ ${(pedido.valor_total || pedido.valor || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                                    <p><strong>Data:</strong> ${new Date(dataPedido).toLocaleString('pt-BR')}</p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
            showStatus(`${pedidos.data.length} pedidos concluídos carregados!`, 'success');
        } else {
            pedidosDiv.innerHTML = `
                <div class="chart-section">
                    <h3>Pedidos Concluídos</h3>
                    <p style="text-align: center; padding: 40px; color: #6B7280;">
                        Nenhum pedido concluído encontrado ainda.
                    </p>
                </div>
            `;
            showStatus('Nenhum pedido concluído encontrado', 'warning');
        }
        
    } catch (error) {
        showStatus(`Erro ao carregar pedidos: ${error.message}`, 'error');
        const pedidosDiv = document.getElementById('pedidosList');
        if (pedidosDiv) {
            pedidosDiv.innerHTML = `
                <div class="chart-section">
                    <h3>Pedidos Concluídos</h3>
                    <p style="text-align: center; padding: 40px; color: #EF4444;">
                        Erro ao carregar pedidos: ${error.message}
                    </p>
                </div>
            `;
        }
    }
}

// 🔥 CORREÇÃO CRÍTICA: Usar var para evitar redeclaração (principal causa do SyntaxError)
var chartData = {
    vendas: {
        labels: ['17/10', '18/10', '19/10', '20/10', '21/10', '22/10', '23/10'],
        datasets: [{
            label: 'Vendas (R$)',
            data: [0, 0, 0, 0, 0, 0, 0],
            backgroundColor: '#3B82F6',
            borderColor: '#3B82F6',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y'
        }]
    },
    produtos: {
        labels: ['17/10', '18/10', '19/10', '20/10', '21/10', '22/10', '23/10'],
        datasets: [{
            label: 'Produtos Vendidos',
            data: [0, 0, 0, 0, 0, 0, 0],
            backgroundColor: '#10B981',
            borderColor: '#10B981',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
        }]
    }
};

// Inicializar gráfico com tratamento de dados vazios
function initChart() {
    // Destruir gráfico anterior antes de criar novo
    if (chart) {
        try {
            chart.destroy();
        } catch (e) {
            console.warn('[DASHBOARD] Erro ao destruir gráfico anterior:', e);
        }
        chart = null;
        window.chart = null;
    }
    
    let canvas = document.getElementById('mainChart');
    
    // Se o canvas não existe, pode ter sido substituído por mensagem vazia
    if (!canvas) {
        // Tentar restaurar o canvas
        const container = document.querySelector('.chart-container');
        if (container) {
            // Verificar se há mensagem vazia
            const emptyMessage = container.querySelector('#emptyChartMessage');
            if (emptyMessage) {
                container.innerHTML = '<canvas id="mainChart"></canvas>';
                canvas = document.getElementById('mainChart');
                isShowingEmptyMessage = false;
            } else {
                // Criar canvas se não existe
                container.innerHTML = '<canvas id="mainChart"></canvas>';
                canvas = document.getElementById('mainChart');
            }
        }
    }
    
    if (!canvas) {
        console.warn('[DASHBOARD] Não foi possível obter ou criar o canvas');
        return;
    }
    
    // Verificar se há dados significativos
    const currentData = chartData[currentTab].datasets[0].data || [];
    const hasLabels = chartData[currentTab].labels && chartData[currentTab].labels.length > 0;
    // CORREÇÃO: Aceitar dados mesmo que alguns sejam zero, desde que tenha labels
    const hasAnyData = currentData.length > 0;
    // CORREÇÃO: Aceita array de zeros [0,0,0,0,0,0,0] - não precisa ter valor > 0
    const hasMeaningfulData = currentData.length > 0;

    console.log('[DASHBOARD] initChart - Verificando dados:', {
        currentTab,
        currentData,
        hasLabels,
        hasAnyData,
        hasMeaningfulData,
        labels: chartData[currentTab].labels,
        labelsCount: chartData[currentTab].labels ? chartData[currentTab].labels.length : 0
    });

    // CORREÇÃO: Se não há labels OU se há labels mas nenhum dado, mostrar mensagem vazia
    // Mas se há labels e dados (mesmo que alguns sejam zero), renderizar gráfico
    if (!hasLabels || (hasLabels && !hasAnyData)) {
        // Destruir qualquer gráfico antigo
        if (chart) {
            try {
                chart.destroy();
            } catch (e) {
                console.warn('[DASHBOARD] Erro ao destruir gráfico:', e);
            }
            chart = null;
            window.chart = null;
        }
        
        // Marcar que estamos mostrando mensagem vazia
        isShowingEmptyMessage = true;
        
        // Substituir o canvas por uma mensagem amigável
        const container = canvas.parentNode;
        if (container) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-48 text-gray-500" id="emptyChartMessage">
                    <div class="text-center">
                        <span class="text-lg block mb-2">📊 Sem dados para exibir</span>
                        <span class="text-sm text-gray-400">Este restaurante ainda não possui vendas registradas</span>
                    </div>
                </div>`;
        }
        return;
    }
    
    // Se chegou aqui, há dados (mesmo que alguns sejam zero) - criar gráfico
    isShowingEmptyMessage = false;
    console.log('[DASHBOARD] Criando gráfico com dados:', {
        labels: chartData[currentTab].labels,
        data: currentData
    });
    
    const ctx = canvas.getContext('2d');
    
    chart = new Chart(ctx, {
        type: 'bar',
        data: chartData[currentTab],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    grid: {
                        color: '#F3F4F6',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#6B7280',
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            // Formatação dinâmica baseada na aba atual
                            if (currentTab === 'vendas') {
                                return 'R$ ' + value.toLocaleString();
                            } else if (currentTab === 'produtos') {
                                return value.toLocaleString() + ' unidades';
                            }
                            return value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6B7280',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
    
    // Expor via window para acesso externo
    window.chart = chart;
    window.currentTab = currentTab;
}

// Trocar aba do gráfico
function switchTab(tab) {
    // Verificar se o botão clicado está desabilitado
    if (event && event.target && event.target.disabled) {
        return;
    }
    
    currentTab = tab;
    
    // Atualizar botões
    document.querySelectorAll('.chart-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Se estamos mostrando mensagem vazia, não processar switchTab
    if (isShowingEmptyMessage) {
        return;
    }
    
    // Verificar se canvas existe antes de tentar operar
    const canvas = document.getElementById('mainChart');
    if (!canvas) {
        return;
    }
    
    // Se gráfico não existe MAS canvas existe, tentar inicializar
    if (!chart) {
        // Verificar se já há dados significativos para a aba selecionada
        const currentData = chartData[tab].datasets[0].data;
        const hasMeaningfulData = currentData.some(value => value > 0);
        
        if (!hasMeaningfulData) {
            return;
        }
        
        initChart();
        return;
    }
    
    // Atualizar gráfico existente
    chart.data = chartData[tab];
    
    // Atualizar título do gráfico baseado na aba
    const chartTitle = document.querySelector('.chart-title');
    if (tab === 'vendas') {
        chartTitle.textContent = 'Análise de Vendas';
    } else if (tab === 'produtos') {
        chartTitle.textContent = 'Análise de Produtos';
    }
    
    // Forçar atualização da escala Y para mostrar formatação correta
    chart.options.scales.y.ticks.callback = function(value) {
        if (tab === 'vendas') {
            return 'R$ ' + value.toLocaleString();
        } else if (tab === 'produtos') {
            return value.toLocaleString() + ' unidades';
        }
        return value.toLocaleString();
    };
    
    chart.update('active');
    
    // Sincronizar com window
    window.chart = chart;
    window.currentTab = currentTab;
}

// Logout
function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        showStatus('Saindo do sistema...', 'loading');
        // Aqui você pode adicionar lógica de logout
        setTimeout(() => {
            window.close();
        }, 1000);
    }
}

// Função de inicialização com proteções para DOM
function inicializarDashboard() {
    // Verificar se elementos essenciais existem
    const mainChart = document.getElementById('mainChart');
    const faturamentoHoje = document.getElementById('faturamento-hoje');
    
    if (!mainChart) {
        setTimeout(() => {
            inicializarDashboard();
        }, 300);
        return;
    }
    
    if (!faturamentoHoje) {
        setTimeout(() => {
            inicializarDashboard();
        }, 300);
        return;
    }
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        setTimeout(() => {
            inicializarDashboard();
        }, 300);
        return;
    }
    
    // Aguardar um pouco para garantir que o DOM esteja totalmente pronto
    setTimeout(() => {
        carregarDashboard();
    }, 100);
}

// Expor função para index.html (carregamento dinâmico)
window.inicializarDashboard = inicializarDashboard;
