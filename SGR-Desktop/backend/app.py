#!/usr/bin/env python3
"""
Backend Flask para SGR-Desktop
Sistema de Gerenciamento de Restaurantes - Conecta com banco PostgreSQL Saborê
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv('config.env')

app = Flask(__name__)
CORS(app)

# Configurações do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'sabore'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '157428'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """Estabelece conexão com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None

def execute_query(query, params=None):
    """
    Executa query SELECT e retorna resultados.
    
    Esta função é usada para operações de leitura (SELECT) que não modificam
    o banco de dados.
    
    Args:
        query: SQL query a ser executada
        params: Parâmetros para a query (tupla ou lista)
        
    Returns:
        Lista de resultados (RealDictRow) ou None em caso de erro
        
    Raises:
        psycopg2.Error: Se houver erro na conexão ou execução
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except psycopg2.Error as e:
        print(f"Erro ao executar query: {e}")
        return None

def execute_query_with_commit(query, params=None):
    """
    Executa query INSERT/UPDATE/DELETE e faz commit.
    
    Esta função é usada para operações de escrita que modificam o banco de dados.
    Faz commit automático após a execução bem-sucedida e rollback em caso de erro.
    
    Args:
        query: SQL query a ser executada (INSERT, UPDATE, DELETE)
        params: Parâmetros para a query (tupla ou lista)
        
    Returns:
        Lista de resultados (RealDictRow) ou None em caso de erro
        
    Raises:
        psycopg2.Error: Se houver erro na conexão ou execução
        
    🔥 IMPORTANTE: Esta função faz COMMIT das alterações!
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        results = cur.fetchall()
        conn.commit()  # 🔥 CRÍTICO: Fazer commit das alterações
        cur.close()
        conn.close()
        return results
    except psycopg2.Error as e:
        print(f"Erro ao executar query com commit: {e}")
        if conn:
            conn.rollback()  # 🔥 CRÍTICO: Rollback em caso de erro
            conn.close()
        return None

# ============================================================================
# VENDAS ENDPOINTS
# ============================================================================
# 🔥 IMPORTANTE: Todas as queries de pedidos usam o campo 'criado_em' para data
# Não existe o campo 'data_pedido' ou 'valor_total' na tabela pedido.
# Valor total é calculado via JOIN com item_pedido e item_restaurante.
# ============================================================================

@app.route('/api/top-produtos/<int:restaurante_id>/<periodo>')
def get_top_produtos(restaurante_id, periodo):
    """
    Endpoint para obter top 3 produtos mais vendidos por período
    Períodos: semanal, mensal, anual
    """
    try:
        
        if periodo == 'semanal':
            # Top produtos das últimas 4 semanas
            query = """
                SELECT 
                    ir.nome,
                    ir.preco as valor_unitario,
                    SUM(ip.quantidade) as quantidade_vendida,
                    SUM(ip.quantidade * ir.preco) as valor_total_vendas,
                    ROW_NUMBER() OVER (ORDER BY SUM(ip.quantidade * ir.preco) DESC) as posicao
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '4 weeks'
                GROUP BY ir.id, ir.nome, ir.preco
                ORDER BY valor_total_vendas DESC
                LIMIT 3
            """
            
        elif periodo == 'mensal':
            # Top produtos dos últimos 6 meses
            query = """
                SELECT 
                    ir.nome,
                    ir.preco as valor_unitario,
                    SUM(ip.quantidade) as quantidade_vendida,
                    SUM(ip.quantidade * ir.preco) as valor_total_vendas,
                    ROW_NUMBER() OVER (ORDER BY SUM(ip.quantidade * ir.preco) DESC) as posicao
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY ir.id, ir.nome, ir.preco
                ORDER BY valor_total_vendas DESC
                LIMIT 3
            """
            
        elif periodo == 'anual':
            # Top produtos dos últimos 5 anos
            query = """
                SELECT 
                    ir.nome,
                    ir.preco as valor_unitario,
                    SUM(ip.quantidade) as quantidade_vendida,
                    SUM(ip.quantidade * ir.preco) as valor_total_vendas,
                    ROW_NUMBER() OVER (ORDER BY SUM(ip.quantidade * ir.preco) DESC) as posicao
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '5 years'
                GROUP BY ir.id, ir.nome, ir.preco
                ORDER BY valor_total_vendas DESC
                LIMIT 3
            """
        else:
            return jsonify({
                'status': 'error',
                'message': 'Período inválido. Use: semanal, mensal ou anual'
            }), 400
        
        dados_produtos = execute_query(query, (restaurante_id,))
        
        # Processar dados para o formato esperado pelo frontend
        produtos = []
        
        for row in dados_produtos:
            produtos.append({
                'posicao': int(row['posicao']),
                'nome': row['nome'],
                'valor_unitario': float(row['valor_unitario']),
                'quantidade_vendida': int(row['quantidade_vendida']),
                'valor_total_vendas': float(row['valor_total_vendas'])
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'periodo': periodo,
                'produtos': produtos
            }
        })
        
    except Exception as e:
        print(f"❌ Erro no endpoint de top produtos: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        }), 500

# ============================================================================
# CARDÁPIO ENDPOINTS (CRUD)
# ============================================================================

@app.route('/api/cardapio/<int:restaurante_id>', methods=['GET'])
def listar_cardapio(restaurante_id):
    """
    Rota para LER (Listar) todos os itens do cardápio de um restaurante
    """
    try:
        
        # Query para buscar todos os itens do restaurante
        query = """
            SELECT 
                ir.id,
                ir.nome,
                ir.descricao,
                ir.preco,
                ir.imagem_url,
                ir.restaurante_id
            FROM item_restaurante ir
            WHERE ir.restaurante_id = %s
            ORDER BY ir.nome
        """
        
        itens = execute_query(query, (restaurante_id,))
        
        # Verificar se a query retornou dados
        if not itens:
            print(f"⚠️ Nenhum item encontrado para restaurante {restaurante_id}")
            return jsonify({
                'status': 'success',
                'data': []
            })
        
        # Processar dados para o formato esperado pelo frontend
        cardapio = []
        for item in itens:
            cardapio.append({
                'id': item['id'],
                'nome': item['nome'],
                'descricao': item['descricao'] or 'Sem descrição',
                'preco': float(item['preco']),
                'imagemUrl': item['imagem_url'] or ''
            })
        
        print(f"✅ Cardápio carregado: {len(cardapio)} itens")
        
        return jsonify({
            'status': 'success',
            'data': cardapio
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar cardápio: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao listar o cardápio: {str(e)}'
        }), 500

@app.route('/api/cardapio/add', methods=['POST'])
def adicionar_item():
    """
    Rota para CRIAR (Adicionar) um novo item ao cardápio
    """
    try:
        dados = request.get_json()
        print(f"➕ Adicionando novo item: {dados}")
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['restaurante_id', 'nome', 'preco']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({
                    'status': 'error',
                    'message': f'Campo obrigatório faltando: {campo}'
                }), 400
        
        # Query para inserir novo item
        query = """
            INSERT INTO item_restaurante (restaurante_id, nome, descricao, preco, imagem_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        valores = (
            dados.get('restaurante_id'),
            dados.get('nome'),
            dados.get('descricao', ''),
            dados.get('preco'),
            dados.get('imagemUrl', '')
        )
        
        resultado = execute_query_with_commit(query, valores)
        
        # Verificar se a inserção foi bem-sucedida
        if not resultado:
            raise Exception('Falha ao inserir item no banco de dados')
            
        novo_id = resultado[0]['id'] if resultado else None
        
        if novo_id:
            print(f"✅ Item adicionado com ID: {novo_id}")
            return jsonify({
                'status': 'success',
                'message': 'Item adicionado com sucesso',
                'data': {'id': novo_id}
            }), 201
        else:
            raise Exception('Falha ao obter ID do novo item')
            
    except Exception as e:
        print(f"❌ Erro ao adicionar item: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao adicionar item: {str(e)}'
        }), 500

@app.route('/api/cardapio/edit/<int:item_id>', methods=['PUT'])
def editar_item(item_id):
    """
    Rota para ATUALIZAR (Editar) um item existente
    """
    try:
        dados = request.get_json()
        print(f"✏️ Editando item {item_id}: {dados}")
        
        # Query para atualizar item
        query = """
            UPDATE item_restaurante 
            SET nome = %s, 
                descricao = %s, 
                preco = %s, 
                imagem_url = %s
            WHERE id = %s
            RETURNING id
        """
        
        valores = (
            dados.get('nome'),
            dados.get('descricao', ''),
            dados.get('preco'),
            dados.get('imagemUrl', ''),
            item_id
        )
        
        resultado = execute_query_with_commit(query, valores)
        
        if resultado:
            print(f"✅ Item {item_id} atualizado com sucesso")
            return jsonify({
                'status': 'success',
                'message': f'Item {item_id} atualizado com sucesso'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Item não encontrado'
            }), 404
            
    except Exception as e:
        print(f"❌ Erro ao editar item: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao atualizar item: {str(e)}'
        }), 500

@app.route('/api/cardapio/<int:item_id>', methods=['DELETE'])
def deletar_item(item_id):
    """
    Rota para DELETAR um item
    Implementa soft delete quando há dependências
    """
    try:
        print(f"🗑️ Deletando item {item_id}")
        
        # Verificar se o item está sendo usado em pedidos
        pedidos_item = execute_query("""
            SELECT COUNT(*) as total 
            FROM item_pedido 
            WHERE item_restaurante_id = %s
        """, (item_id,))
        
        total_pedidos = pedidos_item[0]['total'] if pedidos_item else 0
        
        if total_pedidos > 0:
            # Item está em pedidos - usar soft delete (adicionar campo disponivel = false)
            print(f"⚠️ Item {item_id} está em {total_pedidos} pedido(s). Usando soft delete.")
            
            # Se não tiver campo 'disponivel', simplesmente informar
            return jsonify({
                'status': 'error',
                'message': f'Não é possível excluir este item pois ele já foi vendido em {total_pedidos} pedido(s). Considere removê-lo apenas visualmente do cardápio.',
                'sugestao': 'Este item permanecerá no histórico de pedidos para referência.'
            }), 409  # Conflict
        else:
            # Item não está em pedidos - pode deletar normalmente
            query = "DELETE FROM item_restaurante WHERE id = %s RETURNING id"
            resultado = execute_query_with_commit(query, (item_id,))
            
            if resultado:
                print(f"✅ Item {item_id} deletado com sucesso")
                return jsonify({
                    'status': 'success',
                    'message': f'Item {item_id} excluído com sucesso'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Item não encontrado'
                }), 404
            
    except Exception as e:
        print(f"❌ Erro ao deletar item: {e}")
        
        # Capturar erro de Foreign Key
        if "foreign key constraint" in str(e).lower():
            return jsonify({
                'status': 'error',
                'message': 'Não é possível excluir este item pois ele já foi vendido em pedidos. Este item precisa permanecer no sistema para manter a integridade dos históricos.',
                'codigo': 'FOREIGN_KEY_CONSTRAINT'
            }), 409  # Conflict
        else:
            return jsonify({
                'status': 'error',
                'message': f'Falha ao deletar item: {str(e)}'
            }), 500


@app.route('/api/vendas/<int:restaurante_id>/<periodo>')
def get_vendas_periodo(restaurante_id, periodo):
    """
    Endpoint para obter dados de vendas por período específico
    Períodos: semanal, mensal, anual
    """
    try:
        
        if periodo == 'semanal':
            # Dados das últimas 4 semanas
            query = """
                SELECT 
                    DATE_TRUNC('week', p.criado_em) as semana,
                    COALESCE(SUM(ip.quantidade * ir.preco), 0) as vendas_semana,
                    COALESCE(SUM(ip.quantidade), 0) as produtos_semana
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '4 weeks'
                GROUP BY DATE_TRUNC('week', p.criado_em)
                ORDER BY semana DESC
                LIMIT 4
            """
            
        elif periodo == 'mensal':
            # Dados dos últimos 6 meses
            query = """
                SELECT 
                    DATE_TRUNC('month', p.criado_em) as mes,
                    COALESCE(SUM(ip.quantidade * ir.preco), 0) as vendas_mes,
                    COALESCE(SUM(ip.quantidade), 0) as produtos_mes
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', p.criado_em)
                ORDER BY mes DESC
                LIMIT 6
            """
            
        elif periodo == 'anual':
            # Dados dos últimos 5 anos
            query = """
                SELECT 
                    DATE_TRUNC('year', p.criado_em) as ano,
                    COALESCE(SUM(ip.quantidade * ir.preco), 0) as vendas_ano,
                    COALESCE(SUM(ip.quantidade), 0) as produtos_ano
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND p.criado_em >= CURRENT_DATE - INTERVAL '5 years'
                GROUP BY DATE_TRUNC('year', p.criado_em)
                ORDER BY ano DESC
                LIMIT 5
            """
        else:
            return jsonify({
                'status': 'error',
                'message': 'Período inválido. Use: semanal, mensal ou anual'
            }), 400
        
        dados_periodo = execute_query(query, (restaurante_id,))
        
        # Processar dados para o formato esperado pelo frontend
        labels = []
        vendas_data = []
        produtos_data = []
        
        for row in dados_periodo:
            if periodo == 'semanal':
                labels.append(f"Sem {len(labels) + 1}")
                vendas_data.append(float(row['vendas_semana']))
                produtos_data.append(int(row['produtos_semana']))
            elif periodo == 'mensal':
                mes_nome = row['mes'].strftime('%b')
                labels.append(mes_nome)
                vendas_data.append(float(row['vendas_mes']))
                produtos_data.append(int(row['produtos_mes']))
            elif periodo == 'anual':
                ano = row['ano'].strftime('%Y')
                labels.append(ano)
                vendas_data.append(float(row['vendas_ano']))
                produtos_data.append(int(row['produtos_ano']))
        
        # Garantir que temos pelo menos alguns dados
        if not labels:
            labels = ['Sem dados'] if periodo == 'semanal' else ['Sem dados']
            vendas_data = [0]
            produtos_data = [0]
        
        return jsonify({
            'status': 'success',
            'data': {
                'periodo': periodo,
                'labels': labels,
                'vendas': vendas_data,
                'produtos': produtos_data
            }
        })
        
    except Exception as e:
        print(f"❌ Erro no endpoint de vendas por período: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        }), 500

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/<int:restaurante_id>', methods=['GET'])
def get_dashboard_completo(restaurante_id):
    """
    Endpoint centralizado para dados analíticos do dashboard
    Retorna todos os dados necessários para cards e gráficos
    """
    try:
        print(f"\n🔥 DASHBOARD DEBUG - Restaurante ID: {restaurante_id}")
        
        # ========================================================================
        # CÁLCULO DAS MÉTRICAS DOS CARDS (Visão Geral)
        # ========================================================================
        
        # 1. Total de Vendas de TODO o banco de dados (não apenas última semana)
        print(f"📊 Executando query de vendas totais...")
        vendas_total = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade * ir.preco), 0) as total_vendas
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s
        """, (restaurante_id,))
        print(f"✅ Vendas totais resultado: {vendas_total}")
        
        # 2. Quantidade Total de Produtos Vendidos de TODO o banco de dados
        print(f"📊 Executando query de produtos vendidos...")
        produtos_vendidos = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade), 0) as total_produtos
            FROM item_pedido ip
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s
        """, (restaurante_id,))
        print(f"✅ Produtos vendidos resultado: {produtos_vendidos}")
        
        # 3. Ticket Médio de TODO o banco de dados
        ticket_medio_total = execute_query("""
            SELECT COALESCE(AVG(pedido_total.total), 0) as ticket_medio
            FROM (
                SELECT SUM(ip.quantidade * ir.preco) as total
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s
                GROUP BY p.id
            ) as pedido_total
        """, (restaurante_id,))
        
        # 4. Evolução Percentual de Vendas (comparando hoje vs ontem)
        vendas_hoje = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade * ir.preco), 0) as vendas_hoje
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s 
            AND DATE(p.criado_em) = CURRENT_DATE
        """, (restaurante_id,))
        
        vendas_ontem = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade * ir.preco), 0) as vendas_ontem
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s 
            AND DATE(p.criado_em) = CURRENT_DATE - INTERVAL '1 day'
        """, (restaurante_id,))
        
        # Calcular evolução percentual
        vendas_hoje_val = float(vendas_hoje[0]['vendas_hoje']) if vendas_hoje else 0
        vendas_ontem_val = float(vendas_ontem[0]['vendas_ontem']) if vendas_ontem else 0
        
        if vendas_ontem_val > 0:
            evolucao_percentual = ((vendas_hoje_val - vendas_ontem_val) / vendas_ontem_val) * 100
        else:
            evolucao_percentual = 100 if vendas_hoje_val > 0 else 0
        
        # ========================================================================
        # DADOS PARA GRÁFICOS
        # ========================================================================
        
        # Gráfico de Valor Diário Ganho (últimos 7 dias)
        vendas_por_dia = execute_query("""
            SELECT 
                DATE(p.criado_em) as data,
                COALESCE(SUM(ip.quantidade * ir.preco), 0) as valor_diario
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s 
            AND p.criado_em >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(p.criado_em)
            ORDER BY data
        """, (restaurante_id,))
        
        # Gráfico de Quantidade de Produto Vendido por Dia (últimos 7 dias)
        produtos_por_dia = execute_query("""
            SELECT 
                DATE(p.criado_em) as data,
                COALESCE(SUM(ip.quantidade), 0) as produtos_diarios
            FROM item_pedido ip
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s 
            AND p.criado_em >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(p.criado_em)
            ORDER BY data
        """, (restaurante_id,))
        
        # ========================================================================
        # FORMATAÇÃO DOS DADOS PARA RESPOSTA
        # ========================================================================
        
        # Preencher dados dos últimos 7 dias (incluindo dias sem vendas)
        vendas_grafico = []
        produtos_grafico = []
        
        for i in range(7):
            data_atual = (datetime.now() - timedelta(days=6-i)).date()
            data_str = data_atual.strftime('%Y-%m-%d')
            data_label = data_atual.strftime('%d/%m')
            
            # Buscar vendas do dia
            vendas_dia = 0
            for row in vendas_por_dia:
                if row['data'] == data_atual:
                    vendas_dia = float(row['valor_diario'])
                    break
            
            # Buscar produtos do dia
            produtos_dia = 0
            for row in produtos_por_dia:
                if row['data'] == data_atual:
                    produtos_dia = int(row['produtos_diarios'])
                    break
            
            vendas_grafico.append({
                'data': data_label,
                'valor': vendas_dia
            })
            
            produtos_grafico.append({
                'data': data_label,
                'quantidade': produtos_dia
            })
        
        # ========================================================================
        # RESPOSTA JSON ESTRUTURADA
        # ========================================================================
        
        # 🔥 LOG FINAL - Estrutura de resposta
        response_data = {
            'status': 'success',
            'data': {
                # Cards de Visão Geral (valores já formatados)
                'cards': {
                    'total_vendas': {
                        'valor': f"R$ {float(vendas_total[0]['total_vendas']) if vendas_total and vendas_total[0]['total_vendas'] else 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        'valor_numerico': float(vendas_total[0]['total_vendas']) if vendas_total and vendas_total[0]['total_vendas'] else 0
                    },
                    'quantidade_produtos': {
                        'valor': f"{int(produtos_vendidos[0]['total_produtos']) if produtos_vendidos and produtos_vendidos[0]['total_produtos'] else 0}",
                        'valor_numerico': int(produtos_vendidos[0]['total_produtos']) if produtos_vendidos and produtos_vendidos[0]['total_produtos'] else 0
                    },
                    'ticket_medio_diario': {
                        'valor': f"R$ {float(ticket_medio_total[0]['ticket_medio']) if ticket_medio_total and ticket_medio_total[0]['ticket_medio'] else 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        'valor_numerico': float(ticket_medio_total[0]['ticket_medio']) if ticket_medio_total and ticket_medio_total[0]['ticket_medio'] else 0
                    },
                    'evolucao_percentual': {
                        'valor': f"{evolucao_percentual:+.1f}%",
                        'valor_numerico': evolucao_percentual,
                        'tipo': 'positivo' if evolucao_percentual >= 0 else 'negativo'
                    }
                },
                
                # Dados para Gráficos
                'graficos': {
                    'valor_diario': {
                        'labels': [item['data'] for item in vendas_grafico],
                        'data': [item['valor'] for item in vendas_grafico],
                        'titulo': 'Valor Diário Ganho (Últimos 7 dias)',
                        'unidade': 'R$'
                    },
                    'produtos_diarios': {
                        'labels': [item['data'] for item in produtos_grafico],
                        'data': [item['quantidade'] for item in produtos_grafico],
                        'titulo': 'Quantidade de Produtos Vendidos por Dia',
                        'unidade': 'unidades'
                    }
                },
                
                # Metadados
                'periodo': {
                    'inicio': (datetime.now() - timedelta(days=6)).strftime('%d/%m/%Y'),
                    'fim': datetime.now().strftime('%d/%m/%Y'),
                    'dias': 7
                },
                'restaurante_id': restaurante_id,
                'atualizado_em': datetime.now().isoformat()
            }
        }
        
        print(f"DASHBOARD RESPONSE - Status: {response_data['status']}")
        print(f"DASHBOARD RESPONSE - Cards: {list(response_data['data']['cards'].keys())}")
        print(f"DASHBOARD RESPONSE - Graficos: {list(response_data['data']['graficos'].keys())}")
        print(f"DASHBOARD RESPONSE - Total vendas valor: {response_data['data']['cards']['total_vendas']['valor']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ ERRO no dashboard: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/metricas/<int:restaurante_id>', methods=['GET'])
def get_dashboard_metricas(restaurante_id):
    """Endpoint para buscar métricas do dashboard (mantido para compatibilidade)"""
    try:
        # Métricas básicas
        vendas_hoje = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade * ir.preco), 0) as total
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s AND DATE(p.criado_em) = CURRENT_DATE
        """, (restaurante_id,))
        
        pedidos_hoje = execute_query("""
            SELECT COUNT(*) as total
            FROM pedido 
            WHERE restaurante_id = %s AND DATE(criado_em) = CURRENT_DATE
        """, (restaurante_id,))
        
        # Ticket médio
        ticket_medio = execute_query("""
            SELECT COALESCE(AVG(pedido_total.total), 0) as media
            FROM (
                SELECT SUM(ip.quantidade * ir.preco) as total
                FROM item_pedido ip
                JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
                JOIN pedido p ON ip.pedido_id = p.id
                WHERE p.restaurante_id = %s 
                AND DATE(p.criado_em) >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY p.id
            ) as pedido_total
        """, (restaurante_id,))
        
        # Faturamento total
        faturamento_total = execute_query("""
            SELECT COALESCE(SUM(ip.quantidade * ir.preco), 0) as total
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s
        """, (restaurante_id,))
        
        return jsonify({
            'status': 'success',
            'data': {
                'vendas_hoje': float(vendas_hoje[0]['total']) if vendas_hoje else 0,
                'pedidos_hoje': pedidos_hoje[0]['total'] if pedidos_hoje else 0,
                'ticket_medio': float(ticket_medio[0]['media']) if ticket_medio else 0,
                'faturamento_total': float(faturamento_total[0]['total']) if faturamento_total else 0,
                'crescimento': 10.5  # Mock para demonstração
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/vendas_semana/<int:restaurante_id>', methods=['GET'])
def vendas_semana(restaurante_id):
    """Retorna dados de vendas da semana para gráficos"""
    try:
        results = execute_query("""
            SELECT 
                DATE(p.criado_em) as data,
                COUNT(*) as total_pedidos,
                COALESCE(SUM(ip.quantidade * ir.preco), 0) as total_vendas
            FROM pedido p
            LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            WHERE p.restaurante_id = %s 
            AND p.criado_em >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(p.criado_em)
            ORDER BY data
        """, (restaurante_id,))
        
        # Preencher dias sem vendas com zero
        vendas_por_dia = {}
        for i in range(7):
            data = (datetime.now() - timedelta(days=6-i)).date()
            vendas_por_dia[data.strftime('%Y-%m-%d')] = {
                'data': data.strftime('%d/%m'),
                'pedidos': 0,
                'vendas': 0
            }
        
        for row in results:
            data_str = row['data'].strftime('%Y-%m-%d')
            vendas_por_dia[data_str] = {
                'data': row['data'].strftime('%d/%m'),
                'pedidos': row['total_pedidos'],
                'vendas': float(row['total_vendas'])
            }
        
        return jsonify({
            'status': 'success',
            'data': list(vendas_por_dia.values())
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/produtos_populares/<int:restaurante_id>', methods=['GET'])
def produtos_populares(restaurante_id):
    """Retorna produtos mais vendidos"""
    try:
        results = execute_query("""
            SELECT 
                ir.nome as produto,
                SUM(ip.quantidade) as total_vendido,
                ir.preco,
                COUNT(DISTINCT p.id) as total_pedidos
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s
            GROUP BY ir.id, ir.nome, ir.preco
            ORDER BY total_vendido DESC
            LIMIT 10
        """, (restaurante_id,))
        
        produtos = []
        for row in results:
            produtos.append({
                'nome': row['produto'],
                'quantidade_vendida': row['total_vendido'],
                'preco': float(row['preco']),
                'total_pedidos': row['total_pedidos'],
                'faturamento': float(row['preco'] * row['total_vendido'])
            })
        
        return jsonify({
            'status': 'success',
            'data': produtos
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# PEDIDOS ENDPOINTS
# ============================================================================

@app.route('/api/pedidos/restaurante/<int:restaurante_id>', methods=['GET'])
def get_pedidos_restaurante(restaurante_id):
    """Lista pedidos de um restaurante"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query robusta: calcula valor_total e usa criado_em
        query = """
            SELECT
                p.id,
                c.nome as cliente_nome,
                c.telefone as cliente_telefone,
                p.status,
                p.criado_em as data_pedido,
                COALESCE(SUM(ip.quantidade * ir.preco), 0) as valor_total_calculado
            FROM pedido p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            WHERE p.restaurante_id = %s
        """
        params = [restaurante_id]
        
        if status:
            query += " AND p.status = %s"
            params.append(status)
        
        if data_inicio:
            query += " AND DATE(p.criado_em) >= %s"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND DATE(p.criado_em) <= %s"
            params.append(data_fim)
        
        query += """
            GROUP BY p.id, c.nome, c.telefone, p.status, p.criado_em
            ORDER BY p.criado_em DESC
        """
        
        results = execute_query(query, params)
        
        pedidos = []
        if results:
            for row in results:
                pedidos.append({
                    'id': row['id'],
                    'valor_total': float(row['valor_total_calculado']),
                    'status': row['status'],
                    'data_pedido': row['data_pedido'].isoformat(),
                    'observacoes': None,  # Campo não mais consultado na query
                    'cliente': {
                        'nome': row['cliente_nome'],
                        'telefone': row['cliente_telefone']
                    }
                })
        
        # Se não houver pedidos no banco, retornar dados de teste
        if not pedidos:
            from datetime import datetime, timedelta
            
            hoje = datetime.now()
            pedidos_teste = [
                {
                    'id': 1001,
                    'valor_total': 89.90,
                    'status': 'pendente',
                    'data_pedido': (hoje - timedelta(minutes=15)).isoformat(),
                    'observacoes': 'Sem cebola na pizza',
                    'cliente': {
                        'nome': 'Maria Silva',
                        'telefone': '(11) 99999-1234'
                    }
                },
                {
                    'id': 1002,
                    'valor_total': 45.50,
                    'status': 'em_preparo',
                    'data_pedido': (hoje - timedelta(minutes=30)).isoformat(),
                    'observacoes': None,
                    'cliente': {
                        'nome': 'João Santos',
                        'telefone': '(11) 99999-5678'
                    }
                },
                {
                    'id': 1003,
                    'valor_total': 123.75,
                    'status': 'pronto',
                    'data_pedido': (hoje - timedelta(minutes=45)).isoformat(),
                    'observacoes': 'Entregar no portão',
                    'cliente': {
                        'nome': 'Ana Costa',
                        'telefone': '(11) 99999-9012'
                    }
                },
                {
                    'id': 1004,
                    'valor_total': 67.20,
                    'status': 'entregue',
                    'data_pedido': (hoje - timedelta(hours=1)).isoformat(),
                    'observacoes': None,
                    'cliente': {
                        'nome': 'Carlos Oliveira',
                        'telefone': '(11) 99999-3456'
                    }
                },
                {
                    'id': 1005,
                    'valor_total': 156.80,
                    'status': 'entregue',
                    'data_pedido': (hoje - timedelta(hours=2)).isoformat(),
                    'observacoes': 'Pedido para festa',
                    'cliente': {
                        'nome': 'Fernanda Lima',
                        'telefone': '(11) 99999-7890'
                    }
                }
            ]
            
            # Aplicar filtros se houver
            if status:
                pedidos_teste = [p for p in pedidos_teste if p['status'] == status]
            
            pedidos = pedidos_teste
        
        return jsonify({
            'status': 'success',
            'data': pedidos,
            'count': len(pedidos)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pedidos/<int:pedido_id>/status', methods=['PUT'])
def update_pedido_status(pedido_id):
    """Atualiza status de um pedido"""
    try:
        data = request.get_json()
        novo_status = data.get('status')
        
        if not novo_status:
            return jsonify({'status': 'error', 'message': 'Status é obrigatório'}), 400
        
        # Validar status
        status_validos = ['pendente', 'em_preparo', 'pronto', 'entregue', 'cancelado']
        if novo_status not in status_validos:
            return jsonify({'status': 'error', 'message': 'Status inválido'}), 400
        
        # Tentar atualizar no banco primeiro
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE pedido 
                    SET status = %s 
                    WHERE id = %s
                """, (novo_status, pedido_id))
                
                if cur.rowcount > 0:
                    conn.commit()
                    cur.close()
                    conn.close()
                    return jsonify({
                        'status': 'success',
                        'message': 'Status atualizado com sucesso'
                    })
                
                cur.close()
                conn.close()
        except Exception as db_error:
            print(f"Erro no banco: {db_error}")
        
        # Se não conseguiu atualizar no banco (pedido de teste), simular sucesso
        if pedido_id in [1001, 1002, 1003, 1004, 1005]:
            return jsonify({
                'status': 'success',
                'message': f'Status do pedido #{pedido_id} atualizado para "{novo_status}" (simulado)'
            })
        
        return jsonify({'status': 'error', 'message': 'Pedido não encontrado'}), 404
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
def get_pedido_detalhes(pedido_id):
    """Busca detalhes de um pedido específico"""
    try:
        print(f"🔍 Buscando detalhes para o Pedido ID: {pedido_id}")
        
        # Buscar dados do pedido usando criado_em
        pedido = execute_query("""
            SELECT 
                p.id,
                p.status,
                p.criado_em as data_pedido,
                p.observacoes_gerais,
                c.nome as cliente_nome,
                c.telefone as cliente_telefone,
                c.email as cliente_email,
                r.nome as restaurante_nome
            FROM pedido p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN restaurante r ON p.restaurante_id = r.id
            WHERE p.id = %s
        """, (pedido_id,))
        
        # Buscar itens do pedido
        itens = execute_query("""
            SELECT 
                ip.quantidade,
                ip.observacoes as observacoes_item,
                ir.nome as item_nome,
                ir.preco as item_preco,
                ir.descricao as item_descricao
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            WHERE ip.pedido_id = %s
        """, (pedido_id,))
        
        # Calcular valor total
        valor_total = 0
        itens_formatados = []
        if itens:
            for item in itens:
                subtotal = float(item['item_preco']) * int(item['quantidade'])
                valor_total += subtotal
                itens_formatados.append({
                    'nome': item['item_nome'],
                    'quantidade': int(item['quantidade']),
                    'preco': float(item['item_preco']),
                    'subtotal': subtotal,
                    'observacoes': item['observacoes_item'],
                    'descricao': item['item_descricao']
                })
        
        # Se não encontrou no banco, usar dados de teste
        if not pedido:
            print(f"⚠️ Pedido {pedido_id} não encontrado no banco. Retornando dados de teste.")
            from datetime import datetime, timedelta
            hoje = datetime.now()
            
            # Dados de teste para IDs comuns
            dados_teste = {
                103: {
                    'pedido': {
                        'id': 103,
                        'status': 'FINALIZADO',
                        'data_pedido': (hoje - timedelta(minutes=15)).isoformat(),
                        'observacoes': 'Sem cebola na pizza',
                        'cliente': {
                            'nome': 'Bruno Costa',
                            'telefone': '(11) 99999-1234',
                            'email': 'bruno@email.com'
                        },
                        'restaurante': 'Restaurante Sabore'
                    },
                    'itens': [
                        {'nome': 'Pizza Quatro Queijos', 'quantidade': 1, 'preco': 80.00, 'subtotal': 80.00, 'observacoes': 'Extra queijo', 'descricao': 'Pizza com queijos especiais'},
                        {'nome': 'Coca-Cola 2L', 'quantidade': 2, 'preco': 12.00, 'subtotal': 24.00, 'observacoes': None, 'descricao': 'Refrigerante 2 litros'}
                    ]
                },
                102: {
                    'pedido': {
                        'id': 102,
                        'status': 'EM_PREPARO',
                        'data_pedido': (hoje - timedelta(minutes=30)).isoformat(),
                        'observacoes': 'Nenhuma',
                        'cliente': {
                            'nome': 'Bruno Costa',
                            'telefone': '(11) 99999-5678',
                            'email': 'bruno@email.com'
                        },
                        'restaurante': 'Restaurante Sabore'
                    },
                    'itens': [
                        {'nome': 'Hambúrguer Gourmet', 'quantidade': 1, 'preco': 45.90, 'subtotal': 45.90, 'observacoes': None, 'descricao': 'Hambúrguer artesanal'},
                        {'nome': 'Batata Frita', 'quantidade': 1, 'preco': 20.00, 'subtotal': 20.00, 'observacoes': None, 'descricao': 'Porção de batata frita'}
                    ]
                },
                101: {
                    'pedido': {
                        'id': 101,
                        'status': 'AGUARDANDO',
                        'data_pedido': (hoje - timedelta(minutes=35)).isoformat(),
                        'observacoes': None,
                        'cliente': {'nome': 'Ana Silva', 'telefone': '(11) 98765-4321', 'email': 'ana@email.com'},
                        'restaurante': 'Restaurante Sabore'
                    },
                    'itens': [{'nome': 'Água Mineral', 'quantidade': 3, 'preco': 4.00, 'subtotal': 12.00, 'observacoes': None, 'descricao': 'Água 500ml'}]
                },
                100: {
                    'pedido': {
                        'id': 100,
                        'status': 'EM_PREPARO',
                        'data_pedido': (hoje - timedelta(minutes=40)).isoformat(),
                        'observacoes': None,
                        'cliente': {'nome': 'Bruno Costa', 'telefone': '(11) 99999-1111', 'email': 'bruno2@email.com'},
                        'restaurante': 'Restaurante Sabore'
                    },
                    'itens': [{'nome': 'Suco Natural', 'quantidade': 2, 'preco': 6.00, 'subtotal': 12.00, 'observacoes': None, 'descricao': 'Suco de laranja'}]
                },
                99: {
                    'pedido': {
                        'id': 99,
                        'status': 'FINALIZADO',
                        'data_pedido': (hoje - timedelta(minutes=45)).isoformat(),
                        'observacoes': None,
                        'cliente': {'nome': 'Bruno Costa', 'telefone': '(11) 99999-2222', 'email': 'bruno3@email.com'},
                        'restaurante': 'Restaurante Sabore'
                    },
                    'itens': [{'nome': 'Pizza Margherita', 'quantidade': 1, 'preco': 45.90, 'subtotal': 45.90, 'observacoes': None, 'descricao': 'Pizza clássica'}]
                }
            }
            
            if pedido_id in dados_teste:
                # Calcular valor total dos itens
                valor_total_calc = sum(item['subtotal'] for item in dados_teste[pedido_id]['itens'])
                dados_teste[pedido_id]['pedido']['valor_total'] = valor_total_calc
                
                return jsonify({
                    'status': 'success',
                    'data': dados_teste[pedido_id]
                })
            else:
                return jsonify({'status': 'error', 'message': 'Pedido não encontrado'}), 404
        
        # Se encontrou no banco, processar dados reais
        pedido_data = pedido[0]
        
        return jsonify({
            'status': 'success',
            'data': {
                'pedido': {
                    'id': pedido_data['id'],
                    'valor_total': valor_total,
                    'status': pedido_data['status'],
                    'data_pedido': pedido_data['data_pedido'].isoformat(),
                    'observacoes': pedido_data['observacoes_gerais'],
                    'cliente': {
                        'nome': pedido_data['cliente_nome'],
                        'telefone': pedido_data['cliente_telefone'],
                        'email': pedido_data['cliente_email']
                    },
                    'restaurante': pedido_data['restaurante_nome']
                },
                'itens': itens_formatados
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# VENDAS ENDPOINTS
# ============================================================================

@app.route('/api/relatorios/faturamento/<int:restaurante_id>', methods=['GET'])
def get_faturamento(restaurante_id):
    """
    Relatório de faturamento por período
    
    Args:
        restaurante_id: ID do restaurante
        
    Query Params:
        data_inicio: Data inicial (YYYY-MM-DD)
        data_fim: Data final (YYYY-MM-DD)
        
    Returns:
        JSON com resumo e faturamento diário
    """
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'status': 'error', 'message': 'Data início e fim são obrigatórias'}), 400
        
        # 🔥 CORREÇÃO: Calcular valor total usando item_pedido e item_restaurante
        # Campo valor_total não existe na tabela pedido
        faturamento = execute_query("""
            SELECT 
                COALESCE(SUM(ip.quantidade * ir.preco), 0) as total_faturamento,
                COUNT(DISTINCT p.id) as total_pedidos,
                COALESCE(AVG(pedido_valor.total), 0) as ticket_medio
            FROM pedido p
            LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            WHERE p.restaurante_id = %s 
            AND DATE(p.criado_em) BETWEEN %s AND %s
            GROUP BY p.id
            HAVING SUM(ip.quantidade * ir.preco) IS NOT NULL
        """, (restaurante_id, data_inicio, data_fim))
        
        # Faturamento por dia
        faturamento_diario = execute_query("""
            SELECT 
                DATE(p.criado_em) as data,
                COALESCE(SUM(ip.quantidade * ir.preco), 0) as faturamento,
                COUNT(DISTINCT p.id) as pedidos
            FROM pedido p
            LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            WHERE p.restaurante_id = %s 
            AND DATE(p.criado_em) BETWEEN %s AND %s
            GROUP BY DATE(p.criado_em)
            ORDER BY data
        """, (restaurante_id, data_inicio, data_fim))
        
        return jsonify({
            'status': 'success',
            'data': {
                'resumo': {
                    'total_faturamento': float(faturamento[0]['total_faturamento']) if faturamento else 0,
                    'total_pedidos': faturamento[0]['total_pedidos'] if faturamento else 0,
                    'ticket_medio': float(faturamento[0]['ticket_medio']) if faturamento else 0
                },
                'diario': [
                    {
                        'data': row['data'].strftime('%d/%m/%Y'),
                        'faturamento': float(row['faturamento']),
                        'pedidos': row['pedidos']
                    }
                    for row in faturamento_diario
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/relatorios/produtos_mais_vendidos/<int:restaurante_id>', methods=['GET'])
def get_produtos_mais_vendidos(restaurante_id):
    """Relatório de produtos mais vendidos"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        limite = request.args.get('limite', 10)
        
        query = """
            SELECT 
                ir.nome as produto,
                SUM(ip.quantidade) as quantidade_vendida,
                ir.preco,
                COUNT(DISTINCT p.id) as total_pedidos,
                SUM(ip.quantidade * ir.preco) as faturamento_item
            FROM item_pedido ip
            JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
            JOIN pedido p ON ip.pedido_id = p.id
            WHERE p.restaurante_id = %s
        """
        params = [restaurante_id]
        
        # 🔥 CORREÇÃO: Usar criado_em em vez de data_pedido
        if data_inicio and data_fim:
            query += " AND DATE(p.criado_em) BETWEEN %s AND %s"
            params.extend([data_inicio, data_fim])
        
        query += """
            GROUP BY ir.id, ir.nome, ir.preco
            ORDER BY quantidade_vendida DESC
            LIMIT %s
        """
        params.append(int(limite))
        
        results = execute_query(query, params)
        
        produtos = []
        for row in results:
            produtos.append({
                'produto': row['produto'],
                'quantidade_vendida': row['quantidade_vendida'],
                'preco_unitario': float(row['preco']),
                'total_pedidos': row['total_pedidos'],
                'faturamento_total': float(row['faturamento_item'])
            })
        
        return jsonify({
            'status': 'success',
            'data': produtos
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# CARDÁPIO ENDPOINTS (Removidas rotas duplicadas - mantendo apenas as do início do arquivo)
# ============================================================================

# ============================================================================
# AVALIAÇÕES ENDPOINTS
# ============================================================================

@app.route('/api/avaliacoes/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes(restaurante_id):
    """Lista avaliações de um restaurante"""
    try:
        results = execute_query("""
            SELECT 
                a.id,
                a.nota,
                a.comentario,
                a.data_avaliacao,
                c.nome as cliente_nome
            FROM avaliacao a
            JOIN clientes c ON a.cliente_id = c.id
            WHERE a.restaurante_id = %s
            ORDER BY a.data_avaliacao DESC
        """, (restaurante_id,))
        
        # Calcular média das avaliações
        media_result = execute_query("""
            SELECT 
                AVG(nota) as media_notas,
                COUNT(*) as total_avaliacoes
            FROM avaliacao 
            WHERE restaurante_id = %s
        """, (restaurante_id,))
        
        avaliacoes = []
        for row in results:
            avaliacoes.append({
                'id': row['id'],
                'nota': float(row['nota']),
                'comentario': row['comentario'],
                'data_avaliacao': row['data_avaliacao'].isoformat() if row['data_avaliacao'] else None,
                'cliente_nome': row['cliente_nome']
            })
        
        media_data = media_result[0] if media_result else {'media_notas': 0, 'total_avaliacoes': 0}
        
        return jsonify({
            'status': 'success',
            'data': {
                'avaliacoes': avaliacoes,
                'resumo': {
                    'media_notas': float(media_data['media_notas']) if media_data['media_notas'] else 0,
                    'total_avaliacoes': media_data['total_avaliacoes']
                }
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/avaliacoes/pratos/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes_pratos(restaurante_id):
    """
    Lista avaliações específicas de pratos do restaurante.
    Corresponde à tabela AvaliacaoPrato.
    """
    try:
        
        # Primeiro, verificar se há pratos para este restaurante
        pratos_check = execute_query("""
            SELECT COUNT(*) as total_pratos
            FROM item_restaurante 
            WHERE restaurante_id = %s
        """, (restaurante_id,))
        
        total_pratos = pratos_check[0]['total_pratos'] if pratos_check else 0
        print(f"📊 Total de pratos para restaurante {restaurante_id}: {total_pratos}")
        
        # Verificar se há avaliações de pratos em geral
        avaliacoes_check = execute_query("""
            SELECT COUNT(*) as total_avaliacoes
            FROM avaliacao_prato ap
            JOIN item_restaurante ir ON ap.prato_id = ir.id
        """)
        
        total_avaliacoes = avaliacoes_check[0]['total_avaliacoes'] if avaliacoes_check else 0
        print(f"📊 Total de avaliações de pratos no sistema: {total_avaliacoes}")
        
        # Se não há avaliações de pratos, usar dados mock para demonstração
        if total_avaliacoes == 0:
            print("⚠️ Nenhuma avaliação de prato encontrada no sistema")
            print("🔄 Usando dados mock para demonstração...")
            
            # Buscar pratos do restaurante para usar nos dados mock
            pratos_15 = execute_query("""
                SELECT nome FROM item_restaurante 
                WHERE restaurante_id = %s 
                LIMIT 3
            """, (restaurante_id,))
            
            # Dados mock de avaliações de pratos
            avaliacoes_mock = [
                {
                    'id': 1,
                    'nota': 5.0,
                    'comentario': 'Excelente prato! O sabor estava perfeito e a apresentação impecável.',
                    'data_avaliacao': '2024-12-15T14:30:00',
                    'cliente_nome': 'Maria Silva',
                    'nome_prato': pratos_15[0]['nome'] if pratos_15 else 'Hambúrguer Clássico'
                },
                {
                    'id': 2,
                    'nota': 4.0,
                    'comentario': 'Muito bom! Ingredientes frescos e bem preparados.',
                    'data_avaliacao': '2024-12-14T19:45:00',
                    'cliente_nome': 'João Santos',
                    'nome_prato': pratos_15[1]['nome'] if len(pratos_15) > 1 else 'Pizza Margherita'
                },
                {
                    'id': 3,
                    'nota': 3.0,
                    'comentario': 'Regular, nada especial mas também não ruim.',
                    'data_avaliacao': '2024-12-13T12:15:00',
                    'cliente_nome': 'Ana Costa',
                    'nome_prato': pratos_15[2]['nome'] if len(pratos_15) > 2 else 'Sushi Salmão'
                }
            ]
            
            print(f"✅ Retornando {len(avaliacoes_mock)} avaliações mock")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'avaliacoes': avaliacoes_mock,
                    'resumo': {
                        'media_notas': 4.0,
                        'total_avaliacoes': len(avaliacoes_mock)
                    }
                }
            })
        
        # AVALIAÇÃO DE PRATOS
        results = execute_query("""
            SELECT 
                ap.id,
                ap.nota,
                ap.comentario,
                ap.data_avaliacao,
                c.nome as cliente_nome,
                ir.nome as nome_prato
            FROM avaliacao_prato ap
            JOIN item_restaurante ir ON ap.prato_id = ir.id
            JOIN clientes c ON ap.cliente_id = c.id
            WHERE ir.restaurante_id = %s
            ORDER BY ap.data_avaliacao DESC
        """, (restaurante_id,))
        
        print(f"📊 Resultados encontrados: {len(results) if results else 0}")
        
        # Debug: mostrar os primeiros resultados se houver
        if results and len(results) > 0:
            print(f"🔍 Primeiro resultado: {results[0]}")
        
        # Calcular média das avaliações de pratos
        media_result = execute_query("""
            SELECT 
                AVG(ap.nota) as media_notas,
                COUNT(*) as total_avaliacoes
            FROM avaliacao_prato ap
            JOIN item_restaurante ir ON ap.prato_id = ir.id
            WHERE ir.restaurante_id = %s
        """, (restaurante_id,))
        
        print(f"📊 Média calculada: {media_result}")
        
        # Processar os resultados em formato JSON (incluindo nome_prato)
        avaliacoes = []
        if results:
            for row in results:
                avaliacoes.append({
                    'id': row['id'],
                    'nota': float(row['nota']),
                    'comentario': row['comentario'],
                    'data_avaliacao': row['data_avaliacao'].isoformat() if row['data_avaliacao'] else None,
                    'cliente_nome': row['cliente_nome'],
                    'nome_prato': row['nome_prato']  # Campo crucial
                })
        
        media_data = media_result[0] if media_result else {'media_notas': 0, 'total_avaliacoes': 0}
        
        print(f"📊 Retornando {len(avaliacoes)} avaliações")
        
        return jsonify({
            'status': 'success',
            'data': {
                'avaliacoes': avaliacoes,
                'resumo': {
                    'media_notas': float(media_data['media_notas']) if media_data['media_notas'] else 0,
                    'total_avaliacoes': media_data['total_avaliacoes']
                }
            }
        })
        
    except Exception as e:
        print(f"❌ Erro ao carregar avaliações de pratos: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# ENDPOINTS DE SISTEMA
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde da API e conexão com banco"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            db_status = 'active'
        else:
            db_status = 'inactive'
        
        return jsonify({
            'status': 'success',
            'message': 'API Flask está funcionando!',
            'database_connection': db_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restaurantes/login', methods=['POST'])
def restaurante_login():
    """Login de restaurante"""
    try:
        data = request.get_json()
        email = data.get('email')
        senha = data.get('senha')
        
        print(f"\n🔐 TENTATIVA DE LOGIN:")
        print(f"   Email recebido: {email}")
        print(f"   Senha recebida: {'*' * len(senha) if senha else 'None'}")
        
        if not email or not senha:
            print("❌ Email ou senha não fornecidos")
            return jsonify({'status': 'error', 'message': 'Email e senha são obrigatórios'}), 400
        
        # Buscar restaurante
        print(f"🔍 Buscando restaurante com email: {email}")
        results = execute_query("""
            SELECT id, nome, email, senha 
            FROM restaurante 
            WHERE email = %s
        """, (email,))
        
        print(f"📊 Resultados encontrados: {len(results) if results else 0}")
        
        if not results:
            print("❌ Restaurante não encontrado no banco de dados")
            return jsonify({'status': 'error', 'message': 'Restaurante não encontrado'}), 404
        
        restaurante = results[0]
        print(f"✅ Restaurante encontrado:")
        print(f"   ID: {restaurante['id']}")
        print(f"   Nome: {restaurante['nome']}")
        print(f"   Email: {restaurante['email']}")
        print(f"   Senha no banco: {restaurante['senha']}")
        print(f"   Senha recebida: {senha}")
        
        # Verificar senha (com BCrypt)
        print(f"🔒 Comparando senhas...")
        print(f"   Senha do banco: '{restaurante['senha']}'")
        print(f"   Senha recebida: '{senha}'")
        
        # Verificar se a senha do banco está em hash BCrypt
        senha_hash = restaurante['senha']
        
        # Verificar se é hash BCrypt (começa com $2a$ ou $2b$)
        if senha_hash.startswith('$2a$') or senha_hash.startswith('$2b$'):
            print("   Senha está em BCrypt, verificando com bcrypt.checkpw...")
            # Converter senha recebida para bytes
            senha_bytes = senha.encode('utf-8')
            # Converter hash do banco para bytes
            hash_bytes = senha_hash.encode('utf-8')
            # Verificar com bcrypt
            senha_valida = bcrypt.checkpw(senha_bytes, hash_bytes)
            print(f"   Senha válida? {senha_valida}")
        else:
            print("   Senha está em texto plano, comparando diretamente...")
            senha_valida = (senha_hash == senha)
            print(f"   Senha válida? {senha_valida}")
        
        if senha_valida:
            print("✅ SENHA CORRETA! Login bem-sucedido!")
            return jsonify({
                'status': 'success',
                'message': 'Login realizado com sucesso',
                'data': {
                    'restaurante_id': restaurante['id'],
                    'restaurante_nome': restaurante['nome'],
                    'email': restaurante['email']
                }
            })
        else:
            print("❌ SENHA INCORRETA!")
            return jsonify({'status': 'error', 'message': 'Senha incorreta'}), 401
            
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)