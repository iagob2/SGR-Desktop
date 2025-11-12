"""
🧪 TESTES DE INTEGRAÇÃO - Proxy Flask ↔️ API Externa

Foco: Testar interação entre Flask e API externa Java
Estratégia: Mock da API externa para simular respostas
"""

import pytest
from unittest.mock import patch, MagicMock
from app.proxy import proxy_request


class TestProxyRequest:
    """
    Teste: Proxy de Requisições para API Externa
    
    Objetivo: Garantir que o Flask consegue:
    1. Chamar a API Java corretamente
    2. Receber e processar respostas (HTML/JSON)
    3. Manter sessão (cookies JSESSIONID)
    4. Retornar JSON limpo para o frontend
    5. Tratar erros adequadamente
    """
    
    @patch('app.proxy.api_session')
    def test_proxy_request_sucesso_json(self, mock_session):
        """
        Teste: Proxy retorna JSON quando API externa retorna JSON
        
        Simula resposta JSON da API Java
        """
        # Mock da resposta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'status': 'success', 'data': {'id': 1}}
        mock_response.text = ''
        mock_response.headers.get_list.return_value = []
        
        mock_session.request.return_value = mock_response
        
        status_code, response_data = proxy_request('GET', 'restaurantes/perfil')
        
        assert status_code == 200
        assert response_data['status'] == 'success'
        assert 'data' in response_data
    
    @patch('app.proxy.api_session')
    def test_proxy_request_sucesso_html(self, mock_session):
        """
        Teste: Proxy converte HTML para JSON quando API externa retorna HTML
        
        Simula resposta HTML da API Java (comum em alguns endpoints)
        """
        html_response = """
        <html>
        <script>var restaurante_id = 123;</script>
        <body>Login bem-sucedido</body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = html_response
        mock_response.headers.get_list.return_value = []
        
        mock_session.request.return_value = mock_response
        
        status_code, response_data = proxy_request('POST', 'restaurantes/login', {'email': 'test@test.com'})
        
        assert status_code == 200
        # Deve ter tentado parsear o HTML
        assert isinstance(response_data, dict)
    
    @patch('app.proxy.api_session')
    def test_proxy_request_manutencao_cookies(self, mock_session):
        """
        Teste: Proxy mantém cookies JSESSIONID entre requisições
        
        Simula recebimento de cookie JSESSIONID e verifica se é armazenado
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'application/json',
            'Set-Cookie': 'JSESSIONID=ABC123XYZ; Path=/; HttpOnly'
        }
        mock_response.json.return_value = {'status': 'success'}
        mock_response.text = ''
        mock_response.headers.get_list.return_value = ['JSESSIONID=ABC123XYZ; Path=/; HttpOnly']
        
        mock_session.request.return_value = mock_response
        mock_session.cookies = MagicMock()
        mock_session.cookies.items.return_value = []
        mock_session.cookies.get.return_value = None
        mock_session.cookies.set = MagicMock()
        
        status_code, _ = proxy_request('POST', 'restaurantes/login', {'email': 'test@test.com'})
        
        assert status_code == 200
        # Verificar se cookie foi armazenado (mock verifica chamada)
        mock_session.cookies.set.assert_called()
    
    @patch('app.proxy.api_session')
    def test_proxy_request_timeout(self, mock_session):
        """
        Teste: Proxy trata timeout da API externa adequadamente
        
        Simula timeout na conexão com API externa
        """
        import requests
        
        mock_session.request.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
        
        assert status_code == 504  # Gateway Timeout
        assert response_data['status'] == 'error'
        assert 'timeout' in response_data.get('message', '').lower() or 'timeout' in str(response_data)
    
    @patch('app.proxy.api_session')
    def test_proxy_request_connection_error(self, mock_session):
        """
        Teste: Proxy trata erro de conexão adequadamente
        
        Simula API externa indisponível
        """
        import requests
        
        mock_session.request.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
        
        assert status_code == 503  # Service Unavailable
        assert response_data['status'] == 'error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

