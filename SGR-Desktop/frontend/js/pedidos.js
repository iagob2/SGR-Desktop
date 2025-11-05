// Sistema de Pedidos - JavaScript Organizado e Limpo
// =============================================================

// Configurações e Estado
const PedidosApp = {
    // Configurações
    config: {
        API_BASE_URL: 'http://localhost:5000/api',
        restaurante_id: null,
        elementos: {}
    },
    
    // Estado da aplicação
    state: {
        pedidos: [],
        pedidoAtual: null,
        filtros: {
            status: '',
            data: ''
        }
    },

    // =============================
    // INICIALIZAÇÃO
    // =============================
    
    init() {
        console.log('🎯 Inicializando PedidosApp...');
        
        // Sempre reconfigurar ao iniciar (pode mudar de página)
        this.obterRestauranteId();
        this.configurarElementos();
        this.configurarEventos();
        this.carregarPedidos();
    },

    obterRestauranteId() {
    const id = localStorage.getItem('restaurante_id');
        this.config.restaurante_id = parseInt(id, 10);
    
        if (!this.config.restaurante_id || isNaN(this.config.restaurante_id)) {
            alert('Sessão inválida. Redirecionando para login...');
    window.location.href = '../paginas/login.html';
            return;
        }
    },

    configurarElementos() {
        const elementosConfig = {
            // Filtros
            statusFilter: document.getElementById('statusFilter'),
            dataFilter: document.getElementById('dataFilter'),
            limparFiltros: document.getElementById('limparFiltros'),
            atualizarPedidos: document.getElementById('atualizarPedidos'),
            
            // KPIs
            totalPedidos: document.getElementById('totalPedidos'),
            pendentes: document.getElementById('pendentes'),
            emPreparo: document.getElementById('emPreparo'),
            entregues: document.getElementById('entregues'),
            
            // Tabela
            tableBody: document.getElementById('pedidosTableBody'),
            loadingState: document.getElementById('loadingState'),
            emptyState: document.getElementById('emptyState'),
            
            // Modal
            modal: document.getElementById('modalDetalhes'),
            modalTitulo: document.getElementById('modalTitulo'),
            fecharModal: document.getElementById('fecharModal'),
            
            // Detalhes do pedido
            detalheCliente: document.getElementById('detalheCliente'),
            detalheTelefone: document.getElementById('detalheTelefone'),
            detalheDataHora: document.getElementById('detalheDataHora'),
            detalheStatus: document.getElementById('detalheStatus'),
            detalheItens: document.getElementById('detalheItens'),
            detalheObservacoes: document.getElementById('detalheObservacoes'),
            detalheTotal: document.getElementById('detalheTotal'),
            
            // Atualização de status
            novoStatus: document.getElementById('novoStatus'),
            atualizarStatus: document.getElementById('atualizarStatus')
        };
        
        // Verificar se elementos críticos existem
        if (!elementosConfig.statusFilter || !elementosConfig.tableBody) {
            console.error('❌ Elementos DOM não encontrados. Aguardando...');
            setTimeout(() => this.configurarElementos(), 100);
            return;
        }
        
        this.config.elementos = elementosConfig;
        console.log('✅ Elementos configurados com sucesso');
    },

    configurarEventos() {
        const { elementos } = this.config;
        
        // Verificar se elementos existem antes de adicionar listeners
        if (!elementos.statusFilter || !elementos.fecharModal) {
            console.error('❌ Elementos não configurados ainda. Tentando novamente...');
            setTimeout(() => this.configurarEventos(), 100);
            return;
        }
        
        // Remover listeners antigos se existirem
        const novosEventos = {
            onStatusFilterChange: () => this.aplicarFiltros(),
            onDataFilterChange: () => this.aplicarFiltros(),
            onLimparClick: () => this.limparFiltros(),
            onAtualizarClick: () => this.carregarPedidos(),
            onFecharModalClick: () => this.fecharModal(),
            onModalClick: (e) => {
                if (e.target === elementos.modal) this.fecharModal();
            },
            onAtualizarStatusClick: () => this.atualizarStatusPedido(),
            onEscapeKey: (e) => {
                if (e.key === 'Escape') this.fecharModal();
            }
        };
        
        // Armazenar referências para poder remover depois
        this._eventHandlers = novosEventos;
        
        // Filtros
        elementos.statusFilter.addEventListener('change', novosEventos.onStatusFilterChange);
        elementos.dataFilter.addEventListener('change', novosEventos.onDataFilterChange);
        elementos.limparFiltros.addEventListener('click', novosEventos.onLimparClick);
        elementos.atualizarPedidos.addEventListener('click', novosEventos.onAtualizarClick);
        
        // Modal
        elementos.fecharModal.addEventListener('click', novosEventos.onFecharModalClick);
        elementos.modal.addEventListener('click', novosEventos.onModalClick);
        
        // Atualização de status
        elementos.atualizarStatus.addEventListener('click', novosEventos.onAtualizarStatusClick);
        
        // Atalhos de teclado (apenas uma vez)
        if (!this._escapeListener) {
            document.addEventListener('keydown', novosEventos.onEscapeKey);
            this._escapeListener = novosEventos.onEscapeKey;
        }
        
        console.log('✅ Eventos configurados com sucesso');
    },

    // =============================
    // CARREGAMENTO DE DADOS
    // =============================
    
    async carregarPedidos() {
        try {
            this.mostrarLoading(true);
            
            const params = new URLSearchParams();
            if (this.state.filtros.status) {
                params.append('status', this.state.filtros.status);
            }
            if (this.state.filtros.data) {
                params.append('data_inicio', this.state.filtros.data);
                params.append('data_fim', this.state.filtros.data);
            }
            
            const url = `${this.config.API_BASE_URL}/pedidos/restaurante/${this.config.restaurante_id}?${params}`;
            const response = await fetch(url);
        
        if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.state.pedidos = data.data;
                this.renderizarPedidos();
                this.atualizarKPIs();
            } else {
                throw new Error(data.message || 'Erro ao carregar pedidos');
            }
            
    } catch (error) {
            this.mostrarErro(`Erro ao carregar pedidos: ${error.message}`);
            this.state.pedidos = [];
            this.renderizarPedidos();
        } finally {
            this.mostrarLoading(false);
        }
    },

    async carregarDetalhesPedido(pedidoId) {
        try {
            const url = `${this.config.API_BASE_URL}/pedidos/${pedidoId}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                return data.data;
            } else {
                throw new Error(data.message || 'Erro ao carregar detalhes');
            }
            
        } catch (error) {
            this.mostrarErro(`Erro ao carregar detalhes: ${error.message}`);
            return null;
        }
    },

    // =============================
    // RENDERIZAÇÃO
    // =============================
    
    renderizarPedidos() {
        const { tableBody, emptyState } = this.config.elementos;
        
        if (this.state.pedidos.length === 0) {
            tableBody.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        
        tableBody.innerHTML = this.state.pedidos.map(pedido => {
            // CORREÇÃO: Extrair nome do cliente de diferentes formatos possíveis
            let clienteNome = 'N/A';
            if (pedido.cliente && typeof pedido.cliente === 'object') {
                clienteNome = pedido.cliente.nome || pedido.cliente.nomeCliente || 'N/A';
            } else if (pedido.cliente_nome) {
                clienteNome = pedido.cliente_nome;
            }
            
            // CORREÇÃO: Extrair data do pedido de diferentes formatos possíveis
            let dataPedido = pedido.data_pedido || pedido.criadoEm || pedido.criado_em || new Date().toISOString();
            
            // CORREÇÃO: Calcular valor total se não existir
            let valorTotal = pedido.valor_total || pedido.valor || pedido.valorTotal || 0;
            if (valorTotal == 0 && pedido.itens && Array.isArray(pedido.itens)) {
                // Tentar calcular pela soma dos itens
                valorTotal = pedido.itens.reduce((total, item) => {
                    const quantidade = item.quantidade || 0;
                    let preco = 0;
                    if (item.itemRestaurante && item.itemRestaurante.preco) {
                        preco = item.itemRestaurante.preco;
                    } else if (item.item_restaurante && item.item_restaurante.preco) {
                        preco = item.item_restaurante.preco;
                    } else if (item.preco) {
                        preco = item.preco;
                    }
                    return total + (quantidade * preco);
                }, 0);
            }
            
            return `
            <tr onclick="PedidosApp.abrirDetalhesPedido(${pedido.id})" data-pedido-id="${pedido.id}">
                <td><strong>#${pedido.id}</strong></td>
                <td>${clienteNome}</td>
                <td>${this.formatarDataHora(dataPedido)}</td>
                <td><strong>${this.formatarMoeda(valorTotal)}</strong></td>
                <td><span class="status-badge status-${pedido.status}">${this.formatarStatus(pedido.status)}</span></td>
                <td>
                    <button onclick="event.stopPropagation(); PedidosApp.abrirDetalhesPedido(${pedido.id})" 
                            class="btn-primary" style="padding: 4px 8px; font-size: 12px;">
                        Ver Detalhes
                    </button>
            </td>
            </tr>
        `;
        }).join('');
    },

    atualizarKPIs() {
        const { elementos } = this.config;
        const pedidos = this.state.pedidos;
        
        const kpis = {
            total: pedidos.length,
            // Mapear diferentes formatos de status
            aguardando: pedidos.filter(p => {
                const status = (p.status || '').toLowerCase();
                return status === 'pendente' || status === 'aguardando' || status === 'novo';
            }).length,
            em_preparo: pedidos.filter(p => {
                const status = (p.status || '').toLowerCase();
                return status === 'em_preparo' || status === 'em preparo';
            }).length,
            entregue: pedidos.filter(p => {
                const status = (p.status || '').toLowerCase();
                return status === 'entregue' || status === 'concluido' || status === 'concluído' || 
                       status === 'finalizado' || status === 'pronto';
            }).length,
            cancelado: pedidos.filter(p => {
                const status = (p.status || '').toLowerCase();
                return status === 'cancelado';
            }).length
        };
        
        elementos.totalPedidos.textContent = kpis.total;
        elementos.pendentes.textContent = kpis.aguardando;
        elementos.emPreparo.textContent = kpis.em_preparo;
        elementos.entregues.textContent = kpis.entregue;
        
        // Atualizar cancelados se o elemento existir
        const cancelados = document.getElementById('cancelados');
        if (cancelados) {
            cancelados.textContent = kpis.cancelado;
        }
    },

    // =============================
    // MODAL DE DETALHES
    // =============================
    
    async abrirDetalhesPedido(pedidoId) {
        const detalhes = await this.carregarDetalhesPedido(pedidoId);
        if (!detalhes) return;
        
        this.state.pedidoAtual = detalhes;
        this.renderizarDetalhes(detalhes);
        this.config.elementos.modal.style.display = 'flex';
    },

    renderizarDetalhes(detalhes) {
        const { elementos } = this.config;
        const { pedido, itens } = detalhes;
        
        // CORREÇÃO: Extrair dados do pedido de diferentes formatos possíveis
        const clienteObj = pedido.cliente || {};
        const clienteNome = clienteObj.nome || clienteObj.nomeCliente || 'N/A';
        const clienteTelefone = clienteObj.telefone || 'Não informado';
        const dataPedido = pedido.data_pedido || pedido.criadoEm || pedido.criado_em || new Date().toISOString();
        const valorTotal = pedido.valor_total || pedido.valor || pedido.valorTotal || 0;
        
        // Informações básicas
        elementos.modalTitulo.textContent = `Pedido #${pedido.id}`;
        elementos.detalheCliente.textContent = clienteNome;
        elementos.detalheTelefone.textContent = clienteTelefone;
        elementos.detalheDataHora.textContent = this.formatarDataHora(dataPedido);
        elementos.detalheStatus.textContent = this.formatarStatus(pedido.status);
        elementos.detalheStatus.className = `info-value status-badge status-${pedido.status}`;
        elementos.detalheTotal.textContent = this.formatarMoeda(valorTotal);
        
        // Observações
        if (pedido.observacoes) {
            elementos.detalheObservacoes.textContent = pedido.observacoes;
            document.getElementById('observacoesSection').style.display = 'block';
        } else {
            document.getElementById('observacoesSection').style.display = 'none';
        }
        
        // CORREÇÃO: Itens do pedido - extrair dados de diferentes formatos possíveis
        elementos.detalheItens.innerHTML = (itens || []).map(item => {
            const nome = item.nome || item.item_nome || 'Item sem nome';
            const preco = item.preco || item.item_preco || item.valorUnitario || 0;
            const quantidade = item.quantidade || 0;
            const observacoes = item.observacoes || item.observacoes_item || null;
            
            return `
            <div class="item-pedido">
                <div class="item-info">
                    <div class="item-nome">${nome}</div>
                    <div class="item-preco">${this.formatarMoeda(preco)} cada</div>
                    ${observacoes ? `<div class="item-obs">Obs: ${observacoes}</div>` : ''}
                </div>
                <div class="item-quantidade">${quantidade}x</div>
            </div>
        `;
        }).join('');
        
        // Status atual no select - mapear para o formato do select
        const statusAtual = pedido.status || '';
        const statusMap = {
            'pendente': 'pendente',
            'PENDENTE': 'pendente',
            'novo': 'pendente',
            'NOVO': 'pendente',
            'em_preparo': 'em_preparo',
            'EM_PREPARO': 'em_preparo',
            'pronto': 'pronto',
            'PRONTO': 'pronto',
            'concluido': 'concluido',
            'concluído': 'concluido',
            'CONCLUIDO': 'concluido',
            'CONCLUÍDO': 'concluido',
            'finalizado': 'concluido',
            'FINALIZADO': 'concluido',
            'entregue': 'entregue',
            'ENTREGUE': 'entregue',
            'cancelado': 'cancelado',
            'CANCELADO': 'cancelado'
        };
        
        const statusParaSelect = statusMap[statusAtual] || statusAtual.toLowerCase() || 'pendente';
        elementos.novoStatus.value = statusParaSelect;
        
        console.log(`[PEDIDOS] Status atual do pedido: ${statusAtual} -> mapeado para select: ${statusParaSelect}`);
    },

    fecharModal() {
        this.config.elementos.modal.style.display = 'none';
        this.state.pedidoAtual = null;
    },

    // =============================
    // FILTROS
    // =============================
    
    aplicarFiltros() {
        const { elementos } = this.config;
        
        this.state.filtros = {
            status: elementos.statusFilter.value,
            data: elementos.dataFilter.value
        };
        
        this.carregarPedidos();
    },

    limparFiltros() {
        const { elementos } = this.config;
        
        elementos.statusFilter.value = '';
        elementos.dataFilter.value = '';
        
        this.state.filtros = { status: '', data: '' };
        this.carregarPedidos();
    },

    // =============================
    // ATUALIZAÇÃO DE STATUS
    // =============================
    
    async atualizarStatusPedido() {
        if (!this.state.pedidoAtual) {
            this.mostrarErro('Nenhum pedido selecionado');
            return;
        }
        
        const novoStatus = this.config.elementos.novoStatus.value;
        const pedidoId = this.state.pedidoAtual.pedido.id;
        
        if (!novoStatus) {
            this.mostrarErro('Por favor, selecione um status');
            return;
        }
        
        console.log(`[PEDIDOS] Atualizando status do pedido ${pedidoId} para: ${novoStatus}`);
        
        try {
            const response = await fetch(`${this.config.API_BASE_URL}/pedidos/${pedidoId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: novoStatus })
            });
            
            // Verificar se a resposta é ok antes de parsear JSON
            if (!response.ok) {
                let errorMsg = `Erro HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.message || errorData.error || errorMsg;
                } catch (e) {
                    errorMsg = `Erro ao atualizar status (Status ${response.status})`;
                }
                console.error(`[PEDIDOS] Erro HTTP: ${response.status} - ${errorMsg}`);
                throw new Error(errorMsg);
            }
            
            const data = await response.json();
            
            console.log(`[PEDIDOS] Resposta da API:`, data);
            
            if (data.status === 'success') {
                this.mostrarSucesso('Status atualizado com sucesso!');
                this.fecharModal();
                // Aguardar um pouco antes de recarregar para garantir que a atualização foi processada
                setTimeout(() => {
                    this.carregarPedidos(); // Recarregar lista
                }, 500);
            } else {
                const errorMsg = data.message || data.error || 'Erro ao atualizar status';
                console.error(`[PEDIDOS] Erro na resposta: ${errorMsg}`);
                throw new Error(errorMsg);
            }
        
        } catch (error) {
            console.error(`[PEDIDOS] Erro ao atualizar status:`, error);
            // Evitar mensagem duplicada
            const errorMsg = error.message || 'Erro ao atualizar status';
            if (!errorMsg.includes('Erro ao atualizar status')) {
                this.mostrarErro(errorMsg);
            } else {
                this.mostrarErro('Não foi possível atualizar o status. Verifique os logs do servidor.');
            }
        }
    },

    // =============================
    // UTILITÁRIOS
    // =============================
    
    formatarDataHora(dataISO) {
        const data = new Date(dataISO);
        return data.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    },

    formatarStatus(status) {
        const statusMap = {
           
            'em_preparo': 'Em Preparo',
            'EM_PREPARO': 'Em Preparo',
            
            'concluido': 'Concluído',
            'concluído': 'Concluído',
            'CONCLUIDO': 'Concluído',
            'CONCLUÍDO': 'Concluído',
           
            
            'cancelado': 'Cancelado',
            'CANCELADO': 'Cancelado'
        };
        
        // Buscar com case-sensitive primeiro
        if (statusMap[status]) {
            return statusMap[status];
        }
        
        // Buscar com case-insensitive
        const statusLower = status?.toLowerCase();
        for (const [key, value] of Object.entries(statusMap)) {
            if (key.toLowerCase() === statusLower) {
                return value;
            }
        }
        
        // Fallback: retornar o status original capitalizado
        return status?.charAt(0).toUpperCase() + status?.slice(1).toLowerCase() || status;
    },

    mostrarLoading(mostrar) {
        const { loadingState } = this.config.elementos;
        
        if (mostrar) {
            loadingState.classList.remove('hidden');
            } else {
            loadingState.classList.add('hidden');
        }
    },

    mostrarErro(mensagem) {
        // Toast simples para erros
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            background: #fee2e2; color: #991b1b; padding: 12px 20px;
            border-radius: 8px; border-left: 4px solid #dc2626;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-width: 400px; word-wrap: break-word;
        `;
        toast.textContent = mensagem;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 5000);
    },

    mostrarSucesso(mensagem) {
        // Toast simples para sucesso
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            background: #d1fae5; color: #065f46; padding: 12px 20px;
            border-radius: 8px; border-left: 4px solid #10b981;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-width: 400px; word-wrap: break-word;
        `;
        toast.textContent = mensagem;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 3000);
    }
};

// =============================
// INICIALIZAÇÃO AUTOMÁTICA
// =============================

// Expor para uso global
window.PedidosApp = PedidosApp;

// NÃO inicializar automaticamente - deixar index.html chamar via loadPage()
// Isso evita múltiplas inicializações ao navegar entre páginas
console.log('✅ PedidosApp registrado globalmente. Aguardando inicialização via loadPage().');