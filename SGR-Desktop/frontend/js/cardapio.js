// cardapio.js - Funcionalidades específicas da página de Cardápio

// 🔥 REFATORAÇÃO: Usar window.variavel para evitar redeclaração
window.API_BASE_URL = 'http://localhost:5000/api';

// 🛑 CORREÇÃO CRÍTICA: Obter ID do localStorage sem fallback
window.restauranteIdStringCardapio = localStorage.getItem('restaurante_id');
window.restaurante_id = parseInt(window.restauranteIdStringCardapio, 10);

console.log('🔍 ID do restaurante (cardapio):', window.restauranteIdStringCardapio, '-> parsed:', window.restaurante_id);

// Verificar se o ID é válido
if (!window.restaurante_id || isNaN(window.restaurante_id)) {
    console.error('❌ ERRO CRÍTICO: ID do restaurante inválido no cardápio!');
    console.error('❌ localStorage restaurante_id:', window.restauranteIdStringCardapio);
    alert('Erro: Sessão inválida. Redirecionando para login...');
    window.location.href = '../paginas/login.html';
}

// ID já obtido e validado no topo do arquivo - usar variável restaurante_id diretamente

// Variáveis globais
// 🔥 CORREÇÃO CRÍTICA: Usar var para evitar redeclaração (SyntaxError)
var dishes = [];
var selectedDishes = new Set();
var currentEditId = null; // Para controlar se estamos editando um item

// 🎯 FUNÇÕES DO MODAL
function abrirModal(modo = 'novo', itemId = null) {
    const modal = document.getElementById('modalForm');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('pratoForm');
    
    // Limpar formulário
    form.reset();
    
    if (modo === 'novo') {
        modalTitle.textContent = 'Novo Prato';
        currentEditId = null;
    } else if (modo === 'editar' && itemId) {
        modalTitle.textContent = 'Editar Prato';
        currentEditId = itemId;
        
        // Preencher formulário com dados do item
        const prato = dishes.find(d => d.id == itemId);
        if (prato) {
            document.getElementById('nomePrato').value = prato.nome;
            document.getElementById('descricaoPrato').value = prato.descricao || '';
            document.getElementById('precoPrato').value = prato.preco;
            document.getElementById('imagemPrato').value = prato.imagemUrl || '';
        }
    }
    
    // Mostrar modal
    modal.classList.remove('hidden');
}

function fecharModal() {
    const modal = document.getElementById('modalForm');
    modal.classList.add('hidden');
    currentEditId = null;
}

function obterDadosFormulario() {
    return {
        nome: document.getElementById('nomePrato').value.trim(),
        descricao: document.getElementById('descricaoPrato').value.trim(),
        preco: parseFloat(document.getElementById('precoPrato').value),
        imagemUrl: document.getElementById('imagemPrato').value.trim()
    };
}

function validarFormulario(dados) {
    if (!dados.nome) {
        showStatus('Nome do prato é obrigatório', 'error');
        return false;
    }
    
    if (isNaN(dados.preco) || dados.preco <= 0) {
        showStatus('Preço deve ser um valor válido maior que zero', 'error');
        return false;
    }
    
    return true;
}

// 🎯 FUNÇÃO CRÍTICA: Rastreia o ID do item selecionado na tabela
function getSelectedItemId() {
    // Retorna o ID do item que está com a checkbox marcada
    const checkedBoxes = document.querySelectorAll('input[name="item_select"]:checked');
    
    if (checkedBoxes.length === 1) {
        return checkedBoxes[0].value; // Retorna o ID (que deve ser o valor da checkbox)
    }
    return null; 
}

// 🎯 LÓGICA: Controla o estado dos botões de Editar/Deletar
function updateButtonStates() {
    const selectedCount = document.querySelectorAll('input[name="item_select"]:checked').length;
    const btnEditar = document.getElementById('btnEditar');
    const btnRemover = document.getElementById('btnRemover');
    
    // Regra: Editar SÓ pode se houver 1 item selecionado
    btnEditar.disabled = (selectedCount !== 1);
    btnEditar.className = `btn-edit bg-blue-500 text-white px-4 py-2.5 rounded-lg flex items-center space-x-2 ${btnEditar.disabled ? 'opacity-50 cursor-not-allowed' : 'transition-colors hover:bg-blue-600'}`;
    
    // Regra: Deletar pode se houver 1 ou mais itens selecionados
    btnRemover.disabled = (selectedCount === 0);
    btnRemover.className = `btn-remove border-2 border-red-500 text-red-500 px-4 py-2 rounded-lg flex items-center space-x-2 ${btnRemover.disabled ? 'opacity-50 cursor-not-allowed' : 'transition-colors hover:bg-red-50'}`;
}

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
        console.error('Erro na requisição:', error);
        throw error;
    }
}

// 4. CARREGAR TABELA (Conexão ao GET do Flask)
async function carregarTabela() {
    try {
        showStatus('Carregando cardápio...', 'loading');
        
        // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
        console.log(`🍽️ Carregando cardápio do restaurante ${window.restaurante_id}`);
        
        // 🔥 CORREÇÃO: Adicionar prefixo /cardapio na URL
        const response = await fetch(`${window.API_BASE_URL}/cardapio/${window.restaurante_id}`);
        const cardapioData = await response.json();
        
        // 🔥 VERIFICAÇÃO CRÍTICA - Log completo da resposta
        console.log('✅ Resposta completa da API (cardápio):', cardapioData);
        console.log('✅ Status da resposta:', cardapioData.status);
        console.log('✅ Dados recebidos:', cardapioData.data);
        
        if (cardapioData.status === 'success') {
            const dadosCardapio = cardapioData.data || [];
            
            // 🔥 VERIFICAÇÃO CRÍTICA - Estrutura dos dados
            console.log('🍽️ Pratos recebidos:', dadosCardapio);
            console.log('🔍 Quantidade de pratos:', dadosCardapio.length);
            
            if (dadosCardapio.length === 0) {
                console.warn('⚠️ AVISO: Nenhum prato encontrado para o restaurante', restauranteId);
                showStatus(`Restaurante ${restauranteId} não possui pratos cadastrados ainda.`, 'warning');
                
                // Exibir tabela vazia em vez de quebrar
                dishes = [];
                renderTable([]);
            } else {
                dishes = dadosCardapio;
                renderTable(dishes);
                showStatus(`Cardápio carregado: ${dishes.length} pratos`, 'success');
                console.log(`✅ Cardápio carregado com sucesso:`, dishes);
            }
            
            atualizarKPIs();
            
        } else {
            console.error('❌ Falha na resposta da API (cardápio):', cardapioData.message);
            throw new Error(cardapioData.message || 'Erro ao carregar cardápio');
        }
        
    } catch (error) {
        console.error('❌ ERRO FATAL na requisição do cardápio:', error);
        console.error('❌ Stack trace:', error.stack);
        showStatus(`Erro ao carregar cardápio: ${error.message}`, 'error');
        
        // Em caso de erro, usar dados mock
        console.log('🔄 Carregando dados mock como fallback...');
        usarDadosMock();
    }
    
    updateButtonStates(); // Atualiza o estado dos botões após carregar a tabela
}

// Atualizar KPIs com dados reais (função desabilitada - KPIs removidos)
function atualizarKPIs() {
    // KPIs removidos da interface - função mantida para compatibilidade
    console.log('📊 KPIs removidos da interface');
}

// Função para renderizar a tabela com nova estrutura
function renderTable(filteredDishes = dishes) {
    const tbody = document.getElementById('dishesTable');
    tbody.innerHTML = '';

    filteredDishes.forEach(dish => {
        const isSelected = selectedDishes.has(dish.id);
        
        // Emoji baseado no nome do prato
        const emoji = obterEmojiPrato(dish.nome);

        const row = document.createElement('tr');
        row.className = isSelected ? 'bg-blue-50' : 'hover:bg-gray-50';
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="checkbox" name="item_select" class="dish-checkbox rounded border-gray-300" 
                       value="${dish.id}" ${isSelected ? 'checked' : ''}>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-sm font-medium text-gray-900">${dish.id}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${emoji} ${dish.nome}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">${dish.descricao}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-sm font-medium text-gray-900">R$ ${dish.preco.toFixed(2).replace('.', ',')}</span>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Adicionar event listeners para checkboxes
    document.querySelectorAll('input[name="item_select"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const dishId = parseInt(this.value);
            if (this.checked) {
                selectedDishes.add(dishId);
            } else {
                selectedDishes.delete(dishId);
            }
            updateButtonStates();
            renderTable(filteredDishes);
        });
    });
}

// Função para obter emoji baseado no nome do prato
function obterEmojiPrato(nome) {
    const nomeLower = nome.toLowerCase();
    
    if (nomeLower.includes('hambúrguer') || nomeLower.includes('burger')) return '🍔';
    if (nomeLower.includes('pizza')) return '🍕';
    if (nomeLower.includes('sushi') || nomeLower.includes('salmão')) return '🍣';
    if (nomeLower.includes('lasanha') || nomeLower.includes('massa')) return '🍝';
    if (nomeLower.includes('risotto')) return '🍄';
    if (nomeLower.includes('bruschetta') || nomeLower.includes('entrada')) return '🥖';
    if (nomeLower.includes('tiramisu') || nomeLower.includes('sobremesa')) return '🍰';
    if (nomeLower.includes('vinho') || nomeLower.includes('bebida')) return '🍷';
    if (nomeLower.includes('batata') || nomeLower.includes('frita')) return '🍟';
    if (nomeLower.includes('frango')) return '🍗';
    if (nomeLower.includes('peixe') || nomeLower.includes('pescado')) return '🐟';
    if (nomeLower.includes('carne')) return '🥩';
    if (nomeLower.includes('salada')) return '🥗';
    if (nomeLower.includes('sopa')) return '🍲';
    
    return '🍽️'; // Emoji padrão
}

// Função para filtrar pratos
function filterDishes() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    const filtered = dishes.filter(dish => {
        // 🚨 MUDANÇA AQUI 🚨
        const dishIdString = String(dish.id); // Converte o ID numérico para string
        
        const matchesSearch = 
            dish.nome.toLowerCase().includes(searchTerm) || // Busca por nome
            dishIdString.includes(searchTerm);             // Busca por ID
        
        return matchesSearch;
    });

    renderTable(filtered);
}

// 1. ADICIONAR NOVO ITEM (Abre o Modal)
function handleNovoPrato() {
    console.log("Abrindo modal para Adicionar Novo Prato.");
    abrirModal('novo');
}

// 2. MODIFICAR (LIGADO ao botão 'Editar')
function handleEditarPrato() {
    const itemId = getSelectedItemId();
    if (!itemId) return; 

    const prato = dishes.find(d => d.id == itemId);
    if (!prato) {
        showStatus('Prato não encontrado', 'error');
        return;
    }
    
    console.log(`Abrindo modal para Editar Item ID: ${itemId}`);
    abrirModal('editar', itemId);
}

// 3. SALVAR PRATO (Chamado pelo botão Salvar do modal)
async function salvarPrato() {
    const dados = obterDadosFormulario();
    
    if (!validarFormulario(dados)) {
        return;
    }
    
    try {
        if (currentEditId) {
            // EDITAR item existente
            await editarPratoAPI(currentEditId, dados);
        } else {
            // ADICIONAR novo item
            await adicionarPratoAPI(dados);
        }
        
        fecharModal();
        carregarTabela(); // Recarrega a tabela
        
    } catch (error) {
        console.error('Erro ao salvar prato:', error);
        showStatus(`Erro ao salvar prato: ${error.message}`, 'error');
    }
}

// Função para adicionar prato via API
async function adicionarPratoAPI(dados) {
    // 🔥 CORREÇÃO: Usar variável restaurante_id diretamente
    const novoPrato = {
        restaurante_id: window.restaurante_id,
        nome: dados.nome,
        descricao: dados.descricao || 'Sem descrição',
        preco: dados.preco,
        imagemUrl: dados.imagemUrl
    };
    
    // 🔥 CORREÇÃO: Adicionar prefixo /cardapio na URL
    const response = await fetch(`${window.API_BASE_URL}/cardapio/add`, { 
        method: 'POST', 
        body: JSON.stringify(novoPrato), 
        headers: { 'Content-Type': 'application/json' } 
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
        showStatus('Prato adicionado com sucesso!', 'success');
    } else {
        throw new Error(data.message);
    }
}

// Função para editar prato via API
async function editarPratoAPI(itemId, dados) {
    const novosDados = {
        nome: dados.nome,
        descricao: dados.descricao || 'Sem descrição',
        preco: dados.preco,
        imagemUrl: dados.imagemUrl
    };
    
    // 🔥 CORREÇÃO: Adicionar prefixo /cardapio na URL
    const response = await fetch(`${window.API_BASE_URL}/cardapio/edit/${itemId}`, { 
        method: 'PUT', 
        body: JSON.stringify(novosDados), 
        headers: { 'Content-Type': 'application/json' } 
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
        showStatus('Prato editado com sucesso!', 'success');
    } else {
        throw new Error(data.message);
    }
}

// 3. DELETAR (LIGADO ao botão 'Remover')
async function handleRemoverPrato() {
    const itemIds = Array.from(document.querySelectorAll('input[name="item_select"]:checked')).map(cb => cb.value);
    
    if (itemIds.length === 0) {
        showStatus('Selecione pelo menos um item para remover', 'error');
        return;
    }
    
    const confirmMessage = itemIds.length === 1 
        ? `Tem certeza que deseja remover este item?`
        : `Tem certeza que deseja remover ${itemIds.length} itens?`;
    
    if (!confirm(confirmMessage)) return;

    try {
        showStatus(`Removendo ${itemIds.length} item(s)...`, 'loading');
        
        let sucessos = 0;
        let erros = 0;
        let itens_protegidos = [];
        
        for (const itemId of itemIds) {
            try {
                // 🔥 CORREÇÃO: Adicionar prefixo /cardapio na URL
                const response = await fetch(`${window.API_BASE_URL}/cardapio/${itemId}`, { method: 'DELETE' });
                
                // 🔥 CORREÇÃO CRÍTICA: Interceptar o status 409 Conflict
                if (response.status === 409) {
                    const data = await response.json();
                    erros++;
                    itens_protegidos.push(itemId);
                    console.warn(`⚠️ Item ${itemId} não pode ser deletado (já foi vendido):`, data.message);
                    continue; // Pular para o próximo item
                }
                
                // Processar resposta JSON para outros status
                const data = await response.json();
                
                // Tratar sucesso (200 OK)
                if (response.ok && data.status === 'success') {
                    sucessos++;
                    console.log(`✅ Item ${itemId} deletado com sucesso`);
                } else {
                    erros++;
                    console.warn(`❌ Falha ao deletar item ${itemId}:`, data.message || 'Erro desconhecido');
                }
            } catch (error) {
                erros++;
                console.error(`❌ Erro na requisição para item ${itemId}:`, error);
            }
        }
        
        // Mostrar resultado com mensagem apropriada
        if (sucessos > 0 && erros === 0) {
            showStatus(`${sucessos} item(s) removido(s) com sucesso!`, 'success');
        } else if (sucessos > 0 && erros > 0) {
            if (itens_protegidos.length > 0) {
                showStatus(
                    `${sucessos} item(s) removido(s). ${itens_protegidos.length} item(s) não podem ser excluídos pois já foram vendidos em pedidos.`, 
                    'error'
                );
            } else {
                showStatus(`${sucessos} item(s) removido(s), ${erros} falharam`, 'error');
            }
        } else {
            if (itens_protegidos.length > 0) {
                showStatus(
                    'Não foi possível excluir os itens selecionados pois eles já foram vendidos em pedidos. Estes itens precisam permanecer no sistema para manter a integridade dos históricos.', 
                    'error'
                );
            } else {
                showStatus('Falha ao remover todos os itens', 'error');
            }
        }
        
        carregarTabela(); // Recarrega a tabela após a deleção
        
    } catch (error) {
        console.error('Erro ao remover pratos:', error);
        showStatus(`Erro ao remover pratos: ${error.message}`, 'error');
    }
}

// Função para usar dados mock em caso de erro
function usarDadosMock() {
    console.log('🔄 Usando dados mock para cardápio');
    
    dishes = [
        { id: 1, nome: "Salmão Grelhado", categoria: "principais", preco: 45.90, descricao: "Salmão fresco grelhado com ervas" },
        { id: 2, nome: "Risotto de Cogumelos", categoria: "principais", preco: 38.50, descricao: "Risotto cremoso com cogumelos frescos" },
        { id: 3, nome: "Bruschetta", categoria: "entradas", preco: 18.90, descricao: "Pão italiano com tomate e manjericão" },
        { id: 4, nome: "Tiramisu", categoria: "sobremesas", preco: 22.90, descricao: "Sobremesa italiana tradicional" },
        { id: 5, nome: "Vinho Tinto", categoria: "bebidas", preco: 85.00, descricao: "Vinho tinto selecionado" },
        { id: 6, nome: "Lasanha Bolonhesa", categoria: "principais", preco: 42.90, descricao: "Lasanha tradicional italiana" }
    ];
    
    renderTable();
    updateButtonStates();
    atualizarKPIs();
    
    showStatus('Usando dados de demonstração', 'loading');
}

// Função para inicializar a página de cardápio
function inicializarCardapio() {
    console.log('🍽️ Inicializando página de cardápio...');
    
    // Verificar se os elementos existem antes de adicionar event listeners
    const novoPratoBtn = document.getElementById('novoPratoBtn');
    const btnEditar = document.getElementById('btnEditar');
    const btnRemover = document.getElementById('btnRemover');
    const searchInput = document.getElementById('searchInput');
    const selectAll = document.getElementById('selectAll');
    
    // Event listeners dos botões principais
    if (novoPratoBtn) {
        novoPratoBtn.addEventListener('click', handleNovoPrato);
        console.log('✅ Event listener adicionado ao botão Novo Prato');
    }
    
    if (btnEditar) {
        btnEditar.addEventListener('click', handleEditarPrato);
        console.log('✅ Event listener adicionado ao botão Editar');
    }
    
    if (btnRemover) {
        btnRemover.addEventListener('click', handleRemoverPrato);
        console.log('✅ Event listener adicionado ao botão Remover');
    }

    // Event listeners do modal
    const modalClose = document.getElementById('modalClose');
    const modalCancel = document.getElementById('modalCancel');
    const modalSave = document.getElementById('modalSave');
    const modalForm = document.getElementById('modalForm');
    
    if (modalClose) {
        modalClose.addEventListener('click', fecharModal);
        console.log('✅ Event listener adicionado ao botão Fechar do modal');
    }
    
    if (modalCancel) {
        modalCancel.addEventListener('click', fecharModal);
        console.log('✅ Event listener adicionado ao botão Cancelar do modal');
    }
    
    if (modalSave) {
        modalSave.addEventListener('click', salvarPrato);
        console.log('✅ Event listener adicionado ao botão Salvar do modal');
    }
    
    // Fechar modal ao clicar fora dele
    if (modalForm) {
        modalForm.addEventListener('click', (e) => {
            if (e.target === modalForm) {
                fecharModal();
            }
        });
        console.log('✅ Event listener adicionado para fechar modal ao clicar fora');
    }

    // Event listeners de filtros e busca
    if (searchInput) {
        searchInput.addEventListener('input', filterDishes);
        console.log('✅ Event listener adicionado ao campo de busca');
    }

    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="item_select"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                const dishId = parseInt(checkbox.value);
                if (this.checked) {
                    selectedDishes.add(dishId);
                } else {
                    selectedDishes.delete(dishId);
                }
            });
            updateButtonStates();
            renderTable();
        });
        console.log('✅ Event listener adicionado ao checkbox Selecionar Todos');
    }

    // Adiciona listener para qualquer mudança no estado das checkboxes (delegação)
    const table = document.querySelector('.chart-section table');
    if (table) {
        table.addEventListener('change', (e) => {
            if (e.target.name === 'item_select') {
                updateButtonStates();
            }
        });
        console.log('✅ Event listener de delegação adicionado à tabela');
    }

    // Carregar dados da tabela
    console.log('🎯 Iniciando carregamento da tabela...');
    carregarTabela();
}

// ✅ CORREÇÃO: Expor função para index.html (carregamento dinâmico)
window.inicializarCardapio = inicializarCardapio;

