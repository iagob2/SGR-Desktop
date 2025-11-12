"""
Configuração global de testes pytest

Fixtures compartilhadas e configurações de ambiente de teste
"""

import pytest
import os
import sys

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session')
def test_config():
    """
    Fixture: Configurações de teste
    
    Define variáveis de ambiente para testes (mock da API externa)
    """
    os.environ['API_EXTERNA_URL'] = 'http://localhost:9999'  # Porta de teste
    os.environ['API_TIMEOUT'] = '5'
    yield
    # Cleanup após todos os testes


@pytest.fixture
def sample_pedidos():
    """
    Fixture: Dados de exemplo de pedidos
    
    Retorna lista de pedidos simulados para testes
    """
    return [
        {
            'id': 1,
            'status': 'FINALIZADO',
            'valor_total': 50.0,
            'restaurante_id': 1,
            'criadoEm': '2024-01-15T10:00:00',
            'itens': [
                {'quantidade': 2, 'preco': 25.0, 'nome': 'Hambúrguer'}
            ]
        },
        {
            'id': 2,
            'status': 'PENDENTE',
            'valor_total': 30.0,
            'restaurante_id': 1,
            'criadoEm': '2024-01-15T11:00:00',
            'itens': [
                {'quantidade': 1, 'preco': 30.0, 'nome': 'Pizza'}
            ]
        },
    ]


@pytest.fixture
def sample_html_login():
    """
    Fixture: HTML de exemplo de resposta de login
    
    Retorna HTML simulado da API Java
    """
    return """
    <html>
    <head>
        <script>
            var restaurante_id = 123;
        </script>
    </head>
    <body>
        <h1>Login bem-sucedido</h1>
        <p>Bem-vindo(a), Restaurante Teste.</p>
    </body>
    </html>
    """

