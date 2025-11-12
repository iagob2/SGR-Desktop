import json
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify

from ..proxy import proxy_request
from ..utils.status import is_status_concluido

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/top-produtos/<int:restaurante_id>/<periodo>')
def get_top_produtos(restaurante_id, periodo):
    """
    Endpoint para obter top 3 produtos mais vendidos.
    Usa /pedidos/restaurante da API Java e calcula localmente.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[TOP-PRODUTOS] Buscando top produtos {periodo} para restaurante {restaurante_id}")

        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')

        if status_code != 200:
            print(f"[TOP-PRODUTOS] Erro ao buscar pedidos: {status_code}")
            return jsonify({'status': 'error', 'message': f'Erro ao buscar pedidos: Status {status_code}'}), status_code

        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []

        hoje = datetime.now().date()
        if periodo == 'semanal':
            data_inicio = hoje - timedelta(days=7)
        elif periodo == 'mensal':
            data_inicio = hoje - timedelta(days=30)
        elif periodo == 'anual':
            data_inicio = hoje - timedelta(days=365)
        else:
            return jsonify({'status': 'error', 'message': 'Período inválido. Use: semanal, mensal ou anual'}), 400

        produtos_vendidos = defaultdict(
            lambda: {'quantidade': 0, 'valor_total': 0, 'nome': None, 'preco_unitario': 0}
        )

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

            data_pedido = None
            if pedido.get('criadoEm'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                except Exception:
                    pass
            elif pedido.get('criado_em'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                except Exception:
                    pass

            if not data_pedido or data_pedido < data_inicio:
                continue

            if not is_status_concluido(pedido.get('status')):
                continue

            if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                for item in pedido['itens']:
                    if not isinstance(item, dict):
                        continue

                    produto_id = None
                    produto_nome = None
                    quantidade = item.get('quantidade', 0) or item.get('quantidadeItem', 0) or 1
                    preco_unitario = 0

                    if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                        item_rest = item['itemRestaurante']
                        produto_id = item_rest.get('id')
                        produto_nome = item_rest.get('nome')
                        preco_unitario = float(item_rest.get('preco', 0) or 0)
                    elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                        item_rest = item['item_restaurante']
                        produto_id = item_rest.get('id')
                        produto_nome = item_rest.get('nome')
                        preco_unitario = float(item_rest.get('preco', 0) or 0)

                    if not produto_nome:
                        produto_id = item.get('produto_id') or item.get('id')
                        produto_nome = item.get('nome') or item.get('produto_nome') or f"Item #{produto_id}"

                    if preco_unitario == 0:
                        preco_unitario = float(
                            item.get('preco', 0)
                            or item.get('valorUnitario', 0)
                            or item.get('valor', 0)
                            or 0
                        )

                    if preco_unitario == 0 and item.get('subtotal'):
                        preco_unitario = float(item['subtotal']) / quantidade

                    if produto_nome:
                        chave_produto = produto_id or produto_nome

                        produtos_vendidos[chave_produto]['quantidade'] += quantidade
                        produtos_vendidos[chave_produto]['valor_total'] += quantidade * preco_unitario
                        if not produtos_vendidos[chave_produto]['nome']:
                            produtos_vendidos[chave_produto]['nome'] = produto_nome
                        if preco_unitario > produtos_vendidos[chave_produto]['preco_unitario']:
                            produtos_vendidos[chave_produto]['preco_unitario'] = preco_unitario

        produtos_ordenados = sorted(
            produtos_vendidos.items(), key=lambda item: item[1]['quantidade'], reverse=True
        )[:3]

        produtos_formatados = []
        for posicao, (produto_key, dados) in enumerate(produtos_ordenados, 1):
            valor_unitario = (
                dados['preco_unitario']
                if dados['preco_unitario'] > 0
                else (dados['valor_total'] / dados['quantidade'] if dados['quantidade'] > 0 else 0)
            )
            produtos_formatados.append({
                'posicao': posicao,
                'nome': dados['nome'] or f'Produto {produto_key}',
                'quantidade_vendida': dados['quantidade'],
                'valor_unitario': valor_unitario,
                'valor_total_vendas': dados['valor_total'],
            })

        print(f"[TOP-PRODUTOS] Top 3 produtos encontrados: {len(produtos_formatados)}")

        return jsonify({
            'status': 'success',
            'data': {'periodo': periodo, 'produtos': produtos_formatados},
        }), 200

    except Exception as exc:
        print(f"[ERRO] Erro no endpoint de top produtos: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro interno: {str(exc)}'}), 500


@analytics_bp.route('/api/vendas/<int:restaurante_id>/<periodo>')
def get_vendas_periodo(restaurante_id, periodo):
    """
    Endpoint para obter dados de vendas por período.
    Usa /pedidos/restaurante da API Java e calcula localmente.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[VENDAS-PERIODO] Buscando vendas {periodo} para restaurante {restaurante_id}")

        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')

        if status_code != 200:
            print(f"[VENDAS-PERIODO] Erro ao buscar pedidos: {status_code}")
            return jsonify({'status': 'error', 'message': f'Erro ao buscar pedidos: Status {status_code}'}), status_code

        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []

        pedidos_restaurante = []
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

            if 'itens' not in pedido:
                pedido['itens'] = []

            pedidos_restaurante.append(pedido)

        print(f"[VENDAS-PERIODO] Total de pedidos do restaurante: {len(pedidos_restaurante)}")

        hoje = datetime.now().date()
        if periodo == 'semanal':
            data_inicio = hoje - timedelta(days=28)
            dias_agrupamento = 7
        elif periodo == 'mensal':
            data_inicio = hoje - timedelta(days=180)
            dias_agrupamento = 30
        elif periodo == 'anual':
            data_inicio = hoje - timedelta(days=1825)
            dias_agrupamento = 365
        else:
            return jsonify({'status': 'error', 'message': 'Período inválido. Use: semanal, mensal ou anual'}), 400

        vendas_por_periodo = {}
        produtos_por_periodo = {}

        for pedido in pedidos_restaurante:
            data_pedido = None
            if pedido.get('criadoEm'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                except Exception:
                    pass
            elif pedido.get('criado_em'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                except Exception:
                    pass

            if not data_pedido or data_pedido < data_inicio:
                continue

            valor_pedido = 0
            quantidade_itens = 0

            if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                for item in pedido['itens']:
                    if isinstance(item, dict):
                        quantidade = item.get('quantidade', 0) or 0
                        preco = 0

                        if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                            preco = float(item['itemRestaurante'].get('preco', 0) or 0)
                        elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                            preco = float(item['item_restaurante'].get('preco', 0) or 0)
                        elif item.get('preco'):
                            preco = float(item.get('preco', 0) or 0)
                        elif item.get('valorUnitario'):
                            preco = float(item.get('valorUnitario', 0) or 0)

                        valor_pedido += quantidade * preco
                        quantidade_itens += quantidade

            if valor_pedido == 0:
                valor_pedido = float(
                    pedido.get('valor_total', 0)
                    or pedido.get('valor', 0)
                    or pedido.get('valorTotal', 0)
                    or 0
                )

            if periodo == 'semanal':
                dias_diferenca = (hoje - data_pedido).days
                semana_num = 3 - (dias_diferenca // 7)
                if semana_num < 0 or semana_num > 3:
                    continue
                periodo_key = f'Sem {semana_num + 1}'
            elif periodo == 'mensal':
                periodo_key = data_pedido.strftime('%Y-%m')
            else:
                periodo_key = data_pedido.strftime('%Y')

            if periodo_key not in vendas_por_periodo:
                vendas_por_periodo[periodo_key] = 0
                produtos_por_periodo[periodo_key] = 0

            vendas_por_periodo[periodo_key] += valor_pedido
            produtos_por_periodo[periodo_key] += quantidade_itens

        if periodo == 'semanal':
            labels = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
        elif periodo == 'mensal':
            labels = []
            meses_abreviados_pt = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez',
            }
            for indice in range(6):
                mes_atual = hoje.month
                ano_atual = hoje.year
                mes_num = mes_atual - indice
                ano_num = ano_atual
                while mes_num <= 0:
                    mes_num += 12
                    ano_num -= 1
                chave_mes = f'{ano_num}-{mes_num:02d}'
                label_mes = meses_abreviados_pt[mes_num]
                labels.insert(0, label_mes)
                if chave_mes not in vendas_por_periodo:
                    vendas_por_periodo[chave_mes] = 0
                    produtos_por_periodo[chave_mes] = 0
        else:
            labels = []
            for indice in range(5):
                ano = hoje.year - indice
                labels.insert(0, str(ano))

        if periodo == 'mensal':
            vendas_data = []
            produtos_data = []
            for indice in range(6):
                mes_atual = hoje.month
                ano_atual = hoje.year
                mes_num = mes_atual - indice
                ano_num = ano_atual
                while mes_num <= 0:
                    mes_num += 12
                    ano_num -= 1
                chave_mes = f'{ano_num}-{mes_num:02d}'
                vendas_data.insert(0, vendas_por_periodo.get(chave_mes, 0))
                produtos_data.insert(0, produtos_por_periodo.get(chave_mes, 0))
        else:
            vendas_data = [vendas_por_periodo.get(label, 0) for label in labels]
            produtos_data = [produtos_por_periodo.get(label, 0) for label in labels]

        print(f"[VENDAS-PERIODO] Dados calculados: labels={labels}, vendas={vendas_data}, produtos={produtos_data}")

        return jsonify({
            'status': 'success',
            'data': {
                'periodo': periodo,
                'labels': labels,
                'vendas': vendas_data,
                'produtos': produtos_data,
            },
        }), 200

    except Exception as exc:
        print(f"[ERRO] Erro no endpoint de vendas por periodo: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro interno: {str(exc)}'}), 500


@analytics_bp.route('/api/dashboard/<int:restaurante_id>', methods=['GET'])
def get_dashboard_completo(restaurante_id):
    """
    Endpoint centralizado para dados analíticos do dashboard.
    Busca pedidos da API externa e calcula métricas baseado em pedidos concluídos.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[DASHBOARD] Buscando dados para restaurante {restaurante_id}")

        try:
            from ..services.diagnostics import verificar_conectividade_api  # noqa: F401  # Import only for side-effects?
        except Exception:
            pass

        try:
            from flask import current_app  # noqa: F401
        except Exception:
            pass

        try:
            response_internal = requests.get(
                f'http://localhost:5000/api/pedidos/restaurante/{restaurante_id}/concluidos',
                timeout=10,
            )

            if response_internal.status_code == 200:
                data_internal = response_internal.json()
                if data_internal.get('status') == 'success':
                    pedidos = data_internal.get('data', [])
                    print(f"[DASHBOARD] Pedidos CONCLUÍDOS encontrados via endpoint específico: {len(pedidos)}")
                else:
                    pedidos = []
                    print(f"[DASHBOARD] Endpoint retornou erro: {data_internal.get('message')}")
            else:
                print(f"[DASHBOARD] Erro ao chamar endpoint de pedidos concluídos: {response_internal.status_code}")
                pedidos = []
        except Exception as exc:
            print(f"[DASHBOARD] Erro ao buscar pedidos concluídos: {exc}")
            import traceback

            print(f"[DASHBOARD] Traceback: {traceback.format_exc()}")
            pedidos = []

        pedidos_concluidos = pedidos
        print(f"[DASHBOARD] Total de pedidos concluídos do restaurante: {len(pedidos_concluidos)}")

        if len(pedidos_concluidos) > 0:
            print(f"[DASHBOARD] Primeiro pedido encontrado: {json.dumps(pedidos_concluidos[0], indent=2, default=str)[:300]}")
        else:
            print(f"[DASHBOARD] ⚠️ Nenhum pedido concluído encontrado para restaurante {restaurante_id}")

        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)
        semana_atras = hoje - timedelta(days=7)
        mes_atras = hoje - timedelta(days=30)

        total_vendas = 0
        produtos_vendidos = 0
        pedidos_hoje = 0
        vendas_hoje = 0

        vendas_ontem = 0
        pedidos_ontem = 0

        vendas_por_dia = {}
        produtos_por_dia = {}

        for indice in range(7):
            data = hoje - timedelta(days=6 - indice)
            vendas_por_dia[data.strftime('%Y-%m-%d')] = 0
            produtos_por_dia[data.strftime('%Y-%m-%d')] = 0

        for pedido in pedidos_concluidos:
            valor_pedido = 0
            quantidade_itens = 0

            if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                for item in pedido['itens']:
                    if isinstance(item, dict):
                        quantidade = item.get('quantidade', 0) or item.get('quantidadeItem', 0) or 0
                        preco = 0

                        if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                            preco = float(item['itemRestaurante'].get('preco', 0) or item['itemRestaurante'].get('valor', 0) or 0)
                        elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                            preco = float(item['item_restaurante'].get('preco', 0) or item['item_restaurante'].get('valor', 0) or 0)
                        elif item.get('preco'):
                            preco = float(item.get('preco', 0) or 0)
                        elif item.get('valorUnitario'):
                            preco = float(item.get('valorUnitario', 0) or 0)
                        elif item.get('valor'):
                            preco = float(item.get('valor', 0) or 0)
                        elif item.get('subtotal') and quantidade > 0:
                            preco = float(item.get('subtotal', 0) or 0) / quantidade

                        valor_pedido += quantidade * preco
                        quantidade_itens += quantidade

            if valor_pedido == 0:
                valor_pedido = float(
                    pedido.get('valor_total', 0)
                    or pedido.get('valor', 0)
                    or pedido.get('valorTotal', 0)
                    or pedido.get('total', 0)
                    or 0
                )

            if valor_pedido == 0:
                print(f"[DASHBOARD] AVISO: Pedido {pedido.get('id')} tem valor zero. Estrutura: {json.dumps(pedido, indent=2, default=str)[:500]}")

            data_pedido_str = None
            if pedido.get('criadoEm'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                    data_pedido_str = data_pedido.strftime('%Y-%m-%d')
                except Exception:
                    pass
            elif pedido.get('criado_em'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                    data_pedido_str = data_pedido.strftime('%Y-%m-%d')
                except Exception:
                    pass

            total_vendas += valor_pedido
            produtos_vendidos += quantidade_itens

            if data_pedido_str:
                if data_pedido_str in vendas_por_dia:
                    vendas_por_dia[data_pedido_str] += valor_pedido
                    produtos_por_dia[data_pedido_str] += quantidade_itens

                if data_pedido_str == hoje.strftime('%Y-%m-%d'):
                    vendas_hoje += valor_pedido
                    pedidos_hoje += 1
                elif data_pedido_str == ontem.strftime('%Y-%m-%d'):
                    vendas_ontem += valor_pedido
                    pedidos_ontem += 1

        ticket_medio = total_vendas / len(pedidos_concluidos) if len(pedidos_concluidos) > 0 else 0

        if vendas_ontem > 0:
            evolucao_percentual = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
        elif vendas_hoje > 0 and vendas_ontem == 0:
            evolucao_percentual = 100
        elif vendas_hoje == 0 and vendas_ontem == 0:
            evolucao_percentual = 0
        elif vendas_hoje == 0 and vendas_ontem > 0:
            evolucao_percentual = -100
        else:
            evolucao_percentual = 0

        print(f"[DASHBOARD] Evolução calculada: vendas_hoje={vendas_hoje}, vendas_ontem={vendas_ontem}, evolucao={evolucao_percentual:.1f}%")

        cards = {
            'total_vendas': {
                'valor': f'R$ {total_vendas:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                'valor_numerico': total_vendas,
            },
            'quantidade_produtos': {
                'valor': str(produtos_vendidos),
                'valor_numerico': produtos_vendidos,
            },
            'ticket_medio_diario': {
                'valor': f'R$ {ticket_medio:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                'valor_numerico': ticket_medio,
            },
            'evolucao_percentual': {
                'valor': f'{evolucao_percentual:+.1f}%',
                'valor_numerico': evolucao_percentual,
                'tipo': 'positive' if evolucao_percentual >= 0 else 'negative',
            },
        }

        hoje_data = datetime.now().date()
        todos_os_dias = [(hoje_data - timedelta(days=6 - indice)).strftime('%Y-%m-%d') for indice in range(7)]

        dias_ordenados = sorted(set(todos_os_dias + list(vendas_por_dia.keys())))
        labels_vendas = [datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m') for data in dias_ordenados]
        data_vendas = [vendas_por_dia.get(data, 0) for data in dias_ordenados]

        dias_ordenados_produtos = sorted(set(todos_os_dias + list(produtos_por_dia.keys())))
        labels_produtos = [datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m') for data in dias_ordenados_produtos]
        data_produtos = [produtos_por_dia.get(data, 0) for data in dias_ordenados_produtos]

        graficos = {
            'valor_diario': {
                'labels': labels_vendas,
                'data': data_vendas,
            },
            'produtos_diarios': {
                'labels': labels_produtos,
                'data': data_produtos,
            },
        }

        print(f"[DASHBOARD] Tem vendas significativas: {any(v > 0 for v in data_vendas)}, Tem produtos significativos: {any(p > 0 for p in data_produtos)}")
        print(f"[DASHBOARD] Labels vendas: {labels_vendas}")
        print(f"[DASHBOARD] Data vendas: {data_vendas}")
        print(f"[DASHBOARD] Labels produtos: {labels_produtos}")
        print(f"[DASHBOARD] Data produtos: {data_produtos}")
        print(f"[DASHBOARD] Métricas calculadas:")
        print(f"   Total de vendas: R$ {total_vendas:.2f}")
        print(f"   Produtos vendidos: {produtos_vendidos}")
        print(f"   Ticket médio: R$ {ticket_medio:.2f}")
        print(f"   Evolução: {evolucao_percentual:.1f}%")
        print(f"   Pedidos processados: {len(pedidos_concluidos)}")
        print(f"[DASHBOARD] Cards a retornar: {json.dumps(cards, indent=2, default=str)}")
        print(f"[DASHBOARD] Graficos a retornar: labels={graficos.get('valor_diario', {}).get('labels', [])[:3]}..., data={graficos.get('valor_diario', {}).get('data', [])[:3]}...")

        return jsonify({'status': 'success', 'data': {'cards': cards, 'graficos': graficos}}), 200

    except Exception as exc:
        print(f"[ERRO] ERRO no dashboard: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'success',
            'data': {'cards': {}, 'graficos': {}},
            'message': 'Dashboard carregado (erro ao buscar dados)',
        }), 200

