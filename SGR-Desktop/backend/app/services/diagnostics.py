import socket

import requests

from ..config import (
    API_EXTERNA_BASE_URL,
    API_EXTERNA_HOST,
    API_EXTERNA_PORT,
    API_EXTERNA_PROTOCOL,
    API_TIMEOUT,
)


def verificar_conectividade_api() -> bool:
    """
    Verifica se consegue conectar com a API externa realizando diagnóstico completo.
    """
    print(f"\n{'='*70}")
    print("[CHECKLIST] CONECTIVIDADE - API EXTERNA")
    print(f"{'='*70}")
    print(f"[URL] Base: {API_EXTERNA_BASE_URL}")
    print(f"[PROTOCOLO] {API_EXTERNA_PROTOCOL.upper()}")
    print(f"[HOST/IP] {API_EXTERNA_HOST}")
    print(f"[PORTA] {API_EXTERNA_PORT}")
    print(f"[TIMEOUT] {API_TIMEOUT}s")
    print(f"{'='*70}\n")

    print("[TESTE] Conectividade basica (raiz)...")
    try:
        health_url = f"{API_EXTERNA_BASE_URL}"
        response = requests.get(health_url, timeout=5)

        if response.status_code == 200:
            print("[SUCESSO] API Externa acessivel!")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text[:100]}...")
            print(f"\n{'='*70}")
            print("[OK] DIAGNOSTICO: API Externa operacional")
            print(f"{'='*70}\n")
            return True

        print(f"[AVISO] API respondeu mas com status {response.status_code}")
        print(f"   Resposta: {response.text[:100]}...")
    except requests.exceptions.Timeout:
        print("[ERRO] TIMEOUT: Servidor nao respondeu em 5 segundos")
    except requests.exceptions.ConnectionError as exc:
        print("[ERRO] FALHA DE CONEXAO: Nao foi possivel conectar")
        print(f"   Erro: {str(exc)[:100]}")
    except Exception as exc:
        print(f"[ERRO] {type(exc).__name__}: {str(exc)}")

    print(f"\n[TESTE] Conectividade do host {API_EXTERNA_HOST}...")
    try:
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((API_EXTERNA_HOST, API_EXTERNA_PORT))
        sock.close()

        if result == 0:
            print(f"[OK] Porta {API_EXTERNA_PORT} esta ABERTA e acessivel")
        else:
            print(f"[ERRO] Porta {API_EXTERNA_PORT} esta FECHADA ou bloqueada")
    except Exception as exc:
        print(f"[AVISO] Nao foi possivel testar porta: {str(exc)}")

    print(f"\n{'='*70}")
    print("[AVISO] API Externa nao esta acessivel no momento")
    print(f"{'='*70}")
    print("[INFO] O Flask continuara rodando, mas requisicoes podem falhar")
    print("[INFO] Verifique:")
    print("   1. Se o servidor está rodando")
    print(f"   2. Se IP e porta estão corretos: {API_EXTERNA_HOST}:{API_EXTERNA_PORT}")
    print("   3. Se firewall permite conexões")
    print("   4. Se servidor aceita conexões externas")
    print(f"   5. Teste manual: curl {API_EXTERNA_BASE_URL}")
    print(f"{'='*70}\n")

    return False


__all__ = ['verificar_conectividade_api']

