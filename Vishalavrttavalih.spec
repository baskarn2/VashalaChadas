# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

added_files = [
    ('data', 'data'),
    ('templates', 'templates'),
    ('static', 'static'),
]

hidden_imports = [
    'indic_transliteration',
    'indic_transliteration.sanscript',
    'indic_transliteration.detect',
    'indic_transliteration.sanscript.schemes',
    'sanskrit_text',
    'Levenshtein',
    'flask',
    'werkzeug',
    'jinja2',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'webview.platforms.edgehtml',
    'PIL',
    'pytesseract',
]

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'torch'],
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
    name='Vishalavrttavalih',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Vishalavrttavalih',
)
