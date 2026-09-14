"""Carga de configuración desde variables de entorno (.env)."""
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass  # python-dotenv no instalado; usa variables de entorno del sistema


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.environ.get(key, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Variable de entorno requerida no definida: {key}")
    return value or ""


def get_env_int(key: str, default: int = 0) -> int:
    try:
        return int(get_env(key, str(default)))
    except ValueError:
        return default


def get_env_list(key: str, default: list = None) -> list:
    raw = get_env(key, "")
    if not raw:
        return default or []
    return [x.strip() for x in raw.split(",") if x.strip()]


# ============================================================
# CONFIGURACIÓN CENTRALIZADA
# ============================================================

# Bot Telegram
BOT_TOKEN: str = get_env("BOT_TOKEN", required=False)
PASSWORD_AUTORIZACION: str = get_env("PASSWORD_AUTORIZACION", "mobiladmin2026")
ADMIN_USER_IDS: list[int] = [int(x) for x in get_env_list("ADMIN_USER_IDS") if x.isdigit()]
MASTER_SECRET: bytes = get_env("MASTER_SECRET", "KIOSKO_POS_PROTECTED_MASTER_SECRET_2026_V1").encode("utf-8")
LICENSE_SERVER_URL: str = get_env("LICENSE_SERVER_URL", "https://mobildesk-keybot.onrender.com").rstrip("/")

# Supabase Sync
SUPABASE_URL: str = get_env("SUPABASE_URL", "https://atxeuhqhariymdqsbmpd.supabase.co").rstrip("/")
SUPABASE_KEY: str = get_env("SUPABASE_KEY", "sb_publishable_6a_o_Jv_XhqZE9TP7mO2EA_gOeak-mL")

# GitHub Updater
GITHUB_REPO: str = get_env("GITHUB_REPO", "USmind/mobildesk-releases")
VERSION_JSON_URL: str = get_env("VERSION_JSON_URL", f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json")
GITHUB_API_URL: str = get_env("GITHUB_API_URL", f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")

# Database
DB_PATH: Optional[str] = get_env("MOBILDESK_DB_PATH") or None