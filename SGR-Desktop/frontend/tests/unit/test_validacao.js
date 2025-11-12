/**
 * 🧪 TESTES DE UNIDADE - Validação de Formulários
 * 
 * Foco: Testar lógica de validação de dados de entrada
 */

// Funções de validação (extraídas do código real)
function validarFormularioCardapio(dados) {
    /**
     * Valida dados do formulário de cardápio
     * 
     * Campos obrigatórios:
     * - nome: string não vazia
     * - preco: número > 0
     * - categoria: string não vazia
     * - restaurante_id: número válido
     */
    const erros = [];

    if (!dados.nome || dados.nome.trim() === '') {
        erros.push('Nome é obrigatório');
    }

    if (!dados.preco || parseFloat(dados.preco) <= 0) {
        erros.push('Preço deve ser maior que zero');
    }

    if (!dados.categoria || dados.categoria.trim() === '') {
        erros.push('Categoria é obrigatória');
    }

    if (!dados.restaurante_id || isNaN(parseInt(dados.restaurante_id))) {
        erros.push('ID do restaurante é obrigatório');
    }

    return {
        valido: erros.length === 0,
        erros: erros
    };
}

function validarEmail(email) {
    /**
     * Valida formato de email
     */
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Testes
describe('Validação de Formulário de Cardápio', () => {
    /**
     * Teste: Validação de campos obrigatórios do formulário
     * 
     * Objetivo: Garantir que todos os campos obrigatórios são validados
     */
    test('deve validar formulário completo corretamente', () => {
        const dados = {
            nome: 'Hambúrguer',
            preco: 25.50,
            categoria: 'PRATO_PRINCIPAL',
            restaurante_id: 1
        };

        const resultado = validarFormularioCardapio(dados);
        expect(resultado.valido).toBe(true);
        expect(resultado.erros.length).toBe(0);
    });

    test('deve rejeitar formulário sem nome', () => {
        const dados = {
            nome: '',
            preco: 25.50,
            categoria: 'PRATO_PRINCIPAL',
            restaurante_id: 1
        };

        const resultado = validarFormularioCardapio(dados);
        expect(resultado.valido).toBe(false);
        expect(resultado.erros).toContain('Nome é obrigatório');
    });

    test('deve rejeitar formulário com preço inválido', () => {
        const dados = {
            nome: 'Hambúrguer',
            preco: 0,
            categoria: 'PRATO_PRINCIPAL',
            restaurante_id: 1
        };

        const resultado = validarFormularioCardapio(dados);
        expect(resultado.valido).toBe(false);
        expect(resultado.erros).toContain('Preço deve ser maior que zero');
    });

    test('deve rejeitar formulário sem categoria', () => {
        const dados = {
            nome: 'Hambúrguer',
            preco: 25.50,
            categoria: '',
            restaurante_id: 1
        };

        const resultado = validarFormularioCardapio(dados);
        expect(resultado.valido).toBe(false);
        expect(resultado.erros).toContain('Categoria é obrigatória');
    });

    test('deve rejeitar formulário com múltiplos erros', () => {
        const dados = {
            nome: '',
            preco: -10,
            categoria: '',
            restaurante_id: null
        };

        const resultado = validarFormularioCardapio(dados);
        expect(resultado.valido).toBe(false);
        expect(resultado.erros.length).toBeGreaterThan(1);
    });
});

describe('Validação de Email', () => {
    /**
     * Teste: Validação de formato de email
     * 
     * Objetivo: Garantir que emails são validados corretamente
     */
    test('deve validar email válido', () => {
        expect(validarEmail('teste@exemplo.com')).toBe(true);
        expect(validarEmail('usuario@dominio.com.br')).toBe(true);
    });

    test('deve rejeitar email inválido', () => {
        expect(validarEmail('email-invalido')).toBe(false);
        expect(validarEmail('sem@dominio')).toBe(false);
        expect(validarEmail('@dominio.com')).toBe(false);
        expect(validarEmail('usuario@')).toBe(false);
    });
});

// Exportar para uso em outros testes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validarFormularioCardapio,
        validarEmail
    };
}

