# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

base_dir = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(base_dir, 'static'), 'static'),
    (os.path.join(base_dir, 'zoom.pdf'), '.'),
]

# Include optional credentials/token/icon if present
if os.path.exists(os.path.join(base_dir, 'app_icon.ico')):
    datas.append((os.path.join(base_dir, 'app_icon.ico'), '.'))
if os.path.exists(os.path.join(base_dir, 'credentials.json')):
    datas.append((os.path.join(base_dir, 'credentials.json'), '.'))
if os.path.exists(os.path.join(base_dir, 'token.json')):
    datas.append((os.path.join(base_dir, 'token.json'), '.'))

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'websockets',
    'pydantic',
    'requests',
    'python-multipart',
    'pypdf',
    'docx',
    'speech_recognition',
    'soundcard',
    'av',
    'numpy',
    'langchain',
    'langchain_community',
    'langchain_chroma',
    'langchain_ollama',
    'chromadb',
    'jwt',
    'passlib',
    'passlib.handlers.bcrypt',
    'bcrypt',
    'googleapiclient',
    'google.oauth2',
    'google_auth_oauthlib',
    'sqlite3',
    'models_db',
    'auth_service',
    'gdrive_service',
    'doc_processor',
    'stt_engine',
    'rag_engine',
    'server'
]

a = Analysis(
    ['launcher_prod.py'],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'notebook', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SalesCoPilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, 'app_icon.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SalesCoPilot',
)
