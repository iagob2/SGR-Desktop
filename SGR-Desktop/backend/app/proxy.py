import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

from .config import (
    API_EXTERNA_BASE_URL,
    API_EXTERNA_HOST,
    API_EXTERNA_PORT,
    API_EXTERNA_PROTOCOL,
    API_TIMEOUT,
)

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("AVISO: beautifulsoup4 nao instalado. Execute: pip install beautifulsoup4")

api_session = requests.Session()
session_cookies_store: Dict[Any, str] = {}


def get_session_cookie(restaurante_id: Optional[int] = None) -> Optional[str]:
    """Obtém cookie de sessão do restaurante."""
    if restaurante_id:
        return session_cookies_store.get(restaurante_id)
    return session_cookies_store.get('latest') if session_cookies_store else None


def set_session_cookie(cookie_value: str, restaurante_id: Optional[int] = None) -> None:
    """Armazena cookie de sessão, removendo duplicatas."""
    if cookie_value and '=' in cookie_value:
        cookie_name, cookie_val = cookie_value.split('=', 1)
        try:
            cookies_to_keep = {
                name: value for name, value in api_session.cookies.items() if name != cookie_name
            }
            api_session.cookies.clear()
            for name, value in cookies_to_keep.items():
                api_session.cookies.set(name, value)
        except Exception as exc:  # pragma: no cover - logs
            print(f"[SESSION] Erro ao limpar cookies: {exc}")
        api_session.cookies.set(cookie_name, cookie_val)
        if restaurante_id:
            session_cookies_store[restaurante_id] = cookie_value
        session_cookies_store['latest'] = cookie_value


def clear_session_cookie(restaurante_id: Optional[int] = None) -> None:
    """Limpa cookie de sessão."""
    if restaurante_id:
        session_cookies_store.pop(restaurante_id, None)
    else:
        session_cookies_store.clear()
        api_session.cookies.clear()


def parse_html_response(html_content: str, endpoint: str = '') -> Dict[str, Any]:
    """
    Parseia resposta HTML da API externa e converte para JSON estruturado.
    Especializado para extrair dados de login e listagem de itens.
    """
    try:
        if not BS4_AVAILABLE:
            return {
                'status': 'success',
                'message': 'Resposta HTML recebida (beautifulsoup4 nao instalado)',
                'raw_html': html_content[:500],
            }

        soup = BeautifulSoup(html_content, 'html.parser')

        if 'restaurantes/login' in endpoint or 'restaurante.html' in html_content.lower():
            success_pattern = re.compile(
                r'Login bem-sucedido.*?Bem-vindo\(a\),\s*(.+?)\.', re.IGNORECASE
            )
            match = success_pattern.search(html_content)
            restaurante_nome = None

            if match:
                restaurante_nome = match.group(1).strip()
                print(f"[PARSE] Nome do restaurante extraido: {restaurante_nome}")

            scripts = soup.find_all('script')
            restaurante_id = None

            for script in scripts:
                if script.string:
                    id_match = re.search(
                        r'restaurante[_\s]*id\s*[=:]\s*(\d+)', script.string, re.IGNORECASE
                    )
                    if id_match:
                        restaurante_id = int(id_match.group(1))
                        print(f"[PARSE] restaurante_id encontrado em script: {restaurante_id}")
                        break

                    json_match = re.search(
                        r'\{[^}]*restaurante[_\s]*id[^}]*\}', script.string, re.IGNORECASE | re.DOTALL
                    )
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group().replace("'", '"'))
                            if 'restaurante_id' in json_data:
                                restaurante_id = json_data['restaurante_id']
                                print(f"[PARSE] restaurante_id do JSON: {restaurante_id}")
                                break
                        except Exception:
                            pass

            if not restaurante_id:
                hidden_inputs = soup.find_all('input', {'type': 'hidden'})
                for inp in hidden_inputs:
                    if 'restaurante' in inp.get('name', '').lower() and 'id' in inp.get(
                        'name', ''
                    ).lower():
                        try:
                            restaurante_id = int(inp.get('value', 0))
                            print(f"[PARSE] restaurante_id em input hidden: {restaurante_id}")
                            break
                        except Exception:
                            pass

            if not restaurante_id:
                elements = soup.find_all(attrs={'data-restaurante-id': True})
                if elements:
                    try:
                        restaurante_id = int(elements[0].get('data-restaurante-id'))
                        print(f"[PARSE] restaurante_id em data-attribute: {restaurante_id}")
                    except Exception:
                        pass

            if not restaurante_id:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    id_match = re.search(r'[?&](?:id|restaurante_id)=(\d+)', href, re.IGNORECASE)
                    if id_match:
                        restaurante_id = int(id_match.group(1))
                        print(f"[PARSE] restaurante_id em URL: {restaurante_id}")
                        break

            result: Dict[str, Any] = {
                'status': 'success',
                'message': 'Login realizado com sucesso',
                'data': {},
            }

            if restaurante_id:
                result['data']['restaurante_id'] = restaurante_id
                print(f"[PARSE] restaurante_id incluído na resposta: {restaurante_id}")
            else:
                print("[AVISO] restaurante_id nao encontrado no HTML, mas login teve sucesso")

            if match and restaurante_nome:
                result['data']['restaurante_nome'] = restaurante_nome
                print(f"[PARSE] restaurante_nome incluído na resposta: {restaurante_nome}")

            if not restaurante_id and match:
                print("[INFO] Login bem-sucedido mas restaurante_id não encontrado")
                print("[INFO] Frontend pode tentar buscar ID via endpoint /restaurantes/perfil")

            return result

        if (
            'itens' in endpoint.lower()
            or 'cardapio' in endpoint.lower()
            or 'tabelaItens' in html_content
        ):
            print("[PARSE] Tentando parsear lista de itens do HTML...")
            items = []

            tabela = soup.find('table', id='tabelaItens')
            if not tabela:
                tabela = soup.find('table')

            if tabela:
                rows = tabela.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        try:
                            item: Dict[str, Any] = {}
                            if len(cells) > 0:
                                texto = cells[0].get_text(strip=True)
                                item['id'] = int(texto) if texto.isdigit() else None
                            if len(cells) > 1:
                                item['nome'] = cells[1].get_text(strip=True)
                            if len(cells) > 2:
                                preco_text = (
                                    cells[2].get_text(strip=True).replace('R$', '').replace(',', '.').strip()
                                )
                                try:
                                    item['preco'] = float(preco_text)
                                except Exception:
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

                            if item.get('nome') and item.get('id'):
                                items.append(item)
                        except Exception as exc:
                            print(f"[PARSE] Erro ao parsear linha da tabela: {exc}")
                            continue

                if items:
                    print(f"[PARSE] Parseou {len(items)} itens da tabela HTML")
                    return items

        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if isinstance(parsed, dict) and 'status' in parsed:
                            return parsed
                    except Exception:
                        pass

        data: Dict[str, Any] = {}
        elements_with_data = soup.find_all(
            attrs=lambda attrs: attrs and any(k.startswith('data-') for k in attrs.keys())
        )
        for elem in elements_with_data:
            for key, value in elem.attrs.items():
                if key.startswith('data-'):
                    data_key = key.replace('data-', '').replace('-', '_')
                    data[data_key] = value

        main_content = soup.find('main') or soup.find('body') or soup
        text_content = main_content.get_text(strip=True) if main_content else ''

        if any(palavra in text_content.lower() for palavra in ['erro', 'error', 'falha', 'inválido', 'incorreto']):
            return {
                'status': 'error',
                'message': 'Erro no login. Verifique suas credenciais.',
            }

        if data:
            return {
                'status': 'success',
                'data': data,
                'html_content': text_content[:500],
            }

        return {
            'status': 'success',
            'message': 'Resposta HTML recebida',
            'content': text_content[:1000],
            'note': 'API retornou HTML. Dados podem precisar de parsing adicional.',
        }

    except Exception as exc:
        print(f"[AVISO] Erro ao parsear HTML: {exc}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return {
            'status': 'success',
            'message': 'Resposta HTML recebida (não parseado)',
            'raw_html': html_content[:500],
        }


def mapear_endpoint_flask_para_api(flask_endpoint: str) -> str:
    """Mapeia endpoints do Flask para endpoints da API externa."""
    endpoint = flask_endpoint.replace('/api/', '/').lstrip('/')

    if endpoint.startswith('cardapio/'):
        if endpoint.startswith('cardapio/add'):
            return 'itens'
        if endpoint.startswith('cardapio/edit/'):
            item_id = endpoint.replace('cardapio/edit/', '')
            return f'itens/{item_id}'
        if re.match(r'cardapio/\d+$', endpoint):
            return 'itens'

    return endpoint


def proxy_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    """
    Função helper aprimorada para fazer proxy de requisições para a API externa.
    Inclui logs detalhados e diagnóstico completo de erros de rede.
    """
    endpoint_api = endpoint
    url = f'{API_EXTERNA_BASE_URL}{endpoint.lstrip("/")}'

    try:
        endpoint_api = mapear_endpoint_flask_para_api(endpoint)
        endpoint_api = endpoint_api.lstrip('/') if endpoint_api.startswith('/') else endpoint_api
        url = f'{API_EXTERNA_BASE_URL}{endpoint_api}'

        headers: Dict[str, str] = {
            'Accept': 'text/html,application/json,application/xhtml+xml,text/plain,*/*',
            'User-Agent': 'SGR-Desktop-Flask-Proxy/1.0',
            'Origin': 'http://localhost:5000',
        }

        if data and method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'
        elif method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        jsessionid_count = sum(1 for name in api_session.cookies.keys() if name == 'JSESSIONID')
        if jsessionid_count > 1:
            print(f"   [COOKIE] AVISO: Encontrados {jsessionid_count} cookies JSESSIONID - limpando duplicatas...")
            jsessionid_val = api_session.cookies.get('JSESSIONID')
            cookies_backup = {name: value for name, value in api_session.cookies.items() if name != 'JSESSIONID'}
            api_session.cookies.clear()
            for name, value in cookies_backup.items():
                api_session.cookies.set(name, value)
            if jsessionid_val:
                api_session.cookies.set('JSESSIONID', jsessionid_val)
            print("   [COOKIE] Duplicatas removidas - mantido apenas 1 JSESSIONID")
        elif jsessionid_count == 1:
            print("   [COOKIE] JSESSIONID presente na sessao - será enviado automaticamente")

        if len(api_session.cookies) > 0:
            cookie_list = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"   [COOKIE] Sessao tem {len(api_session.cookies)} cookie(s): {', '.join(cookie_list)}")

        try:
            print(f"\n{'='*60}")
            print("[PROXY] PROXY REQUEST")
            print(f"{'='*60}")
            print(f"   Metodo: {method}")
            print(f"   URL Completa: {url}")
            print(f"   Base URL: {API_EXTERNA_BASE_URL}")
            print(f"   Endpoint Flask: {endpoint}")
            print(f"   Endpoint API Externa: {endpoint_api}")
        except UnicodeEncodeError:
            print(f"\n{'='*60}")
            print("[PROXY] PROXY REQUEST")
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
            data_log = data.copy()
            if 'senha' in data_log:
                data_log['senha'] = '***'
            if 'password' in data_log:
                data_log['password'] = '***'
            print(f"   Body Data: {json.dumps(data_log, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}\n")

        response = api_session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
            timeout=API_TIMEOUT,
            allow_redirects=True,
        )

        set_cookie_headers = (
            response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
        )
        if not set_cookie_headers and 'Set-Cookie' in response.headers:
            set_cookie_headers = [response.headers.get('Set-Cookie')]

        if set_cookie_headers:
            jsessionid_value = None

            for cookie_header in set_cookie_headers:
                cookie_value = cookie_header.split(';')[0].strip()

                if cookie_value.startswith('JSESSIONID='):
                    jsessionid_value = cookie_value
                    print(f"   [COOKIE] JSESSIONID recebido: {cookie_value[:50]}...")

            if jsessionid_value:
                cookie_name, cookie_val = jsessionid_value.split('=', 1)

                if 'JSESSIONID' in api_session.cookies:
                    cookies_backup = {}
                    for name, value in api_session.cookies.items():
                        if name != 'JSESSIONID':
                            cookies_backup[name] = value

                    api_session.cookies.clear()

                    for name, value in cookies_backup.items():
                        api_session.cookies.set(name, value)

                    print("   [COOKIE] JSESSIONID antigo removido para evitar duplicata")

                api_session.cookies.set('JSESSIONID', cookie_val)

                restaurante_id = None
                if data and isinstance(data, dict) and 'restaurante_id' in data:
                    restaurante_id = data.get('restaurante_id')

                session_cookies_store['latest'] = jsessionid_value
                if restaurante_id:
                    session_cookies_store[restaurante_id] = jsessionid_value

                print("   [COOKIE] JSESSIONID salvo na sessao e store")

        if len(api_session.cookies) > 0:
            cookie_info = [f"{name}={value[:20]}..." for name, value in list(api_session.cookies.items())[:3]]
            print(f"   [COOKIE] Sessao agora tem {len(api_session.cookies)} cookie(s): {', '.join(cookie_info)}")

        print(f"[RESPOSTA] Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        if response.status_code in [401, 403]:
            status_name = "401 - Não autorizado" if response.status_code == 401 else "403 - Acesso negado"
            print(f"\n[ERRO] Status {response.status_code} - {status_name}")
            print(f"{'='*60}")
            print(f"   URL testada: {url}")
            print(f"   Host: {API_EXTERNA_HOST}")
            print(f"   Porta: {API_EXTERNA_PORT}")
            print(f"\n[DIAGNOSTICO] Possiveis causas:")

            if API_EXTERNA_HOST == 'localhost' or API_EXTERNA_HOST == '127.0.0.1':
                print("   ⚠️  ATENÇÃO: Tentando conectar em localhost:8080")
                print("   1. Formato de dados pode estar incorreto (tentando JSON, pode precisar form-urlencoded)")
                print("   2. Endpoint pode estar incorreto")
                print("   3. Credenciais podem estar incorretas")
                print("\n   💡 SOLUCAO:")
                print("   - Tentando automaticamente como form-urlencoded...")
            else:
                print("   1. Formato de dados incorreto (JSON vs Form-urlencoded)")
                print("   2. Endpoint requer autenticacao")
                print("   3. CORS bloqueando requisicao")
                print("   4. Headers incorretos ou faltando")
                print("   5. Credenciais incorretas")

            print(f"{'='*60}\n")

            if method == 'POST' and data:
                print("[TENTATIVA] Reenviando como form-urlencoded...")
                try:
                    headers_form = headers.copy()
                    headers_form['Content-Type'] = 'application/x-www-form-urlencoded'

                    if isinstance(data, dict):
                        form_data = urlencode(data)
                    else:
                        form_data = data

                    response_retry = api_session.post(
                        url, data=form_data, headers=headers_form, timeout=API_TIMEOUT, allow_redirects=True
                    )

                    if response_retry.status_code not in [401, 403]:
                        print(f"[SUCESSO] Form-urlencoded funcionou! Status: {response_retry.status_code}")
                        response = response_retry
                    else:
                        print(f"[FALHA] Form-urlencoded tambem retornou {response_retry.status_code}")
                except Exception as exc:
                    print(f"[ERRO] Erro ao tentar form-urlencoded: {exc}")

        content_type = response.headers.get('Content-Type', '').lower()

        response_data_json = None
        try:
            response_data_json = response.json()
            print("   Response (JSON detectado): OK")
        except (ValueError, json.JSONDecodeError):
            pass

        if response_data_json is not None:
            response_data = response_data_json

            try:
                if 'restaurantes/login' in endpoint_api and isinstance(response_data, dict):
                    if 'error' in response_data or (response.status_code >= 400):
                        error_msg = response_data.get('error') or response_data.get('message', 'Erro no login')
                        status_final = 401 if response.status_code == 200 else response.status_code
                        response_data = {
                            'status': 'error',
                            'message': error_msg,
                        }
                        print(f"[PARSE] Login JSON erro: {error_msg}")
                        return status_final, response_data

                    if response_data.get('status') == 'success' and 'data' in response_data:
                        if 'restaurante_id' in response_data['data'] or 'restaurante_nome' in response_data['data']:
                            print("[PARSE] Login JSON ja formatado corretamente")
                            return response.status_code, response_data

                    restaurante_id = None
                    restaurante_nome = None

                    if 'nome' in response_data and ('id' in response_data or 'restaurante_id' in response_data):
                        restaurante_id = response_data.get('id') or response_data.get('restaurante_id')
                        restaurante_nome = response_data.get('nome')
                        print(f"[PARSE] Login JSON formato direto: id={restaurante_id}, nome={restaurante_nome}")
                    elif 'restaurante' in response_data:
                        restaurante = response_data.get('restaurante', {})
                        restaurante_id = restaurante.get('id') or restaurante.get('restaurante_id')
                        restaurante_nome = restaurante.get('nome')
                        print(f"[PARSE] Login JSON formato aninhado: id={restaurante_id}, nome={restaurante_nome}")
                    elif 'email' in response_data and 'id' in response_data:
                        restaurante_id = response_data.get('id') or response_data.get('restaurante_id')
                        restaurante_nome = response_data.get('nome') or response_data.get('restaurante_nome')
                        print(f"[PARSE] Login JSON formato com email: id={restaurante_id}, nome={restaurante_nome}")

                    if restaurante_id or restaurante_nome:
                        response_data = {
                            'status': 'success',
                            'message': 'Login realizado com sucesso',
                            'data': {},
                        }
                        if restaurante_id:
                            response_data['data']['restaurante_id'] = restaurante_id
                            print(f"[PARSE] restaurante_id incluído na resposta: {restaurante_id}")
                        if restaurante_nome:
                            response_data['data']['restaurante_nome'] = restaurante_nome
                            print(f"[PARSE] restaurante_nome incluído na resposta: {restaurante_nome}")
                        print("[PARSE] Login JSON convertido para formato desktop")
                    else:
                        print("[AVISO] Formato JSON de login nao reconhecido completamente")
                        print(f"[DEBUG] Chaves recebidas: {list(response_data.keys())}")
                        print(f"[DEBUG] Conteudo: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")

                        if 'erro' in str(response_data).lower() or 'fail' in str(response_data).lower():
                            response_data = {
                                'status': 'error',
                                'message': 'Erro no login. Verifique suas credenciais.',
                            }
                        else:
                            if 'status' not in response_data:
                                response_data = {
                                    'status': 'success' if response.status_code < 400 else 'error',
                                    'message': 'Resposta do servidor recebida',
                                    'raw_data': response_data,
                                }

                return response.status_code, response_data

            except Exception as exc:
                print(f"[AVISO] Erro ao processar JSON: {exc}")
                import traceback

                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
                return response.status_code, response_data_json

        if response_data_json is None:
            if 'text/html' in content_type or (
                response.text
                and (response.text.strip().startswith('<!DOCTYPE') or response.text.strip().startswith('<html'))
            ):
                print("   Response (HTML): Detectado - Convertendo para JSON...")
                response_data = parse_html_response(response.text, endpoint_api)
                print("   Response convertido: OK")
                return response.status_code, response_data

            if response.status_code >= 400:
                error_data: Dict[str, Any] = {
                    'status': 'error',
                    'message': f'Erro HTTP {response.status_code}',
                    'status_code': response.status_code,
                }

                if response.status_code == 403 and (API_EXTERNA_HOST in ['localhost', '127.0.0.1']):
                    error_data['message'] = (
                        'Servidor não encontrado em localhost:8080. Verifique se o servidor está rodando ou use a URL da nuvem no config.env'
                    )
                    error_data['diagnostico'] = {
                        'tipo_erro': 'servidor_nao_encontrado',
                        'url_configurada': API_EXTERNA_BASE_URL,
                        'sugestao': 'Use API_EXTERNA_URL=http://3.90.155.156:8080 no config.env para usar o servidor da nuvem',
                    }

                if response.text:
                    error_data['response_text'] = response.text[:500]
                return response.status_code, error_data

            response_data = {
                'status': 'success' if response.status_code < 400 else 'error',
                'message': response.text[:500] if response.text else 'Resposta vazia',
                'raw_response': response.text[:200] if response.text else '',
            }
            print(f"   Response (Text): {response.text[:100] if response.text else 'vazio'}...")
            return response.status_code, response_data

    except requests.exceptions.Timeout:
        print(f"\n[ERRO] TIMEOUT")
        print(f"{'='*60}")
        print(f"   Timeout configurado: {API_TIMEOUT}s")
        print(f"   Protocolo: {API_EXTERNA_PROTOCOL}")
        print(f"   Host: {API_EXTERNA_HOST}")
        print(f"   Porta: {API_EXTERNA_PORT}")
        print(f"\n[DIAGNOSTICO] Possiveis causas:")
        print("   1. Servidor pode estar sobrecarregado")
        print("   2. Rede lenta ou instável")
        print("   3. Firewall bloqueando conexões")
        print("   4. Servidor não está respondendo a tempo")
        print("   5. IP/Porta podem estar incorretos")
        print(f"\n🔧 SUGESTÕES:")
        print(f"   - Verificar se servidor está rodando: ping {API_EXTERNA_HOST}")
        print(f"   - Testar conectividade: curl {API_EXTERNA_BASE_URL}")
        print(f"   - Aumentar timeout no config.env (atual: {API_TIMEOUT}s)")
        print(f"{'='*60}\n")

        return 504, {
            'status': 'error',
            'message': f'Timeout ({API_TIMEOUT}s) ao conectar com o servidor',
            'diagnostico': {
                'tipo_erro': 'timeout',
                'timeout_configurado': f'{API_TIMEOUT}s',
                'protocolo': API_EXTERNA_PROTOCOL,
                'host': API_EXTERNA_HOST,
                'porta': API_EXTERNA_PORT,
                'sugestoes': [
                    'Verificar se o servidor está rodando',
                    'Testar conectividade de rede',
                    'Verificar configurações de firewall',
                    'Considerar aumentar o timeout',
                ],
            },
        }

    except requests.exceptions.ConnectionError as exc:
        print(f"\n[ERRO] CONEXAO FALHOU")
        print(f"{'='*60}")
        print(f"   Protocolo: {API_EXTERNA_PROTOCOL}")
        print(f"   Host: {API_EXTERNA_HOST}")
        print(f"   Porta: {API_EXTERNA_PORT}")
        print(f"   Erro tecnico: {str(exc)}")
        print(f"\n[DIAGNOSTICO] Possiveis causas:")
        print(f"   1. Servidor não está rodando na porta {API_EXTERNA_PORT}")
        print(f"   2. IP {API_EXTERNA_HOST} está incorreto ou mudou")
        print(f"   3. Firewall bloqueando conexões na porta {API_EXTERNA_PORT}")
        print("   4. Servidor não está configurado para aceitar conexões externas")
        print("   5. Protocolo incorreto (tentando HTTP mas servidor usa HTTPS ou vice-versa)")
        print(f"\n🔧 SUGESTÕES:")
        print(f"   - Verificar se servidor está ativo: ping {API_EXTERNA_HOST}")
        print(f"   - Testar porta: telnet {API_EXTERNA_HOST} {API_EXTERNA_PORT}")
        print(f"   - Testar URL manualmente: curl {API_EXTERNA_BASE_URL}")
        print(f"   - Verificar config.env: API_EXTERNA_URL={API_EXTERNA_BASE_URL}")
        print("   - Confirmar com administrador se API está acessível externamente")
        print(f"{'='*60}\n")

        return 503, {
            'status': 'error',
            'message': 'Servidor não está disponível ou não acessível',
            'diagnostico': {
                'tipo_erro': 'connection_error',
                'protocolo': API_EXTERNA_PROTOCOL,
                'host': API_EXTERNA_HOST,
                'porta': API_EXTERNA_PORT,
                'erro_tecnico': str(exc),
                'sugestoes': [
                    'Verificar se o servidor está rodando',
                    'Confirmar IP e porta estão corretos',
                    'Verificar configurações de firewall',
                    'Testar conectividade de rede',
                    'Confirmar se servidor aceita conexões externas',
                ],
            },
        }

    except requests.exceptions.RequestException as exc:
        error_type = type(exc).__name__
        print(f"\n[ERRO] {error_type}")
        print(f"{'='*60}")
        print(f"   Erro: {str(exc)}")

        if 'Failed to parse' in str(exc) or 'Invalid URL' in str(exc):
            print("\n[DIAGNOSTICO] Erro de parsing da URL")
            print("   URL pode estar malformada")
            print("   Verifique config.env - API_EXTERNA_URL")
            print(f"   URL atual: {API_EXTERNA_BASE_URL}")
            print("\n[SOLUCAO]")
            print("   - Remova comentários inline da URL no config.env")
            print("   - Formato correto: API_EXTERNA_URL=http://127.0.0.1:8080")
            print("   - Não inclua comentários na mesma linha")
        elif 'SSL' in error_type or 'certificate' in str(exc).lower():
            print("\n[INFO] Problema com certificado SSL")
            print("   Servidor pode estar usando HTTPS mas URL está como HTTP")

        print("\n[SUGESTAO]")
        print("   - Verificar se URL deve ser https:// em vez de http://")
        print(f"   - Atualizar config.env: API_EXTERNA_URL=https://{API_EXTERNA_HOST}:{API_EXTERNA_PORT}")
        print(f"{'='*60}\n")

        if 'Failed to parse' in str(exc) or 'Invalid URL' in str(exc):
            error_msg = 'URL inválida no config.env. Remova comentários inline da linha API_EXTERNA_URL.'
            error_type_key = 'url_parse_error'
        elif 'SSL' in error_type or 'certificate' in str(exc).lower():
            error_msg = 'Erro de SSL/TLS - Protocolo pode estar incorreto'
            error_type_key = 'ssl_error'
        else:
            error_msg = f'Erro na requisição: {str(exc)[:100]}'
            error_type_key = 'request_error'

        return 502, {
            'status': 'error',
            'message': error_msg,
            'diagnostico': {
                'tipo_erro': error_type_key,
                'url_testada': url,
                'url_base': API_EXTERNA_BASE_URL,
                'sugestao': 'Verifique config.env e remova comentários inline da URL',
            },
        }

    except Exception as exc:  # pragma: no cover - fallback
        print(f"\n[ERRO] GENERICO")
        print(f"{'='*60}")
        print(f"   Tipo: {type(exc).__name__}")
        print(f"   Mensagem: {str(exc)}")
        print(f"{'='*60}\n")

        return 500, {
            'status': 'error',
            'message': f'Erro inesperado: {str(exc)}',
            'tipo_erro': type(exc).__name__,
        }


__all__ = [
    'api_session',
    'session_cookies_store',
    'proxy_request',
    'parse_html_response',
    'mapear_endpoint_flask_para_api',
    'get_session_cookie',
    'set_session_cookie',
    'clear_session_cookie',
    'BS4_AVAILABLE',
]

