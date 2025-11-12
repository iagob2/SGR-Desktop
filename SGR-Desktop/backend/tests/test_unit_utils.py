"""
🧪 TESTES DE UNIDADE - Utilitários

Foco: Testar funções puras e isoladas (Caixa-Branca)
Princípio FIRST: Fast, Independent, Repeatable, Self-validating, Timely
"""

import pytest
from app.utils.status import is_status_concluido


class TestIsStatusConcluido:
    """
    Teste: Verificação de Status de Pedidos
    
    Objetivo: Garantir que a função is_status_concluido() identifica corretamente
    quais status indicam que um pedido foi concluído/finalizado.
    
    Cenários testados:
    - Status concluídos válidos (FINALIZADO, CONCLUIDO, ENTREGUE)
    - Variações de maiúsculas/minúsculas
    - Status não concluídos (PENDENTE, EM_PREPARO, CANCELADO)
    - Valores inválidos (None, string vazia, espaços)
    """
    
    def test_status_finalizado_deve_retornar_true(self):
        """Teste: Status 'FINALIZADO' deve ser considerado concluído"""
        assert is_status_concluido('FINALIZADO') is True
        assert is_status_concluido('finalizado') is True  # Case insensitive
        assert is_status_concluido('Finalizado') is True
    
    def test_status_concluido_deve_retornar_true(self):
        """Teste: Status 'CONCLUIDO' e variações devem ser considerados concluídos"""
        assert is_status_concluido('CONCLUIDO') is True
        assert is_status_concluido('CONCLUÍDO') is True  # Com acento
        assert is_status_concluido('concluido') is True
        assert is_status_concluido('Concluído') is True
    
    def test_status_entregue_deve_retornar_true(self):
        """Teste: Status 'ENTREGUE' deve ser considerado concluído"""
        assert is_status_concluido('ENTREGUE') is True
        assert is_status_concluido('entregue') is True
    
    def test_status_pendente_deve_retornar_false(self):
        """Teste: Status 'PENDENTE' NÃO deve ser considerado concluído"""
        assert is_status_concluido('PENDENTE') is False
        assert is_status_concluido('pendente') is False
    
    def test_status_em_preparo_deve_retornar_false(self):
        """Teste: Status 'EM_PREPARO' NÃO deve ser considerado concluído"""
        assert is_status_concluido('EM_PREPARO') is False
        assert is_status_concluido('PRONTO') is False
        assert is_status_concluido('CANCELADO') is False
    
    def test_status_none_deve_retornar_false(self):
        """Teste: Status None ou vazio deve retornar False"""
        assert is_status_concluido(None) is False
        assert is_status_concluido('') is False
        assert is_status_concluido('   ') is False  # Apenas espaços
    
    def test_status_com_espacos_deve_normalizar(self):
        """Teste: Status com espaços devem ser normalizados corretamente"""
        assert is_status_concluido('  FINALIZADO  ') is True
        assert is_status_concluido('  PENDENTE  ') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

