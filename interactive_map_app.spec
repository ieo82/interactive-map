
import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)
import geopandas
import shapely
import pyproj

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['interactive_map_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data.csv', '.'),
        (os.path.join(os.path.dirname(geopandas.__file__), 'datasets'), 'geopandas/datasets'),
        (os.path.join(os.path.dirname(shapely.__file__), '.libs'), 'shapely/.libs'),
        (os.path.join(os.path.dirname(pyproj.__file__), '.libs'), 'pyproj/.libs'),
    ],
    hiddenimports=[
        'shapely', 'pyproj', 'geopandas', 'branca.colormap.linear'
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
    a.binaries,
    a.datas,
    [],
    name='interactive_map_app',
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
)
