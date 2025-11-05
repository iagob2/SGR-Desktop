#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Flask para SGR-Desktop - Proxy REST
Sistema de Gerenciamento de Restaurantes - Proxy para API externa na nuvem
Arquitetura: Electron -> Flask (localhost:5000) -> API Externa (nuvem:8080) -> PostgreSQL
"""

import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, urlencode

# Import BeautifulSoup com try/except para instalação opcional
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("AVISO: beautifulsoup4 nao instalado. Execute: pip install beautifulsoup4")

import re

load_dotenv('config.env')

app = Flask(__name__)
CORS(app)

api_session = requests.Session()
session_cookies_store = {}

def get_session_cookie(restaurante_id=None):
    """Obtém cookie de sessão do restaurante"""
    if restaurante_id:
        return session_cookies_store.get(restaurante_id)
    return session_cookies_store.get('latest') if session_cookies_store else None

def set_session_cookie(cookie_value, restaurante_id=None):
    """Armazena cookie de sessão, removendo duplicatas"""
    if cookie_value and '=' in cookie_value:
        cookie_name, cookie_val = cookie_value.split('=', 1)
        try:
            cookies_to_keep = {name: value for name, value in api_session.cookies.items() if name != cookie_name}
            api_session.cookies.clear()
            for name, value in cookies_to_keep.items():
                api_session.cookies.set(name, value)
        except Exception as e:
            print(f"[SESSION] Erro ao limpar cookies: {e}")
        api_session.cookies.set(cookie_name, cookie_val)
        if restaurante_id:
            session_cookies_store[restaurante_id] = cookie_value
        session_cookies_store['latest'] = cookie_value

def clear_session_cookie(restaurante_id=None):
    """Limpa cookie de sessão"""
    if restaurante_id:
        session_cookies_store.pop(restaurante_id, None)
    else:
        session_cookies_store.clear()
        api_session.cookies.clear()

API_EXTERNA_BASE_URL = os.getenv('API_EXTERNA_URL', 'http://3.90.155.156:8080')

# Limpar a URL removendo espaços e comentários inline que podem ter sido incluídos
if API_EXTERNA_BASE_URL:
    # Remover espaços no início e fim
    API_EXTERNA_BASE_URL = API_EXTERNA_BASE_URL.strip()
    # Remover qualquer texto após comentário inline (se houver)
    if ' <--' in API_EXTERNA_BASE_URL or ' #' in API_EXTERNA_BASE_URL:
        # Extrair apenas a URL antes do comentário
        API_EXTERNA_BASE_URL = API_EXTERNA_BASE_URL.split(' <--')[0].split(' #')[0].strip()
    # Garantir que termina com barra
    if not API_EXTERNA_BASE_URL.endswith('/'):
        API_EXTERNA_BASE_URL = API_EXTERNA_BASE_URL + '/'

API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

try:
    parsed_url = urlparse(API_EXTERNA_BASE_URL.rstrip('/'))
    API_EXTERNA_PROTOCOL = parsed_url.scheme
    API_EXTERNA_HOST = parsed_url.hostname
    API_EXTERNA_PORT = parsed_url.port or (443 if API_EXTERNA_PROTOCOL == 'https' else 80)
except:
    API_EXTERNA_PROTOCOL = 'http'
    API_EXTERNA_HOST = '3.90.155.156'
    API_EXTERNA_PORT = 8080


def parse_html_response(html_content, endpoint=''):
    """
    Parseia resposta HTML da API externa e converte para JSON estruturado.
    Especializado para extrair dados de login (restaurante_id, restaurante_nome)
    e listagem de itens do cardápio.
    
    Args:
        html_content: Conteúdo HTML recebido
        endpoint: Endpoint chamado (para contexto)
        
    Returns:
        dict: Dados estruturados em formato JSON
    """
    try:
        if not BS4_AVAILABLE:
            return {
                'status': 'success',
                'message': 'Resposta HTML recebida (beautifulsoup4 nao instalado)',
                'raw_html': html_content[:500]
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # ESPECIAL: Parse específico para login
        if 'restaurantes/login' in endpoint or 'restaurante.html' in html_content.lower():
            # Procurar mensagem de sucesso: "Login bem-sucedido! Bem-vindo(a), [Nome]"
            success_pattern = re.compile(r'Login bem-sucedido.*?Bem-vindo\(a\),\s*(.+?)\.', re.IGNORECASE)
            match = success_pattern.search(html_content)
            restaurante_nome = None
            
            if match:
                restaurante_nome = match.group(1).strip()
                print(f"[PARSE] Nome do restaurante extraido: {restaurante_nome}")
            
            # Procurar restaurante_id em:
            # 1. Scripts JavaScript (variáveis como var restaurante_id = ...)
            scripts = soup.find_all('script')
            restaurante_id = None
            
            for script in scripts:
                if script.string:
                    # Procurar: var restaurante_id = X ou restaurante_id: X
                    id_match = re.search(r'restaurante[_\s]*id\s*[=:]\s*(\d+)', script.string, re.IGNORECASE)
                    if id_match:
                        restaurante_id = int(id_match.group(1))
                        print(f"[PARSE] restaurante_id encontrado em script: {restaurante_id}")
                        break
                    
                    # Procurar JSON completo
                    json_match = re.search(r'\{[^}]*restaurante[_\s]*id[^}]*\}', script.string, re.IGNORECASE | re.DOTALL)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group().replace("'", '"'))
                            if 'restaurante_id' in json_data:
                                restaurante_id = json_data['restaurante_id']
                                print(f"[PARSE] restaurante_id do JSON: {restaurante_id}")
                                break
                        except:
                            pass
            
            # 2. Inputs hidden ou data-attributes
            if not restaurante_id:
                hidden_inputs = soup.find_all('input', {'type': 'hidden'})
                for inp in hidden_inputs:
                    if 'restaurante' in inp.get('name', '').lower() and 'id' in inp.get('name', '').lower():
                        try:
                            restaurante_id = int(inp.get('value', 0))
                            print(f"[PARSE] restaurante_id em input hidden: {restaurante_id}")
                            break
                        except:
                            pass
            
            # 3. Data-attributes
            if not restaurante_id:
                elements = soup.find_all(attrs={'data-restaurante-id': True})
                if elements:
                    try:
                        restaurante_id = int(elements[0].get('data-restaurante-id'))
                        print(f"[PARSE] restaurante_id em data-attribute: {restaurante_id}")
                    except:
                        pass
            
            # 4. Procurar em links ou URLs no HTML (ex: dashboard?id=15)
            if not restaurante_id:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    id_match = re.search(r'[?&](?:id|restaurante_id)=(\d+)', href, re.IGNORECASE)
                    if id_match:
                        restaurante_id = int(id_match.group(1))
                        print(f"[PARSE] restaurante_id em URL: {restaurante_id}")
                        break
            
            # Se encontrou dados de login, retornar formato esperado pelo frontend
            result = {
                'status': 'success',
                'message': 'Login realizado com sucesso',
                'data': {}
            }
            
            if restaurante_id:
                result['data']['restaurante_id'] = restaurante_id
                print(f"[PARSE] restaurante_id incluído na resposta: {restaurante_id}")
            else:
                print(f"[AVISO] restaurante_id nao encontrado no HTML, mas login teve sucesso")
            
            if match and restaurante_nome:
                result['data']['restaurante_nome'] = restaurante_nome
                print(f"[PARSE] restaurante_nome incluído na resposta: {restaurante_nome}")
            
            # Se não encontrou ID mas tem nome, ainda retornar sucesso
            # O frontend pode tentar buscar o ID via endpoint adicional
            if not restaurante_id and match:
                print(f"[INFO] Login bem-sucedido mas restaurante_id não encontrado")
                print(f"[INFO] Frontend pode tentar buscar ID via endpoint /restaurantes/perfil")
            
            return result
        
        # ESPECIAL: Parse de listagem de itens (tabela HTML)
        if 'itens' in endpoint.lower() or 'cardapio' in endpoint.lower() or 'tabelaItens' in html_content:
            print(f"[PARSE] Tentando parsear lista de itens do HTML...")
            items = []
            
            # Procurar por tabela com id="tabelaItens" ou class que contenha "itens"
            tabela = soup.find('table', id='tabelaItens')
            if not tabela:
                tabela = soup.find('table')
            
            if tabela:
                # Encontrar todas as linhas da tabela (exceto header)
                rows = tabela.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # Pelo menos ID, Nome, Preço
                        try:
                            item = {}
                            # Assumir ordem: ID, Nome, Preço, ID Restaurante, Imagem
                            if len(cells) > 0:
                                item['id'] = int(cells[0].get_text(strip=True)) if cells[0].get_text(strip=True).isdigit() else None
                            if len(cells) > 1:
                                item['nome'] = cells[1].get_text(strip=True)
                            if len(cells) > 2:
                                preco_text = cells[2].get_text(strip=True).replace('R$', '').replace(',', '.').strip()
                                try:
                                    item['preco'] = float(preco_text)
                                except:
                                    item['preco'] = 0.0
                            if len(cells) > 3:
                                restaurante_cell = cells[3].get_text(strip=True)
                                if restaurante_cell.isdigit():
                                    item['restaurante_id'] = int(restaurante_cell)
                                    item['restaurante'] = {'id': int(restaurante_cell)}
                            if len(cells) > 4:
                                img_link = cells[4].find('a')
                                if img_link:
                                    item['imagemUrl'] = img_link.get('href', '')
                            
                            # Só adicionar se tem nome (não é header)
                            if item.get('nome') and item.get('id'):
                                items.append(item)
                        except Exception as e:
                            print(f"[PARSE] Erro ao parsear linha da tabela: {e}")
                            continue
                
                if items:
                    print(f"[PARSE] Parseou {len(items)} itens da tabela HTML")
                    return items
        
        # CASO GERAL: Tentar encontrar JSON dentro do HTML
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if isinstance(parsed, dict) and 'status' in parsed:
                            return parsed
                    except:
                        pass
        
        # Tentar encontrar dados em elementos data-*
        data = {}
        elements_with_data = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
        for elem in elements_with_data:
            for key, value in elem.attrs.items():
                if key.startswith('data-'):
                    data_key = key.replace('data-', '').replace('-', '_')
                    data[data_key] = value
        
        # Tentar extrair texto principal
        main_content = soup.find('main') or soup.find('body') or soup
        text_content = main_content.get_text(strip=True) if main_content else ''
        
        # Verificar se há mensagem de erro
        if any(palavra in text_content.lower() for palavra in ['erro', 'error', 'falha', 'inválido', 'incorreto']):
            return {
                'status': 'error',
                'message': 'Erro no login. Verifique suas credenciais.'
            }
        
        # Se encontrou dados estruturados, retornar
        if data:
            return {
                'status': 'success',
                'data': data,
                'html_content': text_content[:500]
            }
        
        # Se não encontrou dados estruturados, retornar texto
        return {
            'status': 'success',
            'message': 'Resposta HTML recebida',
            'content': text_content[:1000],
            'note': 'API retornou HTML. Dados podem precisar de parsing adicional.'
        }
        
    except Exception as e:
        print(f"[AVISO] Erro ao parsear HTML: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return {
            'status': 'success',
            'message': 'Resposta HTML recebida (não parseado)',
            'raw_html': html_content[:500]
        }

# ============================================================================
# MAPEAMENTO DE ENDPOINTS FLASK -> API EXTERNA
# ============================================================================

def mapear_endpoint_flask_para_api(flask_endpoint):
    """
    Mapeia endpoints do Flask para endpoints da API externa.
    
    Endpoints da API Externa:
    - /restaurantes/** (público)
    - /itens/** (GET público, POST/PUT/DELETE públicos)
    - /avaliacoes/** (GET público)
    - /avaliacoes-prato/** (GET público)
    - /pedidos/** (protegido)
    
    Args:
        flask_endpoint: Endpoint do Flask (ex: '/api/restaurantes/login')
        
    Returns:
        str: Endpoint da API externa (ex: '/restaurantes/login')
    """
    # Remover prefixo /api/ se existir
    endpoint = flask_endpoint.replace('/api/', '/').lstrip('/')
    
    # Mapeamentos específicos
    # Cardápio -> Itens
    if endpoint.startswith('cardapio/'):
        # IMPORTANTE: A API externa usa /itens diretamente
        # O filtro por restaurante pode ser feito via cookie de sessão
        if endpoint.startswith('cardapio/add'):
            return 'itens'  # POST para criar
        elif endpoint.startswith('cardapio/edit/'):
            item_id = endpoint.replace('cardapio/edit/', '')
            return f'itens/{item_id}'  # PUT para editar
        elif re.match(r'cardapio/\d+$', endpoint):
            # GET para listar - API externa usa /itens (todos os itens do restaurante logado)
            return 'itens'
    
    # Avaliações de pratos - não mapear, será tratado no endpoint Flask
    # A API Java não tem endpoint /avaliacoes-prato/restaurante/{id}
    # Usamos GET /avaliacoes-prato e filtramos no Flask
    # if endpoint.startswith('avaliacoes/pratos/'):
    #     restaurante_id = endpoint.replace('avaliacoes/pratos/', '')
    #     return f'avaliacoes-prato/restaurante/{restaurante_id}'
    
    # Outros mapeamentos simples (remover /api/)
    return endpoint

# ============================================================================
# FUNÇÃO DE PROXY COM DIAGNÓSTICO AVANÇADO
# ============================================================================

def proxy_request(method, endpoint, data=None, params=None):
    """
    Função helper aprimorada para fazer proxy de requisições para a API externa.
    Inclui logs detalhados e diagnóstico completo de erros de rede.
    
    Args:
        method: Método HTTP (GET, POST, PUT, DELETE)
        endpoint: Endpoint da API (ex: '/api/dashboard/15')
        data: Dados para enviar no body (para POST/PUT)
        params: Parâmetros de query string
        
    Returns:
        Tuple (status_code, response_data) com diagnóstico completo
    """
    try:
        # Mapear endpoint do Flask para endpoint da API externa
        endpoint_api = mapear_endpoint_flask_para_api(endpoint)
        
        # Construir URL completa (API_EXTERNA_BASE_URL já tem barra final)
        endpoint_api = endpoint_api.lstrip('/') if endpoint_api.startswith('/') else endpoint_api
        url = f"{API_EXTERNA_BASE_URL}{endpoint_api}"
        
        # Headers - ajustar Content-Type baseado no método
        headers = {
            'Accept': 'text/html,application/json,application/xhtml+xml,text/plain,*/*',
            'User-Agent': 'SGR-Desktop-Flask-Proxy/1.0',
            'Origin': 'http://localhost:5000'
        }
        
        # Content-Type apenas para POST/PUT com dados
        if data and method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'
        elif method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # IMPORTANTE: requests.Session() mantém cookies automaticamente
        # Mas precisamos garantir que não há JSESSIONID duplicado ANTES de fazer a requisição
        # Limpar JSESSIONID duplicados antes de fazer requisição
        jsessionid_count = sum(1 for name in api_session.cookies.keys() if name == 'JSESSIONID')
        if jsessionid_count > 1:
            print(f"   [COOKIE] AVISO: Encontrados {jsessionid_count} cookies JSESSIONID - limpando duplicatas...")
            # Manter apenas um JSESSIONID (o último valor)
            jsessionid_val = api_session.cookies.get('JSESSIONID')
            cookies_backup = {name: value for name, value in api_session.cookies.items() if name != 'JSESSIONID'}
            api_session.cookies.clear()
            for name, value in cookies_backup.items():
                api_session.cookies.set(name, value)
            if jsessionid_val:
                api_session.cookies.set('JSESSIONID', jsessionid_val)
            print(f"   [COOKIE] Duplicatas removidas - mantido apenas 1 JSESSIONID")
        elif jsessionid_count == 1:
            print(f"   [COOKIE] JSESSIONID presente na sessao - será enviado automaticamente")
        
        # Log dos cookies que serão enviados
        if len(api_session.cookies) > 0:
            cookie_list = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"   [COOKIE] Sessao tem {len(api_session.cookies)} cookie(s): {', '.join(cookie_list)}")
        
        # Cookies serão enviados automaticamente pela sessão - não precisa adicionar manualmente aos headers
        
        # Log detalhado da requisição (sem emojis para compatibilidade Windows)
        try:
            print(f"\n{'='*60}")
            print(f"[PROXY] PROXY REQUEST")
            print(f"{'='*60}")
            print(f"   Metodo: {method}")
            print(f"   URL Completa: {url}")
            print(f"   Base URL: {API_EXTERNA_BASE_URL}")
            print(f"   Endpoint Flask: {endpoint}")
            print(f"   Endpoint API Externa: {endpoint_api}")
        except UnicodeEncodeError:
            # Fallback para Windows sem suporte a Unicode
            print(f"\n{'='*60}")
            print(f"[PROXY] PROXY REQUEST")
            print(f"{'='*60}")
            print(f"   Metodo: {method}")
            print(f"   URL Completa: {url}")
            print(f"   Endpoint API Externa: {endpoint_api}")
        print(f"   Timeout: {API_TIMEOUT}s")
        print(f"   Protocolo: {API_EXTERNA_PROTOCOL.upper()}")
        print(f"   Host: {API_EXTERNA_HOST}")
        print(f"   Porta: {API_EXTERNA_PORT}")
        
        if params:
            print(f"   Query Params: {params}")
        if data:
            # Ocultar senha nos logs
            data_log = data.copy()
            if 'senha' in data_log:
                data_log['senha'] = '***'
            if 'password' in data_log:
                data_log['password'] = '***'
            print(f"   Body Data: {json.dumps(data_log, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}\n")
        
        # Fazer requisição usando SESSÃO (mantém cookies automaticamente)
        response = api_session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
            timeout=API_TIMEOUT,
            allow_redirects=True
        )
        
        # IMPORTANTE: requests.Session() já salva cookies automaticamente
        # Mas se houver múltiplos Set-Cookie, precisamos tratar manualmente para evitar duplicatas
        
        # Verificar se há Set-Cookie na resposta
        set_cookie_headers = response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
        if not set_cookie_headers and 'Set-Cookie' in response.headers:
            # Se não tem get_list, pegar como string única
            set_cookie_headers = [response.headers.get('Set-Cookie')]
        
        if set_cookie_headers:
            # Processar cada cookie recebido
            jsessionid_value = None
            
            for cookie_header in set_cookie_headers:
                # Extrair valor do cookie (JSESSIONID=...)
                cookie_value = cookie_header.split(';')[0].strip()
                
                if cookie_value.startswith('JSESSIONID='):
                    # Se for JSESSIONID, guardar (usar o último se houver múltiplos)
                    jsessionid_value = cookie_value
                    print(f"   [COOKIE] JSESSIONID recebido: {cookie_value[:50]}...")
            
            # Se encontrou JSESSIONID, garantir que está na sessão (requests.Session já fez, mas garantir que não há duplicatas)
            if jsessionid_value:
                cookie_name, cookie_val = jsessionid_value.split('=', 1)
                
                # Remover JSESSIONID antigo se existir para evitar duplicata
                if 'JSESSIONID' in api_session.cookies:
                    # requests.Session() pode ter múltiplos - limpar todos e adicionar apenas um
                    cookies_backup = {}
                    for name, value in api_session.cookies.items():
                        if name != 'JSESSIONID':
                            cookies_backup[name] = value
                    
                    # Limpar todos
                    api_session.cookies.clear()
                    
                    # Restaurar outros cookies
                    for name, value in cookies_backup.items():
                        api_session.cookies.set(name, value)
                    
                    print(f"   [COOKIE] JSESSIONID antigo removido para evitar duplicata")
                
                # Adicionar novo JSESSIONID
                api_session.cookies.set('JSESSIONID', cookie_val)
                
                # Salvar no store manual também
                restaurante_id = None
                if data and isinstance(data, dict) and 'restaurante_id' in data:
                    restaurante_id = data.get('restaurante_id')
                
                session_cookies_store['latest'] = jsessionid_value
                if restaurante_id:
                    session_cookies_store[restaurante_id] = jsessionid_value
                
                print(f"   [COOKIE] JSESSIONID salvo na sessao e store")
        
        # Verificar cookies na sessão após requisição
        if len(api_session.cookies) > 0:
            cookie_info = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"   [COOKIE] Sessao agora tem {len(api_session.cookies)} cookie(s): {', '.join(cookie_info)}")
        
        # Log de resposta
        print(f"[RESPOSTA] Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        # Tratar erros 401/403 (Unauthorized/Forbidden) - tentar diferentes formatos
        if response.status_code in [401, 403]:
            status_name = "401 - Não autorizado" if response.status_code == 401 else "403 - Acesso negado"
            print(f"\n[ERRO] Status {response.status_code} - {status_name}")
            print(f"{'='*60}")
            print(f"   URL testada: {url}")
            print(f"   Host: {API_EXTERNA_HOST}")
            print(f"   Porta: {API_EXTERNA_PORT}")
            print(f"\n[DIAGNOSTICO] Possiveis causas:")
            
            # Diagnóstico específico para localhost
            if API_EXTERNA_HOST == 'localhost' or API_EXTERNA_HOST == '127.0.0.1':
                print(f"   ⚠️  ATENÇÃO: Tentando conectar em localhost:8080")
                print(f"   1. Formato de dados pode estar incorreto (tentando JSON, pode precisar form-urlencoded)")
                print(f"   2. Endpoint pode estar incorreto")
                print(f"   3. Credenciais podem estar incorretas")
                print(f"\n   💡 SOLUCAO:")
                print(f"   - Tentando automaticamente como form-urlencoded...")
            else:
                print(f"   1. Formato de dados incorreto (JSON vs Form-urlencoded)")
                print(f"   2. Endpoint requer autenticacao")
                print(f"   3. CORS bloqueando requisicao")
                print(f"   4. Headers incorretos ou faltando")
                print(f"   5. Credenciais incorretas")
            
            print(f"{'='*60}\n")
            
            # Se for POST e retornou 401/403, tentar como form-urlencoded
            if method == 'POST' and data:
                print(f"[TENTATIVA] Reenviando como form-urlencoded...")
                try:
                    headers_form = headers.copy()
                    headers_form['Content-Type'] = 'application/x-www-form-urlencoded'
                    
                    # Converter dados JSON para form-urlencoded
                    if isinstance(data, dict):
                        form_data = urlencode(data)
                    else:
                        form_data = data
                    
                    response_retry = api_session.post(url, data=form_data, headers=headers_form, timeout=API_TIMEOUT, allow_redirects=True)
                    
                    if response_retry.status_code not in [401, 403]:
                        print(f"[SUCESSO] Form-urlencoded funcionou! Status: {response_retry.status_code}")
                        response = response_retry
                    else:
                        print(f"[FALHA] Form-urlencoded tambem retornou {response_retry.status_code}")
                except Exception as e:
                    print(f"[ERRO] Erro ao tentar form-urlencoded: {e}")
        
        # Verificar tipo de conteúdo
        content_type = response.headers.get('Content-Type', '').lower()
        
        # IMPORTANTE: Tentar parsear como JSON PRIMEIRO, independente do Content-Type
        # Muitas APIs retornam JSON mas com Content-Type incorreto (text/html ou text/plain)
        response_data_json = None
        try:
            # Tentar parsear como JSON sempre
            response_data_json = response.json()
            print(f"   Response (JSON detectado): OK")
        except (ValueError, json.JSONDecodeError):
            # Não é JSON válido
            pass
        
        # Se conseguiu parsear como JSON, usar JSON
        if response_data_json is not None:
            response_data = response_data_json
            
            try:
                # ESPECIAL: Se for resposta de login, ajustar formato para o frontend desktop
                if 'restaurantes/login' in endpoint_api and isinstance(response_data, dict):
                    # Verificar se é erro primeiro (mas não tratar 'message' como erro sozinho)
                    if 'error' in response_data or (response.status_code >= 400):
                        # Se é erro, formatar como erro
                        error_msg = response_data.get('error') or response_data.get('message', 'Erro no login')
                        # Se status code é 200 mas tem erro, mudar para 401
                        status_final = 401 if response.status_code == 200 else response.status_code
                        response_data = {
                            'status': 'error',
                            'message': error_msg
                        }
                        print(f"[PARSE] Login JSON erro: {error_msg}")
                        return status_final, response_data
                    
                    # A API pode retornar vários formatos de sucesso:
                    # 1. {nome: "X", id: Y} - Formato direto
                    # 2. {restaurante: {nome: "X", id: Y}} - Formato aninhado
                    # 3. {status: "success", data: {...}} - Já formatado
                    
                    # Se já tem o formato esperado, não alterar
                    if response_data.get('status') == 'success' and 'data' in response_data:
                        if 'restaurante_id' in response_data['data'] or 'restaurante_nome' in response_data['data']:
                            print(f"[PARSE] Login JSON ja formatado corretamente")
                            return response.status_code, response_data
                    
                    restaurante_id = None
                    restaurante_nome = None
                    
                    # Tentar formato direto: {nome: "X", id: Y} ou {nome: "X", restaurante_id: Y}
                    if 'nome' in response_data and ('id' in response_data or 'restaurante_id' in response_data):
                        restaurante_id = response_data.get('id') or response_data.get('restaurante_id')
                        restaurante_nome = response_data.get('nome')
                        print(f"[PARSE] Login JSON formato direto: id={restaurante_id}, nome={restaurante_nome}")
                    
                    # Tentar formato aninhado: {restaurante: {nome: "X", id: Y}}
                    elif 'restaurante' in response_data:
                        restaurante = response_data.get('restaurante', {})
                        restaurante_id = restaurante.get('id') or restaurante.get('restaurante_id')
                        restaurante_nome = restaurante.get('nome')
                        print(f"[PARSE] Login JSON formato aninhado: id={restaurante_id}, nome={restaurante_nome}")
                    
                    # Tentar outros formatos possíveis
                    elif 'email' in response_data and 'id' in response_data:
                        # Formato: {email: "X", id: Y, nome: "Z"}
                        restaurante_id = response_data.get('id') or response_data.get('restaurante_id')
                        restaurante_nome = response_data.get('nome') or response_data.get('restaurante_nome')
                        print(f"[PARSE] Login JSON formato com email: id={restaurante_id}, nome={restaurante_nome}")
                    
                    # Se encontrou dados, formatar para o frontend desktop
                    if restaurante_id or restaurante_nome:
                        response_data = {
                            'status': 'success',
                            'message': 'Login realizado com sucesso',
                            'data': {}
                        }
                        if restaurante_id:
                            response_data['data']['restaurante_id'] = restaurante_id
                            print(f"[PARSE] restaurante_id incluído na resposta: {restaurante_id}")
                        if restaurante_nome:
                            response_data['data']['restaurante_nome'] = restaurante_nome
                            print(f"[PARSE] restaurante_nome incluído na resposta: {restaurante_nome}")
                        print(f"[PARSE] Login JSON convertido para formato desktop")
                    else:
                        # Se não encontrou dados conhecidos, logar o que foi recebido para debug
                        print(f"[AVISO] Formato JSON de login nao reconhecido completamente")
                        print(f"[DEBUG] Chaves recebidas: {list(response_data.keys())}")
                        print(f"[DEBUG] Conteudo: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")
                        
                        # Verificar se há alguma indicação de erro
                        if 'erro' in str(response_data).lower() or 'fail' in str(response_data).lower():
                            response_data = {
                                'status': 'error',
                                'message': 'Erro no login. Verifique suas credenciais.'
                            }
                        else:
                            # Manter resposta original mas adicionar status
                            if 'status' not in response_data:
                                response_data = {
                                    'status': 'success' if response.status_code < 400 else 'error',
                                    'message': 'Resposta do servidor recebida',
                                    'raw_data': response_data
                                }
                
                # Retornar JSON (já processado ou não)
                return response.status_code, response_data
                
            except Exception as e:
                print(f"[AVISO] Erro ao processar JSON: {e}")
                import traceback
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
                # Se deu erro mas conseguiu parsear JSON, retornar JSON original
                return response.status_code, response_data_json
        
        # Se NÃO foi JSON, verificar se é HTML
        # Só tentar HTML se realmente não conseguiu parsear como JSON
        if response_data_json is None:
            # Verificar se é HTML
            if 'text/html' in content_type or (response.text and (response.text.strip().startswith('<!DOCTYPE') or response.text.strip().startswith('<html'))):
                print(f"   Response (HTML): Detectado - Convertendo para JSON...")
                response_data = parse_html_response(response.text, endpoint_api)
                print(f"   Response convertido: OK")
                return response.status_code, response_data
            
            # Se não é JSON nem HTML, tratar como texto ou erro
            if response.status_code >= 400:
                error_data = {
                    'status': 'error',
                    'message': f'Erro HTTP {response.status_code}',
                    'status_code': response.status_code
                }
                
                # Mensagem específica para erro 403 em localhost
                if response.status_code == 403 and (API_EXTERNA_HOST == 'localhost' or API_EXTERNA_HOST == '127.0.0.1'):
                    error_data['message'] = 'Servidor não encontrado em localhost:8080. Verifique se o servidor está rodando ou use a URL da nuvem no config.env'
                    error_data['diagnostico'] = {
                        'tipo_erro': 'servidor_nao_encontrado',
                        'url_configurada': API_EXTERNA_BASE_URL,
                        'sugestao': 'Use API_EXTERNA_URL=http://3.90.155.156:8080 no config.env para usar o servidor da nuvem'
                    }
                
                if response.text:
                    error_data['response_text'] = response.text[:500]
                return response.status_code, error_data
            
            # Retornar como texto genérico
            response_data = {
                'status': 'success' if response.status_code < 400 else 'error',
                'message': response.text[:500] if response.text else 'Resposta vazia',
                'raw_response': response.text[:200] if response.text else ''
            }
            print(f"   Response (Text): {response.text[:100] if response.text else 'vazio'}...")
            return response.status_code, response_data
        
    except requests.exceptions.Timeout as e:
        # Timeout detalhado
        print(f"\n[ERRO] TIMEOUT")
        print(f"{'='*60}")
        print(f"   URL: {url}")
        print(f"   Timeout configurado: {API_TIMEOUT}s")
        print(f"   Protocolo: {API_EXTERNA_PROTOCOL}")
        print(f"   Host: {API_EXTERNA_HOST}")
        print(f"   Porta: {API_EXTERNA_PORT}")
        print(f"\n[DIAGNOSTICO] Possiveis causas:")
        print(f"   1. Servidor pode estar sobrecarregado")
        print(f"   2. Rede lenta ou instável")
        print(f"   3. Firewall bloqueando conexões")
        print(f"   4. Servidor não está respondendo a tempo")
        print(f"   5. IP/Porta podem estar incorretos")
        print(f"\n🔧 SUGESTÕES:")
        print(f"   - Verificar se servidor está rodando: ping {API_EXTERNA_HOST}")
        print(f"   - Testar conectividade: curl {url}")
        print(f"   - Aumentar timeout no config.env (atual: {API_TIMEOUT}s)")
        print(f"{'='*60}\n")
        
        return 504, {
            'status': 'error',
            'message': f'Timeout ({API_TIMEOUT}s) ao conectar com o servidor',
            'diagnostico': {
                'tipo_erro': 'timeout',
                'url_testada': url,
                'timeout_configurado': f'{API_TIMEOUT}s',
                'protocolo': API_EXTERNA_PROTOCOL,
                'host': API_EXTERNA_HOST,
                'porta': API_EXTERNA_PORT,
                'sugestoes': [
                    'Verificar se o servidor está rodando',
                    'Testar conectividade de rede',
                    'Verificar configurações de firewall',
                    'Considerar aumentar o timeout'
                ]
            }
        }
        
    except requests.exceptions.ConnectionError as e:
        # Erro de conexão detalhado
        print(f"\n[ERRO] CONEXAO FALHOU")
        print(f"{'='*60}")
        print(f"   URL: {url}")
        print(f"   Protocolo: {API_EXTERNA_PROTOCOL}")
        print(f"   Host: {API_EXTERNA_HOST}")
        print(f"   Porta: {API_EXTERNA_PORT}")
        print(f"   Erro tecnico: {str(e)}")
        print(f"\n[DIAGNOSTICO] Possiveis causas:")
        print(f"   1. Servidor não está rodando na porta {API_EXTERNA_PORT}")
        print(f"   2. IP {API_EXTERNA_HOST} está incorreto ou mudou")
        print(f"   3. Firewall bloqueando conexões na porta {API_EXTERNA_PORT}")
        print(f"   4. Servidor não está configurado para aceitar conexões externas")
        print(f"   5. Protocolo incorreto (tentando HTTP mas servidor usa HTTPS ou vice-versa)")
        print(f"\n🔧 SUGESTÕES:")
        print(f"   - Verificar se servidor está ativo: ping {API_EXTERNA_HOST}")
        print(f"   - Testar porta: telnet {API_EXTERNA_HOST} {API_EXTERNA_PORT}")
        print(f"   - Testar URL manualmente: curl {API_EXTERNA_BASE_URL}")
        print(f"   - Verificar config.env: API_EXTERNA_URL={API_EXTERNA_BASE_URL}")
        print(f"   - Confirmar com administrador se API está acessível externamente")
        print(f"{'='*60}\n")
        
        return 503, {
            'status': 'error',
            'message': 'Servidor não está disponível ou não acessível',
            'diagnostico': {
                'tipo_erro': 'connection_error',
                'url_testada': url,
                'protocolo': API_EXTERNA_PROTOCOL,
                'host': API_EXTERNA_HOST,
                'porta': API_EXTERNA_PORT,
                'erro_tecnico': str(e),
                'sugestoes': [
                    'Verificar se o servidor está rodando',
                    'Confirmar IP e porta estão corretos',
                    'Verificar configurações de firewall',
                    'Testar conectividade de rede',
                    'Confirmar se servidor aceita conexões externas'
                ]
            }
        }
        
    except requests.exceptions.RequestException as e:
        # Erro genérico de requisição (inclui parsing de URL, SSLError, etc)
        error_type = type(e).__name__
        print(f"\n[ERRO] {error_type}")
        print(f"{'='*60}")
        print(f"   URL: {url}")
        print(f"   Erro: {str(e)}")
        
        if 'Failed to parse' in str(e) or 'Invalid URL' in str(e):
            print(f"\n[DIAGNOSTICO] Erro de parsing da URL")
            print(f"   URL pode estar malformada")
            print(f"   Verifique config.env - API_EXTERNA_URL")
            print(f"   URL atual: {API_EXTERNA_BASE_URL}")
            print(f"\n[SOLUCAO]")
            print(f"   - Remova comentários inline da URL no config.env")
            print(f"   - Formato correto: API_EXTERNA_URL=http://127.0.0.1:8080")
            print(f"   - Não inclua comentários na mesma linha")
        elif 'SSL' in error_type or 'certificate' in str(e).lower():
            print(f"\n[INFO] Problema com certificado SSL")
            print(f"   Servidor pode estar usando HTTPS mas URL está como HTTP")
        
        print(f"\n[SUGESTAO]")
        print(f"   - Verificar se URL deve ser https:// em vez de http://")
        print(f"   - Atualizar config.env: API_EXTERNA_URL=https://{API_EXTERNA_HOST}:{API_EXTERNA_PORT}")
        print(f"{'='*60}\n")
        
        # Mensagem de erro específica baseada no tipo
        if 'Failed to parse' in str(e) or 'Invalid URL' in str(e):
            error_msg = 'URL inválida no config.env. Remova comentários inline da linha API_EXTERNA_URL.'
            error_type = 'url_parse_error'
        elif 'SSL' in error_type or 'certificate' in str(e).lower():
            error_msg = 'Erro de SSL/TLS - Protocolo pode estar incorreto'
            error_type = 'ssl_error'
        else:
            error_msg = f'Erro na requisição: {str(e)[:100]}'
            error_type = 'request_error'
        
        return 502, {
            'status': 'error',
            'message': error_msg,
            'diagnostico': {
                'tipo_erro': error_type,
                'url_testada': url,
                'url_base': API_EXTERNA_BASE_URL,
                'sugestao': 'Verifique config.env e remova comentários inline da URL'
            }
        }
        
    except Exception as e:
        # Erro genérico
        print(f"\n[ERRO] GENERICO")
        print(f"{'='*60}")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"   URL: {url}")
        print(f"{'='*60}\n")
        
        return 500, {
            'status': 'error',
            'message': f'Erro inesperado: {str(e)}',
            'tipo_erro': type(e).__name__
        }

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
    Endpoint para obter top 3 produtos mais vendidos
    CORREÇÃO: Usa /pedidos/restaurante da API Java e calcula localmente
    """
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        print(f"\n{'='*60}")
        print(f"[TOP-PRODUTOS] Buscando top produtos {periodo} para restaurante {restaurante_id}")
        
        # Buscar todos os pedidos do restaurante usando o endpoint correto
        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
        
        if status_code != 200:
            print(f"[TOP-PRODUTOS] Erro ao buscar pedidos: {status_code}")
            return jsonify({
                'status': 'error',
                'message': f'Erro ao buscar pedidos: Status {status_code}'
            }), status_code
        
        # Extrair lista de pedidos
        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []
        
        # Filtrar pedidos do restaurante e do período
        hoje = datetime.now().date()
        if periodo == 'semanal':
            data_inicio = hoje - timedelta(days=7)
        elif periodo == 'mensal':
            data_inicio = hoje - timedelta(days=30)
        elif periodo == 'anual':
            data_inicio = hoje - timedelta(days=365)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Período inválido. Use: semanal, mensal ou anual'
            }), 400
        
        # Agregar produtos vendidos
        produtos_vendidos = defaultdict(lambda: {'quantidade': 0, 'valor_total': 0, 'nome': None, 'preco_unitario': 0})
        
        for pedido in pedidos_todos:
            if not isinstance(pedido, dict):
                continue
            
            # Verificar restaurante
            pedido_restaurante_id = None
            if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                pedido_restaurante_id = pedido['restaurante'].get('id')
            elif pedido.get('restaurante_id'):
                pedido_restaurante_id = pedido['restaurante_id']
            
            if not pedido_restaurante_id or int(pedido_restaurante_id) != int(restaurante_id):
                continue
            
            # Verificar data
            data_pedido = None
            if pedido.get('criadoEm'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                except:
                    pass
            elif pedido.get('criado_em'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                except:
                    pass
            
            if not data_pedido or data_pedido < data_inicio:
                continue
            
            # CORREÇÃO: Filtrar apenas pedidos concluídos para top produtos
            # Apenas pedidos com status FINALIZADO, CONCLUIDO, CONCLUÍDO ou ENTREGUE
            if not is_status_concluido(pedido.get('status')):
                continue
            
            # Processar itens do pedido
            if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                for item in pedido['itens']:
                    if not isinstance(item, dict):
                        continue
                    
                    # Extrair informações do produto
                    produto_id = None
                    produto_nome = None
                    # CORREÇÃO: Garante que quantidade seja pelo menos 1 se não encontrar
                    quantidade = item.get('quantidade', 0) or item.get('quantidadeItem', 0) or 1 
                    preco_unitario = 0
                    
                    # TENTATIVA 1: Estrutura aninhada padrão (Java/JPA comum)
                    if item.get('itemRestaurante') and isinstance(item.get('itemRestaurante'), dict):
                        item_rest = item['itemRestaurante']
                        produto_id = item_rest.get('id')
                        produto_nome = item_rest.get('nome')
                        preco_unitario = float(item_rest.get('preco', 0) or 0)
                    
                    # TENTATIVA 2: Estrutura snake_case
                    elif item.get('item_restaurante') and isinstance(item.get('item_restaurante'), dict):
                        item_rest = item['item_restaurante']
                        produto_id = item_rest.get('id')
                        produto_nome = item_rest.get('nome')
                        preco_unitario = float(item_rest.get('preco', 0) or 0)
                    
                    # TENTATIVA 3: Dados direto no item (fallback comum)
                    if not produto_nome:
                        produto_id = item.get('produto_id') or item.get('id')
                        produto_nome = item.get('nome') or item.get('produto_nome') or f"Item #{produto_id}"
                    
                    # TENTATIVA 4: Preço direto no item se não achou no aninhado
                    if preco_unitario == 0:
                        preco_unitario = float(item.get('preco', 0) or item.get('valorUnitario', 0) or item.get('valor', 0) or 0)
                    
                    # TENTATIVA 5: Calcular preço unitário pelo subtotal
                    if preco_unitario == 0 and item.get('subtotal'):
                        preco_unitario = float(item['subtotal']) / quantidade
                    
                    # CORREÇÃO: Só processa se tivermos pelo menos um nome
                    if produto_nome:
                        # Use o nome como chave se o ID for None, para evitar agrupar itens diferentes
                        chave_produto = produto_id or produto_nome
                        
                        produtos_vendidos[chave_produto]['quantidade'] += quantidade
                        produtos_vendidos[chave_produto]['valor_total'] += quantidade * preco_unitario
                        # Garante que o nome fique salvo
                        if not produtos_vendidos[chave_produto]['nome']:
                            produtos_vendidos[chave_produto]['nome'] = produto_nome
                        # Atualiza o preço unitário se acharmos um maior (evita zeros)
                        if preco_unitario > produtos_vendidos[chave_produto]['preco_unitario']:
                            produtos_vendidos[chave_produto]['preco_unitario'] = preco_unitario
        
        # Ordenar por quantidade vendida e pegar top 3
        produtos_ordenados = sorted(
            produtos_vendidos.items(),
            key=lambda x: x[1]['quantidade'],
            reverse=True
        )[:3]
        
        # Formatar resposta
        produtos_formatados = []
        for posicao, (produto_key, dados) in enumerate(produtos_ordenados, 1):
            produtos_formatados.append({
                'posicao': posicao,
                'nome': dados['nome'] or f'Produto {produto_key}',
                'quantidade_vendida': dados['quantidade'],
                'valor_unitario': dados['preco_unitario'] if dados['preco_unitario'] > 0 else (dados['valor_total'] / dados['quantidade'] if dados['quantidade'] > 0 else 0),
                'valor_total_vendas': dados['valor_total']
            })
        
        print(f"[TOP-PRODUTOS] Top 3 produtos encontrados: {len(produtos_formatados)}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'periodo': periodo,
                'produtos': produtos_formatados
            }
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro no endpoint de top produtos: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro interno: {str(e)}'}), 500

# ============================================================================
# CARDÁPIO ENDPOINTS (CRUD)
# ============================================================================

@app.route('/api/cardapio/<int:restaurante_id>', methods=['GET'])
def listar_cardapio(restaurante_id):
    """Rota para LER (Listar) todos os itens do cardápio - Proxy para API externa"""
    try:
        print(f"[CARDAPIO] Listando cardápio para restaurante {restaurante_id}")
        
        # Passar restaurante_id nos params para que o cookie seja buscado corretamente
        params = {'restaurante_id': restaurante_id}
        
        status_code, response_data = proxy_request('GET', f'cardapio/{restaurante_id}', params=params)
        
        print(f"[CARDAPIO] Resposta da API externa (GET): Status {status_code}")
        print(f"[CARDAPIO] Tipo de resposta: {type(response_data)}")
        
        # Se a resposta foi bem-sucedida, formatar para o frontend
        if 200 <= status_code < 300:
            # Se response_data é uma lista, formatar como esperado pelo frontend
            if isinstance(response_data, list):
                print(f"[CARDAPIO] Resposta é lista com {len(response_data)} itens")
                return jsonify({
                    'status': 'success',
                    'data': response_data
                }), 200
            # Se response_data é dict mas tem 'data' ou 'itens', usar isso
            elif isinstance(response_data, dict):
                if 'data' in response_data:
                    print(f"[CARDAPIO] Resposta tem campo 'data'")
                    return jsonify({
                        'status': 'success',
                        'data': response_data.get('data', [])
                    }), 200
                elif 'itens' in response_data:
                    print(f"[CARDAPIO] Resposta tem campo 'itens'")
                    return jsonify({
                        'status': 'success',
                        'data': response_data.get('itens', [])
                    }), 200
                elif isinstance(response_data.get('data'), list):
                    print(f"[CARDAPIO] Resposta dict com data array")
                    return jsonify({
                        'status': 'success',
                        'data': response_data.get('data', [])
                    }), 200
                else:
                    # Se já tem status, retornar como está
                    print(f"[CARDAPIO] Resposta dict com status")
                    return jsonify(response_data), status_code
            else:
                # Resposta inesperada - retornar lista vazia
                print(f"[CARDAPIO] AVISO: Formato de resposta inesperado: {type(response_data)}")
                return jsonify({
                    'status': 'success',
                    'data': []
                }), 200
        
        # Se retornou erro, retornar resposta formatada
        if status_code == 401 or status_code == 403:
            error_msg = 'Sessão expirada. Faça login novamente.' if isinstance(response_data, dict) else str(response_data)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), status_code
        
        # Outros erros
        return jsonify({
            'status': 'error',
            'message': response_data.get('message', 'Erro ao carregar cardápio') if isinstance(response_data, dict) else 'Erro ao carregar cardápio'
        }), status_code
        
    except Exception as e:
        print(f"[ERRO] Erro ao listar cardapio: {e}")
        import traceback
        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao listar o cardápio: {str(e)}'
        }), 500

@app.route('/api/cardapio/add', methods=['POST'])
def adicionar_item():
    """Rota para CRIAR (Adicionar) um novo item ao cardápio - Proxy para API externa"""
    try:
        dados = request.get_json()
        
        # Validação de dados obrigatórios
        if not dados:
            print("[ERRO] Nenhum dado recebido no POST /api/cardapio/add")
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400
        
        print(f"[CARDAPIO] Dados recebidos para adicionar item: {json.dumps(dados, indent=2, ensure_ascii=False)}")
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'preco', 'restaurante_id']
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in dados or dados[campo] is None]
        
        if campos_faltando:
            print(f"[ERRO] Campos obrigatórios faltando: {campos_faltando}")
            return jsonify({
                'status': 'error',
                'message': f'Campos obrigatórios faltando: {", ".join(campos_faltando)}'
            }), 400
        
        # Validar tipos
        if not isinstance(dados.get('nome'), str) or not dados['nome'].strip():
            return jsonify({'status': 'error', 'message': 'Nome do prato é obrigatório e deve ser texto'}), 400
        
        if not isinstance(dados.get('preco'), (int, float)) or dados['preco'] <= 0:
            return jsonify({'status': 'error', 'message': 'Preço deve ser um número maior que zero'}), 400
        
        # IMPORTANTE: A API externa espera restaurante como objeto aninhado { id: ... }
        # Formato esperado pela API externa (conforme código do site):
        # {
        #   "nome": "...",
        #   "descricao": "...",
        #   "preco": 50.0,
        #   "imagemUrl": "...",
        #   "restaurante": { "id": 4 }
        # }
        
        # Preparar dados para API externa no formato correto
        dados_para_api = {
            'nome': dados['nome'].strip(),
            'descricao': dados.get('descricao', '').strip() or '',
            'preco': float(dados['preco']),
            'restaurante': {
                'id': int(dados['restaurante_id'])
            }
        }
        
        # Adicionar imagemUrl se fornecido (pode ser string vazia)
        if 'imagemUrl' in dados:
            dados_para_api['imagemUrl'] = dados['imagemUrl'].strip() if dados['imagemUrl'] else ''
        else:
            dados_para_api['imagemUrl'] = ''
        
        print(f"[CARDAPIO] Dados preparados para API externa:")
        print(f"   {json.dumps(dados_para_api, indent=2, ensure_ascii=False)}")
        
        # Verificar cookies disponíveis
        print(f"[CARDAPIO] Cookies na sessão: {len(api_session.cookies)} cookie(s)")
        for cookie in api_session.cookies:
            print(f"   Cookie: {cookie.name} = {cookie.value[:20]}...")
        
        # Verificar cookie armazenado manualmente
        restaurante_id_para_cookie = dados_para_api['restaurante']['id']
        cookie_manual = get_session_cookie(restaurante_id_para_cookie)
        if cookie_manual:
            print(f"[CARDAPIO] Cookie manual encontrado para restaurante {restaurante_id_para_cookie}: {cookie_manual[:30]}...")
        else:
            print(f"[CARDAPIO] AVISO: Nenhum cookie encontrado para restaurante {restaurante_id_para_cookie}")
        
        # Fazer proxy para API externa: /itens (mapeado de /api/cardapio/add)
        # IMPORTANTE: Passar restaurante_id nos params para que o cookie seja buscado corretamente
        params = {'restaurante_id': restaurante_id_para_cookie}
        
        print(f"[CARDAPIO] Fazendo requisição POST para 'cardapio/add' (mapeado para 'itens')")
        
        # Tentar primeiro com JSON
        status_code, response_data = proxy_request('POST', 'cardapio/add', data=dados_para_api, params=params)
        
        print(f"\n[CARDAPIO] === RESPOSTA DA API EXTERNA ===")
        print(f"[CARDAPIO] Status Code: {status_code}")
        print(f"[CARDAPIO] Tipo de Resposta: {type(response_data)}")
        
        if isinstance(response_data, dict):
            print(f"[CARDAPIO] Response Data (dict):")
            print(f"   {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        elif isinstance(response_data, str):
            print(f"[CARDAPIO] Response Data (string): {response_data[:500]}")
        else:
            print(f"[CARDAPIO] Response Data (outro tipo): {str(response_data)[:500]}")
        print(f"[CARDAPIO] ===================================\n")
        
        # Se retornou 400, pode ser problema de formato de dados
        # Verificar se a mensagem indica problema de formato
        if status_code == 400 and isinstance(response_data, dict):
            error_msg_check = response_data.get('message', '').lower()
            # Se o erro mencionar formato/form/data, tentar form-urlencoded
            if any(palavra in error_msg_check for palavra in ['formato', 'format', 'content-type', 'invalid', 'form']):
                print(f"[CARDAPIO] Erro pode ser de formato - tentando form-urlencoded...")
                try:
                    # Criar uma nova requisição manual com form-urlencoded
                    endpoint_api = mapear_endpoint_flask_para_api('cardapio/add')
                    url = f"{API_EXTERNA_BASE_URL}{endpoint_api}"
                    
                    headers_form = {
                        'Accept': 'text/html,application/json,application/xhtml+xml,text/plain,*/*',
                        'User-Agent': 'SGR-Desktop-Flask-Proxy/1.0',
                        'Origin': 'http://localhost:5000',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    
                    # Adicionar cookie se houver
                    if len(api_session.cookies) > 0:
                        cookie_header = '; '.join([f"{name}={value}" for name, value in api_session.cookies.items()])
                        headers_form['Cookie'] = cookie_header
                    
                    # Converter dados para form-urlencoded
                    # IMPORTANTE: Para objeto aninhado 'restaurante', precisamos converter manualmente
                    # O Spring espera: restaurante.id=4 (notação de ponto)
                    import urllib.parse
                    form_data_parts = []
                    for k, v in dados_para_api.items():
                        if k == 'restaurante' and isinstance(v, dict):
                            # Para restaurante.id usar a notação esperada pelo Spring
                            restaurante_id = v.get('id', '')
                            form_data_parts.append(f"restaurante.id={urllib.parse.quote(str(restaurante_id))}")
                        elif k == 'nome' or k == 'descricao' or k == 'imagemUrl':
                            # Fazer URL encoding de strings
                            form_data_parts.append(f"{k}={urllib.parse.quote(str(v))}")
                        else:
                            # Números e outros valores
                            form_data_parts.append(f"{k}={urllib.parse.quote(str(v))}")
                    form_data = '&'.join(form_data_parts)
                    
                    print(f"[CARDAPIO] Tentando form-urlencoded:")
                    print(f"   URL: {url}")
                    print(f"   Form Data: {form_data}")
                    
                    response_form = api_session.post(url, data=form_data, headers=headers_form, timeout=API_TIMEOUT)
                    
                    if response_form.status_code != 400:
                        print(f"[CARDAPIO] Form-urlencoded funcionou! Status: {response_form.status_code}")
                        # Processar resposta
                        try:
                            response_data = response_form.json()
                        except:
                            response_data = parse_html_response(response_form.text, endpoint_api)
                        status_code = response_form.status_code
                    else:
                        print(f"[CARDAPIO] Form-urlencoded também retornou 400")
                except Exception as e:
                    print(f"[CARDAPIO] Erro ao tentar form-urlencoded: {e}")
        
        # Se ainda retornou 400 da API externa, extrair mensagem de erro
        if status_code == 400:
            error_msg = 'Erro ao adicionar item'
            
            print(f"[CARDAPIO] Extraindo mensagem de erro do status 400...")
            
            if isinstance(response_data, dict):
                error_msg = response_data.get('message', response_data.get('error', response_data.get('mensagem', 'Dados inválidos')))
                print(f"[CARDAPIO] Mensagem extraída do dict: {error_msg}")
            elif isinstance(response_data, str):
                # Pode ser HTML ou texto de erro
                print(f"[CARDAPIO] Resposta é string, procurando mensagens de erro...")
                # Tentar extrair mensagem de erro do HTML usando BeautifulSoup
                if BS4_AVAILABLE and ('<' in response_data and '>' in response_data):
                    try:
                        soup = BeautifulSoup(response_data, 'html.parser')
                        # Procurar por divs/alerts de erro
                        error_div = soup.find(class_=['error', 'alert-danger', 'message', 'error'])
                        if error_div:
                            error_msg = error_div.get_text(strip=True)
                            print(f"[CARDAPIO] Mensagem extraída do HTML: {error_msg}")
                        else:
                            # Pegar texto do body
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
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        # Se retornou 403, pode ser problema de autenticação
        if status_code == 403:
            print(f"[ERRO] API externa retornou 403 - Acesso negado")
            return jsonify({
                'status': 'error',
                'message': 'Acesso negado. Verifique se você está autenticado.'
            }), 403
        
        # Verificar se a resposta foi bem-sucedida (2xx)
        if 200 <= status_code < 300:
            print(f"[CARDAPIO] Sucesso! Status {status_code}")
            
            # Se a resposta não tem formato padrão, formatar
            if not isinstance(response_data, dict):
                # Se for string, tentar converter ou retornar como sucesso genérico
                if isinstance(response_data, str):
                    response_data = {
                        'status': 'success',
                        'message': 'Item adicionado com sucesso',
                        'data': response_data
                    }
                else:
                    response_data = {
                        'status': 'success',
                        'message': 'Item adicionado com sucesso',
                        'data': str(response_data)
                    }
            elif 'status' not in response_data:
                # Adicionar status se não tiver
                response_data['status'] = 'success'
            
            print(f"[CARDAPIO] Retornando resposta formatada: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return jsonify(response_data), status_code
        
        # Qualquer outro status (5xx, etc)
        print(f"[CARDAPIO] Status não tratado: {status_code}")
        return jsonify({
            'status': 'error',
            'message': response_data.get('message', f'Erro ao adicionar item (status {status_code})') if isinstance(response_data, dict) else f'Erro ao adicionar item (status {status_code})'
        }), status_code
        
    except ValueError as e:
        print(f"[ERRO] Erro de validação: {e}")
        return jsonify({'status': 'error', 'message': f'Erro de validação: {str(e)}'}), 400
    except Exception as e:
        print(f"[ERRO] Erro ao adicionar item: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Falha ao adicionar item: {str(e)}'}), 500

@app.route('/api/cardapio/edit/<int:item_id>', methods=['PUT'])
def editar_item(item_id):
    """Rota para ATUALIZAR (Editar) um item existente - Proxy para API externa"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400
        
        print(f"[CARDAPIO] Editando item {item_id}")
        print(f"[CARDAPIO] Dados recebidos: {json.dumps(dados, indent=2, ensure_ascii=False)}")
        
        # IMPORTANTE: Formatar dados igual ao adicionar (restaurante como objeto aninhado)
        dados_para_api = {
            'nome': dados.get('nome', '').strip(),
            'descricao': dados.get('descricao', '').strip() or '',
            'preco': float(dados.get('preco', 0)),
            'imagemUrl': dados.get('imagemUrl', '').strip() if dados.get('imagemUrl') else ''
        }
        
        # Se tiver restaurante_id, adicionar como objeto aninhado
        if 'restaurante_id' in dados:
            dados_para_api['restaurante'] = {'id': int(dados['restaurante_id'])}
        
        params = {}
        if 'restaurante_id' in dados:
            params['restaurante_id'] = dados['restaurante_id']
        
        # Mapear para API externa: /itens/{id} com PUT
        status_code, response_data = proxy_request('PUT', f'itens/{item_id}', data=dados_para_api, params=params)
        
        print(f"[CARDAPIO] Resposta da API externa (PUT): Status {status_code}")
        
        # Se editou com sucesso
        if 200 <= status_code < 300:
            return jsonify({
                'status': 'success',
                'message': 'Item editado com sucesso',
                'data': response_data if isinstance(response_data, dict) else {}
            }), status_code
        
        # Se retornou erro
        error_msg = 'Erro ao editar item'
        if isinstance(response_data, dict):
            error_msg = response_data.get('message', error_msg)
        
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), status_code
        
    except Exception as e:
        print(f"[ERRO] Erro ao editar item: {e}")
        import traceback
        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao atualizar item: {str(e)}'
        }), 500

@app.route('/api/cardapio/delete/<int:item_id>', methods=['DELETE'])
def deletar_item(item_id):
    """Rota para DELETAR um item - Proxy para API externa"""
    try:
        print(f"[CARDAPIO] Deletando item {item_id}")
        
        # Mapear para API externa: /itens/{id} com DELETE
        # Passar restaurante_id nos params para cookie
        # Pegar restaurante_id do cookie ou header se disponível
        params = {}
        
        status_code, response_data = proxy_request('DELETE', f'itens/{item_id}', params=params)
        
        print(f"[CARDAPIO] Resposta da API externa (DELETE): Status {status_code}")
        
        # Se deletou com sucesso (200 ou 204)
        if status_code == 200 or status_code == 204:
            return jsonify({
                'status': 'success',
                'message': 'Item deletado com sucesso'
            }), 200
        
        # Se retornou erro, retornar mensagem
        error_msg = 'Erro ao deletar item'
        if isinstance(response_data, dict):
            error_msg = response_data.get('message', error_msg)
        
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), status_code
        
    except Exception as e:
        print(f"[ERRO] Erro ao deletar item: {e}")
        import traceback
        print(f"[ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Falha ao deletar item: {str(e)}'
        }), 500


@app.route('/api/vendas/<int:restaurante_id>/<periodo>')
def get_vendas_periodo(restaurante_id, periodo):
    """
    Endpoint para obter dados de vendas por período
    CORREÇÃO: Usa /pedidos/restaurante da API Java e calcula localmente
    """
    try:
        from datetime import datetime, timedelta
        
        print(f"\n{'='*60}")
        print(f"[VENDAS-PERIODO] Buscando vendas {periodo} para restaurante {restaurante_id}")
        
        # Buscar todos os pedidos do restaurante usando o endpoint correto
        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
        
        if status_code != 200:
            print(f"[VENDAS-PERIODO] Erro ao buscar pedidos: {status_code}")
            return jsonify({
                'status': 'error',
                'message': f'Erro ao buscar pedidos: Status {status_code}'
            }), status_code
        
        # Extrair lista de pedidos
        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []
        
        # Filtrar pedidos do restaurante específico (sem filtro de status rigoroso)
        pedidos_restaurante = []
        for pedido in pedidos_todos:
            if not isinstance(pedido, dict):
                continue
            
            # Verificar se é do restaurante correto
            pedido_restaurante_id = None
            if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                pedido_restaurante_id = pedido['restaurante'].get('id')
            elif pedido.get('restaurante_id'):
                pedido_restaurante_id = pedido['restaurante_id']
            
            if not pedido_restaurante_id or int(pedido_restaurante_id) != int(restaurante_id):
                continue
            
            # CORREÇÃO: Filtrar apenas pedidos concluídos para vendas
            # Apenas pedidos com status FINALIZADO, CONCLUIDO, CONCLUÍDO ou ENTREGUE
            if not is_status_concluido(pedido.get('status')):
                continue
            
            # Apenas garantir estrutura básica
            if 'itens' not in pedido:
                pedido['itens'] = []
            
            pedidos_restaurante.append(pedido)
        
        print(f"[VENDAS-PERIODO] Total de pedidos do restaurante: {len(pedidos_restaurante)}")
        
        # Determinar período
        hoje = datetime.now().date()
        if periodo == 'semanal':
            data_inicio = hoje - timedelta(days=28)  # 4 semanas
            dias_agrupamento = 7
            labels_format = 'Sem {num}'
        elif periodo == 'mensal':
            data_inicio = hoje - timedelta(days=180)  # 6 meses
            dias_agrupamento = 30
            labels_format = 'mes'
        elif periodo == 'anual':
            data_inicio = hoje - timedelta(days=1825)  # 5 anos
            dias_agrupamento = 365
            labels_format = 'ano'
        else:
            return jsonify({
                'status': 'error',
                'message': 'Período inválido. Use: semanal, mensal ou anual'
            }), 400
        
        # Agrupar pedidos por período e calcular totais
        vendas_por_periodo = {}
        produtos_por_periodo = {}
        
        for pedido in pedidos_restaurante:
            # Extrair data do pedido
            data_pedido = None
            if pedido.get('criadoEm'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                except:
                    pass
            elif pedido.get('criado_em'):
                try:
                    data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                except:
                    pass
            
            if not data_pedido or data_pedido < data_inicio:
                continue
            
            # Calcular valor total do pedido (múltiplas tentativas)
            valor_pedido = 0
            quantidade_itens = 0
            
            # Tentar 1: Calcular pelos itens
            if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                for item in pedido['itens']:
                    if isinstance(item, dict):
                        quantidade = item.get('quantidade', 0) or 0
                        preco = 0
                        
                        # Tentar diferentes caminhos para o preço
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
            
            # Tentar 2: Valor direto do pedido (se cálculo acima deu zero)
            if valor_pedido == 0:
                valor_pedido = float(pedido.get('valor_total', 0) or pedido.get('valor', 0) or pedido.get('valorTotal', 0) or 0)
            
            # Agrupar por período
            if periodo == 'semanal':
                # Calcular semana (0-3 para últimas 4 semanas)
                dias_diferenca = (hoje - data_pedido).days
                semana_num = 3 - (dias_diferenca // 7)
                if semana_num < 0 or semana_num > 3:
                    continue
                periodo_key = f'Sem {semana_num + 1}'
            elif periodo == 'mensal':
                # CORREÇÃO: Agrupar por mês usando formato YYYY-MM para garantir consistência
                # Depois convertemos para nomes abreviados
                periodo_key = data_pedido.strftime('%Y-%m')
            elif periodo == 'anual':
                # Agrupar por ano
                periodo_key = data_pedido.strftime('%Y')
            
            # Acumular valores
            if periodo_key not in vendas_por_periodo:
                vendas_por_periodo[periodo_key] = 0
                produtos_por_periodo[periodo_key] = 0
            
            vendas_por_periodo[periodo_key] += valor_pedido
            produtos_por_periodo[periodo_key] += quantidade_itens
        
        # Criar arrays ordenados
        if periodo == 'semanal':
            labels = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
        elif periodo == 'mensal':
            # CORREÇÃO: Últimos 6 meses usando meses reais (não 30 dias)
            # Garantir que o mês atual está incluído
            labels = []
            meses_abreviados_pt = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }
            for i in range(6):
                # Calcular mês: começar do mês atual e ir para trás
                mes_atual = hoje.month
                ano_atual = hoje.year
                # Subtrair i meses
                mes_num = mes_atual - i
                ano_num = ano_atual
                while mes_num <= 0:
                    mes_num += 12
                    ano_num -= 1
                # Criar chave YYYY-MM e label
                chave_mes = f'{ano_num}-{mes_num:02d}'
                label_mes = meses_abreviados_pt[mes_num]
                labels.insert(0, label_mes)
                # Garantir que a chave existe no dicionário (mesmo que zero)
                if chave_mes not in vendas_por_periodo:
                    vendas_por_periodo[chave_mes] = 0
                    produtos_por_periodo[chave_mes] = 0
        elif periodo == 'anual':
            labels = []
            for i in range(5):
                ano = hoje.year - i
                labels.insert(0, str(ano))
        
        # CORREÇÃO: Para período mensal, mapear labels para chaves YYYY-MM
        if periodo == 'mensal':
            meses_abreviados_pt = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }
            vendas_data = []
            produtos_data = []
            for i in range(6):
                mes_atual = hoje.month
                ano_atual = hoje.year
                mes_num = mes_atual - i
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
                'produtos': produtos_data
            }
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro no endpoint de vendas por periodo: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro interno: {str(e)}'}), 500

# Função get_top_produtos_old removida - código antigo não utilizado

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/<int:restaurante_id>', methods=['GET'])
def get_dashboard_completo(restaurante_id):
    """
    Endpoint centralizado para dados analíticos do dashboard
    Busca pedidos da API externa e calcula métricas baseado em pedidos CONCLUIDOS/FINALIZADOS
    CORREÇÃO: Usa apenas pedidos com status FINALIZADO, CONCLUIDO, CONCLUÍDO ou ENTREGUE
    (case-insensitive - aceita variações de maiúsculas/minúsculas)
    """
    try:
        print(f"\n{'='*60}")
        print(f"[DASHBOARD] Buscando dados para restaurante {restaurante_id}")
        
        # Buscar pedidos da API externa (como no HTML fornecido)
        # O endpoint /pedidos retorna todos os pedidos do cliente logado
        # Para restaurante, precisamos buscar pedidos do restaurante
        try:
            # Buscar pedidos do restaurante usando o endpoint interno
            # Este endpoint busca diretamente do banco (já que a API externa não tem endpoint para restaurante)
            from datetime import datetime, timedelta
            import requests
            
            # Buscar pedidos CONCLUÍDOS do restaurante usando o novo endpoint específico
            try:
                # Usar o novo endpoint /api/pedidos/restaurante/{id}/concluidos
                response_internal = requests.get(
                    f'http://localhost:5000/api/pedidos/restaurante/{restaurante_id}/concluidos',
                    timeout=10
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
            except Exception as e:
                print(f"[DASHBOARD] Erro ao buscar pedidos concluídos: {e}")
                import traceback
                print(f"[DASHBOARD] Traceback: {traceback.format_exc()}")
                pedidos = []
            
            pedidos_concluidos = pedidos  # Já filtrados pelo endpoint
            print(f"[DASHBOARD] Total de pedidos concluídos do restaurante: {len(pedidos_concluidos)}")
            
            # Debug: mostrar detalhes dos pedidos encontrados
            if len(pedidos_concluidos) > 0:
                import json
                print(f"[DASHBOARD] Primeiro pedido encontrado: {json.dumps(pedidos_concluidos[0], indent=2, default=str)[:300]}")
            else:
                print(f"[DASHBOARD] ⚠️ Nenhum pedido concluído encontrado para restaurante {restaurante_id}")
            
            # Calcular métricas
            hoje = datetime.now().date()
            ontem = hoje - timedelta(days=1)
            semana_atras = hoje - timedelta(days=7)
            mes_atras = hoje - timedelta(days=30)
            
            # 1. Total de Vendas (soma de todos os pedidos concluídos)
            total_vendas = 0
            produtos_vendidos = 0
            pedidos_hoje = 0
            vendas_hoje = 0
            
            # 2. Vendas de hoje
            vendas_ontem = 0
            pedidos_ontem = 0
            
            # 3. Dados para gráfico (últimos 7 dias)
            vendas_por_dia = {}
            produtos_por_dia = {}
            
            # Inicializar últimos 7 dias
            for i in range(7):
                data = hoje - timedelta(days=6-i)
                vendas_por_dia[data.strftime('%Y-%m-%d')] = 0
                produtos_por_dia[data.strftime('%Y-%m-%d')] = 0
            
            for pedido in pedidos_concluidos:
                # Calcular valor total do pedido (múltiplas tentativas para lidar com lazy loading)
                valor_pedido = 0
                quantidade_itens = 0
                
                # Tentar 1: Calcular pelos itens (com vários caminhos possíveis)
                if pedido.get('itens') and isinstance(pedido.get('itens'), list):
                    for item in pedido['itens']:
                        if isinstance(item, dict):
                            quantidade = item.get('quantidade', 0) or item.get('quantidadeItem', 0) or 0
                            preco = 0
                            
                            # Tentar MÚLTIPLOS caminhos para o preço (lazy loading pode não serializar)
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
                                # Se tem subtotal, calcular preço unitário
                                preco = float(item.get('subtotal', 0) or 0) / quantidade
                            
                            valor_pedido += quantidade * preco
                            quantidade_itens += quantidade
                
                # Tentar 2: Valor direto do pedido (se cálculo acima deu zero ou não tinha itens)
                if valor_pedido == 0:
                    valor_pedido = float(
                        pedido.get('valor_total', 0) or 
                        pedido.get('valor', 0) or 
                        pedido.get('valorTotal', 0) or 
                        pedido.get('total', 0) or 
                        0
                    )
                
                # Debug: logar se valor ainda está zero
                if valor_pedido == 0:
                    import json
                    print(f"[DASHBOARD] AVISO: Pedido {pedido.get('id')} tem valor zero. Estrutura: {json.dumps(pedido, indent=2, default=str)[:500]}")
                
                # Data do pedido
                data_pedido_str = None
                if pedido.get('criadoEm'):
                    try:
                        data_pedido = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                        data_pedido_str = data_pedido.strftime('%Y-%m-%d')
                    except:
                        pass
                elif pedido.get('criado_em'):
                    try:
                        data_pedido = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                        data_pedido_str = data_pedido.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Acumular totais
                total_vendas += valor_pedido
                produtos_vendidos += quantidade_itens
                
                # Acumular por dia
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
            
            # 4. Ticket médio (valor médio por pedido)
            ticket_medio = total_vendas / len(pedidos_concluidos) if len(pedidos_concluidos) > 0 else 0
            
            # 5. Evolução percentual (comparar hoje com ontem)
            evolucao_percentual = 0
            if vendas_ontem > 0:
                evolucao_percentual = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
            elif vendas_hoje > 0 and vendas_ontem == 0:
                evolucao_percentual = 100  # Se não tinha ontem e tem hoje, é 100% de crescimento
            elif vendas_hoje == 0 and vendas_ontem == 0:
                evolucao_percentual = 0  # Sem vendas em ambos os dias
            elif vendas_hoje == 0 and vendas_ontem > 0:
                evolucao_percentual = -100  # Tinha vendas ontem mas não hoje
            
            print(f"[DASHBOARD] Evolução calculada: vendas_hoje={vendas_hoje}, vendas_ontem={vendas_ontem}, evolucao={evolucao_percentual:.1f}%")
            
            # Formatar dados para o frontend
            cards = {
                'total_vendas': {
                    'valor': f'R$ {total_vendas:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_numerico': total_vendas
                },
                'quantidade_produtos': {
                    'valor': str(produtos_vendidos),
                    'valor_numerico': produtos_vendidos
                },
                'ticket_medio_diario': {
                    'valor': f'R$ {ticket_medio:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_numerico': ticket_medio
                },
                'evolucao_percentual': {
                    'valor': f'{evolucao_percentual:+.1f}%',
                    'valor_numerico': evolucao_percentual,
                    'tipo': 'positive' if evolucao_percentual >= 0 else 'negative'
                }
            }
            
            # Dados para gráficos
            # CORREÇÃO: Garantir que sempre temos labels para os últimos 7 dias, mesmo sem vendas
            # Isso permite que o gráfico seja renderizado mesmo que alguns dias tenham zero
            hoje = datetime.now().date()
            todos_os_dias = [(hoje - timedelta(days=6-i)).strftime('%Y-%m-%d') for i in range(7)]
            
            # Preencher com zeros os dias que não têm dados
            dias_ordenados = sorted(set(todos_os_dias + list(vendas_por_dia.keys())))
            labels_vendas = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in dias_ordenados]
            data_vendas = [vendas_por_dia.get(d, 0) for d in dias_ordenados]
            
            dias_ordenados_produtos = sorted(set(todos_os_dias + list(produtos_por_dia.keys())))
            labels_produtos = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in dias_ordenados_produtos]
            data_produtos = [produtos_por_dia.get(d, 0) for d in dias_ordenados_produtos]
            
            # Verificar se há dados significativos (pelo menos um valor > 0)
            tem_vendas = any(v > 0 for v in data_vendas)
            tem_produtos = any(p > 0 for p in data_produtos)
            
            graficos = {
                'valor_diario': {
                    'labels': labels_vendas,
                    'data': data_vendas
                },
                'produtos_diarios': {
                    'labels': labels_produtos,
                    'data': data_produtos
                }
            }
            
            # Debug: verificar se há dados significativos
            print(f"[DASHBOARD] Tem vendas significativas: {tem_vendas}, Tem produtos significativos: {tem_produtos}")
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
            
            # Debug: mostrar estrutura dos cards
            import json
            print(f"[DASHBOARD] Cards a retornar: {json.dumps(cards, indent=2, default=str)}")
            print(f"[DASHBOARD] Graficos a retornar: labels={graficos.get('valor_diario', {}).get('labels', [])[:3]}..., data={graficos.get('valor_diario', {}).get('data', [])[:3]}...")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'cards': cards,
                    'graficos': graficos
                }
            }), 200
            
        except Exception as proxy_error:
            print(f"[DASHBOARD] Erro ao buscar pedidos: {proxy_error}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            # Retornar estrutura vazia mas válida
            return jsonify({
                'status': 'success',
                'data': {
                    'cards': {},
                    'graficos': {}
                },
                'message': 'Dashboard carregado (sem dados disponíveis)'
            }), 200
            
    except Exception as e:
        print(f"[ERRO] ERRO no dashboard: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        # Em caso de erro, retornar estrutura vazia em vez de erro
        return jsonify({
            'status': 'success',
            'data': {
                'cards': {},
                'graficos': {}
            },
            'message': 'Dashboard carregado (erro ao buscar dados)'
        }), 200

# ============================================================================
# FUNÇÃO AUXILIAR: Verificar se status é concluído
# ============================================================================

def is_status_concluido(status):
    """
    Verifica se um status é considerado concluído/finalizado
    Aceita apenas: FINALIZADO, CONCLUIDO, CONCLUÍDO, ENTREGUE
    Case-insensitive (aceita variações de maiúsculas/minúsculas)
    """
    if not status:
        return False
    
    # Normalizar: remover espaços e converter para maiúsculas
    status_normalizado = str(status).strip().upper()
    
    # Lista de status concluídos aceitos (apenas os 4 principais com variações)
    status_concluidos = [
        # FINALIZADO (com variações)
        'FINALIZADO', 'FINALIZADA', 'FINALIZADOS', 'FINALIZADAS',
        # CONCLUIDO/CONCLUÍDO (com variações)
        'CONCLUIDO', 'CONCLUÍDO', 'CONCLUIDA', 'CONCLUÍDA', 
        'CONCLUIDOS', 'CONCLUÍDOS', 'CONCLUIDAS', 'CONCLUÍDAS',
        # ENTREGUE (com variações)
        'ENTREGUE', 'ENTREGUES'
    ]
    
    return status_normalizado in status_concluidos

# ============================================================================
# PEDIDOS ENDPOINTS
# ============================================================================

@app.route('/api/pedidos/restaurante/<int:restaurante_id>', methods=['GET'])
def get_pedidos_restaurante(restaurante_id):
    """
    Lista pedidos de um restaurante - Proxy para API externa
    Busca todos os pedidos da API externa e filtra por restaurante_id e status
    """
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        print(f"\n{'='*60}")
        print(f"[PEDIDOS-RESTAURANTE] Buscando pedidos para restaurante {restaurante_id}")
        print(f"[PEDIDOS-RESTAURANTE] Filtro de status: {status}")
        
        # CORREÇÃO: Usar o endpoint correto /pedidos/restaurante da API Java
        # Este endpoint retorna todos os pedidos do restaurante logado
        try:
            status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
            
            print(f"[PEDIDOS-RESTAURANTE] Status code da API externa: {status_code}")
            
            if status_code != 200:
                print(f"[PEDIDOS-RESTAURANTE] Erro ao buscar pedidos: {status_code}")
                return jsonify({
                    'status': 'error',
                    'message': f'Erro ao buscar pedidos: Status {status_code}'
                }), status_code
            
            # Extrair lista de pedidos
            pedidos_todos = []
            if isinstance(response_data, list):
                pedidos_todos = response_data
            elif isinstance(response_data, dict):
                pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
                if not isinstance(pedidos_todos, list):
                    pedidos_todos = []
            
            print(f"[PEDIDOS-RESTAURANTE] Total de pedidos recebidos da API: {len(pedidos_todos)}")
            
            # Debug: mostrar estrutura de um pedido (se houver)
            if len(pedidos_todos) > 0:
                import json
                primeiro_pedido = pedidos_todos[0]
                print(f"[PEDIDOS-RESTAURANTE] Estrutura do primeiro pedido: {json.dumps(primeiro_pedido, indent=2, default=str)[:500]}")
            
            # Filtrar pedidos do restaurante específico
            pedidos_filtrados = []
            for pedido in pedidos_todos:
                if not isinstance(pedido, dict):
                    continue
                
                # Verificar se é do restaurante
                pedido_restaurante_id = None
                if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                    pedido_restaurante_id = pedido['restaurante'].get('id')
                elif pedido.get('restaurante_id'):
                    pedido_restaurante_id = pedido['restaurante_id']
                
                # CORREÇÃO: O endpoint /pedidos/restaurante já retorna apenas pedidos do restaurante logado
                # Não precisamos filtrar por restaurante_id aqui, mas podemos manter como validação extra
                # Se o pedido tiver restaurante_id, validar; caso contrário, aceitar (já vem filtrado)
                if pedido_restaurante_id and int(pedido_restaurante_id) != int(restaurante_id):
                    print(f"[PEDIDOS-RESTAURANTE] Pedido {pedido.get('id')} - restaurante_id diferente: {pedido_restaurante_id} != {restaurante_id}")
                    continue
                
                # Filtrar por status se fornecido
                if status:
                    pedido_status = (pedido.get('status') or '').upper()
                    status_upper = status.upper()
                    
                    # Aceitar múltiplas variações
                    if status_upper in ['FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO']:
                        if pedido_status not in ['FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO']:
                            continue
                    else:
                        if pedido_status != status_upper:
                            continue
                
                # Filtrar por data se fornecido
                if data_inicio or data_fim:
                    pedido_data_str = None
                    if pedido.get('criadoEm'):
                        try:
                            pedido_data = datetime.fromisoformat(str(pedido['criadoEm']).replace('Z', '+00:00')).date()
                            pedido_data_str = pedido_data.strftime('%Y-%m-%d')
                        except:
                            pass
                    elif pedido.get('criado_em'):
                        try:
                            pedido_data = datetime.fromisoformat(str(pedido['criado_em']).replace('Z', '+00:00')).date()
                            pedido_data_str = pedido_data.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    if pedido_data_str:
                        if data_inicio and pedido_data_str < data_inicio:
                            continue
                        if data_fim and pedido_data_str > data_fim:
                            continue
                
                # Garantir que tem restaurante_id
                if 'restaurante_id' not in pedido:
                    pedido['restaurante_id'] = restaurante_id
                
                # Garantir que tem ambos os formatos de data
                if 'criadoEm' not in pedido and 'criado_em' in pedido:
                    pedido['criadoEm'] = pedido['criado_em']
                elif 'criado_em' not in pedido and 'criadoEm' in pedido:
                    pedido['criado_em'] = pedido['criadoEm']
                
                # Garantir que tem itens (pode já vir do API)
                if 'itens' not in pedido:
                    pedido['itens'] = []
                
                pedidos_filtrados.append(pedido)
            
            print(f"[PEDIDOS-RESTAURANTE] Pedidos filtrados: {len(pedidos_filtrados)}")
            
            # Ordenar por data (mais recente primeiro)
            pedidos_filtrados.sort(key=lambda p: (
                p.get('criadoEm') or p.get('criado_em') or ''
            ), reverse=True)
            
            pedidos = pedidos_filtrados
            
        except Exception as e:
            print(f"[PEDIDOS-RESTAURANTE] Erro ao buscar pedidos da API externa: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            # Retornar lista vazia em caso de erro
            pedidos = []
        
        print(f"[PEDIDOS-RESTAURANTE] Retornando {len(pedidos)} pedidos para restaurante {restaurante_id}")
        
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

@app.route('/api/pedidos/restaurante/<int:restaurante_id>/concluidos', methods=['GET'])
def get_pedidos_concluidos_restaurante(restaurante_id):
    """
    Lista pedidos CONCLUÍDOS/FINALIZADOS de um restaurante específico
    Usa o endpoint /pedidos/restaurante da API Java (Spring Boot)
    CORREÇÃO: Filtro flexível - aceita apenas status concluídos:
    - FINALIZADO, CONCLUIDO, CONCLUÍDO, ENTREGUE
    - Case-insensitive (aceita variações de maiúsculas/minúsculas)
    """
    try:
        print(f"\n{'='*60}")
        print(f"[PEDIDOS-CONCLUIDOS] Buscando pedidos concluídos para restaurante {restaurante_id}")
        
        # Buscar pedidos do restaurante usando o endpoint /pedidos/restaurante da API Java
        try:
            # CORREÇÃO: Usar o endpoint correto /pedidos/restaurante da API Java (Spring Boot)
            # Este endpoint retorna todos os pedidos do restaurante logado
            status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
            
            print(f"[PEDIDOS-CONCLUIDOS] Status code da API externa: {status_code}")
            
            if status_code != 200:
                print(f"[PEDIDOS-CONCLUIDOS] Erro ao buscar pedidos: {status_code}")
                return jsonify({
                    'status': 'error',
                    'message': f'Erro ao buscar pedidos: Status {status_code}',
                    'data': []
                }), status_code
            
            # Extrair lista de pedidos
            pedidos_todos = []
            if isinstance(response_data, list):
                pedidos_todos = response_data
            elif isinstance(response_data, dict):
                pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
                if not isinstance(pedidos_todos, list):
                    pedidos_todos = []
            
            print(f"[PEDIDOS-CONCLUIDOS] Total de pedidos recebidos da API: {len(pedidos_todos)}")
            
            # Filtrar apenas pedidos CONCLUÍDOS/FINALIZADOS do restaurante específico
            pedidos_concluidos = []
            for pedido in pedidos_todos:
                if not isinstance(pedido, dict):
                    continue
                
                # Verificar se é do restaurante correto
                pedido_restaurante_id = None
                if pedido.get('restaurante') and isinstance(pedido.get('restaurante'), dict):
                    pedido_restaurante_id = pedido['restaurante'].get('id')
                elif pedido.get('restaurante_id'):
                    pedido_restaurante_id = pedido['restaurante_id']
                
                # Filtrar por restaurante_id
                if not pedido_restaurante_id or int(pedido_restaurante_id) != int(restaurante_id):
                    continue
                
                # CORREÇÃO: Filtro flexível para status concluídos (case-insensitive)
                # Aceita apenas: FINALIZADO, CONCLUIDO, CONCLUÍDO, ENTREGUE (com variações de maiúsculas/minúsculas)
                if not is_status_concluido(pedido.get('status')):
                    continue
                
                # Garantir que tem restaurante_id
                if 'restaurante_id' not in pedido:
                    pedido['restaurante_id'] = restaurante_id
                
                # Garantir que tem ambos os formatos de data
                if 'criadoEm' not in pedido and 'criado_em' in pedido:
                    pedido['criadoEm'] = pedido['criado_em']
                elif 'criado_em' not in pedido and 'criadoEm' in pedido:
                    pedido['criado_em'] = pedido['criadoEm']
                
                # Garantir que tem itens (pode já vir do API)
                if 'itens' not in pedido:
                    pedido['itens'] = []
                
                pedidos_concluidos.append(pedido)
            
            print(f"[PEDIDOS-CONCLUIDOS] Pedidos concluídos encontrados: {len(pedidos_concluidos)}")
            
            # Ordenar por data (mais recente primeiro)
            pedidos_concluidos.sort(key=lambda p: (
                p.get('criadoEm') or p.get('criado_em') or ''
            ), reverse=True)
            
            return jsonify({
                'status': 'success',
                'data': pedidos_concluidos,
                'count': len(pedidos_concluidos)
            }), 200
            
        except Exception as e:
            print(f"[PEDIDOS-CONCLUIDOS] Erro ao buscar pedidos da API externa: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'Erro ao buscar pedidos: {str(e)}',
                'data': []
            }), 500
        
    except Exception as e:
        print(f"[PEDIDOS-CONCLUIDOS] Erro geral: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': []
        }), 500

@app.route('/api/pedidos/<int:pedido_id>/status', methods=['PUT'])
def update_pedido_status(pedido_id):
    """
    Atualiza status de um pedido - Proxy para API externa
    CORREÇÃO: Usar endpoint /status-restaurante para restaurantes
    A API Java usa @RequestParam String status, então enviamos como query parameter
    """
    try:
        print(f"\n{'='*60}")
        print(f"[UPDATE-STATUS] Atualizando status do pedido {pedido_id}")
        
        dados = request.get_json()
        if not dados:
            print(f"[UPDATE-STATUS] Erro: Dados não fornecidos")
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400
        
        novo_status = dados.get('status')
        if not novo_status:
            print(f"[UPDATE-STATUS] Erro: Status não fornecido")
            return jsonify({'status': 'error', 'message': 'Status não fornecido'}), 400
        
        print(f"[UPDATE-STATUS] Status recebido: {novo_status}")
        
        # CORREÇÃO: Normalizar status para o formato esperado pela API Java
        # Mapear valores do frontend para valores da API Java
        status_mapeado = novo_status.lower().strip()
        
        # Mapeamento completo de status
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
            'cancelado': 'CANCELADO'
        }
        
        # Buscar no mapeamento
        if status_mapeado in status_mapping:
            status_mapeado = status_mapping[status_mapeado]
        else:
            # Se não encontrou no mapeamento, tentar converter para maiúsculas
            # e verificar se já está no formato esperado
            status_upper = novo_status.upper().strip()
            status_validos = ['PENDENTE', 'NOVO', 'EM_PREPARO', 'PRONTO', 'FINALIZADO', 'CONCLUIDO', 'CONCLUÍDO', 'ENTREGUE', 'CANCELADO']
            
            if status_upper in status_validos:
                status_mapeado = status_upper
            else:
                # Fallback: usar o valor original em maiúsculas
                status_mapeado = status_upper
                print(f"[UPDATE-STATUS] ⚠️ Status não mapeado: {novo_status} -> usando {status_mapeado}")
        
        print(f"[UPDATE-STATUS] Status mapeado para API Java: {status_mapeado}")
        
        # Verificar cookies antes de enviar
        if len(api_session.cookies) > 0:
            cookie_info = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"[UPDATE-STATUS] Cookies na sessão: {', '.join(cookie_info)}")
        else:
            print(f"[UPDATE-STATUS] ⚠️ AVISO: Nenhum cookie na sessão!")
        
        # CORREÇÃO: Usar endpoint /status-restaurante para restaurantes atualizarem status
        # A API Java espera status como @RequestParam, não como JSON body
        # Enviar como query parameter: PUT /pedidos/{id}/status-restaurante?status=...
        params = {'status': status_mapeado}
        print(f"[UPDATE-STATUS] Enviando requisição: PUT pedidos/{pedido_id}/status-restaurante?status={status_mapeado}")
        
        status_code, response_data = proxy_request('PUT', f'pedidos/{pedido_id}/status-restaurante', params=params)
        
        print(f"[UPDATE-STATUS] Resposta da API Java: Status {status_code}")
        if isinstance(response_data, dict):
            print(f"[UPDATE-STATUS] Resposta completa: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"[UPDATE-STATUS] Resposta (tipo {type(response_data)}): {str(response_data)[:200]}")
        
        # Tratar erros HTTP (400, 401, 403, 404, 500, etc.)
        if status_code >= 400:
            error_msg = 'Erro ao atualizar status'
            
            # Extrair mensagem de erro da resposta
            if isinstance(response_data, dict):
                error_msg = response_data.get('message') or response_data.get('error') or response_data.get('mensagem') or error_msg
            elif isinstance(response_data, str):
                error_msg = response_data[:200]
            
            # Mensagens específicas por código de status
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
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'status_code': status_code
            }), status_code
        
        # Se status code é 200 mas não tem formato esperado
        if status_code == 200:
            # A API Java pode retornar o objeto Pedido diretamente (sem wrapper)
            # Se response_data é um dict mas não tem 'status', pode ser o pedido atualizado
            if isinstance(response_data, dict):
                # Se tem campos típicos de um pedido (id, status), assumir sucesso
                if 'id' in response_data or 'status' in response_data:
                    print(f"[UPDATE-STATUS] Resposta parece ser o pedido atualizado - tratando como sucesso")
                    return jsonify({
                        'status': 'success',
                        'message': 'Status atualizado com sucesso',
                        'data': response_data
                    }), 200
                # Se tem 'message' mas não tem 'status', verificar se é erro
                elif 'message' in response_data:
                    # Se a mensagem indica erro, tratar como erro
                    msg_lower = response_data['message'].lower()
                    if any(palavra in msg_lower for palavra in ['erro', 'error', 'falha', 'inválido', 'invalid']):
                        print(f"[UPDATE-STATUS] ⚠️ Mensagem indica erro: {response_data['message']}")
                        return jsonify({
                            'status': 'error',
                            'message': response_data['message']
                        }), 400
                    else:
                        # Mensagem genérica, assumir sucesso
                        return jsonify({
                            'status': 'success',
                            'message': response_data.get('message', 'Status atualizado com sucesso')
                        }), 200
                else:
                    # Dict sem campos conhecidos, assumir sucesso
                    return jsonify({
                        'status': 'success',
                        'message': 'Status atualizado com sucesso',
                        'data': response_data
                    }), 200
            else:
                # Resposta não é dict, assumir sucesso se status code é 200
                return jsonify({
                    'status': 'success',
                    'message': 'Status atualizado com sucesso'
                }), 200
        
        # Garantir formato de resposta correto para outros casos
        if not isinstance(response_data, dict):
            response_data = {
                'status': 'success' if status_code < 400 else 'error',
                'message': 'Status atualizado com sucesso' if status_code < 400 else 'Erro ao atualizar status'
            }
        elif 'status' not in response_data:
            response_data['status'] = 'success' if status_code < 400 else 'error'
        
        print(f"[UPDATE-STATUS] Retornando resposta formatada: status={response_data.get('status')}")
        print(f"{'='*60}\n")
        
        return jsonify(response_data), status_code
    except Exception as e:
        print(f"[UPDATE-STATUS] ⚠️ ERRO: {e}")
        import traceback
        print(f"[UPDATE-STATUS] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Erro ao atualizar status: {str(e)}'}), 500

@app.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
def get_pedido_detalhes(pedido_id):
    """
    Busca detalhes de um pedido específico - Proxy para API externa
    CORREÇÃO: A API Java não tem endpoint GET /pedidos/{id}, então buscamos da lista e filtramos
    """
    try:
        print(f"[PEDIDO-DETALHES] Buscando detalhes do pedido {pedido_id}")
        
        # A API Java não tem endpoint GET /pedidos/{id}
        # Buscar todos os pedidos do restaurante e filtrar por ID
        status_code, response_data = proxy_request('GET', 'pedidos/restaurante')
        
        if status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Erro ao buscar pedidos: Status {status_code}'
            }), status_code
        
        # Extrair lista de pedidos
        pedidos_todos = []
        if isinstance(response_data, list):
            pedidos_todos = response_data
        elif isinstance(response_data, dict):
            pedidos_todos = response_data.get('data', []) or response_data.get('pedidos', [])
            if not isinstance(pedidos_todos, list):
                pedidos_todos = []
        
        # Procurar pedido específico
        pedido_encontrado = None
        for pedido in pedidos_todos:
            if isinstance(pedido, dict) and pedido.get('id') == pedido_id:
                pedido_encontrado = pedido
                break
        
        if not pedido_encontrado:
            return jsonify({
                'status': 'error',
                'message': 'Pedido não encontrado'
            }), 404
        
        # Formatar resposta como esperado pelo frontend
        # O frontend espera: { status: 'success', data: { pedido: {...}, itens: [...] } }
        itens = pedido_encontrado.get('itens', [])
        
        # Calcular valor total se não existir
        valor_total = pedido_encontrado.get('valor_total') or pedido_encontrado.get('valor') or 0
        if valor_total == 0 and itens:
            # Calcular pela soma dos itens
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
        
        # Garantir formato de data
        data_pedido = pedido_encontrado.get('criadoEm') or pedido_encontrado.get('criado_em') or pedido_encontrado.get('data_pedido')
        
        # Formatar itens
        itens_formatados = []
        for item in itens:
            if isinstance(item, dict):
                nome = None
                preco = 0
                quantidade = item.get('quantidade', 0) or 0
                observacoes = item.get('observacoes') or item.get('observacoes_item')
                
                # Extrair nome e preço
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
                        'observacoes': observacoes
                    })
        
        # Extrair cliente
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
                    'cliente': cliente
                },
                'itens': itens_formatados
            }
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar detalhes do pedido: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# VENDAS ENDPOINTS
# ============================================================================

# ============================================================================
# ⚠️ CÓDIGO INUTILIZADO - Endpoint não funciona (execute_query não existe)
# Este endpoint não é chamado pelo frontend e causa erro ao ser executado
# ============================================================================
# @app.route('/api/relatorios/faturamento/<int:restaurante_id>', methods=['GET'])
# def get_faturamento(restaurante_id):
#     """
#     Relatório de faturamento por período
#     
#     Args:
#         restaurante_id: ID do restaurante
#         
#     Query Params:
#         data_inicio: Data inicial (YYYY-MM-DD)
#         data_fim: Data final (YYYY-MM-DD)
#         
#     Returns:
#         JSON com resumo e faturamento diário
#     """
#     try:
#         data_inicio = request.args.get('data_inicio')
#         data_fim = request.args.get('data_fim')
#         
#         if not data_inicio or not data_fim:
#             return jsonify({'status': 'error', 'message': 'Data início e fim são obrigatórias'}), 400
#         
#         # 🔥 CORREÇÃO: Calcular valor total usando item_pedido e item_restaurante
#         # Campo valor_total não existe na tabela pedido
#         faturamento = execute_query("""
#             SELECT 
#                 COALESCE(SUM(ip.quantidade * ir.preco), 0) as total_faturamento,
#                 COUNT(DISTINCT p.id) as total_pedidos,
#                 COALESCE(AVG(pedido_valor.total), 0) as ticket_medio
#             FROM pedido p
#             LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
#             LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
#             WHERE p.restaurante_id = %s 
#             AND DATE(p.criado_em) BETWEEN %s AND %s
#             GROUP BY p.id
#             HAVING SUM(ip.quantidade * ir.preco) IS NOT NULL
#         """, (restaurante_id, data_inicio, data_fim))
#         
#         # Faturamento por dia
#         faturamento_diario = execute_query("""
#             SELECT 
#                 DATE(p.criado_em) as data,
#                 COALESCE(SUM(ip.quantidade * ir.preco), 0) as faturamento,
#                 COUNT(DISTINCT p.id) as pedidos
#             FROM pedido p
#             LEFT JOIN item_pedido ip ON p.id = ip.pedido_id
#             LEFT JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
#             WHERE p.restaurante_id = %s 
#             AND DATE(p.criado_em) BETWEEN %s AND %s
#             GROUP BY DATE(p.criado_em)
#             ORDER BY data
#         """, (restaurante_id, data_inicio, data_fim))
#         
#         return jsonify({
#             'status': 'success',
#             'data': {
#                 'resumo': {
#                     'total_faturamento': float(faturamento[0]['total_faturamento']) if faturamento else 0,
#                     'total_pedidos': faturamento[0]['total_pedidos'] if faturamento else 0,
#                     'ticket_medio': float(faturamento[0]['ticket_medio']) if faturamento else 0
#                 },
#                 'diario': [
#                     {
#                         'data': row['data'].strftime('%d/%m/%Y'),
#                         'faturamento': float(row['faturamento']),
#                         'pedidos': row['pedidos']
#                     }
#                     for row in faturamento_diario
#                 ]
#             }
#         })
#         
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500
# ============================================================================
# ⚠️ CÓDIGO INUTILIZADO - Endpoint não funciona (execute_query não existe)
# Este endpoint não é chamado pelo frontend e causa erro ao ser executado
# ============================================================================
# @app.route('/api/relatorios/produtos_mais_vendidos/<int:restaurante_id>', methods=['GET'])
# def get_produtos_mais_vendidos(restaurante_id):
#     """Relatório de produtos mais vendidos"""
#     try:
#         data_inicio = request.args.get('data_inicio')
#         data_fim = request.args.get('data_fim')
#         limite = request.args.get('limite', 10)
#         
#         query = """
#             SELECT 
#                 ir.nome as produto,
#                 SUM(ip.quantidade) as quantidade_vendida,
#                 ir.preco,
#                 COUNT(DISTINCT p.id) as total_pedidos,
#                 SUM(ip.quantidade * ir.preco) as faturamento_item
#             FROM item_pedido ip
#             JOIN item_restaurante ir ON ip.item_restaurante_id = ir.id
#             JOIN pedido p ON ip.pedido_id = p.id
#             WHERE p.restaurante_id = %s
#         """
#         params = [restaurante_id]
#         
#         # 🔥 CORREÇÃO: Usar criado_em em vez de data_pedido
#         if data_inicio and data_fim:
#             query += " AND DATE(p.criado_em) BETWEEN %s AND %s"
#             params.extend([data_inicio, data_fim])
#         
#         query += """
#             GROUP BY ir.id, ir.nome, ir.preco
#             ORDER BY quantidade_vendida DESC
#             LIMIT %s
#         """
#         params.append(int(limite))
#         
#         results = execute_query(query, params)
#         
#         produtos = []
#         for row in results:
#             produtos.append({
#                 'produto': row['produto'],
#                 'quantidade_vendida': row['quantidade_vendida'],
#                 'preco_unitario': float(row['preco']),
#                 'total_pedidos': row['total_pedidos'],
#                 'faturamento_total': float(row['faturamento_item'])
#             })
#         
#         return jsonify({
#             'status': 'success',
#             'data': produtos
#         })
#         
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# CARDÁPIO ENDPOINTS (Removidas rotas duplicadas - mantendo apenas as do início do arquivo)
# ============================================================================

# ============================================================================
# AVALIAÇÕES ENDPOINTS
# ============================================================================

@app.route('/api/avaliacoes/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes(restaurante_id):
    """Lista avaliações de um restaurante - Proxy para API externa"""
    try:
        print(f"[AVALIACOES] Buscando avaliações para restaurante {restaurante_id}")
        # Fazer proxy para API externa: /avaliacoes/{id} (sem /api/)
        status_code, response_data = proxy_request('GET', f'avaliacoes/{restaurante_id}')
        
        # A API Java pode retornar array direto ou objeto com status
        # Se for array direto, manter como está (igual ao site)
        # Se for objeto, retornar como está
        if isinstance(response_data, list):
            # Retornar array direto (formato do site)
            print(f"[AVALIACOES] Retornando array direto com {len(response_data)} avaliações")
            return jsonify(response_data), status_code
        else:
            # Retornar objeto com status
            print(f"[AVALIACOES] Retornando objeto com status: {response_data.get('status', 'unknown')}")
            return jsonify(response_data), status_code
            
    except Exception as e:
        print(f"[ERRO] Erro ao buscar avaliações: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/avaliacoes-prato', methods=['POST'])
def criar_avaliacao_prato():
    """Cria uma avaliação de prato - Proxy para API externa"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        if not data.get('nota') or not data.get('prato'):
            return jsonify({'status': 'error', 'message': 'Campos obrigatórios: nota e prato.id'}), 400
        
        print(f"[AVALIACOES-PRATO] Criando avaliação de prato:")
        print(f"   Nota: {data.get('nota')}")
        print(f"   Prato ID: {data.get('prato', {}).get('id')}")
        print(f"   Comentário: {data.get('comentario', '')[:50]}...")
        
        # Fazer proxy para API externa: /avaliacoes-prato (sem /api/)
        status_code, response_data = proxy_request('POST', 'avaliacoes-prato', data=data)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        print(f"[ERRO] Erro ao criar avaliação de prato: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/avaliacoes/pratos/<int:restaurante_id>', methods=['GET'])
def get_avaliacoes_pratos(restaurante_id):
    """
    Lista avaliações específicas de pratos por restaurante - Proxy para API externa
    
    NOTA: A API Java não tem endpoint específico para listar por restaurante.
    Buscamos todas as avaliações (GET /avaliacoes-prato) e filtramos por restaurante_id.
    """
    try:
        print(f"\n{'='*60}")
        print(f"[AVALIACOES-PRATO] Buscando avaliações de pratos para restaurante {restaurante_id}")
        print(f"[AVALIACOES-PRATO] Endpoint Flask: /api/avaliacoes/pratos/{restaurante_id}")
        
        # A API Java só tem GET /avaliacoes-prato (lista todas)
        # Precisamos buscar todas e filtrar por restaurante_id
        status_code, response_data = proxy_request('GET', 'avaliacoes-prato')
        
        print(f"[AVALIACOES-PRATO] Status code recebido: {status_code}")
        print(f"[AVALIACOES-PRATO] Tipo de resposta: {type(response_data)}")
        
        # Tratar erros da API externa
        if status_code >= 400:
            print(f"[AVALIACOES-PRATO] ⚠️ Erro na API externa: {status_code}")
            if isinstance(response_data, dict):
                error_msg = response_data.get('message', response_data.get('error', 'Erro desconhecido'))
                print(f"[AVALIACOES-PRATO] Mensagem de erro: {error_msg}")
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), status_code
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Erro ao buscar avaliações de pratos: Status {status_code}'
                }), status_code
        
        # Extrair lista de avaliações
        avaliacoes_todas = []
        if isinstance(response_data, list):
            avaliacoes_todas = response_data
        elif isinstance(response_data, dict):
            # Pode estar em diferentes estruturas
            avaliacoes_todas = response_data.get('avaliacoes', []) or response_data.get('data', [])
            if not isinstance(avaliacoes_todas, list):
                avaliacoes_todas = []
        
        print(f"[AVALIACOES-PRATO] Total de avaliações recebidas: {len(avaliacoes_todas)}")
        
        # Debug: imprimir estrutura de uma avaliação (se houver)
        if len(avaliacoes_todas) > 0:
            import json
            primeira_avaliacao = avaliacoes_todas[0]
            print(f"[AVALIACOES-PRATO] Estrutura da primeira avaliação: {json.dumps(primeira_avaliacao, indent=2, default=str)[:500]}")
        
        # Filtrar avaliações do restaurante específico
        # A estrutura pode variar: prato.restaurante.id, prato.itemRestaurante.restaurante.id, etc.
        avaliacoes_filtradas = []
        
        # Primeiro, buscar todos os itens do restaurante para ter uma lista de IDs
        # Isso ajuda a filtrar mesmo se a estrutura do JSON não tiver o restaurante_id diretamente
        try:
            status_itens, response_itens = proxy_request('GET', 'itens')
            itens_restaurante_ids = set()
            if status_itens == 200:
                itens_data = response_itens if isinstance(response_itens, list) else (response_itens.get('data', []) if isinstance(response_itens, dict) else [])
                for item in itens_data:
                    if isinstance(item, dict):
                        item_id = item.get('id')
                        item_restaurante_id = None
                        # Tentar diferentes caminhos
                        if item.get('restaurante') and isinstance(item.get('restaurante'), dict):
                            item_restaurante_id = item['restaurante'].get('id')
                        elif item.get('restaurante_id'):
                            item_restaurante_id = item['restaurante_id']
                        
                        if item_restaurante_id and int(item_restaurante_id) == int(restaurante_id) and item_id:
                            itens_restaurante_ids.add(int(item_id))
            
            print(f"[AVALIACOES-PRATO] IDs de itens do restaurante {restaurante_id}: {len(itens_restaurante_ids)} itens")
        except Exception as e:
            print(f"[AVALIACOES-PRATO] ⚠️ Erro ao buscar itens do restaurante: {e}")
            itens_restaurante_ids = set()
        
        # Filtrar avaliações
        for avaliacao in avaliacoes_todas:
            if not isinstance(avaliacao, dict):
                continue
                
            # Tentar diferentes caminhos para encontrar o restaurante_id
            restaurante_id_avaliacao = None
            prato_id = None
            
            # Caminho 1: prato.restaurante.id
            if avaliacao.get('prato') and isinstance(avaliacao.get('prato'), dict):
                prato = avaliacao['prato']
                prato_id = prato.get('id')
                
                # Caminho 1a: prato.restaurante.id
                if prato.get('restaurante') and isinstance(prato.get('restaurante'), dict):
                    restaurante_id_avaliacao = prato['restaurante'].get('id')
                # Caminho 1b: prato.restaurante_id (direto)
                elif prato.get('restaurante_id'):
                    restaurante_id_avaliacao = prato['restaurante_id']
                # Caminho 1c: prato.itemRestaurante.restaurante.id
                elif prato.get('itemRestaurante') and isinstance(prato.get('itemRestaurante'), dict):
                    item_restaurante = prato['itemRestaurante']
                    if item_restaurante.get('restaurante') and isinstance(item_restaurante.get('restaurante'), dict):
                        restaurante_id_avaliacao = item_restaurante['restaurante'].get('id')
                    elif item_restaurante.get('restaurante_id'):
                        restaurante_id_avaliacao = item_restaurante['restaurante_id']
            
            # Verificar se pertence ao restaurante
            pertence_ao_restaurante = False
            
            # Método 1: Verificar restaurante_id diretamente
            if restaurante_id_avaliacao and int(restaurante_id_avaliacao) == int(restaurante_id):
                pertence_ao_restaurante = True
            # Método 2: Verificar se o prato_id está na lista de itens do restaurante
            elif prato_id and int(prato_id) in itens_restaurante_ids:
                pertence_ao_restaurante = True
            
            if pertence_ao_restaurante:
                avaliacoes_filtradas.append(avaliacao)
        
        print(f"[AVALIACOES-PRATO] Avaliações filtradas para restaurante {restaurante_id}: {len(avaliacoes_filtradas)}")
        
        # Calcular resumo
        media_notas = 0
        if len(avaliacoes_filtradas) > 0:
            soma_notas = sum(float(av.get('nota', 0)) for av in avaliacoes_filtradas)
            media_notas = soma_notas / len(avaliacoes_filtradas)
        
        # Retornar formato esperado pelo frontend
        resultado = {
            'status': 'success',
            'data': {
                'avaliacoes': avaliacoes_filtradas,
                'resumo': {
                    'media_notas': round(media_notas, 2),
                    'total_avaliacoes': len(avaliacoes_filtradas)
                }
            }
        }
        
        print(f"[AVALIACOES-PRATO] Retornando {len(avaliacoes_filtradas)} avaliações com média {media_notas:.2f}")
        return jsonify(resultado), 200
            
    except Exception as e:
        print(f"[ERRO] Erro ao carregar avaliacoes de pratos: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# ENDPOINTS DE SISTEMA
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde da API Flask (proxy)"""
    try:
        # Verificar se consegue conectar com a API externa (raiz)
        status_code, _ = proxy_request('GET', '')
        api_externa_status = 'active' if status_code == 200 else 'inactive'
        
        return jsonify({
            'status': 'success',
            'message': 'API Flask (Proxy) está funcionando!',
            'api_externa_status': api_externa_status,
            'api_externa_url': API_EXTERNA_BASE_URL,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restaurantes/perfil', methods=['GET'])
def restaurante_perfil():
    """Busca informações do restaurante logado - Proxy para API externa"""
    try:
        # Fazer proxy para API externa: /restaurantes/perfil ou similar
        # Tentar diferentes endpoints possíveis
        status_code, response_data = proxy_request('GET', 'restaurantes/perfil')
        
        if status_code == 200 and isinstance(response_data, dict):
            # Garantir formato esperado pelo frontend
            if 'data' not in response_data:
                response_data['data'] = {}
            
            # Tentar extrair restaurante_id e restaurante_nome de diferentes formatos
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
            
            # Atualizar response_data com dados formatados
            if restaurante_id:
                response_data['data']['restaurante_id'] = restaurante_id
            if restaurante_nome:
                response_data['data']['restaurante_nome'] = restaurante_nome
            
            return jsonify(response_data), status_code
        else:
            return jsonify({
                'status': 'error',
                'message': 'Não foi possível obter informações do restaurante'
            }), status_code
            
    except Exception as e:
        print(f"[ERRO] Erro ao buscar perfil: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restaurantes/<int:restaurante_id>', methods=['GET'])
def get_restaurante_detalhes(restaurante_id):
    """
    Busca detalhes completos de um restaurante (incluindo avaliações) - Proxy
    """
    try:
        print(f"[PROXY] Buscando detalhes completos (com avaliações) para ID: {restaurante_id}")
        
        # Fazer proxy para API externa: /restaurantes/{id}
        # O mapeamento já remove o /api/ automaticamente
        status_code, response_data = proxy_request('GET', f'restaurantes/{restaurante_id}')
        
        # response_data será o JSON completo (perfil + avaliações)
        return jsonify(response_data), status_code
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar detalhes do restaurante: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restaurantes/login', methods=['POST'])
def restaurante_login():
    """Login de restaurante - Proxy para API externa (/restaurantes/login)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'status': 'error', 'message': 'Email e senha são obrigatórios'}), 400
        
        # Fazer proxy para API externa: /restaurantes/login (sem /api/)
        status_code, response_data = proxy_request('POST', 'restaurantes/login', data=data)
        
        # Tratar erro de parsing de URL
        if status_code == 502 and isinstance(response_data, dict) and response_data.get('diagnostico', {}).get('tipo_erro') == 'url_parse_error':
            return jsonify({
                'status': 'error',
                'message': 'URL inválida no config.env. Remova comentários inline da linha API_EXTERNA_URL.',
                'diagnostico': response_data.get('diagnostico', {})
            }), 502
        
        # Tratar erro de timeout
        if status_code == 504:
            error_msg = f'Servidor não respondeu em {API_TIMEOUT} segundos. Verifique se o servidor está rodando em {API_EXTERNA_HOST}:{API_EXTERNA_PORT}'
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 504
        
        # Tratar erro de conexão
        if status_code == 503:
            error_msg = f'Não foi possível conectar ao servidor em {API_EXTERNA_HOST}:{API_EXTERNA_PORT}. Verifique se o servidor está rodando.'
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 503
        
        # Tratar erros 401/403 especificamente para login
        if status_code in [401, 403]:
            # Mensagem melhorada para erro 401/403
            if isinstance(response_data, dict) and response_data.get('message'):
                error_msg = response_data['message']
            else:
                if API_EXTERNA_HOST == 'localhost' or API_EXTERNA_HOST == '127.0.0.1':
                    error_msg = 'Erro de autenticação. Verifique suas credenciais ou se o formato da requisição está correto.'
                else:
                    error_msg = 'Acesso negado. Verifique suas credenciais ou se o servidor está acessível.'
            
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), status_code
        
        # Se login foi bem-sucedido, garantir que cookie foi salvo
        if status_code == 200 and response_data.get('status') == 'success':
            # Garantir que 'data' existe
            if 'data' not in response_data:
                response_data['data'] = {}
            
            # Obter restaurante_id da resposta para associar ao cookie
            restaurante_id = response_data.get('data', {}).get('restaurante_id')
            
            # Verificar se cookie foi salvo na sessão
            if len(api_session.cookies) > 0:
                cookie_names = list(api_session.cookies.keys())
                print(f"[LOGIN] Cookie(s) na sessao: {', '.join(cookie_names)}")
                
                if restaurante_id:
                    # Extrair cookie JSESSIONID se existir
                    jsessionid = api_session.cookies.get('JSESSIONID')
                    if jsessionid:
                        cookie_string = f"JSESSIONID={jsessionid}"
                        set_session_cookie(cookie_string, restaurante_id)
                        print(f"[LOGIN] Login bem-sucedido - Cookie JSESSIONID associado ao restaurante_id {restaurante_id}")
                    else:
                        # Tentar obter qualquer cookie
                        for cookie_name in cookie_names:
                            cookie_val = api_session.cookies.get(cookie_name)
                            if cookie_val:
                                cookie_string = f"{cookie_name}={cookie_val}"
                                set_session_cookie(cookie_string, restaurante_id)
                                print(f"[LOGIN] Login bem-sucedido - Cookie {cookie_name} associado ao restaurante_id {restaurante_id}")
                                break
                else:
                    print(f"[AVISO] Login bem-sucedido mas restaurante_id nao encontrado na resposta")
                    print(f"[AVISO] Cookie salvo mas sem associacao ao restaurante_id")
            else:
                print(f"[AVISO] Login bem-sucedido mas nenhum cookie foi recebido da API externa")
        
        return jsonify(response_data), status_code
            
    except Exception as e:
        print(f"[ERRO] Erro no login: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# VERIFICAÇÃO DE CONECTIVIDADE DA API EXTERNA
# ============================================================================

def verificar_conectividade_api():
    """
    Verifica se consegue conectar com a API externa.
    Executa diagnóstico completo: URL, protocolo, porta, host.
    
    Returns:
        bool: True se conectou, False caso contrário
    """
    print(f"\n{'='*70}")
    print(f"[CHECKLIST] CONECTIVIDADE - API EXTERNA")
    print(f"{'='*70}")
    print(f"[URL] Base: {API_EXTERNA_BASE_URL}")
    print(f"[PROTOCOLO] {API_EXTERNA_PROTOCOL.upper()}")
    print(f"[HOST/IP] {API_EXTERNA_HOST}")
    print(f"[PORTA] {API_EXTERNA_PORT}")
    print(f"[TIMEOUT] {API_TIMEOUT}s")
    print(f"{'='*70}\n")
    
    # Teste 1: Health check básico (raiz)
    print(f"[TESTE] Conectividade basica (raiz)...")
    try:
        health_url = f"{API_EXTERNA_BASE_URL}"  # Raiz do servidor
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print(f"[SUCESSO] API Externa acessivel!")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text[:100]}...")
            print(f"\n{'='*70}")
            print(f"[OK] DIAGNOSTICO: API Externa operacional")
            print(f"{'='*70}\n")
            return True
        else:
            print(f"[AVISO] API respondeu mas com status {response.status_code}")
            print(f"   Resposta: {response.text[:100]}...")
    except requests.exceptions.Timeout:
        print(f"[ERRO] TIMEOUT: Servidor nao respondeu em 5 segundos")
    except requests.exceptions.ConnectionError as e:
        print(f"[ERRO] FALHA DE CONEXAO: Nao foi possivel conectar")
        print(f"   Erro: {str(e)[:100]}")
    except Exception as e:
        print(f"[ERRO] {type(e).__name__}: {str(e)}")
    
    # Teste 2: Tentar ping do host (via conexão TCP simples)
    print(f"\n[TESTE] Conectividade do host {API_EXTERNA_HOST}...")
    try:
        import socket
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((API_EXTERNA_HOST, API_EXTERNA_PORT))
        sock.close()
        
        if result == 0:
            print(f"[OK] Porta {API_EXTERNA_PORT} esta ABERTA e acessivel")
        else:
            print(f"[ERRO] Porta {API_EXTERNA_PORT} esta FECHADA ou bloqueada")
    except Exception as e:
        print(f"[AVISO] Nao foi possivel testar porta: {str(e)}")
    
    # Resumo final
    print(f"\n{'='*70}")
    print(f"[AVISO] API Externa nao esta acessivel no momento")
    print(f"{'='*70}")
    print(f"[INFO] O Flask continuara rodando, mas requisicoes podem falhar")
    print(f"[INFO] Verifique:")
    print(f"   1. Se o servidor está rodando")
    print(f"   2. Se IP e porta estão corretos: {API_EXTERNA_HOST}:{API_EXTERNA_PORT}")
    print(f"   3. Se firewall permite conexões")
    print(f"   4. Se servidor aceita conexões externas")
    print(f"   5. Teste manual: curl {API_EXTERNA_BASE_URL}")
    print(f"{'='*70}\n")
    
    return False

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == '__main__':
    print(f"\n{'='*70}")
    print(f"[INICIO] FLASK PROXY REST")
    print(f"{'='*70}")
    print(f"[DATA] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Verificar conectividade antes de iniciar
    api_online = verificar_conectividade_api()
    
    if api_online:
        print(f"[OK] Flask iniciando com API Externa conectada")
    else:
        print(f"[AVISO] Flask iniciando APESAR da API Externa estar offline")
        print(f"   Requisicoes podem falhar ate que a API esteja disponivel\n")
    
    # Iniciar servidor Flask
    print(f"[SERVIDOR] Iniciando servidor Flask...")
    print(f"   Host: 0.0.0.0")
    print(f"   Porta: 5000")
    print(f"   Debug: False")
    print(f"   URL Local: http://localhost:5000")
    print(f"   URL Externa: http://0.0.0.0:5000")
    print(f"\n{'='*70}\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)