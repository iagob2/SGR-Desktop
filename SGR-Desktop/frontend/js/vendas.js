// vendas.js - Funcionalidades específicas da página de Vendas

// 🔥 REFATORAÇÃO: Usar window.variavel para evitar redeclaração
window.vendasChart = null;
window.currentVendasTab = 'semanal';

// 🔥 REFATORAÇÃO: Usar window.variavel para evitar redeclaração
window.API_BASE_URL = 'http://localhost:5000/api';

// 🛑 CORREÇÃO CRÍTICA: Obter ID do localStorage sem fallback
window.restauranteIdStringVendas = localStorage.getItem('restaurante_id');
window.restaurante_id = parseInt(window.restauranteIdStringVendas, 10);


// Verificar se o ID é válido
if (!window.restaurante_id || isNaN(window.restaurante_id)) {
    console.error('❌ ERRO CRÍTICO: ID do restaurante inválido nas vendas!');
    console.error('❌ localStorage restaurante_id:', window.restauranteIdStringVendas);
    alert('Erro: Sessão inválida. Redirecionando para login...');
    window.location.href = '../paginas/login.html';
}

// ID já obtido e validado no topo do arquivo - usar variável restaurante_id diretamente

// Função para mostrar mensagens de status
function showStatus(message, type = 'success') {
    const statusDiv = document.getElementById('statusMessage');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = `status-message status-${type}`;
        statusDiv.style.display = 'block';
        
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
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
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

// Carregar dados de vendas do backend
async function carregarVendas() {
    try {
        showStatus('Carregando dados de vendas...', 'loading');
        
        // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
        const restauranteId = window.restaurante_id;
        if (!restauranteId) {
            throw new Error('ID do restaurante não encontrado');
        }
        
        // Inicializar gráfico primeiro, depois carregar dados
        initVendasChart();
        
        // Carregar dados semanais por padrão
        await carregarDadosPeriodo('semanal');
        
        // Carregar top produtos semanais por padrão
        await carregarTopProdutos('semanal');
        
        showStatus('Dados de vendas carregados com sucesso!', 'success');
        
    } catch (error) {
        showStatus(`Erro ao carregar vendas: ${error.message}`, 'error');
        
        // NÃO usar dados mock - mostrar gráficos vazios
        atualizarGraficoVazio();
        atualizarTopProdutosVazio();
        showStatus('Sem dados de vendas disponíveis', 'warning');
    }
}

// Carregar top 3 produtos mais vendidos
async function carregarTopProdutos(periodo) {
    try {
        showStatus(`Carregando top produtos ${periodo}...`, 'loading');
        
        // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
        const restauranteId = window.restaurante_id;
        // Usar endpoint específico para top produtos
        const produtosData = await apiRequest(`/top-produtos/${restauranteId}/${periodo}`);
        
        if (produtosData.status === 'success') {
            const dados = produtosData.data;
            
            // Verificar se há produtos reais (não vazios)
            const hasProducts = dados && dados.produtos && Array.isArray(dados.produtos) && dados.produtos.length > 0;
            
            if (hasProducts) {
                // Atualizar interface com dados dos produtos
                atualizarTopProdutos(dados);
                showStatus(`Top produtos ${periodo} carregados!`, 'success');
            } else {
                // Sem produtos - mostrar estado vazio
                atualizarTopProdutosVazio();
                showStatus(`Carregado com sucesso. Ainda não há produtos vendidos no período ${periodo}.`, 'info');
            }
        } else {
            throw new Error(produtosData.message || 'Erro ao carregar dados');
        }
        
    } catch (error) {
        showStatus(`Erro ao carregar top produtos ${periodo}`, 'error');
        
        // NÃO usar dados mock - mostrar estado vazio
        atualizarTopProdutosVazio();
    }
}

// Atualizar interface com dados dos top produtos
function atualizarTopProdutos(dados) {
    const container = document.getElementById('topProductsTable');
    if (!container) return;
    
    const produtos = dados.produtos;
    
    let html = '';
    
    if (produtos.length === 0) {
        html = '<p>Nenhum produto vendido no período selecionado.</p>';
    } else {
        html = '<div class="top-products-grid">';
        
        produtos.forEach((produto, index) => {
            const rankClass = `rank-${produto.posicao}`;
            // CORREÇÃO: Tentar diferentes nomes de campos (backend pode retornar variações)
            const valorUnitario = (produto.valor_unitario || produto.valorUnitario || produto.preco_unitario || 0).toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
            const valorTotal = (produto.valor_total_vendas || produto.valorTotalVendas || produto.total_vendas || 0).toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
            
            html += `
                <div class="product-card">
                    <div class="product-card-header">
                        <div class="product-rank ${rankClass}">${produto.posicao}</div>
                        <div class="product-name">${produto.nome}</div>
                    </div>
                    <div class="product-card-body">
                        <div class="product-metric">
                            <div class="product-metric-label">Valor Unitário</div>
                            <div class="product-metric-value unit">${valorUnitario}</div>
                        </div>
                        <div class="product-metric">
                            <div class="product-metric-label">Quantidade Vendida</div>
                            <div class="product-metric-value quantity">${produto.quantidade_vendida}</div>
                        </div>
                        <div class="product-metric">
                            <div class="product-metric-label">Valor Total</div>
                            <div class="product-metric-value price">${valorTotal}</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    container.innerHTML = html;
}

// Trocar aba dos top produtos
function switchTopProdutosTab(tab) {
    // Atualizar botões da seção de top produtos
    const topProdutosSection = document.querySelector('#topProductsTable').closest('.chart-section');
    const buttons = topProdutosSection.querySelectorAll('.chart-tab');
    
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Carregar top produtos específicos para o período selecionado
    carregarTopProdutos(tab);
}


// 🔥 CORREÇÃO CRÍTICA: Usar var para evitar redeclaração (principal causa do SyntaxError)
var vendasChartData = {
    semanal: {
        labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
        datasets: [{
            label: 'Vendas (R$)',
            data: [0, 0, 0, 0],
            backgroundColor: '#3B82F6',
            borderColor: '#3B82F6',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y'
        }, {
            label: 'Produtos Vendidos',
            data: [0, 0, 0, 0],
            backgroundColor: '#10B981',
            borderColor: '#10B981',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y1'
        }]
    },
    mensal: {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        datasets: [{
            label: 'Vendas (R$)',
            data: [0, 0, 0, 0, 0, 0],
            backgroundColor: '#3B82F6',
            borderColor: '#3B82F6',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y'
        }, {
            label: 'Produtos Vendidos',
            data: [0, 0, 0, 0, 0, 0],
            backgroundColor: '#10B981',
            borderColor: '#10B981',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y1'
        }]
    },
    anual: {
        labels: ['2020', '2021', '2022', '2023', '2024'],
        datasets: [{
            label: 'Vendas (R$)',
            data: [0, 0, 0, 0, 0],
            backgroundColor: '#3B82F6',
            borderColor: '#3B82F6',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y'
        }, {
            label: 'Produtos Vendidos',
            data: [0, 0, 0, 0, 0],
            backgroundColor: '#10B981',
            borderColor: '#10B981',
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            yAxisID: 'y1'
        }]
    }
};

// Inicializar gráfico de vendas com tratamento de dados vazios
function initVendasChart() {
    try {
        // Destruir gráfico anterior antes de criar novo
        if (window.vendasChart) {
            window.vendasChart.destroy();
            window.vendasChart = null;
        }
        
        // Verificar se Chart.js está carregado
        if (typeof Chart === 'undefined') {
            showStatus('Erro: Chart.js não está carregado', 'error');
            return;
        }
        
        // Verificar se o canvas existe
        const canvas = document.getElementById('vendasChart');
        if (!canvas) {
            showStatus('Erro: Canvas do gráfico não encontrado', 'error');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        window.vendasChart = new Chart(ctx, {
            type: 'bar',
            data: vendasChartData[window.currentVendasTab],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
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
                                return 'R$ ' + value.toLocaleString();
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return value.toLocaleString() + ' unidades';
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
        
        showStatus('Gráfico de vendas inicializado!', 'success');
        
    } catch (error) {
        showStatus(`Erro ao inicializar gráfico: ${error.message}`, 'error');
    }
}

// Trocar aba do gráfico de vendas
function switchVendasTab(tab) {
    window.currentVendasTab = tab;
    
    // Atualizar botões
    document.querySelectorAll('.chart-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Carregar dados específicos para o período selecionado
    carregarDadosPeriodo(tab);
}

// Carregar dados específicos para o período selecionado
async function carregarDadosPeriodo(periodo) {
    try {
        showStatus(`Carregando dados ${periodo}...`, 'loading');
        
        // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
        const restauranteId = window.restaurante_id;
        console.log(`📊 Carregando dados ${periodo} para restaurante ${restauranteId}`);
        
        // Usar endpoint específico para vendas por período
        const vendasData = await apiRequest(`/vendas/${restauranteId}/${periodo}`);
        
        if (vendasData.status === 'success') {
            const dados = vendasData.data;
            
            // Verificar se há dados reais (não vazios)
            const hasData = dados && (
                (dados.vendas && dados.vendas.length > 0 && dados.vendas.some(v => v > 0)) ||
                (dados.produtos && dados.produtos.length > 0 && dados.produtos.some(p => p > 0))
            );
            
            if (hasData) {
                // Atualizar gráfico com dados reais
                atualizarGraficoPeriodo(dados);
                showStatus(`Dados ${periodo} carregados!`, 'success');
                console.log(`✅ Dados ${periodo} carregados:`, dados);
            } else {
                // Dados vazios - mostrar gráfico vazio
                atualizarGraficoVazio();
                showStatus(`Carregado com sucesso. Ainda não há vendas no período ${periodo}.`, 'info');
            }
        } else {
            throw new Error(vendasData.message || 'Erro ao carregar dados');
        }
        
    } catch (error) {
        console.error(`Erro ao carregar dados ${periodo}:`, error);
        showStatus(`Erro ao carregar dados ${periodo}`, 'error');
        
        // NÃO usar dados mock - mostrar gráfico vazio
        atualizarGraficoVazio();
        showStatus('Sem dados de vendas para exibir', 'info');
    }
}

// Atualizar gráfico com dados específicos do período
function atualizarGraficoPeriodo(dados) {
    console.log('🔄 atualizarGraficoPeriodo chamado com dados:', dados);
    console.log('🔍 window.vendasChart existe?', !!window.vendasChart);
    console.log('🔍 currentVendasTab:', window.currentVendasTab);
    
    if (!window.vendasChart) {
        console.warn('⚠️ window.vendasChart não existe ainda - dados serão aplicados quando gráfico for criado');
        return;
    }
    
    // 🔥 DEBUG: Verificar estrutura dos dados recebidos
    console.log('📊 Dados recebidos da API:', {
        labels: dados.labels,
        vendas: dados.vendas,
        produtos: dados.produtos
    });
    
    // Atualizar dados do gráfico atual
    vendasChartData[window.currentVendasTab].labels = dados.labels;
    vendasChartData[window.currentVendasTab].datasets[0].data = dados.vendas;
    vendasChartData[window.currentVendasTab].datasets[1].data = dados.produtos;
    
    // Atualizar gráfico
    window.vendasChart.data = vendasChartData[window.currentVendasTab];
    window.vendasChart.update('active');
    
    console.log(`📊 Gráfico ${window.currentVendasTab} atualizado:`, {
        labels: dados.labels,
        vendas: dados.vendas,
        produtos: dados.produtos
    });
}

// Função para mostrar gráfico vazio (sem dados)
function atualizarGraficoVazio() {
    if (!window.vendasChart) return;
    
    const emptyData = {
        labels: [],
        vendas: [],
        produtos: []
    };
    
    atualizarGraficoPeriodo(emptyData);
    console.log('📊 Gráfico atualizado com dados vazios');
}

// Função para mostrar top produtos vazio
function atualizarTopProdutosVazio() {
    const container = document.getElementById('topProductsTable');
    if (!container) return;
    
    container.innerHTML = `
        <tr>
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                <div class="flex flex-col items-center">
                    <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <p class="text-lg font-medium">Sem dados de vendas</p>
                    <p class="text-sm text-gray-400 mt-2">Comece a vender para ver seus produtos mais vendidos aqui.</p>
                </div>
            </td>
        </tr>
    `;
}




// ✅ CORREÇÃO: Criar função de inicialização com proteções para DOM
function inicializarVendas() {
    console.log('🚀 Inicializando página de vendas...');
    
    // 🔥 PROTEÇÃO CRÍTICA: Verificar se canvas existe
    const vendasChart = document.getElementById('vendasChart');
    
    if (!vendasChart) {
        console.error('❌ ERRO: Canvas vendasChart não encontrado! DOM pode não estar pronto.');
        // Tentar novamente após mais tempo
        setTimeout(() => {
            console.log('🔄 Tentando inicializar vendas novamente...');
            inicializarVendas();
        }, 300);
        return;
    }
    
    console.log('✅ Canvas de vendas encontrado, prosseguindo com inicialização...');
    
    // 🔥 CORREÇÃO: NÃO inicializar gráfico aqui - será feito após carregar dados da API
    setTimeout(() => {
        carregarVendas();
    }, 100); // Reduzido de 500ms para 100ms já que temos proteção
}

// Expor função para index.html (carregamento dinâmico)
window.inicializarVendas = inicializarVendas;
