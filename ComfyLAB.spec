# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os

# Define files to collect
added_files = [
    ('frontend/dist', 'frontend/dist'),
    ('backend/adjectives.txt', 'backend'),
    ('backend/nouns.txt', 'backend')
]

if os.path.exists('VERSION'):
    added_files.append(('VERSION', '.'))

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
        'comfylab.blocks.base',
        'comfylab.blocks.loader',
        'comfylab.blocks.cluster'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Block modules are shipped as external source next to the binary
        # (copied by build_exe.py) so they remain extensible at runtime.
        'comfylab.blocks.base_script',
        'comfylab.blocks.basic_math',
        'comfylab.blocks.cluster_boundary',
        'comfylab.blocks.constants',
        'comfylab.blocks.control_flow',
        'comfylab.blocks.dictionary',
        'comfylab.blocks.examples',
        'comfylab.blocks.external_library',
        'comfylab.blocks.io',
        'comfylab.blocks.lists',
        'comfylab.blocks.logic',
        'comfylab.blocks.math_fit',
        'comfylab.blocks.math_functions',
        'comfylab.blocks.ndarrays',
        'comfylab.blocks.outputs_basic',
        'comfylab.blocks.plots',
        'comfylab.blocks.publisher',
        'comfylab.blocks.script',
        'comfylab.blocks.script_external_python',
        'comfylab.blocks.script_js',
        'comfylab.blocks.script_julia',
        'comfylab.blocks.script_lua',
        'comfylab.blocks.script_octave',
        'comfylab.blocks.script_r',
        'comfylab.blocks.script_rust',
        'comfylab.blocks.script_wolfram',
        'comfylab.blocks.signal',
        'comfylab.blocks.strings',
        'comfylab.blocks.timing',
        'comfylab.blocks.utility',
        'comfylab.blocks.visa',
        'comfylab.blocks.instruments.devices',
        'comfylab.blocks.instruments.pfj_osc',
        'comfylab.blocks.instruments.pfj_siggen',
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
