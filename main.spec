# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('webapp/templates', 'templates'), ('webapp/static', 'static')],
    hiddenimports=[
        'webview',
        'webview.platforms.qt',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
    ],
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
    [],
    exclude_binaries=True,
    name='uil-dl',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='uil-dl',
)
app = BUNDLE(
    coll,
    name='uil-dl.app',
    icon=None,
    bundle_identifier='dev.acemavrick.uil-dl',
    info_plist={
        'CFBundleName': 'uil-dl',
        'CFBundleDisplayName': 'UIL-DL',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'NSHumanReadableCopyright': 'Copyright (c) 2025 acemavrick. MIT License. https://github.com/acemavrick/uil-dl/blob/main/LICENSE'
    }
)
