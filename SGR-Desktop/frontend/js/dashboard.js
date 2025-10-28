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
        
        const response = await fetch(`${window.API_BASE_URL}/dashboard/${restauranteId}`);
        const dashboardData = await response.json();
        
        
        if (dashboardData.status === 'success' && dashboardData.data) {
            const data = dashboardData.data;
            
            // Verificar se existem dados ou se estão vazios
            const hasCards = data.cards && Object.keys(data.cards).length > 0;
            const hasGraficos = data.graficos && Object.keys(data.graficos).length > 0;
            
            if (!hasCards) {
                showStatus(`Restaurante ${restauranteId} não possui dados ainda. Exibindo valores zerados.`, 'warning');
                renderizarCardsVazios();
            } else {
                renderizarCards(data.cards);
            }
            
            if (!hasGraficos) {
                atualizarGraficosVazios();
            } else {
                atualizarGraficos(data.graficos);
            }
            
            // 🔥 CORREÇÃO CRÍTICA: NÃO inicializar gráfico aqui se não houver dados
            // A inicialização será feita em atualizarGraficos() ou mensagem será mostrada em atualizarGraficosVazios()
            // initChart() será chamada apenas se houver dados significativos
            
            if (hasCards || hasGraficos) {
                showStatus('Dashboard carregado com sucesso!', 'success');
            }
            
        } else {
            throw new Error(dashboardData.message || 'Erro ao carregar dados do dashboard');
        }
        
    } catch (error) {
        showStatus(`Erro ao carregar dashboard: ${error.message}`, 'error');
        usarDadosMock();
    }
}

// Função para renderizar cards com dados reais
function renderizarCards(cards) {
    
    try {
        // Verificar se cada card existe antes de tentar acessá-lo
        if (cards.total_vendas) {
            const element = document.getElementById('faturamento-hoje');
            if (element) {
                element.textContent = cards.total_vendas.valor || 'R$ 0,00';
            }
        }
        
        if (cards.quantidade_produtos) {
            const element = document.getElementById('pedidos-hoje');
            if (element) {
                element.textContent = cards.quantidade_produtos.valor || '0';
            }
        }
        
        if (cards.ticket_medio_diario) {
            const element = document.getElementById('total-restaurantes');
            if (element) {
                element.textContent = cards.ticket_medio_diario.valor || 'R$ 0,00';
            }
        }
        
        if (cards.evolucao_percentual) {
            const element = document.getElementById('pedidos-pendentes');
            if (element) {
                element.textContent = cards.evolucao_percentual.valor || '0%';
            }
            
            // Atualizar indicadores de crescimento
            const evolucaoElement = document.querySelector('.kpi-growth');
            if (evolucaoElement && cards.evolucao_percentual.valor_numerico !== undefined) {
                evolucaoElement.innerHTML = `
                    <span>${cards.evolucao_percentual.valor_numerico >= 0 ? '↗' : '↘'}</span>
                    ${cards.evolucao_percentual.valor}
                `;
                evolucaoElement.className = `kpi-growth ${cards.evolucao_percentual.tipo || 'neutral'}`;
            }
        }
        
    } catch (error) {
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
    // Verificar se os dados existem
    if (!dadosGraficos || !dadosGraficos.valor_diario || !dadosGraficos.produtos_diarios) {
        atualizarGraficosVazios();
        return;
    }
    
    // Atualizar dados do gráfico de vendas
    chartData.vendas.labels = dadosGraficos.valor_diario.labels || [];
    chartData.vendas.datasets[0].data = dadosGraficos.valor_diario.data || [];
    
    // Atualizar dados do gráfico de produtos
    chartData.produtos.labels = dadosGraficos.produtos_diarios.labels || [];
    chartData.produtos.datasets[0].data = dadosGraficos.produtos_diarios.data || [];
    
    // Verificar se há dados significativos após atualização
    const vendasData = chartData.vendas.datasets[0].data;
    const produtosData = chartData.produtos.datasets[0].data;
    const hasVendasData = vendasData.some(value => value > 0);
    const hasProdutosData = produtosData.some(value => value > 0);
    
    // Se não há dados significativos, mostrar mensagem
    if (!hasVendasData && !hasProdutosData) {
        atualizarGraficosVazios();
        return;
    }
    
    // Se há dados significativos mas canvas foi substituído, restaurar
    let canvas = document.getElementById('mainChart');
    if (!canvas && isShowingEmptyMessage) {
        if (restaurarCanvas()) {
            canvas = document.getElementById('mainChart');
        }
    }
    
    if (!canvas) {
        return;
    }
    
    // Se há gráfico existente, atualizar
    if (chart) {
        // Atualizar o gráfico atual
        chart.data = chartData[currentTab];
        
        // Atualizar título baseado na aba atual
        const chartTitle = document.querySelector('.chart-title');
        if (currentTab === 'vendas') {
            chartTitle.textContent = 'Análise de Vendas';
        } else if (currentTab === 'produtos') {
            chartTitle.textContent = 'Análise de Produtos';
        }
        
        // Forçar atualização da escala Y
        chart.options.scales.y.ticks.callback = function(value) {
            if (currentTab === 'vendas') {
                return 'R$ ' + value.toLocaleString();
            } else if (currentTab === 'produtos') {
                return value.toLocaleString() + ' unidades';
            }
            return value.toLocaleString();
        };
        
        chart.update('active');
        
        // Sincronizar com window
        window.chart = chart;
        window.currentTab = currentTab;
    } else {
        // Se não há gráfico, inicializar agora com dados significativos
        initChart();
    }
}

// Função para usar dados mock em caso de erro
function usarDadosMock() {
    document.getElementById('faturamento-hoje').textContent = 'R$ 0,00';
    document.getElementById('pedidos-hoje').textContent = '0';
    document.getElementById('total-restaurantes').textContent = 'R$ 0,00';
    document.getElementById('pedidos-pendentes').textContent = '0%';
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

// Carregar pedidos
async function carregarPedidos() {
    try {
        showStatus('Carregando pedidos...', 'loading');
        
        const pedidos = await apiRequest('/pedidos/restaurante/15'); // ID do restaurante com dados
        
        const pedidosDiv = document.getElementById('pedidosList');
        pedidosDiv.innerHTML = `
            <div class="chart-section">
                <h3>Pedidos Recentes (${pedidos.data.length})</h3>
                <div style="display: grid; gap: 16px; margin-top: 20px;">
                    ${pedidos.data.slice(0, 10).map(pedido => `
                        <div style="background: #F9FAFB; padding: 16px; border-radius: 8px; border-left: 4px solid #10B981;">
                            <h4>Pedido #${pedido.id}</h4>
                            <p><strong>Status:</strong> ${pedido.status || 'N/A'}</p>
                            <p><strong>Cliente:</strong> ${pedido.cliente_nome || 'N/A'}</p>
                            <p><strong>Valor:</strong> R$ ${(pedido.valor_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                            <p><strong>Data:</strong> ${new Date(pedido.data_pedido).toLocaleString('pt-BR')}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        showStatus(`${pedidos.data.length} pedidos carregados!`, 'success');
        
    } catch (error) {
        showStatus(`Erro ao carregar pedidos: ${error.message}`, 'error');
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
        chart.destroy();
        chart = null;
        window.chart = null;
    }
    
    const canvas = document.getElementById('mainChart');
    
    if (!canvas) {
        return;
    }
    
    // Verificar se há dados significativos
    const currentData = chartData[currentTab].datasets[0].data;
    const hasMeaningfulData = currentData.some(value => value > 0);
    
    if (!hasMeaningfulData) {
        // Destruir qualquer gráfico antigo
        if (chart) {
            chart.destroy();
            chart = null;
            window.chart = null;
        }
        
        // Substituir o canvas por uma mensagem amigável
        const container = canvas.parentNode;
        container.innerHTML = `
            <div class="flex items-center justify-center h-48 text-gray-500">
                <span class="text-lg">📊 Sem dados de ${currentTab === 'vendas' ? 'vendas' : 'produtos'} para exibir.</span>
            </div>`;
        return;
    }
    
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
