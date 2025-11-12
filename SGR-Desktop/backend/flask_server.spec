# -*- mode: python ; coding: utf-8 -*-
# flask_server.spec - Configuração do PyInstaller para empacotar o Flask

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.env', '.'),  # Incluir arquivo de configuração
        ('config.env.example', '.'),  # Incluir exemplo (opcional)
    ],
    hiddenimports=[
        'app',
        'app.config',
        'app.proxy',
        'app.routes.analytics',
        'app.routes.avaliacoes',
        'app.routes.cardapio',
        'app.routes.pedidos',
        'app.routes.system',
        'app.services.diagnostics',
        'app.utils.status',
        'flask',
        'flask_cors',
        'requests',
        'beautifulsoup4',
        'bs4',
        'lxml',
        'dotenv',
        'certifi',
        'urllib3',
        'charset_normalizer',
        'idna',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'blinker',
        'python-dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'pytest',
        'pytest-mock',
        'pytest-cov',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='flask_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Mostrar console para logs do Flask
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Adicione um ícone .ico se quiser
)