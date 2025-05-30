# -- mode: python ; coding: utf-8 --

import pefile
import psutil
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

dlss_updater_imports = collect_submodules('dlss_updater')
dlss_updater_datas = collect_data_files('dlss_updater')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('dlss_updater', 'dlss_updater'),
        ('release_notes.txt', '.'),
        ('dlss_updater/icons/*.png', 'icons/'),
    ],
    hiddenimports=[
        'pefile', 'psutil', 'importlib.metadata', 'packaging',
        'concurrent.futures', 'pywin32', 'PyQt6'
    ] + dlss_updater_imports,
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DLSS_Updater',
    version='version.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    optimize=2,
    icon='dlss_updater/icons/dlss_updater.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DLSS_Updater',
)