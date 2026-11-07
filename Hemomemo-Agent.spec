# -*- mode: python ; coding: utf-8 -*-
# HEMOMEO-AGENT SPEC - thin-console-EXE (folder ke USI dimagh se chalta hai).
# model/ aur agent/ bundle NAHI hote - runtime par EXE ke APNE folder se
# import hote hain (console_app.py sys.path = EXE-folder) - is tarah agent
# aur desktop-app ka dimagh HAMESHA ek hi files ka hai (deeply-linked):
# app naya training ho, agent foran naya dimagh istemal karega.

a = Analysis(
    ['agent/console_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['model', 'agent', 'tkinter', 'server'],
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
    name='Hemomemo-Agent',
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
    icon=['app/genone.ico'],
)
