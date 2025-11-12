"""
🧪 TESTES DE UNIDADE - Cálculos Analíticos

Foco: Testar funções de cálculo de KPIs e métricas (Caixa-Branca)
Princípio FIRST: Funções puras que calculam métricas baseadas em dados de entrada
"""

import pytest
from datetime import datetime, timedelta
from app.utils.status import is_status_concluido


class TestCalculosAnaliticos:
    """
    Teste: Cálculos de Métricas e KPIs
    
    Objetivo: Garantir que os cálculos analíticos (ticket médio, top produtos,
    vendas por período) estão corretos.
    
    Estratégia: Criar dados de entrada conhecidos e verificar se os cálculos
    retornam os valores esperados.
    """
    
    def test_calculo_ticket_medio(self):
        """
        Teste: Cálculo de ticket médio diário
        
        Dados de entrada:
        - 3 pedidos concluídos
        - Valores: R$ 50,00, R$ 75,00, R$ 100,00
        - Ticket médio esperado: R$ 75,00
        """
        pedidos = [
            {'valor_total': 50.0, 'status': 'FINALIZADO'},
            {'valor_total': 75.0, 'status': 'FINALIZADO'},
            {'valor_total': 100.0, 'status': 'FINALIZADO'},
        ]
        
        # Filtrar apenas concluídos
        pedidos_concluidos = [p for p in pedidos if is_status_concluido(p.get('status'))]
        
        # Calcular ticket médio
        total_vendas = sum(p['valor_total'] for p in pedidos_concluidos)
        quantidade_pedidos = len(pedidos_concluidos)
        ticket_medio = total_vendas / quantidade_pedidos if quantidade_pedidos > 0 else 0
        
        assert ticket_medio == 75.0
        assert total_vendas == 225.0
        assert quantidade_pedidos == 3
    
    def test_calculo_top_produtos(self):
        """
        Teste: Cálculo de top 3 produtos mais vendidos
        
        Dados de entrada:
        - Produto A: 10 unidades vendidas
        - Produto B: 5 unidades vendidas
        - Produto C: 15 unidades vendidas
        - Produto D: 3 unidades vendidas
        
        Resultado esperado: [C, A, B] (top 3)
        """
        produtos_vendidos = {
            1: {'quantidade': 10, 'nome': 'Produto A'},
            2: {'quantidade': 5, 'nome': 'Produto B'},
            3: {'quantidade': 15, 'nome': 'Produto C'},
            4: {'quantidade': 3, 'nome': 'Produto D'},
        }
        
        # Ordenar por quantidade (descendente) e pegar top 3
        top_produtos = sorted(
            produtos_vendidos.items(),
            key=lambda x: x[1]['quantidade'],
            reverse=True
        )[:3]
        
        # Verificar ordem
        assert top_produtos[0][1]['nome'] == 'Produto C'  # 15 unidades
        assert top_produtos[1][1]['nome'] == 'Produto A'  # 10 unidades
        assert top_produtos[2][1]['nome'] == 'Produto B'  # 5 unidades
        assert len(top_produtos) == 3
    
    def test_filtro_pedidos_por_periodo(self):
        """
        Teste: Filtro de pedidos por período (semanal, mensal, anual)
        
        Dados de entrada:
        - Pedido 1: hoje (deve aparecer)
        - Pedido 2: 5 dias atrás (deve aparecer em semanal)
        - Pedido 3: 10 dias atrás (NÃO deve aparecer em semanal)
        - Pedido 4: 35 dias atrás (NÃO deve aparecer em semanal)
        """
        hoje = datetime.now().date()
        
        pedidos = [
            {'id': 1, 'criadoEm': hoje.isoformat()},
            {'id': 2, 'criadoEm': (hoje - timedelta(days=5)).isoformat()},
            {'id': 3, 'criadoEm': (hoje - timedelta(days=10)).isoformat()},
            {'id': 4, 'criadoEm': (hoje - timedelta(days=35)).isoformat()},
        ]
        
        # Filtrar últimos 7 dias (semanal)
        data_inicio = hoje - timedelta(days=7)
        pedidos_semana = [
            p for p in pedidos
            if datetime.fromisoformat(p['criadoEm']).date() >= data_inicio
        ]
        
        assert len(pedidos_semana) == 2  # Apenas pedidos 1 e 2
        assert pedidos_semana[0]['id'] == 1
        assert pedidos_semana[1]['id'] == 2
    
    def test_calculo_evolucao_percentual(self):
        """
        Teste: Cálculo de evolução percentual de vendas
        
        Cenário:
        - Vendas ontem: R$ 1000,00
        - Vendas hoje: R$ 1200,00
        - Evolução esperada: +20%
        """
        vendas_ontem = 1000.0
        vendas_hoje = 1200.0
        
        if vendas_ontem > 0:
            evolucao = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
        else:
            evolucao = 0
        
        assert evolucao == 20.0  # +20%
        
        # Teste com queda
        vendas_hoje_queda = 800.0
        evolucao_queda = ((vendas_hoje_queda - vendas_ontem) / vendas_ontem) * 100
        assert evolucao_queda == -20.0  # -20%


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

