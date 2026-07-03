# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define files to collect
added_files = [
    ('frontend/dist', 'frontend/dist'),
    ('backend/adjectives.txt', 'backend'),
    ('backend/nouns.txt', 'backend')
]

a = Analysis(
    ['pyinstaller_entry.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pyvisa',
        'pyvisa_py',
        'uvicorn',
        'fastapi',
        'websockets',
        'cryptography',
        'numpy',
        'pydantic',
        'backend.main',
        'backend.routers.execution',
        'backend.routers.settings',
        'backend.routers.diagnostics',
        'backend.routers.workspace',
        'backend.routers.packages',
        'comfylab.nodes.base',
        'comfylab.nodes.loader',
        'comfylab.nodes.macro'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'comfylab.nodes.standard',
        'comfylab.nodes.visa',
        'comfylab.nodes.publisher',
        'comfylab.nodes.examples',
        'comfylab.nodes.external_library',
        'comfylab.nodes.script',
        'comfylab.nodes.script_external_python',
        'comfylab.nodes.script_lua',
        'comfylab.nodes.script_julia',
        'comfylab.nodes.script_js',
        'comfylab.nodes.script_rust',
        'comfylab.nodes.script_r',
        'comfylab.nodes.script_octave',
        'comfylab.nodes.script_wolfram',
        'tests',
        'frontend/node_modules'
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
    name='ComfyLAB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
