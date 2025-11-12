"""
🧪 TESTES DE UNIDADE - Parsing HTML/JSON

Foco: Testar funções de parsing que convertem HTML da API Java para JSON estruturado
"""

import pytest
from app.proxy import parse_html_response


class TestParseHtmlResponse:
    """
    Teste: Parsing de Respostas HTML
    
    Objetivo: Garantir que a função parse_html_response() converte corretamente
    respostas HTML da API Java para dicionários Python estruturados.
    
    Cenários testados:
    - Parsing de login (extração de restaurante_id e restaurante_nome)
    - Parsing de listagem de itens (extração de tabela HTML)
    - Tratamento de HTML inválido ou malformado
    - Fallback quando beautifulsoup4 não está disponível
    """
    
    def test_parse_login_html_com_restaurante_id(self):
        """
        Teste: Parsing de HTML de login com restaurante_id em script
        
        HTML simula resposta da API Java após login bem-sucedido
        """
        html_login = """
        <html>
        <head>
            <script>
                var restaurante_id = 123;
                var restaurante_nome = "Restaurante Teste";
            </script>
        </head>
        <body>
            <h1>Login bem-sucedido</h1>
            <p>Bem-vindo(a), Restaurante Teste.</p>
        </body>
        </html>
        """
        
        result = parse_html_response(html_login, 'restaurantes/login')
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert result['data'].get('restaurante_id') == 123
        assert result['data'].get('restaurante_nome') == 'Restaurante Teste'
    
    def test_parse_login_html_com_input_hidden(self):
        """
        Teste: Parsing de HTML de login com restaurante_id em input hidden
        
        Simula caso onde a API Java usa inputs hidden para passar dados
        """
        html_login = """
        <html>
        <body>
            <form>
                <input type="hidden" name="restaurante_id" value="456">
            </form>
            <p>Bem-vindo(a), Restaurante Escondido.</p>
        </body>
        </html>
        """
        
        result = parse_html_response(html_login, 'restaurantes/login')
        
        assert result['status'] == 'success'
        assert result['data'].get('restaurante_id') == 456
    
    def test_parse_tabela_itens(self):
        """
        Teste: Parsing de tabela HTML com lista de itens do cardápio
        
        Simula resposta da API Java com tabela de itens
        """
        html_tabela = """
        <html>
        <body>
            <table id="tabelaItens">
                <tr>
                    <td>1</td>
                    <td>Hambúrguer</td>
                    <td>R$ 25,50</td>
                    <td>PRATO_PRINCIPAL</td>
                    <td>1</td>
                    <td><a href="/imagens/hamburger.jpg">Imagem</a></td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Refrigerante</td>
                    <td>R$ 5,00</td>
                    <td>BEBIDA</td>
                    <td>1</td>
                    <td><a href="/imagens/refri.jpg">Imagem</a></td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        result = parse_html_response(html_tabela, 'itens')
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Verificar primeiro item
        item1 = result[0]
        assert item1['id'] == 1
        assert item1['nome'] == 'Hambúrguer'
        assert item1['preco'] == 25.50
        assert item1.get('categoria') == 'PRATO_PRINCIPAL'
        
        # Verificar segundo item
        item2 = result[1]
        assert item2['id'] == 2
        assert item2['nome'] == 'Refrigerante'
        assert item2['preco'] == 5.0
    
    def test_parse_html_invalido_retorna_fallback(self):
        """
        Teste: HTML inválido ou malformado deve retornar resposta de fallback
        
        Garante que erros de parsing não quebram o sistema
        """
        html_invalido = "<html><body><p>Erro no servidor</p></body>"
        
        result = parse_html_response(html_invalido, 'endpoint_qualquer')
        
        # Deve retornar algo estruturado, não quebrar
        assert isinstance(result, dict)
        assert 'status' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

