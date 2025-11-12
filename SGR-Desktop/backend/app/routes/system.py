import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..config import API_EXTERNA_BASE_URL, API_EXTERNA_HOST, API_EXTERNA_PORT, API_TIMEOUT
from ..proxy import api_session, proxy_request, set_session_cookie

system_bp = Blueprint('system', __name__)


@system_bp.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde da API Flask (proxy)."""
    try:
        status_code, _ = proxy_request('GET', '')
        api_externa_status = 'active' if status_code == 200 else 'inactive'

        return jsonify({
            'status': 'success',
            'message': 'API Flask (Proxy) está funcionando!',
            'api_externa_status': api_externa_status,
            'api_externa_url': API_EXTERNA_BASE_URL,
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@system_bp.route('/api/restaurantes/perfil', methods=['GET'])
def restaurante_perfil():
    """Busca informações do restaurante logado - Proxy para API externa."""
    try:
        status_code, response_data = proxy_request('GET', 'restaurantes/perfil')

        if status_code == 200 and isinstance(response_data, dict):
            if 'data' not in response_data:
                response_data['data'] = {}

            restaurante_id = None
            restaurante_nome = None

            if 'restaurante_id' in response_data.get('data', {}):
                restaurante_id = response_data['data']['restaurante_id']
            elif 'id' in response_data.get('data', {}):
                restaurante_id = response_data['data']['id']
            elif 'restaurante_id' in response_data:
                restaurante_id = response_data['restaurante_id']
            elif 'id' in response_data:
                restaurante_id = response_data['id']

            if 'restaurante_nome' in response_data.get('data', {}):
                restaurante_nome = response_data['data']['restaurante_nome']
            elif 'nome' in response_data.get('data', {}):
                restaurante_nome = response_data['data']['nome']
            elif 'restaurante_nome' in response_data:
                restaurante_nome = response_data['restaurante_nome']
            elif 'nome' in response_data:
                restaurante_nome = response_data['nome']

            if restaurante_id:
                response_data['data']['restaurante_id'] = restaurante_id
            if restaurante_nome:
                response_data['data']['restaurante_nome'] = restaurante_nome

            return jsonify(response_data), status_code

        return jsonify({'status': 'error', 'message': 'Não foi possível obter informações do restaurante'}), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao buscar perfil: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@system_bp.route('/api/restaurantes/<int:restaurante_id>', methods=['GET'])
def get_restaurante_detalhes(restaurante_id):
    """Busca detalhes completos de um restaurante (incluindo avaliações) - Proxy."""
    try:
        print(f"[PROXY] Buscando detalhes completos (com avaliações) para ID: {restaurante_id}")

        status_code, response_data = proxy_request('GET', f'restaurantes/{restaurante_id}')

        return jsonify(response_data), status_code
    except Exception as exc:
        print(f"[ERRO] Erro ao buscar detalhes do restaurante: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@system_bp.route('/api/restaurantes/login', methods=['POST'])
def restaurante_login():
    """Login de restaurante - Proxy para API externa (/restaurantes/login)."""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'status': 'error', 'message': 'Email e senha são obrigatórios'}), 400

        status_code, response_data = proxy_request('POST', 'restaurantes/login', data=data)

        if status_code == 502 and isinstance(response_data, dict) and response_data.get('diagnostico', {}).get('tipo_erro') == 'url_parse_error':
            return jsonify({
                'status': 'error',
                'message': 'URL inválida no config.env. Remova comentários inline da linha API_EXTERNA_URL.',
                'diagnostico': response_data.get('diagnostico', {}),
            }), 502

        if status_code == 504:
            error_msg = f'Servidor não respondeu em {API_TIMEOUT} segundos. Verifique se o servidor está rodando em {API_EXTERNA_HOST}:{API_EXTERNA_PORT}'
            return jsonify({'status': 'error', 'message': error_msg}), 504

        if status_code == 503:
            error_msg = f'Não foi possível conectar ao servidor em {API_EXTERNA_HOST}:{API_EXTERNA_PORT}. Verifique se o servidor está rodando.'
            return jsonify({'status': 'error', 'message': error_msg}), 503

        if status_code in [401, 403]:
            if isinstance(response_data, dict) and response_data.get('message'):
                error_msg = response_data['message']
            else:
                if API_EXTERNA_HOST in ['localhost', '127.0.0.1']:
                    error_msg = 'Erro de autenticação. Verifique suas credenciais ou se o formato da requisição está correto.'
                else:
                    error_msg = 'Acesso negado. Verifique suas credenciais ou se o servidor está acessível.'

            return jsonify({'status': 'error', 'message': error_msg}), status_code

        if status_code == 200 and isinstance(response_data, dict) and response_data.get('status') == 'success':
            if 'data' not in response_data:
                response_data['data'] = {}

            restaurante_id = response_data.get('data', {}).get('restaurante_id')

            if len(api_session.cookies) > 0:
                cookie_names = list(api_session.cookies.keys())
                print(f"[LOGIN] Cookie(s) na sessao: {', '.join(cookie_names)}")

                if restaurante_id:
                    jsessionid = api_session.cookies.get('JSESSIONID')
                    if jsessionid:
                        cookie_string = f"JSESSIONID={jsessionid}"
                        set_session_cookie(cookie_string, restaurante_id)
                        print(f"[LOGIN] Login bem-sucedido - Cookie JSESSIONID associado ao restaurante_id {restaurante_id}")
                    else:
                        for cookie_name in cookie_names:
                            cookie_val = api_session.cookies.get(cookie_name)
                            if cookie_val:
                                cookie_string = f"{cookie_name}={cookie_val}"
                                set_session_cookie(cookie_string, restaurante_id)
                                print(f"[LOGIN] Login bem-sucedido - Cookie {cookie_name} associado ao restaurante_id {restaurante_id}")
                                break
                else:
                    print("[AVISO] Login bem-sucedido mas restaurante_id nao encontrado na resposta")
                    print("[AVISO] Cookie salvo mas sem associacao ao restaurante_id")
            else:
                print("[AVISO] Login bem-sucedido mas nenhum cookie foi recebido da API externa")

        return jsonify(response_data), status_code

    except Exception as exc:
        print(f"[ERRO] Erro no login: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500

