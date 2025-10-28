#!/usr/bin/env python3
"""
Configurações do banco de dados PostgreSQL do sistema Saborê
"""

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sabore',
    'user': 'postgres',
    'password': '157428',
    'port': '5432'
}

# Informações do sistema
SYSTEM_INFO = {
    'name': 'Sistema Saborê',
    'version': '1.0.0',
    'database': 'PostgreSQL',
    'api_port': 8080,
    'status': 'Conectado e funcionando'
}

# Tabelas disponíveis
TABLES = [
    'restaurante',
    'clientes', 
    'pedido',
    'item_pedido',
    'item_restaurante',
    'avaliacao',
    'avaliacao_prato'
]

# CNPJs confirmados no banco (da imagem)
CONFIRMED_CNPJS = [
    '4881526639',
    '11222333000144', 
    '22333444000155',
    '33444555000166',
    '44555666000177',
    '55666777000188'
]
