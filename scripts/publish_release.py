import os
import sys
import json
import base64
import subprocess
from pathlib import Path
import requests

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN no configurado. Exporta la variable de entorno antes de publicar.")
REPO_OWNER = "USmind"
REPO_NAME = "mobildesk-releases"
VERSION = "v2.0.16"
CLEAN_VERSION = "2.0.16"
CHANGELOG = "Versión 2.0.16: Corrección de símbolos en instalación inicial, sincronización de licencia mejorada y pagos mixtos en app móvil."

BASE_DIR = Path(__file__).resolve().parent.parent
INSTALLER_PATH = BASE_DIR / "compilados" / "Instalar-MobilDesk.exe"
if not INSTALLER_PATH.exists():
    INSTALLER_PATH = BASE_DIR / "MobilDesk POS" / "release" / "Instalar-MobilDesk.exe"
APK_PATH = BASE_DIR / "compilados" / "mobildesk-movil.apk"
if not APK_PATH.exists():
    APK_PATH = BASE_DIR / "outputs" / "mobildesk-movil.apk"
VERSION_JSON_PATH = BASE_DIR / "version.json"


def get_headers():
    return {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MobilDesk-AutoPublisher",
    }


def update_or_create_version_json():
    print(f"--> [1/3] Actualizando version.json en GitHub ({REPO_OWNER}/{REPO_NAME})...", flush=True)
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/version.json"

    version_content = {
        "version": CLEAN_VERSION,
        "download_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{VERSION}/Instalar-MobilDesk.exe",
        "changelog": CHANGELOG,
        "mobile_version": "1.2.1",
        "mobile_download_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{VERSION}/mobildesk-movil.apk",
        "mobile_changelog": "Versión 1.2.1: Pagos mixtos / fraccionados en app móvil (5 métodos combinables) + correcciones."
    }
    raw_json = json.dumps(version_content, indent=2, ensure_ascii=False)

    sha = None
    r = requests.get(url, headers=get_headers())
    if r.status_code == 200:
        sha = r.json().get("sha")

    payload = {
        "message": f"Release {VERSION} - version.json",
        "content": base64.b64encode(raw_json.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    r_put = requests.put(url, headers=get_headers(), json=payload)
    if r_put.status_code in (200, 201):
        print(f"OK: version.json actualizado a {CLEAN_VERSION} en GitHub.", flush=True)
    else:
        print(f"Aviso al actualizar version.json: {r_put.status_code} - {r_put.text}", flush=True)


def create_or_get_release():
    print(f"--> [2/2] Creando Release {VERSION} en GitHub...", flush=True)
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    
    check_url = f"{url}/tags/{VERSION}"
    r_check = requests.get(check_url, headers=get_headers())
    if r_check.status_code == 200:
        release_data = r_check.json()
        print(f"OK: Release {VERSION} ya existe (ID: {release_data['id']}).", flush=True)
        return release_data

    payload = {
        "tag_name": VERSION,
        "target_commitish": "main",
        "name": f"MobilDesk POS {VERSION}",
        "body": CHANGELOG,
        "draft": False,
        "prerelease": False
    }
    r_create = requests.post(url, headers=get_headers(), json=payload)
    if r_create.status_code in (200, 201):
        release_data = r_create.json()
        print(f"OK: Release {VERSION} creado con éxito en GitHub (ID: {release_data['id']}).", flush=True)
        return release_data
    else:
        raise Exception(f"No se pudo crear el release: {r_create.status_code} - {r_create.text}")


def upload_file_asset(release_id, file_path, asset_name):
    if not file_path.exists():
        print(f"Aviso: Archivo no encontrado para subir: {file_path}", flush=True)
        return
    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"--> Subiendo {asset_name} ({size_mb:.2f} MB) a GitHub...", flush=True)

    # 1. Comprobar si ya existe el asset y eliminarlo
    assets_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets"
    r_assets = requests.get(assets_url, headers=get_headers())
    if r_assets.status_code == 200:
        for asset in r_assets.json():
            if asset.get("name") == asset_name:
                print(f"Reemplazando versión previa de {asset_name} (ID: {asset['id']})...", flush=True)
                requests.delete(asset.get("url"), headers=get_headers())

    # 2. Subir nuevo asset
    upload_url = f"https://uploads.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets?name={asset_name}"
    cmd = [
        "curl.exe",
        "--http1.1",
        "-s",
        "-S",
        "--retry", "5",
        "--retry-delay", "3",
        "--connect-timeout", "60",
        "-X", "POST",
        "-H", f"Authorization: token {TOKEN}",
        "-H", "Content-Type: application/octet-stream",
        "-H", "Expect:",
        "--data-binary", f"@{str(file_path)}",
        upload_url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and ('"id":' in res.stdout or '"name":' in res.stdout):
        print(f"OK: {asset_name} subido exitosamente a GitHub!", flush=True)
    else:
        print(f"Aviso al subir {asset_name}: {res.stderr or res.stdout[:200]}", flush=True)


def upload_all_assets(release_id):
    upload_file_asset(release_id, INSTALLER_PATH, "Instalar-MobilDesk.exe")
    if APK_PATH.exists():
        upload_file_asset(release_id, APK_PATH, "mobildesk-movil.apk")


if __name__ == "__main__":
    try:
        update_or_create_version_json()
        release = create_or_get_release()
        upload_all_assets(release["id"])
        print("\n=======================================================", flush=True)
        print(f"RELEASE {VERSION} PUBLICADO Y CONFIGURADO AL 100% EN GITHUB!", flush=True)
        print(f"Enlace al Release: {release.get('html_url')}")
        print("=======================================================", flush=True)
    except Exception as e:
        print(f"\nERROR: {e}", flush=True)
        sys.exit(1)
