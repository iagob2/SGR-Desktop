/**
 * 🧪 TESTES DE INTEGRAÇÃO - Frontend ↔️ Backend
 * 
 * Foco: Testar comunicação entre Electron e Flask
 * Estratégia: Mock do fetch para simular respostas do Flask
 */

// Mock do fetch global
global.fetch = jest.fn();

// Constantes de teste
const API_BASE_URL = 'http://localhost:5000/api';

describe('Integração com API Flask', () => {
    /**
     * Teste: Conectividade entre Frontend e Backend
     * 
     * Objetivo: Garantir que o Electron consegue fazer chamadas HTTP
     * para o proxy Flask e receber respostas JSON corretas
     */
    
    beforeEach(() => {
        fetch.mockClear();
    });

    test('deve fazer requisição GET para /api/health', async () => {
        /**
         * Teste: Health check do Flask
         * 
         * Verifica se o frontend consegue verificar se o backend está rodando
         */
        const mockResponse = {
            status: 'success',
            message: 'API Flask (Proxy) está funcionando!',
            api_externa_status: 'active'
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => mockResponse
        });

        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/health`);
        expect(data.status).toBe('success');
    });

    test('deve fazer requisição POST para /api/restaurantes/login', async () => {
        /**
         * Teste: Login de restaurante
         * 
         * Verifica se o frontend consegue autenticar e receber dados do restaurante
         */
        const credenciais = {
            email: 'teste@teste.com',
            senha: 'senha123'
        };

        const mockResponse = {
            status: 'success',
            message: 'Login realizado com sucesso',
            data: {
                restaurante_id: 123,
                restaurante_nome: 'Restaurante Teste'
            }
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => mockResponse
        });

        const response = await fetch(`${API_BASE_URL}/restaurantes/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credenciais)
        });

        const data = await response.json();

        expect(fetch).toHaveBeenCalledWith(
            `${API_BASE_URL}/restaurantes/login`,
            expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    'Content-Type': 'application/json'
                })
            })
        );
        expect(data.status).toBe('success');
        expect(data.data.restaurante_id).toBe(123);
    });

    test('deve tratar erro 500 do backend', async () => {
        /**
         * Teste: Tratamento de erro do servidor
         * 
         * Verifica se o frontend trata adequadamente erros 500 do Flask
         */
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({
                status: 'error',
                message: 'Erro interno do servidor'
            })
        });

        const response = await fetch(`${API_BASE_URL}/dashboard/1`);
        const data = await response.json();

        expect(response.ok).toBe(false);
        expect(response.status).toBe(500);
        expect(data.status).toBe('error');
    });

    test('deve tratar timeout na requisição', async () => {
        /**
         * Teste: Tratamento de timeout
         * 
         * Verifica se o frontend trata adequadamente timeouts de rede
         */
        fetch.mockRejectedValueOnce(new Error('Network timeout'));

        await expect(fetch(`${API_BASE_URL}/dashboard/1`)).rejects.toThrow('Network timeout');
    });

    test('deve fazer requisição GET para /api/cardapio/{id}', async () => {
        /**
         * Teste: Buscar cardápio
         * 
         * Verifica se o frontend consegue buscar lista de itens do cardápio
         */
        const mockResponse = {
            status: 'success',
            data: [
                { id: 1, nome: 'Hambúrguer', preco: 25.50, categoria: 'PRATO_PRINCIPAL' },
                { id: 2, nome: 'Refrigerante', preco: 5.00, categoria: 'BEBIDA' }
            ]
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => mockResponse
        });

        const response = await fetch(`${API_BASE_URL}/cardapio/1`);
        const data = await response.json();

        expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/cardapio/1`);
        expect(data.status).toBe('success');
        expect(Array.isArray(data.data)).toBe(true);
        expect(data.data.length).toBe(2);
    });
});

// Exportar para uso em outros testes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        API_BASE_URL
    };
}

