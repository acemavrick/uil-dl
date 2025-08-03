# -*- mode: python ; coding: utf-8 -*-
import re

version_file = 'assets/version.txt'
with open(version_file, 'r') as f:
    content = f.read()

def get_string_struct_value(key, text):
    match = re.search(r"StringStruct\('" + key + r"', u?'(.*?)'\)", text)
    if match:
        return match.group(1)
    return None

company_name = get_string_struct_value('CompanyName', content)
file_description = get_string_struct_value('FileDescription', content)
product_version = get_string_struct_value('ProductVersion', content)
internal_name = get_string_struct_value('InternalName', content)
legal_copyright = get_string_struct_value('LegalCopyright', content)
product_name = get_string_struct_value('ProductName', content)


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
        'portalocker',
        'platformdirs',
        'flask',
        'flask_socketio',
        'flask_sqlalchemy',
        'sqlalchemy',
        'json',
        'pathlib',
        'threading',
        'socket',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
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
    strip=True,
    upx=True,
    console=False,
    icon='assets/icon.png',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='uil-dl',
)
app = BUNDLE(
    coll,
    name='uil-dl.app',
    icon='assets/icon.png',
    bundle_identifier=f'dev.{company_name.lower()}.{internal_name}',
    info_plist={
        'CFBundleName': product_name,
        'CFBundleDisplayName': file_description,
        'CFBundleVersion': product_version,
        'CFBundleShortVersionString': '.'.join(product_version.split('.')[:2]),
        'CFBundleIdentifier': f'dev.{company_name.lower()}.{internal_name}',
        'NSHumanReadableCopyright': legal_copyright + ' https://github.com/acemavrick/uil-dl/blob/main/LICENSE',
    },
)
