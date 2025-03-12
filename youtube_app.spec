# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['youtube_downloader_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6', 'yt_dlp', 'ytsummarator', 'youtube_transcript_api'],
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YouTube Extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YouTube Extractor',
)

app = BUNDLE(
    coll,
    name='YouTube Extractor.app',
    icon='app_icon.icns',
    bundle_identifier='com.youtube.extractor',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'YouTube Extractor',
                'CFBundleTypeRole': 'Viewer',
                'LSHandlerRank': 'Owner'
            }
        ]
    },
) 