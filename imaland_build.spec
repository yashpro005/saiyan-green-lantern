"""
PyInstaller configuration for building Imaland Multiplayer standalone executable
Usage: pyinstaller imaland_build.spec
"""

import os
from pathlib import Path

block_cipher = None

# Get the directory of this file
spec_dir = Path(__file__).parent

a = Analysis(
    ['imaland_multiplayer.py'],
    pathex=[str(spec_dir)],
    binaries=[],
    datas=[
        # Include all game assets and data files
        ('imaland_game_fixed.py', '.'),
        ('imaland_game_with_cloud_sync.py', '.'),
        ('jump_pad.py', '.'),
        ('terabox_sync.py', '.'),
        ('multiplayer_session.py', '.'),
        ('multiplayer_terabox_sync.py', '.'),
    ],
    hiddenimports=[
        'ursina',
        'panda3d',
        'panda3d.core',
        'panda3d.bullet',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImalandMultiplayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='imaland_icon.ico',  # Add your icon here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImalandMultiplayer',
)
