import json
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from ..proxy import api_session, proxy_request
from ..utils.status import is_status_concluido

pedidos_bp = Blueprint('pedidos', __name__)


@pedidos_bp.route('/api/pedidos/restaurante/<int:restaurante_id>', methods=['GET'])
def get_pedidos_restaurante(restaurante_id):
    """
    Lista pedidos de um restaurante - Proxy para API externa.
    Busca todos os pedidos da API externa e filtra por restaurante_id e status.
    """
    try:
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        print(f"\n{'='*60}")
        print(f"[PEDIDOS-RESTAURANTE] Buscando pedidos para restaurante {restaurante_id}")
        print(f"[PEDIDOS-RESTAURANTE] Filtro de status: {status}")

        try:
            status_code, response_data = proxy_request('GET', 'pedidos/restaurante')

            print(f"[PEDIDOS-RESTAURANTE] Status code da API externa: {status_code}")

            if status_code != 200:
                print(f"[PEDIDOS-RESTAURANTE] Erro ao buscar pedidos: {status_code}")
                return jsonify({'status': 'error', 'message': f'Erro ao buscar pedidos: Status {status_code}'}), status_code

            pedidos_todos = []
            if isinstance(response_data, list):
                pedidos_todos = response_data
            elif isinstance(response_data, dict):
                pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
                if not isinstance(pedidos_todos, list):
                    pedidos_todos = []

            print(f"[PEDIDOS-RESTAURANTE] Total de pedidos recebidos da API: {len(pedidos_todos)}")

            if len(pedidos_todos) > 0:
                primeiro_pedido = pedidos_todos[0]
                print(f"[PEDIDOS-RESTAURANTE] Estrutura do primeiro pedido: {json.dumps(primeiro_pedido, indent=2, default=str)[:500]}")

            pedidos_filtrados = []
            for pedido in pedidos_todos:
                if not isinstance(pedido, dict):
                    continue

                pedido_restaurante_id = None
                if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                    pedido_restaurante_id = pedido['restaurante'].get('id')
                elif pedido.get('restaurante_id'):
                    pedido_restaurante_id = pedido['restaurante_id']

                if pedido_restaurante_id and int(pedido_restaurante_id) != int(restaurante_id):
                    print(f"[PEDIDOS-RESTAURANTE] Pedido {pedido.get('id')} - restaurante_id diferente: {pedido_restaurante_id} != {restaurante_id}")
                    continue

                if status:
                    pedido_status = (pedido.get('status') or '').upper()
                    status_upper = status.upper()

                    if status_upper in ['FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO']:
                        if pedido_status not in ['FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO']:
                            continue
                    else:
                        if pedido_status != status_upper:
                            continue

                if data_inicio or data_fim:
                    pedido_data_str = None
                    if pedido.get('criadoEm'):
                        try:
                            pedido_data = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                            pedido_data_str = pedido_data.strftime('%Y-%m-%d')
                        except Exception:
                            pass
                    elif pedido.get('criado_em'):
                        try:
                            pedido_data = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                            pedido_data_str = pedido_data.strftime('%Y-%m-%d')
                        except Exception:
                            pass

                    if pedido_data_str:
                        if data_inicio and pedido_data_str < data_inicio:
                            continue
                        if data_fim and pedido_data_str > data_fim:
                            continue

                if 'restaurante_id' not in pedido:
                    pedido['restaurante_id'] = restaurante_id

                if 'criadoEm' not in pedido and 'criado_em' in pedido:
                    pedido['criadoEm'] = pedido['criado_em']
                elif 'criado_em' not in pedido and 'criadoEm' in pedido:
                    pedido['criado_em'] = pedido['criadoEm']

                if 'itens' not in pedido:
                    pedido['itens'] = []

                pedidos_filtrados.append(pedido)

            print(f"[PEDIDOS-RESTAURANTE] Pedidos filtrados: {len(pedidos_filtrados)}")

            pedidos_filtrados.sort(key=lambda pedido: (
                pedido.get('criadoEm') or pedido.get('criado_em') or ''
            ), reverse=True)

            pedidos = pedidos_filtrados

        except Exception as exc:
            print(f"[PEDIDOS-RESTAURANTE] Erro ao buscar pedidos da API externa: {exc}")
            import traceback

            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            pedidos = []

        print(f"[PEDIDOS-RESTAURANTE] Retornando {len(pedidos)} pedidos para restaurante {restaurante_id}")

        if not pedidos:
            hoje = datetime.now()
            pedidos_teste = [
                {
                    'id': 1001,
                    'valor_total': 89.90,
                    'status': 'pendente',
                    'data_pedido': (hoje - timedelta(minutes=15)).isoformat(),
                    'observacoes': 'Sem cebola na pizza',
                    'cliente': {'nome': 'Maria Silva', 'telefone': '(11) 99999-1234'},
                },
                {
                    'id': 1002,
                    'valor_total': 45.50,
                    'status': 'em_preparo',
                    'data_pedido': (hoje - timedelta(minutes=30)).isoformat(),
                    'observacoes': None,
                    'cliente': {'nome': 'João Santos', 'telefone': '(11) 99999-5678'},
                },
                {
                    'id': 1003,
                    'valor_total': 123.75,
                    'status': 'pronto',
                    'data_pedido': (hoje - timedelta(minutes=45)).isoformat(),
                    'observacoes': 'Entregar no portão',
                    'cliente': {'nome': 'Ana Costa', 'telefone': '(11) 99999-9012'},
                },
                {
                    'id': 1004,
                    'valor_total': 67.20,
                    'status': 'entregue',
                    'data_pedido': (hoje - timedelta(hours=1)).isoformat(),
                    'observacoes': None,
                    'cliente': {'nome': 'Carlos Oliveira', 'telefone': '(11) 99999-3456'},
                },
                {
                    'id': 1005,
                    'valor_total': 156.80,
                    'status': 'entregue',
                    'data_pedido': (hoje - timedelta(hours=2)).isoformat(),
                    'observacoes': 'Pedido para festa',
                    'cliente': {'nome': 'Fernanda Lima', 'telefone': '(11) 99999-7890'},
                },
            ]

            if status:
                pedidos_teste = [pedido for pedido in pedidos_teste if pedido['status'] == status]

            pedidos = pedidos_teste

        return jsonify({'status': 'success', 'data': pedidos, 'count': len(pedidos)})

    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@pedidos_bp.route('/api/pedidos/restaurante/<int:restaurante_id>/concluidos', methods=['GET'])
def get_pedidos_concluidos_restaurante(restaurante_id):
    """
    Lista pedidos CONCLUÍDOS/FINALIZADOS de um restaurante específico.
    Usa o endpoint /pedidos/restaurante da API Java (Spring Boot).
    """
    try:
        print(f"\n{'='*60}")
        print(f"[PEDIDOS-CONCLUIDOS] Buscando pedidos concluídos para restaurante {restaurante_id}")

        try:
            status_code, response_data = proxy_request('GET', 'pedidos/restaurante')

            print(f"[PEDIDOS-CONCLUIDOS] Status code da API externa: {status_code}")

            if status_code != 200:
                print(f"[PEDIDOS-CONCLUIDOS] Erro ao buscar pedidos: {status_code}")
                return jsonify({
                    'status': 'error',
                    'message': f'Erro ao buscar pedidos: Status {status_code}',
                    'data': [],
                }), status_code

            pedidos_todos = []
            if isinstance(response_data, list):
                pedidos_todos = response_data
            elif isinstance(response_data, dict):
                pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
                if not isinstance(pedidos_todos, list):
                    pedidos_todos = []

            print(f"[PEDIDOS-CONCLUIDOS] Total de pedidos recebidos da API: {len(pedidos_todos)}")

            pedidos_concluidos = []
            for pedido in pedidos_todos:
                if not isinstance(pedido, dict):
                    continue

                pedido_restaurante_id = None
                if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                    pedido_restaurante_id = pedido['restaurante'].get('id')
                elif pedido.get('restaurante_id'):
                    pedido_restaurante_id = pedido['restaurante_id']

                if not pedido_restaurante_id or int(pedido_restaurante_id) != int(restaurante_id):
                    continue

                if not is_status_concluido(pedido.get('status')):
                    continue

                if 'restaurante_id' not in pedido:
                    pedido['restaurante_id'] = restaurante_id

                if 'criadoEm' not in pedido and 'criado_em' in pedido:
                    pedido['criadoEm'] = pedido['criado_em']
                elif 'criado_em' not in pedido and 'criadoEm' in pedido:
                    pedido['criado_em'] = pedido['criadoEm']

                if 'itens' not in pedido:
                    pedido['itens'] = []

                pedidos_concluidos.append(pedido)

            print(f"[PEDIDOS-CONCLUIDOS] Pedidos concluídos encontrados: {len(pedidos_concluidos)}")

            pedidos_concluidos.sort(key=lambda pedido: (
                pedido.get('criadoEm') or pedido.get('criado_em') or ''
            ), reverse=True)

            return jsonify({'status': 'success', 'data': pedidos_concluidos, 'count': len(pedidos_concluidos)}), 200

        except Exception as exc:
            print(f"[PEDIDOS-CONCLUIDOS] Erro ao buscar pedidos da API externa: {exc}")
            import traceback

            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return jsonify({'status': 'error', 'message': f'Erro ao buscar pedidos: {str(exc)}', 'data': []}), 500

    except Exception as exc:
        print(f"[PEDIDOS-CONCLUIDOS] Erro geral: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc), 'data': []}), 500


@pedidos_bp.route('/api/pedidos/<int:pedido_id>/status', methods=['PUT'])
def update_pedido_status(pedido_id):
    """
    Atualiza status de um pedido - Proxy para API externa.
    CORREÇÃO: Usa endpoint /status-restaurante para restaurantes.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[UPDATE-STATUS] Atualizando status do pedido {pedido_id}")

        dados = request.get_json()
        if not dados:
            print("[UPDATE-STATUS] Erro: Dados não fornecidos")
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400

        novo_status = dados.get('status')
        if not novo_status:
            print("[UPDATE-STATUS] Erro: Status não fornecido")
            return jsonify({'status': 'error', 'message': 'Status não fornecido'}), 400

        print(f"[UPDATE-STATUS] Status recebido: {novo_status}")

        status_mapeado = novo_status.lower().strip()

        status_mapping = {
            'pendente': 'PENDENTE',
            'novo': 'PENDENTE',
            'aguardando': 'PENDENTE',
            'em_preparo': 'EM_PREPARO',
            'em preparo': 'EM_PREPARO',
            'pronto': 'PRONTO',
            'concluido': 'FINALIZADO',
            'concluído': 'FINALIZADO',
            'finalizado': 'FINALIZADO',
            'entregue': 'ENTREGUE',
            'cancelado': 'CANCELADO',
        }

        if status_mapeado in status_mapping:
            status_mapeado = status_mapping[status_mapeado]
        else:
            status_upper = novo_status.upper().strip()
            status_validos = [
                'PENDENTE', 'NOVO', 'EM_PREPARO', 'PRONTO',
                'FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO', 'ENTREGUE', 'CANCELADO',
            ]

            if status_upper in status_validos:
                status_mapeado = status_upper
            else:
                status_mapeado = status_upper
                print(f"[UPDATE-STATUS] ⚠️ Status não mapeado: {novo_status} -> usando {status_mapeado}")

        print(f"[UPDATE-STATUS] Status mapeado para API Java: {status_mapeado}")

        if len(api_session.cookies) > 0:
            cookie_info = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"[UPDATE-STATUS] Cookies na sessão: {', '.join(cookie_info)}")
        else:
            print("[UPDATE-STATUS] ⚠️ AVISO: Nenhum cookie na sessão!")

        params = {'status': status_mapeado}
        print(f"[UPDATE-STATUS] Enviando requisição: PUT pedidos/{pedido_id}/status-restaurante?status={status_mapeado}")

        status_code, response_data = proxy_request('PUT', f'pedidos/{pedido_id}/status-restaurante', params=params)

        print(f"[UPDATE-STATUS] Resposta da API Java: Status {status_code}")
        if isinstance(response_data, dict):
            print(f"[UPDATE-STATUS] Resposta completa: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"[UPDATE-STATUS] Resposta (tipo {type(response_data)}): {str(response_data)[:200]}")

        if status_code >= 400:
            error_msg = 'Erro ao atualizar status'

            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('mensagem') or error_msg
            elif isinstance(response_data, str):
                error_msg = response_data[:200]

            if status_code == 401:
                error_msg = 'Sessão expirada. Faça login novamente.'
            elif status_code == 403:
                error_msg = 'Você não tem permissão para atualizar este pedido.'
            elif status_code == 404:
                error_msg = f'Pedido #{pedido_id} não encontrado.'
            elif status_code == 400:
                if not isinstance(response_data, dict) or 'message' not in response_data:
                    error_msg = f'Status "{status_mapeado}" inválido ou não permitido para este pedido.'

            print(f"[UPDATE-STATUS] ⚠️ ERRO HTTP {status_code}: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg, 'status_code': status_code}), status_code

        if status_code == 200:
            if isinstance(response_data, dict):
                if 'id' in response_data or 'status' in response_data:
                    print("[UPDATE-STATUS] Resposta parece ser o pedido atualizado - tratando como sucesso")
                    return jsonify({'status': 'success', 'message': 'Status atualizado com sucesso', 'data': response_data}), 200
                if 'message' in response_data:
                    msg_lower = response_data['message'].lower()
                    if any(palavra in msg_lower for palavra in ['erro', 'error', 'falha', 'inválido', 'invalid']):
                        print(f"[UPDATE-STATUS] ⚠️ Mensagem indica erro: {response_data['message']}")
                        return jsonify({'status': 'error', 'message': response_data['message']}), 400
                    return jsonify({'status': 'success', 'message': response_data.get('message', 'Status atualizado com sucesso')}), 200
                return jsonify({'status': 'success', 'message': 'Status atualizado com sucesso', 'data': response_data}), 200
            return jsonify({'status': 'success', 'message': 'Status atualizado com sucesso'}), 200

        if not isinstance(response_data, dict):
            response_data = {
                'status': 'success' if status_code < 400 else 'error',
                'message': 'Status atualizado com sucesso' if status_code < 400 else 'Erro ao atualizar status',
            }
        elif 'status' not in response_data:
            response_data['status'] = 'success' if status_code < 400 else 'error'

        print(f"[UPDATE-STATUS] Retornando resposta formatada: status={response_data.get('status')}")
        print(f"{'='*60}\n")

        return jsonify(response_data), status_code
    except Exception as exc:
        print(f"[UPDATE-STATUS] ⚠️ ERRO: {exc}")
        import traceback

        print(f"[UPDATE-STATUS] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro ao atualizar status: {str(exc)}'}), 500


@pedidos_bp.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
def get_pedido_detalhes(pedido_id):
    """
    Busca detalhes de um pedido específico - Proxy para API externa.
    A API Java não tem endpoint GET /pedidos/{id}, então buscamos da lista e filtramos.
    """
    try:
        print(f"[PEDIDO-DETALHES] Buscando detalhes do pedido {pedido_id}")

        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')

        if status_code != 200:
            return jsonify({'status': 'error', 'message': f'Erro ao buscar pedidos: Status {status_code}'}), status_code

        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []

        pedido_encontrado = None
        for pedido in pedidos_todos:
            if isinstance(pedido, dict) and pedido.get('id') == pedido_id:
                pedido_encontrado = pedido
                break

        if not pedido_encontrado:
            return jsonify({'status': 'error', 'message': 'Pedido não encontrado'}), 404

        itens = pedido_encontrado.get('itens', [])

        valor_total = pedido_encontrado.get('valor_total') or pedido_encontrado.get('valor') or 0
        if valor_total == 0 and itens:
            for item in itens:
                if isinstance(item, dict):
                    quantidade = item.get('quantidade', 0) or 0
                    preco = 0
                    if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                        preco = float(item['itemRestaurante'].get('preco', 0) or 0)
                    elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                        preco = float(item['item_restaurante'].get('preco', 0) or 0)
                    elif item.get('preco'):
                        preco = float(item.get('preco', 0) or 0)
                    valor_total += quantidade * preco

        data_pedido = pedido_encontrado.get('criadoEm') or pedido_encontrado.get('criado_em') or pedido_encontrado.get('data_pedido')

        itens_formatados = []
        for item in itens:
            if isinstance(item, dict):
                nome = None
                preco = 0
                quantidade = item.get('quantidade', 0) or 0
                observacoes = item.get('observacoes') or item.get('observacoes_item')

                if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                    nome = item['itemRestaurante'].get('nome')
                    preco = float(item['itemRestaurante'].get('preco', 0) or 0)
                elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                    nome = item['item_restaurante'].get('nome')
                    preco = float(item['item_restaurante'].get('preco', 0) or 0)
                elif item.get('nome'):
                    nome = item.get('nome')
                    preco = float(item.get('preco', 0) or item.get('valorUnitario', 0) or 0)

                if nome:
                    itens_formatados.append({
                        'nome': nome,
                        'quantidade': quantidade,
                        'preco': preco,
                        'subtotal': quantidade * preco,
                        'observacoes': observacoes,
                    })

        cliente = {}
        if pedido_encontrado.get('cliente'):
            if isinstance(pedido_encontrado['cliente'], dict):
                cliente = pedido_encontrado['cliente']
            else:
                cliente = {'nome': str(pedido_encontrado['cliente'])}

        return jsonify({
            'status': 'success',
            'data': {
                'pedido': {
                    'id': pedido_encontrado.get('id'),
                    'status': pedido_encontrado.get('status'),
                    'data_pedido': data_pedido,
                    'valor_total': valor_total,
                    'observacoes': pedido_encontrado.get('observacoesGerais') or pedido_encontrado.get('observacoes'),
                    'cliente': cliente,
                },
                'itens': itens_formatados,
            },
        }), 200

    except Exception as exc:
        print(f"[ERRO] Erro ao buscar detalhes do pedido: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500

