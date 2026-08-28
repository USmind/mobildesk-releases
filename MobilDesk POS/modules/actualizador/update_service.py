import os
import sys
import json
import urllib.request
import subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal

CURRENT_VERSION = "2.0.19"
APP_NAME = "MobilDesk"

# URLs de actualización (GitHub / Servidor)
GITHUB_REPO = "USmind/mobildesk-releases"
VERSION_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

UPDATES_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MobilDesk" / "updates"


def parse_version(v_str):
    """Convierte un string de versión 'v2.0.1' o '2.0.1' a una tupla de enteros (2, 0, 1)"""
    try:
        clean = v_str.strip().lower().lstrip("v")
        parts = [int(p) for p in clean.split(".") if p.isdigit()]
        return tuple(parts)
    except Exception:
        return (0, 0, 0)


def is_newer_version(remote_version_str, current_version_str=CURRENT_VERSION):
    return parse_version(remote_version_str) > parse_version(current_version_str)


def check_remote_version():
    """
    Consulta si existe una versión más nueva en GitHub de forma silenciosa.
    Retorna un dict con {version, download_url, changelog} o None si no hay actualización o si falla la red.
    """
    headers = {"User-Agent": f"MobilDesk-POS/{CURRENT_VERSION}"}

    # 1. Intentar primero con version.json directo (más rápido y sin límites de API)
    try:
        req = urllib.request.Request(VERSION_JSON_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                remote_v = data.get("version", "").strip()
                if remote_v and is_newer_version(remote_v):
                    return {
                        "version": remote_v,
                        "download_url": data.get("download_url", ""),
                        "changelog": data.get("changelog", "Mejoras de rendimiento y estabilidad."),
                    }
                return None
    except Exception:
        pass

    # 2. Intentar como respaldo con la API de GitHub Releases
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                remote_v = data.get("tag_name", "").strip()
                if remote_v and is_newer_version(remote_v):
                    download_url = ""
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe"):
                            download_url = asset.get("browser_download_url", "")
                            break
                    if download_url:
                        return {
                            "version": remote_v,
                            "download_url": download_url,
                            "changelog": data.get("body", "Mejoras de rendimiento y estabilidad."),
                        }
    except Exception:
        pass

    return None


def download_installer(download_url, version_str, progress_callback=None):
    """
    Descarga el archivo de actualización (.zip o .exe) a la carpeta local reportando progreso (0-100%).
    Retorna la ruta absoluta del archivo descargado.
    """
    if not download_url:
        return None

    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    ext = ".zip" if download_url.lower().endswith(".zip") else ".exe"
    target_path = UPDATES_DIR / f"MobilDesk_Update_v{version_str.lstrip('v')}{ext}"

    headers = {"User-Agent": f"MobilDesk-POS/{CURRENT_VERSION}"}
    req = urllib.request.Request(download_url, headers=headers)

    with urllib.request.urlopen(req, timeout=60) as response:
        total_size = response.headers.get("content-length")
        total_size = int(total_size) if total_size else None
        bytes_downloaded = 0

        with open(target_path, "wb") as out_file:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                out_file.write(chunk)
                bytes_downloaded += len(chunk)
                if total_size and progress_callback:
                    percent = min(99, int((bytes_downloaded / total_size) * 100))
                    progress_callback(percent, bytes_downloaded, total_size)

    if target_path.exists() and target_path.stat().st_size > 5000:
        if progress_callback:
            progress_callback(100, target_path.stat().st_size, target_path.stat().st_size)
        return str(target_path)
    return None


def apply_update_and_restart(installer_path):
    """
    Aplica la actualización de forma inteligente:
    - Si es un Micro-Parche .zip: lo descomprime en 1 segundo y reabre la app.
    - Si es un Instalador .exe: ejecuta Inno Setup en modo silencioso y reinicia.
    """
    if not installer_path or not os.path.exists(installer_path):
        return False

    try:
        # Ocultar ventanas de consola durante la aplicacion de actualizaciones
        no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        path_str = str(installer_path).lower()
        if path_str.endswith(".zip"):
            # Micro-Parche ultra rápido
            if getattr(sys, "frozen", False):
                app_dir = Path(sys.executable).parent
                app_exe = Path(sys.executable)
                cmd_restart = f'start "" "{app_exe}"'
            else:
                app_dir = Path(__file__).resolve().parent.parent.parent
                app_main = app_dir / "main.py"
                cmd_restart = f'start "" "{sys.executable}" "{app_main}"'

            patch_script = UPDATES_DIR / "apply_patch.bat"
            with open(patch_script, "w", encoding="utf-8") as f:
                f.write(f"""@echo off
timeout /t 1 /nobreak > nul
powershell -NoProfile -Command "Expand-Archive -Path '{installer_path}' -DestinationPath '{app_dir}' -Force"
{cmd_restart}
exit
""")
            subprocess.Popen(["cmd.exe", "/c", str(patch_script)], close_fds=True, creationflags=no_window)
            return True
        else:
            # Instalador Full .exe
            cmd = [
                str(installer_path),
                "/SILENT",
                "/SUPPRESSMSGBOXES",
                "/FORCECLOSEAPPLICATIONS",
            ]
            subprocess.Popen(cmd, close_fds=True, creationflags=no_window)
            return True
    except Exception as e:
        print(f"Error al ejecutar actualizador: {e}")
        return False


class DownloadAndApplyWorker(QThread):
    """
    Hilo para descargar la actualización con emisión de progreso continuo.
    """
    progress_signal = Signal(int)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, download_url, version_str):
        super().__init__()
        self.download_url = download_url
        self.version_str = version_str

    def run(self):
        try:
            self.status_signal.emit("Conectando con el servidor de descargas...")

            def progress_cb(percent, downloaded, total):
                self.progress_signal.emit(percent)
                mb_down = downloaded / (1024 * 1024)
                mb_tot = total / (1024 * 1024)
                self.status_signal.emit(f"Descargando: {mb_down:.1f} MB / {mb_tot:.1f} MB ({percent}%)")

            path = download_installer(self.download_url, self.version_str, progress_cb)
            if path:
                self.finished_signal.emit(True, path)
            else:
                self.finished_signal.emit(False, "Error al verificar el archivo descargado.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class BackgroundUpdateWorker(QThread):
    """
    Hilo en segundo plano que consulta si hay versión nueva, la descarga
    silenciosamente y emite la señal cuando el instalador ya está listo en el disco.
    """
    update_ready_signal = Signal(str, str, str)  # (version, installer_path, changelog)

    def run(self):
        try:
            info = check_remote_version()
            if not info or not info.get("download_url"):
                return

            v = info["version"]
            url = info["download_url"]
            changelog = info.get("changelog", "Mejoras de rendimiento y estabilidad.")

            # Descargar instalador en segundo plano
            local_installer = download_installer(url, v)
            if local_installer:
                self.update_ready_signal.emit(v, local_installer, changelog)
        except Exception:
            # Nunca interrumpe al usuario si falla internet o no hay versión
            pass
