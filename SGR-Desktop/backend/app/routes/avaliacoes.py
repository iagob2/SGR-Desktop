import json

from flask import Blueprint, jsonify, request

from ..proxy import proxy_request

avaliacoes_bp = Blueprint('avaliacoes', __name__)


@avaliacoes_bp.route('/api/avaliacoes/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes(restaurante_id):
    """Lista avaliações de um restaurante - Proxy para API externa."""
    try:
        print(f"[AVALIACOES] Buscando avaliações para restaurante {restaurante_id}")
        status_code, response_data = proxy_request('GET', f'avaliacoes/{restaurante_id}')

        if isinstance(response_data, list):
            print(f"[AVALIACOES] Retornando array direto com {len(response_data)} avaliações")
            return jsonify(response_data), status_code

        print(f"[AVALIACOES] Retornando objeto com status: {response_data.get('status', 'unknown')}")
        return jsonify(response_data), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao buscar avaliações: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@avaliacoes_bp.route('/api/avaliacoes-prato', methods=['POST'])
def criar_avaliacao_prato():
    """Cria uma avaliação de prato - Proxy para API externa."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400

        if not data.get('nota') or not data.get('prato'):
            return jsonify({'status': 'error', 'message': 'Campos obrigatórios: nota e prato.id'}), 400

        print("[AVALIACOES-PRATO] Criando avaliação de prato:")
        print(f"   Nota: {data.get('nota')}")
        print(f"   Prato ID: {data.get('prato', {}).get('id')}")
        print(f"   Comentário: {data.get('comentario', '')[:50]}...")

        status_code, response_data = proxy_request('POST', 'avaliacoes-prato', data=data)

        return jsonify(response_data), status_code

    except Exception as exc:
        print(f"[ERRO] Erro ao criar avaliação de prato: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@avaliacoes_bp.route('/api/avaliacoes/pratos/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes_pratos(restaurante_id):
    """
    Lista avaliações específicas de pratos por restaurante - Proxy para API externa.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[AVALIACOES-PRATO] Buscando avaliações de pratos para restaurante {restaurante_id}")
        print(f"[AVALIACOES-PRATO] Endpoint Flask: /api/avaliacoes/pratos/{restaurante_id}")

        status_code, response_data = proxy_request('GET', 'avaliacoes-prato')

        print(f"[AVALIACOES-PRATO] Status code recebido: {status_code}")
        print(f"[AVALIACOES-PRATO] Tipo de resposta: {type(response_data)}")

        if status_code >= 400:
            print(f"[AVALIACOES-PRATO] ⚠️ Erro na API externa: {status_code}")
            if isinstance(response_data, dict):
                error_msg = response_data.get('message', response_data.get('error', 'Erro desconhecido'))
                print(f"[AVALIACOES-PRATO] Mensagem de erro: {error_msg}")
                return jsonify({'status': 'error', 'message': error_msg}), status_code
            return jsonify({'status': 'error', 'message': f'Erro ao buscar avaliações de pratos: Status {status_code}'}), status_code

        avaliacoes_todas = []
        if isinstance(response_data, list):
            avaliacoes_todas = response_data
        elif isinstance(response_data, dict):
            avaliacoes_todas = response_data.get('avaliacoes', []) or response_data.get('data', [])
            if not isinstance(avaliacoes_todas, list):
                avaliacoes_todas = []

        print(f"[AVALIACOES-PRATO] Total de avaliações recebidas: {len(avaliacoes_todas)}")

        if len(avaliacoes_todas) > 0:
            primeira_avaliacao = avaliacoes_todas[0]
            print(f"[AVALIACOES-PRATO] Estrutura da primeira avaliação: {json.dumps(primeira_avaliacao, indent=2, default=str)[:500]}")

        avaliacoes_filtradas = []

        try:
            status_itens, response_itens = proxy_request('GET', 'itens')
            itens_restaurante_ids = set()
            if status_itens == 200:
                itens_data = response_itens if isinstance(response_itens, list) else (
                    response_itens.get('data', []) if isinstance(response_itens, dict) else []
                )
                for item in itens_data:
                    if isinstance(item, dict):
                        item_id = item.get('id')
                        item_restaurante_id = None
                        if item.get('restaurante') and isinstance(item.get('restaurante'), dict):
                            item_restaurante_id = item['restaurante'].get('id')
                        elif item.get('restaurante_id'):
                            item_restaurante_id = item['restaurante_id']

                        if item_restaurante_id and int(item_restaurante_id) == int(restaurante_id) and item_id:
                            itens_restaurante_ids.add(int(item_id))

            print(f"[AVALIACOES-PRATO] IDs de itens do restaurante {restaurante_id}: {len(itens_restaurante_ids)} itens")
        except Exception as exc:
            print(f"[AVALIACOES-PRATO] ⚠️ Erro ao buscar itens do restaurante: {exc}")
            itens_restaurante_ids = set()

        for avaliacao in avaliacoes_todas:
            if not isinstance(avaliacao, dict):
                continue

            restaurante_id_avaliacao = None
            prato_id = None

            if avaliacao.get('prato') and isinstance(avaliacao.get('prato'), dict):
                prato = avaliacao['prato']
                prato_id = prato.get('id')

                if prato.get('restaurante') and isinstance(prato.get('restaurante'), dict):
                    restaurante_id_avaliacao = prato['restaurante'].get('id')
                elif prato.get('restaurante_id'):
                    restaurante_id_avaliacao = prato['restaurante_id']
                elif prato.get('itemRestaurante') and isinstance(prato.get('itemRestaurante'), dict):
                    item_restaurante = prato['itemRestaurante']
                    if item_restaurante.get('restaurante') and isinstance(item_restaurante.get('restaurante'), dict):
                        restaurante_id_avaliacao = item_restaurante['restaurante'].get('id')
                    elif item_restaurante.get('restaurante_id'):
                        restaurante_id_avaliacao = item_restaurante['restaurante_id']

            pertence_ao_restaurante = False

            if restaurante_id_avaliacao and int(restaurante_id_avaliacao) == int(restaurante_id):
                pertence_ao_restaurante = True
            elif prato_id and int(prato_id) in itens_restaurante_ids:
                pertence_ao_restaurante = True

            if pertence_ao_restaurante:
                avaliacoes_filtradas.append(avaliacao)

        print(f"[AVALIACOES-PRATO] Avaliações filtradas para restaurante {restaurante_id}: {len(avaliacoes_filtradas)}")

        media_notas = 0
        if len(avaliacoes_filtradas) > 0:
            soma_notas = sum(float(avaliacao.get('nota', 0)) for avaliacao in avaliacoes_filtradas)
            media_notas = soma_notas / len(avaliacoes_filtradas)

        resultado = {
            'status': 'success',
            'data': {
                'avaliacoes': avaliacoes_filtradas,
                'resumo': {
                    'media_notas': round(media_notas, 2),
                    'total_avaliacoes': len(avaliacoes_filtradas),
                },
            },
        }

        print(f"[AVALIACOES-PRATO] Retornando {len(avaliacoes_filtradas)} avaliações com média {media_notas:.2f}")
        return jsonify(resultado), 200

    except Exception as exc:
        print(f"[ERRO] Erro ao carregar avaliacoes de pratos: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500

