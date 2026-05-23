# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for PDF Search Tool (macOS .app bundle).

Build with: ./scripts/build.sh
"""

from PyInstaller.utils.hooks import collect_all

# PyMuPDF (fitz) ships native libraries that PyInstaller can miss
# without explicit collection.
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all("fitz")

block_cipher = None


a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=fitz_binaries,
    datas=fitz_datas,
    hiddenimports=fitz_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim the bundle: we don't use these standard-library modules
        "tkinter",
        "unittest",
    ],
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
    name="PDF Search Tool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,           # GUI app — no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,        # Builds for whichever arch you're running on
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PDF Search Tool",
)

app = BUNDLE(
    coll,
    name="PDF Search Tool.app",
    icon=None,
    bundle_identifier="com.user.pdfsearchtool",
    info_plist={
        "CFBundleName": "PDF Search Tool",
        "CFBundleDisplayName": "PDF Search Tool",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        # Required so AppleScript / 'open -a Preview' from this app works
        # without prompting on modern macOS.
        "NSAppleEventsUsageDescription":
            "PDF Search Tool uses Apple Events to open matching PDFs "
            "in Preview at the matching page.",
    },
)
