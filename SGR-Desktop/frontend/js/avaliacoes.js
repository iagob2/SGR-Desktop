// avaliacoes.js - Funcionalidades específicas da página de Avaliações

// 🔥 REFATORAÇÃO: Usar window.variavel para evitar redeclaração
window.API_BASE_URL = 'http://localhost:5000/api';

// Variáveis de estado
// 🔥 CORREÇÃO CRÍTICA: Usar var para evitar redeclaração (SyntaxError)
var isPratoView = false; // Começa na visualização geral (restaurante)

// 🛑 CORREÇÃO CRÍTICA: Obter ID do localStorage sem fallback
window.restauranteIdStringAvaliacoes = localStorage.getItem('restaurante_id');
window.restaurante_id = parseInt(window.restauranteIdStringAvaliacoes, 10);

console.log('🔍 ID do restaurante (avaliacoes):', window.restauranteIdStringAvaliacoes, '-> parsed:', window.restaurante_id);

// Verificar se o ID é válido
if (!window.restaurante_id || isNaN(window.restaurante_id)) {
    console.error('❌ ERRO CRÍTICO: ID do restaurante inválido nas avaliações!');
    console.error('❌ localStorage restaurante_id:', window.restauranteIdStringAvaliacoes);
    alert('Erro: Sessão inválida. Redirecionando para login...');
    window.location.href = '../paginas/login.html';
}

// ID já obtido e validado no topo do arquivo - usar variável restaurante_id diretamente

// Variável para armazenar os dados reais da API
// 🔥 CORREÇÃO CRÍTICA: Usar var para evitar redeclaração (SyntaxError)
var apiReviews = []; // Dados reais da API
var apiResumo = { media_notas: 0, total_avaliacoes: 0 }; // Resumo da API

// Função para mostrar mensagens de status
function showStatus(message, type = 'success') {
    const statusDiv = document.getElementById('statusMessage');
    if (!statusDiv) {
        // Elemento não existe nesta página, apenas log
        console.log(`[Avaliações] ${message}`);
        return;
    }
    
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    statusDiv.style.display = 'block';
    
    setTimeout(() => {
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
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
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erro na requisição:', error);
        throw error;
    }
}

// Função para carregar avaliações condicionalmente
async function carregarAvaliacoes(isPrato) {
    // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
    const restauranteId = window.restaurante_id;
    let endpoint = `/avaliacoes/${restauranteId}`; // Rota de Avaliação Geral
    if (isPrato) {
        endpoint = `/avaliacoes/pratos/${restauranteId}`; // Nova Rota de Avaliação de Prato
    }

    try {
        console.log(`🔄 Carregando ${isPrato ? 'avaliações de pratos' : 'avaliações gerais'}`);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        const data = await response.json();

        // 🔥 VERIFICAÇÃO CRÍTICA - Log completo da resposta
        console.log('✅ Resposta completa da API (avaliações):', data);
        console.log('✅ Status da resposta:', data.status);
        console.log('✅ Dados recebidos:', data.data);

        if (data.status === 'success' && data.data) {
            // Armazenar dados reais da API
            const avaliacoesRecebidas = data.data.avaliacoes || [];
            const resumoRecebido = data.data.resumo || { media_notas: 0, total_avaliacoes: 0 };
            
            // 🔥 VERIFICAÇÃO CRÍTICA - Estrutura dos dados
            console.log('📊 Avaliações recebidas:', avaliacoesRecebidas);
            console.log('📈 Resumo recebido:', resumoRecebido);
            console.log('🔍 Quantidade de avaliações:', avaliacoesRecebidas.length);

            apiReviews = avaliacoesRecebidas;
            apiResumo = resumoRecebido;

            // Se não há dados e estamos em modo prato, usar dados mock
            if (apiReviews.length === 0 && isPrato) {
                console.warn('⚠️ AVISO: Nenhuma avaliação de prato encontrada para o restaurante', restauranteId);
                console.log('🔄 Usando dados mock para avaliações de pratos');
                apiReviews = [
                    {
                        id: 1,
                        nota: 5.0,
                        comentario: 'Excelente prato! O sabor estava perfeito e a apresentação impecável.',
                        data_avaliacao: '2024-12-15T14:30:00',
                        cliente_nome: 'Maria Silva',
                        nome_prato: 'Hambúrguer Clássico'
                    },
                    {
                        id: 2,
                        nota: 4.0,
                        comentario: 'Muito bom! Ingredientes frescos e bem preparados.',
                        data_avaliacao: '2024-12-14T19:45:00',
                        cliente_nome: 'João Santos',
                        nome_prato: 'Pizza Margherita'
                    },
                    {
                        id: 3,
                        nota: 3.0,
                        comentario: 'Regular, nada especial mas também não ruim.',
                        data_avaliacao: '2024-12-13T12:15:00',
                        cliente_nome: 'Ana Costa',
                        nome_prato: 'Sushi Salmão'
                    }
                ];
                apiResumo = { media_notas: 4.0, total_avaliacoes: 3 };
                showStatus('Dados de demonstração carregados para avaliações de pratos!', 'success');
            } else if (apiReviews.length === 0) {
                console.warn(`⚠️ AVISO: Nenhuma avaliação encontrada para ${isPrato ? 'pratos' : 'restaurante'} ${restauranteId}`);
                showStatus(`Restaurante ${restauranteId} não possui ${isPrato ? 'avaliações de pratos' : 'avaliações'} ainda.`, 'warning');
            } else {
                showStatus(`${apiReviews.length} avaliação(ões) carregada(s) com sucesso!`, 'success');
                console.log(`✅ Avaliações carregadas com sucesso:`, apiReviews);
            }

            // Chamadas com os dados (reais ou mock)
            renderizarTabela(apiReviews, isPrato);
            updateKPIs(apiResumo);
        } else {
            console.error('❌ Falha na resposta da API (avaliações):', data.message);
            showStatus(`Erro da API: ${data.message}`, 'error');
            apiReviews = [];
            apiResumo = { media_notas: 0, total_avaliacoes: 0 };
            renderizarTabela([], isPrato);
            updateKPIs(apiResumo);
        }
    } catch (error) {
        console.error('❌ ERRO FATAL na requisição das avaliações:', error);
        console.error('❌ Stack trace:', error.stack);
        showStatus(`Erro ao carregar avaliações: ${error.message}`, 'error');
        
        // Em caso de erro total, usar dados vazios
        console.log('🔄 Carregando dados vazios como fallback...');
        apiReviews = [];
        apiResumo = { media_notas: 0, total_avaliacoes: 0 };
        renderizarTabela([], isPrato);
        updateKPIs(apiResumo);
    }
}

// Função para gerar estrelas
function generateStars(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= rating) {
            stars += '<span class="text-yellow-400 text-xl">★</span>';
        } else {
            stars += '<span class="text-gray-300 text-xl">★</span>';
        }
    }
    return stars;
}

// Função para truncar texto
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Função para atualizar KPIs usando resumo da API
function updateKPIs(resumo) {
    // Usar os dados do resumo diretamente da API
    const avgRating = resumo.media_notas || 0;
    const totalReviews = resumo.total_avaliacoes || 0;

    // Calcular % de avaliações positivas usando dados da API
    const positiveReviews = apiReviews.filter(review => review.nota >= 4).length;
    const positivePercentage = (totalReviews > 0) ? (positiveReviews / totalReviews) * 100 : 0;

    // Atualizar Avaliação Média
    const avgCard = document.getElementById('avgRatingCard');
    const avgIcon = document.getElementById('avgRatingIcon');
    const avgValue = document.getElementById('avgRatingValue');
    const avgBadge = document.getElementById('avgRatingBadge');

    avgValue.textContent = avgRating.toFixed(1);

    if (avgRating >= 4.5) {
        avgCard.className = 'p-6 rounded-xl shadow-lg border-l-4 border-green-700 text-white';
        avgCard.style.background = 'linear-gradient(135deg, #10B981, #059669)';
        avgIcon.textContent = '⭐⭐⭐⭐⭐';
        avgBadge.innerHTML = '';
    } else if (avgRating >= 4.0) {
        avgCard.className = 'p-6 rounded-xl shadow-lg border-l-4 border-green-600 text-white';
        avgCard.style.background = 'linear-gradient(135deg, #34D399, #10B981)';
        avgIcon.textContent = '⭐⭐⭐⭐';
        avgBadge.innerHTML = '';
    } else if (avgRating >= 3.0) {
        avgCard.className = 'p-6 rounded-xl shadow-lg border-l-4 border-yellow-600';
        avgCard.style.background = 'linear-gradient(135deg, #FBBF24, #F59E0B)';
        avgCard.style.color = '#78350F';
        avgIcon.textContent = '⚠️';
        avgBadge.innerHTML = '<span class="bg-yellow-200 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">ATENÇÃO NECESSÁRIA</span>';
    } else {
        avgCard.className = 'p-6 rounded-xl shadow-lg border-l-4 border-red-700 text-white pulse-animation';
        avgCard.style.background = 'linear-gradient(135deg, #EF4444, #DC2626)';
        avgIcon.textContent = '🚨';
        avgBadge.innerHTML = '<span class="bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm font-medium">AÇÃO URGENTE</span>';
    }

    // Atualizar Avaliações Positivas
    const positiveCard = document.getElementById('positiveCard');
    const positiveValue = document.getElementById('positiveValue');

    positiveValue.textContent = Math.round(positivePercentage) + '%';

    if (positivePercentage >= 80) {
        positiveCard.style.background = '#D1FAE5';
        positiveCard.style.color = '#065F46';
        positiveCard.style.borderColor = '#10B981';
    } else if (positivePercentage >= 70) {
        positiveCard.style.background = '#FEF3C7';
        positiveCard.style.color = '#92400E';
        positiveCard.style.borderColor = '#F59E0B';
    } else if (positivePercentage >= 50) {
        positiveCard.style.background = '#FFEDD5';
        positiveCard.style.color = '#9A3412';
        positiveCard.style.borderColor = '#F97316';
    } else {
        positiveCard.style.background = '#FEE2E2';
        positiveCard.style.color = '#991B1B';
        positiveCard.style.borderColor = '#EF4444';
    }

    // Atualizar Total de Avaliações
    const totalElement = document.querySelector('.bg-gray-100 .text-4xl');
    if (totalElement) {
        totalElement.textContent = totalReviews;
    }
}

// Função para renderizar tabela condicionalmente
function renderizarTabela(avaliacoes, isPrato) {
    const thead = document.getElementById('avaliacoesTableHead');
    const tbody = document.getElementById('avaliacoesTableBody');

    // 1. ATUALIZAR CABEÇALHO (THEAD)
    let headerHTML = `
        <th class="w-[10%] px-4 py-4 text-left text-sm font-semibold text-gray-700">Data</th>
        <th class="w-[15%] px-4 py-4 text-left text-sm font-semibold text-gray-700">Cliente</th>`;

    if (isPrato) {
        headerHTML += `<th class="w-[15%] px-4 py-4 text-left text-sm font-semibold text-gray-700">Prato</th>`;
    }

    headerHTML += `
        <th class="w-[45%] px-4 py-4 text-left text-sm font-semibold text-gray-700">Comentário</th>
        <th class="w-[15%] px-4 py-4 text-center text-sm font-semibold text-gray-700">Nota</th>`;
    
    thead.innerHTML = `<tr>${headerHTML}</tr>`;

    // 2. PREENCHER CORPO (TBODY)
    tbody.innerHTML = '';
    
    avaliacoes.forEach(avaliacao => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';

        // Determinar cor de fundo baseada na nota (usar apenas nomes da API)
        let rowBg = '';
        if (avaliacao.nota === 5) rowBg = 'bg-yellow-50';
        else if (avaliacao.nota <= 2) rowBg = 'bg-red-50';

        let rowHTML = `
            <td class="px-4 py-4 ${rowBg}">
                <span class="text-sm text-gray-600">${formatarData(avaliacao.data_avaliacao)}</span>
            </td>
            <td class="px-4 py-4 ${rowBg}">
                <span class="text-sm font-medium text-gray-900">${avaliacao.cliente_nome}</span>
            </td>`;

        if (isPrato) {
            rowHTML += `
                <td class="px-4 py-4 ${rowBg}">
                    <span class="text-sm text-gray-700 tooltip" data-tooltip="${avaliacao.nome_prato}">
                        ${truncateText(avaliacao.nome_prato, 25)}
                    </span>
                </td>`;
        }

        rowHTML += `
            <td class="px-4 py-6 ${rowBg}">
                <div class="text-sm text-gray-900 leading-relaxed">
                    <div class="comment-truncated" id="comment-${avaliacoes.indexOf(avaliacao)}">
                        ${avaliacao.comentario}
                    </div>
                    ${avaliacao.comentario.length > 150 ? 
                        `<button onclick="toggleComment(${avaliacoes.indexOf(avaliacao)})" class="text-blue-600 hover:text-blue-800 text-sm mt-2">ler mais</button>` 
                        : ''
                    }
                </div>
            </td>
            <td class="px-4 py-4 ${rowBg} text-center">
                <div class="flex justify-center items-center space-x-1 tooltip" data-tooltip="Nota: ${avaliacao.nota}/5">
                    ${generateStars(avaliacao.nota)}
                </div>
            </td>`;

        row.innerHTML = rowHTML;
        tbody.appendChild(row);
    });
}

// Função para formatar data
function formatarData(dataString) {
    if (!dataString) return 'N/A';
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR');
    } catch (error) {
        return dataString;
    }
}

// Função para expandir/contrair comentário
function toggleComment(index) {
    const commentDiv = document.getElementById(`comment-${index}`);
    const button = commentDiv.nextElementSibling;
    
    if (commentDiv.classList.contains('comment-truncated')) {
        commentDiv.classList.remove('comment-truncated');
        button.textContent = 'ler menos';
    } else {
        commentDiv.classList.add('comment-truncated');
        button.textContent = 'ler mais';
    }
}

// Função para filtrar avaliações usando dados da API
function filterReviews() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const ratingFilter = document.getElementById('ratingFilter').value;

    // Filtrar dados da API usando nomes corretos dos campos
    const filtered = apiReviews.filter(review => {
        const matchesSearch = review.cliente_nome.toLowerCase().includes(searchTerm) || 
                            review.comentario.toLowerCase().includes(searchTerm);
        const matchesRating = !ratingFilter || review.nota.toString() === ratingFilter;

        return matchesSearch && matchesRating;
    });

    // Renderizar tabela com dados filtrados
    renderizarTabela(filtered, isPratoView);
    
    // Mostrar status do filtro
    if (filtered.length === 0 && (searchTerm || ratingFilter)) {
        showStatus('Nenhuma avaliação encontrada com os filtros aplicados.', 'warning');
    } else if (filtered.length < apiReviews.length) {
        showStatus(`${filtered.length} avaliação(ões) encontrada(s) com os filtros aplicados.`, 'success');
    }
}

// Função para limpar filtros
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('ratingFilter').value = '';
    
    // Renderizar tabela com todos os dados da API
    renderizarTabela(apiReviews, isPratoView);
    showStatus('Filtros limpos!', 'success');
}

// Função de inicialização manual (para carregamento dinâmico)
function inicializarAvaliacoes() {
    console.log('🔄 Inicializando avaliações manualmente...');
    
    // Verificar se estamos na página de avaliações
    const avaliacoesSection = document.getElementById('avaliacoesSection');
    console.log('🔍 Procurando elemento avaliacoesSection:', avaliacoesSection);
    
    if (avaliacoesSection) {
        console.log('✅ Seção de avaliações encontrada, iniciando carregamento...');
        
        // Carregar dados iniciais da API
        carregarAvaliacoes(isPratoView);
        
        // Event listeners
        const searchInput = document.getElementById('searchInput');
        const ratingFilter = document.getElementById('ratingFilter');
        const toggleBtn = document.getElementById('toggleViewBtn');
        
        console.log('🔍 Elementos encontrados:', {
            searchInput: !!searchInput,
            ratingFilter: !!ratingFilter,
            toggleBtn: !!toggleBtn
        });
        
        if (searchInput) {
            searchInput.addEventListener('input', filterReviews);
            console.log('✅ Event listener adicionado ao campo de busca');
        }
        
        if (ratingFilter) {
            ratingFilter.addEventListener('change', filterReviews);
            console.log('✅ Event listener adicionado ao filtro de nota');
        }
        
        // Event listener do botão de alternância
        if (toggleBtn) {
            console.log('✅ Botão de alternância encontrado, adicionando event listener');
            toggleBtn.addEventListener('click', () => {
                console.log('🔄 Botão de alternância clicado! Estado atual:', isPratoView);
                isPratoView = !isPratoView; // Inverte o estado
                console.log('🔄 Novo estado:', isPratoView);

                // Atualiza o texto do botão
                toggleBtn.textContent = isPratoView 
                    ? 'Mostrar Avaliações Gerais' 
                    : 'Mostrar Avaliações de Prato';
                console.log('✅ Texto do botão atualizado para:', toggleBtn.textContent);

                // Recarrega os dados com o novo estado
                carregarAvaliacoes(isPratoView);
            });
            console.log('✅ Event listener do botão de alternância adicionado');
        } else {
            console.error('❌ Botão de alternância não encontrado!');
        }
    } else {
        console.log('⚠️ Seção de avaliações não encontrada');
    }
}

// ✅ CORREÇÃO: Expor função para index.html (carregamento dinâmico)
window.inicializarAvaliacoes = inicializarAvaliacoes;
