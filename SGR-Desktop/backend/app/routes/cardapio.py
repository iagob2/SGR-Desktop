import json
from flask import Blueprint, jsonify, request

from ..config import API_EXTERNA_BASE_URL, API_TIMEOUT
from ..proxy import (
    BS4_AVAILABLE,
    api_session,
    get_session_cookie,
    mapear_endpoint_flask_para_api,
    parse_html_response,
    proxy_request,
)

cardapio_bp = Blueprint('cardapio', __name__)


@cardapio_bp.route('/api/cardapio/<int:restaurante_id>', methods=['GET'])
def listar_cardapio(restaurante_id):
    """Rota para LER (Listar) todos os itens do cardápio - Proxy para API externa."""
    try:
        print(f"[CARDAPIO] Listando cardápio para restaurante {restaurante_id}")

        params = {'restaurante_id': restaurante_id}

        status_code, response_data = proxy_request('GET', f'cardapio/{restaurante_id}', params=params)

        print(f"[CARDAPIO] Resposta da API externa (GET): Status {status_code}")
        print(f"[CARDAPIO] Tipo de resposta: {type(response_data)}")

        if 200 <= status_code < 300:
            if isinstance(response_data, list):
                print(f"[CARDAPIO] Resposta é lista com {len(response_data)} itens")
                return jsonify({'status': 'success', 'data': response_data}), 200
            if isinstance(response_data, dict):
                if 'data' in response_data:
                    print("[CARDAPIO] Resposta tem campo 'data'")
                    return jsonify({'status': 'success', 'data': response_data.get('data', [])}), 200
                if 'itens' in response_data:
                    print("[CARDAPIO] Resposta tem campo 'itens'")
                    return jsonify({'status': 'success', 'data': response_data.get('itens', [])}), 200
                if isinstance(response_data.get('data'), list):
                    print("[CARDAPIO] Resposta dict com data array")
                    return jsonify({'status': 'success', 'data': response_data.get('data', [])}), 200
                print("[CARDAPIO] Resposta dict com status")
                return jsonify(response_data), status_code

            print(f"[CARDAPIO] AVISO: Formato de resposta inesperado: {type(response_data)}")
            return jsonify({'status': 'success', 'data': []}), 200

        if status_code in (401, 403):
            error_msg = (
                response_data.get('message', 'Sessão expirada. Faça login novamente.')
                if isinstance(response_data, dict)
                else str(response_data)
            )
            return jsonify({'status': 'error', 'message': error_msg}), status_code

        return jsonify({
            'status': 'error',
            'message': response_data.get('message', 'Erro ao carregar cardápio')
            if isinstance(response_data, dict)
            else 'Erro ao carregar cardápio',
        }), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao listar cardapio: {exc}")
        import traceback

        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Falha ao listar o cardápio: {str(exc)}'}), 500


@cardapio_bp.route('/api/cardapio/add', methods=['POST'])
def adicionar_item():
    """Rota para CRIAR (Adicionar) um novo item ao cardápio - Proxy para API externa."""
    try:
        dados = request.get_json()

        if not dados:
            print("[ERRO] Nenhum dado recebido no POST /api/cardapio/add")
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400

        print(f"[CARDAPIO] Dados recebidos para adicionar item: {json.dumps(dados, indent=2, ensure_ascii=False)}")

        campos_obrigatorios = ['nome', 'preco', 'restaurante_id']
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in dados or dados[campo] is None]

        if campos_faltando:
            print(f"[ERRO] Campos obrigatórios faltando: {campos_faltando}")
            return jsonify({
                'status': 'error',
                'message': f'Campos obrigatórios faltando: {", ".join(campos_faltando)}',
            }), 400

        if not isinstance(dados.get('nome'), str) or not dados['nome'].strip():
            return jsonify({'status': 'error', 'message': 'Nome do prato é obrigatório e deve ser texto'}), 400

        if not isinstance(dados.get('preco'), (int, float)) or dados['preco'] <= 0:
            return jsonify({'status': 'error', 'message': 'Preço deve ser um número maior que zero'}), 400

        dados_para_api = {
            'nome': dados['nome'].strip(),
            'descricao': dados.get('descricao', '').strip() or '',
            'preco': float(dados['preco']),
            'categoria': dados.get('categoria', 'OUTROS').strip() or 'OUTROS',
            'restaurante': {
                'id': int(dados['restaurante_id']),
            },
        }

        if 'imagemUrl' in dados:
            dados_para_api['imagemUrl'] = dados['imagemUrl'].strip() if dados['imagemUrl'] else ''
        else:
            dados_para_api['imagemUrl'] = ''

        print("[CARDAPIO] Dados preparados para API externa:")
        print(f"   {json.dumps(dados_para_api, indent=2, ensure_ascii=False)}")

        print(f"[CARDAPIO] Cookies na sessão: {len(api_session.cookies)} cookie(s)")
        for cookie in api_session.cookies:
            print(f"   Cookie: {cookie.name} = {cookie.value[:20]}...")

        restaurante_id_para_cookie = dados_para_api['restaurante']['id']
        cookie_manual = get_session_cookie(restaurante_id_para_cookie)
        if cookie_manual:
            print(f"[CARDAPIO] Cookie manual encontrado para restaurante {restaurante_id_para_cookie}: {cookie_manual[:30]}...")
        else:
            print(f"[CARDAPIO] AVISO: Nenhum cookie encontrado para restaurante {restaurante_id_para_cookie}")

        params = {'restaurante_id': restaurante_id_para_cookie}

        print("[CARDAPIO] Fazendo requisição POST para 'cardapio/add' (mapeado para 'itens')")

        status_code, response_data = proxy_request('POST', 'cardapio/add', data=dados_para_api, params=params)

        print("\n[CARDAPIO] === RESPOSTA DA API EXTERNA ===")
        print(f"[CARDAPIO] Status Code: {status_code}")
        print(f"[CARDAPIO] Tipo de Resposta: {type(response_data)}")

        if isinstance(response_data, dict):
            print("[CARDAPIO] Response Data (dict):")
            print(f"   {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        elif isinstance(response_data, str):
            print(f"[CARDAPIO] Response Data (string): {response_data[:500]}")
        else:
            print(f"[CARDAPIO] Response Data (outro tipo): {str(response_data)[:500]}")
        print("[CARDAPIO] ===================================\n")

        if status_code == 400 and isinstance(response_data, dict):
            error_msg_check = response_data.get('message', '').lower()
            if any(palavra in error_msg_check for palavra in ['formato', 'format', 'content-type', 'invalid', 'form']):
                print("[CARDAPIO] Erro pode ser de formato - tentando form-urlencoded...")
                try:
                    endpoint_api = mapear_endpoint_flask_para_api('cardapio/add')
                    url = f"{API_EXTERNA_BASE_URL}{endpoint_api}"

                    headers_form = {
                        'Accept': 'text/html,application/json,application/xhtml+xml,text/plain,*/*',
                        'User-Agent': 'SGR-Desktop-Flask-Proxy/1.0',
                        'Origin': 'http://localhost:5000',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }

                    if len(api_session.cookies) > 0:
                        cookie_header = '; '.join([f"{name}={value}" for name, value in api_session.cookies.items()])
                        headers_form['Cookie'] = cookie_header

                    import urllib.parse

                    form_data_parts = []
                    for key, value in dados_para_api.items():
                        if key == 'restaurante' and isinstance(value, dict):
                            restaurante_id = value.get('id', '')
                            form_data_parts.append(f"restaurante.id={urllib.parse.quote(str(restaurante_id))}")
                        elif key in {'nome', 'descricao', 'imagemUrl', 'categoria'}:
                            form_data_parts.append(f"{key}={urllib.parse.quote(str(value))}")
                        else:
                            form_data_parts.append(f"{key}={urllib.parse.quote(str(value))}")
                    form_data = '&'.join(form_data_parts)

                    print("[CARDAPIO] Tentando form-urlencoded:")
                    print(f"   URL: {url}")
                    print(f"   Form Data: {form_data}")

                    response_form = api_session.post(url, data=form_data, headers=headers_form, timeout=API_TIMEOUT)

                    if response_form.status_code != 400:
                        print(f"[CARDAPIO] Form-urlencoded funcionou! Status: {response_form.status_code}")
                        try:
                            response_data = response_form.json()
                        except Exception:
                            response_data = parse_html_response(response_form.text, endpoint_api)
                        status_code = response_form.status_code
                    else:
                        print("[CARDAPIO] Form-urlencoded também retornou 400")
                except Exception as exc:
                    print(f"[CARDAPIO] Erro ao tentar form-urlencoded: {exc}")

        if status_code == 400:
            error_msg = 'Erro ao adicionar item'

            print("[CARDAPIO] Extraindo mensagem de erro do status 400...")

            if isinstance(response_data, dict):
                error_msg = response_data.get('message', response_data.get('error', response_data.get('mensagem', 'Dados inválidos')))
                print(f"[CARDAPIO] Mensagem extraída do dict: {error_msg}")
            elif isinstance(response_data, str):
                print("[CARDAPIO] Resposta é string, procurando mensagens de erro...")
                if BS4_AVAILABLE and ('<' in response_data and '>' in response_data):
                    try:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(response_data, 'html.parser')
                        error_div = soup.find(class_=['error', 'alert-danger', 'message', 'error'])
                        if error_div:
                            error_msg = error_div.get_text(strip=True)
                            print(f"[CARDAPIO] Mensagem extraída do HTML: {error_msg}")
                        else:
                            body = soup.find('body')
                            if body:
                                error_msg = body.get_text(strip=True)[:200]
                            else:
                                error_msg = response_data[:200]
                    except Exception as parse_error:
                        print(f"[CARDAPIO] Erro ao fazer parse HTML: {parse_error}")
                        error_msg = response_data[:200]
                else:
                    if 'erro' in response_data.lower() or 'error' in response_data.lower():
                        error_msg = response_data[:200]
                    else:
                        error_msg = 'Erro ao adicionar item. Verifique os dados enviados.'

            print(f"[ERRO] API externa retornou 400: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400

        if status_code == 403:
            print("[ERRO] API externa retornou 403 - Acesso negado")
            return jsonify({'status': 'error', 'message': 'Acesso negado. Verifique se você está autenticado.'}), 403

        if 200 <= status_code < 300:
            print(f"[CARDAPIO] Sucesso! Status {status_code}")

            if not isinstance(response_data, dict):
                if isinstance(response_data, str):
                    response_data = {
                        'status': 'success',
                        'message': 'Item adicionado com sucesso',
                        'data': response_data,
                    }
                else:
                    response_data = {
                        'status': 'success',
                        'message': 'Item adicionado com sucesso',
                        'data': str(response_data),
                    }
            elif 'status' not in response_data:
                response_data['status'] = 'success'

            print(f"[CARDAPIO] Retornando resposta formatada: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return jsonify(response_data), status_code

        print(f"[CARDAPIO] Status não tratado: {status_code}")
        return jsonify({
            'status': 'error',
            'message': response_data.get('message', f'Erro ao adicionar item (status {status_code})')
            if isinstance(response_data, dict)
            else f'Erro ao adicionar item (status {status_code})',
        }), status_code

    except ValueError as exc:
        print(f"[ERRO] Erro de validação: {exc}")
        return jsonify({'status': 'error', 'message': f'Erro de validação: {str(exc)}'}), 400
    except Exception as exc:
        print(f"[ERRO] Erro ao adicionar item: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Falha ao adicionar item: {str(exc)}'}), 500


@cardapio_bp.route('/api/cardapio/edit/<int:item_id>', methods=['PUT'])
def editar_item(item_id):
    """Rota para ATUALIZAR (Editar) um item existente - Proxy para API externa."""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400

        print(f"[CARDAPIO] Editando item {item_id}")
        print(f"[CARDAPIO] Dados recebidos: {json.dumps(dados, indent=2, ensure_ascii=False)}")

        dados_para_api = {
            'nome': dados.get('nome', '').strip(),
            'descricao': dados.get('descricao', '').strip() or '',
            'preco': float(dados.get('preco', 0)),
            'categoria': dados.get('categoria', 'OUTROS').strip() or 'OUTROS',
            'imagemUrl': dados.get('imagemUrl', '').strip() if dados.get('imagemUrl') else '',
        }

        if 'restaurante_id' in dados:
            dados_para_api['restaurante'] = {'id': int(dados['restaurante_id'])}

        params = {}
        if 'restaurante_id' in dados:
            params['restaurante_id'] = dados['restaurante_id']

        status_code, response_data = proxy_request('PUT', f'itens/{item_id}', data=dados_para_api, params=params)

        print(f"[CARDAPIO] Resposta da API externa (PUT): Status {status_code}")

        if 200 <= status_code < 300:
            return jsonify({
                'status': 'success',
                'message': 'Item editado com sucesso',
                'data': response_data if isinstance(response_data, dict) else {},
            }), status_code

        error_msg = 'Erro ao editar item'
        if isinstance(response_data, dict):
            error_msg = response_data.get('message', error_msg)

        return jsonify({'status': 'error', 'message': error_msg}), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao editar item: {exc}")
        import traceback

        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Falha ao atualizar item: {str(exc)}'}), 500


@cardapio_bp.route('/api/cardapio/delete/<int:item_id>', methods=['DELETE'])
def deletar_item(item_id):
    """Rota para DELETAR um item - Proxy para API externa."""
    try:
        print(f"[CARDAPIO] Deletando item {item_id}")

        params = {}

        status_code, response_data = proxy_request('DELETE', f'itens/{item_id}', params=params)

        print(f"[CARDAPIO] Resposta da API externa (DELETE): Status {status_code}")

        if status_code in (200, 204):
            return jsonify({'status': 'success', 'message': 'Item deletado com sucesso'}), 200

        error_msg = 'Erro ao deletar item'
        if isinstance(response_data, dict):
            error_msg = response_data.get('message', error_msg)

        return jsonify({'status': 'error', 'message': error_msg}), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao deletar item: {exc}")
        import traceback

        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Falha ao deletar item: {str(exc)}'}), 500

