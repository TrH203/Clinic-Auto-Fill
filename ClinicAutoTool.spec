# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interface.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('staff_group_1.json', '.'),
        ('staff_group_2.json', '.'),
        ('VERSION', '.'),
        ('ai', 'ai'),  # Include entire ai directory
    ],
    hiddenimports=[
        'pywinauto',
        'pywinauto.application',
        'pywinauto.keyboard',
        'pywinauto.mouse',
        'PIL',
        'PIL.Image',
        'pytesseract',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='ClinicAutoTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
