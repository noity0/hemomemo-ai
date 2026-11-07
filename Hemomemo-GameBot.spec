# -*- mode: python ; coding: utf-8 -*-
# HEMOMEO GAME-BOT SPEC - thin-console-EXE (folder ke USI dimagh se chalta hai).
# model/ aur agent/ bundle NAHI hote - runtime par EXE ke APNE folder se
# import hote hain (console_app.py sys.path = EXE-folder) - is tarah bot
# aur desktop-app ka dimagh HAMESHA ek hi files ka hai (deeply-linked):
# app naya training ho, bot foran naya dimagh istemal karega.
#
# AANKH/HAATH (PC-DIRECT/PC-WATCH): numpy + PIL YAHIN bundle hote hain
# (hiddenimports) - warna frozen-EXE mein `from PIL import ImageGrab` /
# `import numpy` fail hota hai ("aankh nahi khuli" bug - fixed).

a = Analysis(
    ['agent/console_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=['numpy', 'numpy.core', 'PIL', 'PIL.Image',
                   'PIL.ImageGrab', 'PIL.ImageOps'],
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
    name='Hemomemo-GameBot',
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
