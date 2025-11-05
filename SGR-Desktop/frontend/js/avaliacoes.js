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
    let endpoint = `/avaliacoes/${restauranteId}`; // Rota de avaliações (igual ao site que funciona)
    if (isPrato) {
        endpoint = `/avaliacoes/pratos/${restauranteId}`; // Nova Rota de Avaliação de Prato
    }

    try {
        console.log(`🔄 Carregando ${isPrato ? 'avaliações de pratos' : 'avaliações gerais'}`);
        console.log(`🔗 Endpoint completo: ${window.API_BASE_URL}${endpoint}`);
        console.log(`🆔 Restaurante ID: ${restauranteId}`);
        
        const response = await fetch(`${window.API_BASE_URL}${endpoint}`);
        
        console.log(`📡 Status HTTP: ${response.status}`);
        console.log(`📋 Headers:`, [...response.headers.entries()]);
        
        // Verificar status HTTP primeiro
        if (response.status === 401 || response.status === 403) {
            console.error('❌ ERRO DE AUTENTICAÇÃO: Redirecionando para login...');
            alert('Sua sessão expirou. Redirecionando para login...');
            localStorage.removeItem('authenticated');
            localStorage.removeItem('restaurante_id');
            localStorage.removeItem('restaurante_nome');
            window.location.href = '../paginas/login.html';
            return;
        }
        
        // Verificar se a resposta é JSON válido
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('❌ Resposta não é JSON:', text.substring(0, 200));
            throw new Error(`Resposta inválida da API: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();

        // 🔥 VERIFICAÇÃO CRÍTICA - Log completo da resposta
        console.log('✅ Resposta completa da API (avaliações):', data);
        console.log('✅ Status da resposta:', data.status);
        console.log('✅ Dados recebidos:', data.data);

        // A API pode retornar:
        // 1. Array direto: [{...}, {...}] (como o site funciona)
        // 2. Objeto com status: {status: 'success', data: [...]}
        // 3. Objeto com data: {data: [...]}
        let avaliacoesRecebidas = [];
        let resumoRecebido = { media_notas: 0, total_avaliacoes: 0 };
        
        // Verificar se é array direto
        if (Array.isArray(data)) {
            avaliacoesRecebidas = data;
            console.log('✅ Resposta é array direto');
        }
        // Verificar se tem estrutura com status
        else if (data.status === 'success') {
            if (isPrato) {
                // Avaliações de pratos: estrutura normal com data.data.avaliacoes
                avaliacoesRecebidas = data.data?.avaliacoes || data.data || [];
                if (!Array.isArray(avaliacoesRecebidas)) {
                    avaliacoesRecebidas = avaliacoesRecebidas.avaliacoes || [];
                }
                resumoRecebido = data.data?.resumo || { 
                    media_notas: 0, 
                    total_avaliacoes: Array.isArray(avaliacoesRecebidas) ? avaliacoesRecebidas.length : 0 
                };
                console.log('📊 Avaliações de pratos extraídas:', avaliacoesRecebidas.length);
            } else {
                // Avaliações gerais: pode estar em data.data ou data diretamente
                avaliacoesRecebidas = data.data || data.avaliacoes || [];
                if (!Array.isArray(avaliacoesRecebidas)) {
                    avaliacoesRecebidas = avaliacoesRecebidas.avaliacoes || [];
                }
            }
        }
        // Verificar se tem data direto
        else if (data.data) {
            if (isPrato) {
                // Para pratos, pode estar em data.data.avaliacoes ou data.data direto
                avaliacoesRecebidas = Array.isArray(data.data) ? data.data : (data.data.avaliacoes || []);
            } else {
                avaliacoesRecebidas = Array.isArray(data.data) ? data.data : (data.data.avaliacoes || []);
            }
        }
        // Verificar se tem avaliacoes diretamente
        else if (data.avaliacoes && Array.isArray(data.avaliacoes)) {
            avaliacoesRecebidas = data.avaliacoes;
        }
        
        // Calcular média e total
        if (isPrato) {
            // Para avaliações de pratos, calcular resumo se não vier
            if (avaliacoesRecebidas.length > 0 && (!resumoRecebido || resumoRecebido.total_avaliacoes === 0)) {
                const somaNotas = avaliacoesRecebidas.reduce((sum, a) => sum + (Number(a.nota) || 0), 0);
                resumoRecebido = {
                    media_notas: somaNotas / avaliacoesRecebidas.length,
                    total_avaliacoes: avaliacoesRecebidas.length
                };
            } else if (!resumoRecebido) {
                resumoRecebido = { media_notas: 0, total_avaliacoes: avaliacoesRecebidas.length };
            }
        } else {
            // Para avaliações gerais
            if (avaliacoesRecebidas.length > 0) {
                const somaNotas = avaliacoesRecebidas.reduce((sum, a) => sum + (Number(a.nota) || 0), 0);
                resumoRecebido = {
                    media_notas: somaNotas / avaliacoesRecebidas.length,
                    total_avaliacoes: avaliacoesRecebidas.length
                };
            }
        }
        
        // Sempre processar, mesmo se vazio (para mostrar mensagem de estado vazio)
        // Verificar se temos dados válidos ou se é uma resposta de sucesso
        const deveProcessar = avaliacoesRecebidas.length > 0 || 
                              data.status === 'success' || 
                              Array.isArray(data) || 
                              (isPrato && data.data !== undefined) ||
                              (isPrato && response.status === 200);
        
        if (deveProcessar || avaliacoesRecebidas.length === 0) {
            // 🔥 VERIFICAÇÃO CRÍTICA - Estrutura dos dados
            console.log('📊 Avaliações recebidas (antes normalização):', avaliacoesRecebidas);
            console.log('📈 Resumo recebido:', resumoRecebido);
            console.log('🔍 Quantidade de avaliações:', avaliacoesRecebidas.length);
            
            // Normalizar estrutura das avaliações (o site usa cliente.nome, dataAvaliacao)
            if (Array.isArray(avaliacoesRecebidas)) {
                avaliacoesRecebidas = avaliacoesRecebidas.map(a => {
                    // Normalizar estrutura para o formato esperado pelo frontend
                    // O site usa: cliente.nome, dataAvaliacao, nota, comentario
                    return {
                        nota: a.nota || a.rating || 0,
                        comentario: a.comentario || a.comment || '',
                        cliente_nome: a.cliente?.nome || a.cliente_nome || (typeof a.cliente === 'string' ? a.cliente : 'Cliente'),
                        data_avaliacao: a.dataAvaliacao || a.data_avaliacao || a.data || '',
                        nome_prato: a.nome_prato || a.prato?.nome || (isPrato ? 'Prato' : '') // Para avaliações de pratos
                    };
                });
            } else {
                avaliacoesRecebidas = [];
            }

            console.log('📊 Avaliações normalizadas:', avaliacoesRecebidas);

            apiReviews = avaliacoesRecebidas;
            apiResumo = resumoRecebido;

            // Mostrar mensagem apropriada
            if (apiReviews.length === 0) {
                console.warn(`⚠️ AVISO: Nenhuma avaliação encontrada para ${isPrato ? 'pratos' : 'restaurante'} ${restauranteId}`);
                showStatus(`Restaurante ainda não possui ${isPrato ? 'avaliações de pratos' : 'avaliações'}.`, 'info');
            } else {
                showStatus(`${apiReviews.length} avaliação(ões) carregada(s) com sucesso!`, 'success');
                console.log(`✅ Avaliações carregadas com sucesso:`, apiReviews);
            }

            // Chamadas com os dados reais (vazios se não houver)
            renderizarTabela(apiReviews, isPrato);
            updateKPIs(apiResumo);
        } else {
            const errorMsg = data.message || data.error || 'Erro desconhecido da API';
            console.error('❌ Falha na resposta da API (avaliações):', errorMsg);
            console.error('❌ Resposta completa:', data);
            showStatus(`Erro da API: ${errorMsg}`, 'error');
            // Mostrar estado vazio em caso de erro
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
    // Verificar se resumo existe
    if (!resumo) {
        resumo = { media_notas: 0, total_avaliacoes: 0 };
    }
    
    // Usar os dados do resumo diretamente da API
    const avgRating = resumo.media_notas || 0;
    const totalReviews = resumo.total_avaliacoes || 0;

    // Calcular % de avaliações positivas usando dados da API
    const positiveReviews = apiReviews.filter(review => review.nota >= 4).length;
    const positivePercentage = (totalReviews > 0) ? (positiveReviews / totalReviews) * 100 : 0;

    // Atualizar Avaliação Média - VERIFICAR SE ELEMENTOS EXISTEM
    const avgCard = document.getElementById('avgRatingCard');
    const avgIcon = document.getElementById('avgRatingIcon');
    const avgValue = document.getElementById('avgRatingValue');
    const avgBadge = document.getElementById('avgRatingBadge');
    
    // Se elementos não existem, retornar sem erro
    if (!avgCard || !avgIcon || !avgValue || !avgBadge) {
        console.warn('⚠️ Elementos de KPI não encontrados');
        return;
    }

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

    // Atualizar Avaliações Positivas - VERIFICAR SE ELEMENTOS EXISTEM
    const positiveCard = document.getElementById('positiveCard');
    const positiveValue = document.getElementById('positiveValue');
    
    if (!positiveCard || !positiveValue) {
        console.warn('⚠️ Elementos de avaliações positivas não encontrados');
        return;
    }

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

    // Verificar se elementos existem antes de usar
    if (!thead || !tbody) {
        console.error('❌ ERRO: Elementos da tabela não encontrados (thead ou tbody)');
        return;
    }

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
    
    // Se não há avaliações, mostrar mensagem de estado vazio
    if (!avaliacoes || avaliacoes.length === 0) {
        const emptyMessage = isPrato 
            ? 'Nenhuma avaliação de pratos encontrada ainda.'
            : 'Nenhuma avaliação encontrada ainda.';
        
        tbody.innerHTML = `
            <tr>
                <td colspan="${isPrato ? 5 : 4}" class="px-4 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <p class="text-lg font-medium">${emptyMessage}</p>
                        <p class="text-sm text-gray-400 mt-2">Quando houver avaliações, elas aparecerão aqui.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
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
