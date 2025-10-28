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
        
        tableBody.innerHTML = this.state.pedidos.map(pedido => `
            <tr onclick="PedidosApp.abrirDetalhesPedido(${pedido.id})" data-pedido-id="${pedido.id}">
                <td><strong>#${pedido.id}</strong></td>
                <td>${pedido.cliente.nome}</td>
                <td>${this.formatarDataHora(pedido.data_pedido)}</td>
                <td><strong>${this.formatarMoeda(pedido.valor_total)}</strong></td>
                <td><span class="status-badge status-${pedido.status}">${this.formatarStatus(pedido.status)}</span></td>
                <td>
                    <button onclick="event.stopPropagation(); PedidosApp.abrirDetalhesPedido(${pedido.id})" 
                            class="btn-primary" style="padding: 4px 8px; font-size: 12px;">
                        Ver Detalhes
                    </button>
            </td>
            </tr>
        `).join('');
    },

    atualizarKPIs() {
        const { elementos } = this.config;
        const pedidos = this.state.pedidos;
        
        const kpis = {
            total: pedidos.length,
            // Mapear diferentes formatos de status
            aguardando: pedidos.filter(p => 
                p.status === 'pendente' || 
                p.status === 'AGUARDANDO' || 
                p.status?.toLowerCase() === 'aguardando'
            ).length,
            em_preparo: pedidos.filter(p => 
                p.status === 'em_preparo' || 
                p.status === 'EM_PREPARO' ||
                p.status?.toLowerCase() === 'em_preparo'
            ).length,
            entregue: pedidos.filter(p => 
                p.status === 'entregue' || 
                p.status === 'FINALIZADO' ||
                p.status === 'ENTREGUE' ||
                p.status?.toLowerCase() === 'entregue' ||
                p.status?.toLowerCase() === 'finalizado'
            ).length,
            cancelado: pedidos.filter(p => 
                p.status === 'cancelado' || 
                p.status === 'CANCELADO' ||
                p.status?.toLowerCase() === 'cancelado'
            ).length
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
        
        // Informações básicas
        elementos.modalTitulo.textContent = `Pedido #${pedido.id}`;
        elementos.detalheCliente.textContent = pedido.cliente.nome;
        elementos.detalheTelefone.textContent = pedido.cliente.telefone || 'Não informado';
        elementos.detalheDataHora.textContent = this.formatarDataHora(pedido.data_pedido);
        elementos.detalheStatus.textContent = this.formatarStatus(pedido.status);
        elementos.detalheStatus.className = `info-value status-badge status-${pedido.status}`;
        elementos.detalheTotal.textContent = this.formatarMoeda(pedido.valor_total);
        
        // Observações
        if (pedido.observacoes) {
            elementos.detalheObservacoes.textContent = pedido.observacoes;
            document.getElementById('observacoesSection').style.display = 'block';
        } else {
            document.getElementById('observacoesSection').style.display = 'none';
        }
        
        // Itens do pedido
        elementos.detalheItens.innerHTML = itens.map(item => `
            <div class="item-pedido">
                <div class="item-info">
                    <div class="item-nome">${item.nome || item.item_nome}</div>
                    <div class="item-preco">${this.formatarMoeda(item.preco || item.item_preco)} cada</div>
                    ${item.observacoes || item.observacoes_item ? `<div class="item-obs">Obs: ${item.observacoes || item.observacoes_item}</div>` : ''}
                    </div>
                <div class="item-quantidade">${item.quantidade}x</div>
                    </div>
        `).join('');
        
        // Status atual no select
        elementos.novoStatus.value = pedido.status;
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
        if (!this.state.pedidoAtual) return;
        
        const novoStatus = this.config.elementos.novoStatus.value;
        const pedidoId = this.state.pedidoAtual.pedido.id;
        
        try {
            const response = await fetch(`${this.config.API_BASE_URL}/pedidos/${pedidoId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: novoStatus })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.mostrarSucesso('Status atualizado com sucesso!');
                this.fecharModal();
                this.carregarPedidos(); // Recarregar lista
            } else {
                throw new Error(data.message || 'Erro ao atualizar status');
            }
        
    } catch (error) {
            this.mostrarErro(`Erro ao atualizar status: ${error.message}`);
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
            'pendente': 'Pendente',
            'aguardando': 'Aguardando',
            'AGUARDANDO': 'Aguardando',
            'em_preparo': 'Em Preparo',
            'EM_PREPARO': 'Em Preparo',
            'pronto': 'Pronto',
            'entregue': 'Entregue',
            'ENTREGUE': 'Entregue',
            'finalizado': 'Finalizado',
            'FINALIZADO': 'Finalizado',
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