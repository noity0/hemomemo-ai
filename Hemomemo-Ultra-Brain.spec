# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app/genone_app.py'],
    pathex=[],
    binaries=[],
    datas=[('security/policy.hmhz', 'security'),
           ('security/api_policy.hmhz', 'security'),
           ('security/hmhz.py', 'security'),
           ('security/guard.py', 'security')],
    hiddenimports=['numpy', 'server', 'server.genone_server', 'server.accounts'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Hemomemo-Ultra-Brain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/genone.ico'],
)
