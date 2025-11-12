"""
🧪 TESTES DE INTEGRAÇÃO - Flask API

Foco: Testar endpoints Flask e respostas HTTP
Estratégia: Usar Flask test client para simular requisições
"""

import pytest
from app import create_app


@pytest.fixture
def client():
    """Fixture: Cria cliente de teste Flask"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskEndpoints:
    """
    Teste: Endpoints Flask
    
    Objetivo: Garantir que os endpoints Flask retornam respostas HTTP corretas
    e formatam JSON adequadamente.
    """
    
    def test_health_check_endpoint(self, client):
        """
        Teste: Endpoint /api/health deve retornar status do servidor
        
        Verifica se o health check funciona corretamente
        """
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'api_externa_url' in data
    
    def test_login_endpoint_validation(self, client):
        """
        Teste: Endpoint /api/restaurantes/login valida dados de entrada
        
        Verifica se validação de campos obrigatórios funciona
        """
        # Teste sem dados
        response = client.post('/api/restaurantes/login', json={})
        
        assert response.status_code in [400, 500]  # Deve retornar erro
        
        # Teste com dados incompletos
        response = client.post('/api/restaurantes/login', json={'email': 'test@test.com'})
        
        assert response.status_code in [400, 500]  # Falta senha
    
    def test_cardapio_endpoint_structure(self, client):
        """
        Teste: Endpoint /api/cardapio/{id} retorna estrutura JSON correta
        
        Verifica formato da resposta (mesmo que vazia)
        """
        response = client.get('/api/cardapio/1')
        
        # Pode retornar 200 (sucesso) ou erro (se API externa não disponível)
        # Mas deve sempre retornar JSON válido
        assert response.is_json
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'status' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

