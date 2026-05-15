import shutil
import sys
from pathlib import Path

from branding import ASSET_BASENAME


def get_resource_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def get_runtime_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_base_path() -> Path:
    return get_resource_base_path()


def resource_path(relative_path: str) -> str:
    return str(get_resource_base_path() / relative_path)


def runtime_path(relative_path: str) -> str:
    return str(get_runtime_base_path() / relative_path)


def ensure_runtime_dir(relative_path: str) -> str:
    target_dir = get_runtime_base_path() / relative_path
    target_dir.mkdir(parents=True, exist_ok=True)
    return str(target_dir)


def get_database_path() -> str:
    runtime_db = get_runtime_base_path() / "frutaria.db"
    if getattr(sys, "frozen", False):
        bundled_seed_db = get_resource_base_path() / "frutaria_base.db"
        bundled_legacy_db = get_resource_base_path() / "frutaria.db"
        bundled_db = bundled_seed_db if bundled_seed_db.exists() else bundled_legacy_db
        if not runtime_db.exists() and bundled_db.exists():
            shutil.copy2(bundled_db, runtime_db)
        return str(runtime_db)

    bundled_db = get_resource_base_path() / "frutaria.db"
    if not runtime_db.exists() and bundled_db.exists():
        shutil.copy2(bundled_db, runtime_db)
    return str(runtime_db)


def get_app_icon_path() -> str:
    for icon_name in (
        f"{ASSET_BASENAME}.ico",
        "APP_FRUTAS.ico",
        "APP_FRUTAS_CF.ico",
        "APP_FRUTAS_SF.ico",
    ):
        icon_path = get_resource_base_path() / icon_name
        if icon_path.exists():
            return str(icon_path)
    return resource_path(f"{ASSET_BASENAME}.ico")


def get_app_logo_path() -> str:
    for logo_name in (
        f"{ASSET_BASENAME}.png",
        f"{ASSET_BASENAME}.ico",
        "APP_FRUTAS.png",
        "APP_FRUTAS.ico",
        "APP_FRUTAS_SF.png",
    ):
        logo_path = get_resource_base_path() / logo_name
        if logo_path.exists():
            return str(logo_path)
    return resource_path(f"{ASSET_BASENAME}.ico")


DB_PATH = get_database_path()


def calcular_troco(total_venda: float, valor_pago: float) -> float:
    if valor_pago < total_venda:
        return 0.0
    return round(valor_pago - total_venda, 2)
