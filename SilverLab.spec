# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
import os

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = [
    'cv2',
    'numpy',
    'pydantic',
    'yaml',
    'PySide6'
]
hidden_imports += collect_submodules('src.core.isp.nodes')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # Package presets and assets so the standalone app can find them
    datas=[
        ('presets', 'presets'),
        ('src/assets', 'src/assets')
    ],
    hiddenimports=hidden_imports,
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

if sys.platform == 'darwin':
    icon_path = 'src/assets/icon.icns'
elif sys.platform == 'win32':
    icon_path = 'src/assets/icon.ico'
else:
    icon_path = 'src/assets/icon.png'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SilverLab',
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
    icon=icon_path,
)

if sys.platform.startswith('linux'):
    exclude_libs = ('libstdc++.so', 'libgcc_s.so', 'libc.so', 'libm.so', 'libsystemd.so', 'libglib-2.0.so', 'libselinux.so', 'libmount.so', 'libblkid.so', 'libpcre.so', 'libpcre2.so')
    a.binaries = [x for x in a.binaries if not x[0].startswith(exclude_libs)]

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SilverLab',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SilverLab.app',
        icon=icon_path,
        bundle_identifier='com.silverlab.app',
        info_plist={
            'CFBundleShortVersionString': '0.3.0',
            'CFBundleVersion': '0.3.0',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False'
        }
    )
