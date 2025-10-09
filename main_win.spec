# -*- mode: python ; coding: utf-8 -*-

import os
from tesserocr import get_tesseract_version  # 用于验证

block_cipher = None

# 获取 tesserocr 自动收集的数据（包含 tessdata）
from PyInstaller.utils.hooks import collect_data_files
tesserocr_datas = collect_data_files('tesserocr')

# 手动确保包含中文语言包（如果自动收集没包含）
# 通常 collect_data_files 会包含，但保险起见可检查
# 如果你知道 chi_sim.traineddata 路径，也可手动添加：
# tesserocr_datas.append(('C:/path/to/chi_sim.traineddata', 'tessdata'))

a = Analysis(
    ['lwx_project\\main_prod.py'],
    pathex=["."],
    datas=[
        ('.\\lwx_project\\client\\ui', '.\\ui'),
    ] + tesserocr_datas,  # 👈 关键：加入 tesserocr 的数据
    binaries=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='李文萱的工作空间_v1.1.4',
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
    icon='.\\static\\app.ico'
)
