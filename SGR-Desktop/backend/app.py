#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Flask para SGR-Desktop - Proxy REST
Sistema de Gerenciamento de Restaurantes - Proxy para API externa na nuvem
Arquitetura: Electron -> Flask (localhost:5000) -> API Externa (nuvem:8080) -> PostgreSQL
"""

import io
import sys
from datetime import datetime

from app import app
from app.services.diagnostics import verificar_conectividade_api

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_startup_banner() -> None:
    print(f"\n{'='*70}")
    print("[INICIO] FLASK PROXY REST")
    print(f"{'='*70}")
    print(f"[DATA] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    print_startup_banner()

    api_online = verificar_conectividade_api()

    if api_online:
        print("[OK] Flask iniciando com API Externa conectada")
    else:
        print("[AVISO] Flask iniciando APESAR da API Externa estar offline")
        print("   Requisicoes podem falhar ate que a API esteja disponivel\n")

    print("[SERVIDOR] Iniciando servidor Flask...")
    print("   Host: 0.0.0.0")
    print("   Porta: 5000")
    print("   Debug: False")
    print("   URL Local: http://localhost:5000")
    print("   URL Externa: http://0.0.0.0:5000")
    print(f"\n{'='*70}\n")

    app.run(debug=False, host='0.0.0.0', port=5000)
 