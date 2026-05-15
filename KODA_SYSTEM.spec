from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_root = Path(SPECPATH)


def gather_datas():
    datas = []

    for folder_name in ("imagens", "dados_empresa"):
        folder_path = project_root / folder_name
        if not folder_path.exists():
            continue
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                target_dir = str(file_path.parent.relative_to(project_root))
                datas.append((str(file_path), target_dir))

    for asset_name in ("KODA_SYSTEM.ico", "KODA_SYSTEM.png", "KODA_SYSTEM_wordmark.png"):
        file_path = project_root / asset_name
        if file_path.exists():
            datas.append((str(file_path), "."))

    seed_db = project_root / "frutaria_base.db"
    if seed_db.exists():
        datas.append((str(seed_db), "."))

    template_csv = project_root / "template_importacao_produtos.csv"
    if template_csv.exists():
        datas.append((str(template_csv), "."))

    return datas


hiddenimports = [
    "win32print",
    "win32api",
    "win32ui",
    "pywintypes",
    "pythoncom",
    "PIL._tkinter_finder",
] + collect_submodules("serial") + collect_submodules("reportlab")

datas = gather_datas() + collect_data_files("reportlab")


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="KODA_SYSTEM",
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
    icon=str(project_root / "KODA_SYSTEM.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KODA_SYSTEM",
)
