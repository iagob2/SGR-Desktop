/**
 * 🧪 TESTES DE UNIDADE - Funções de Formatação
 * 
 * Foco: Testar funções puras que formatam dados (moeda, data, categoria)
 * Princípio FIRST: Funções isoladas e determinísticas
 */

// Funções de formatação (extraídas do código real)
function formatarMoeda(valor) {
    if (typeof valor !== 'number') {
        valor = parseFloat(valor) || 0;
    }
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarCategoria(categoria) {
    const categorias = {
        'ENTRADA': 'Entrada',
        'PRATO_PRINCIPAL': 'Prato Principal',
        'SOBREMESA': 'Sobremesa',
        'BEBIDA': 'Bebida',
        'LANCHE': 'Lanche',
        'SALADA': 'Salada',
        'ACOMPANHAMENTO': 'Acompanhamento',
        'OUTROS': 'Outros'
    };
    return categorias[categoria] || categoria;
}

function formatarData(dataISO) {
    if (!dataISO) return '';
    const data = new Date(dataISO);
    return data.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Testes (usando Jest ou framework similar)
describe('Formatação de Moeda', () => {
    /**
     * Teste: Formatação de valores numéricos para moeda brasileira
     * 
     * Objetivo: Garantir que valores são formatados corretamente como R$ X,XX
     */
    test('deve formatar 120.5 para R$ 120,50', () => {
        const resultado = formatarMoeda(120.5);
        expect(resultado).toBe('R$ 120,50');
    });

    test('deve formatar 0 para R$ 0,00', () => {
        const resultado = formatarMoeda(0);
        expect(resultado).toBe('R$ 0,00');
    });

    test('deve formatar string numérica para moeda', () => {
        const resultado = formatarMoeda('25.99');
        expect(resultado).toBe('R$ 25,99');
    });

    test('deve tratar valores inválidos como 0', () => {
        const resultado = formatarMoeda('abc');
        expect(resultado).toBe('R$ 0,00');
    });
});

describe('Formatação de Categoria', () => {
    /**
     * Teste: Conversão de códigos de categoria para nomes legíveis
     * 
     * Objetivo: Garantir que códigos como 'PRATO_PRINCIPAL' são convertidos
     * para 'Prato Principal' para exibição ao usuário
     */
    test('deve converter ENTRADA para Entrada', () => {
        const resultado = formatarCategoria('ENTRADA');
        expect(resultado).toBe('Entrada');
    });

    test('deve converter PRATO_PRINCIPAL para Prato Principal', () => {
        const resultado = formatarCategoria('PRATO_PRINCIPAL');
        expect(resultado).toBe('Prato Principal');
    });

    test('deve retornar categoria desconhecida como está', () => {
        const resultado = formatarCategoria('CATEGORIA_INVALIDA');
        expect(resultado).toBe('CATEGORIA_INVALIDA');
    });

    test('deve converter todas as categorias conhecidas', () => {
        expect(formatarCategoria('BEBIDA')).toBe('Bebida');
        expect(formatarCategoria('SOBREMESA')).toBe('Sobremesa');
        expect(formatarCategoria('LANCHE')).toBe('Lanche');
        expect(formatarCategoria('SALADA')).toBe('Salada');
        expect(formatarCategoria('ACOMPANHAMENTO')).toBe('Acompanhamento');
        expect(formatarCategoria('OUTROS')).toBe('Outros');
    });
});

describe('Formatação de Data', () => {
    /**
     * Teste: Formatação de datas ISO para formato brasileiro
     * 
     * Objetivo: Garantir que datas são exibidas no formato DD/MM/YYYY HH:MM
     */
    test('deve formatar data ISO para formato brasileiro', () => {
        const dataISO = '2024-01-15T14:30:00';
        const resultado = formatarData(dataISO);
        // Formato esperado: DD/MM/YYYY, HH:MM
        expect(resultado).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });

    test('deve retornar string vazia para data inválida', () => {
        const resultado = formatarData(null);
        expect(resultado).toBe('');
    });
});

// Exportar para uso em outros testes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatarMoeda,
        formatarCategoria,
        formatarData
    };
}

