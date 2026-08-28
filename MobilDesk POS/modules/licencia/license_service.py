import hashlib
import json
import os
import platform
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection

DEMO_DAYS = 7


def _publicar_licencia_nube(conn, estado, plan, fecha_expiracion_iso):
    """Publica el estado de la licencia en la nube para que la app movil
    quede sincronizada con el PC (mismos dias y horas restantes)."""
    try:
        queue_event_with_connection(conn, "licencia_negocio", {
            "estado": estado,
            "plan": plan,
            "fecha_expiracion": fecha_expiracion_iso,
        })
    except Exception:
        pass

# Días entre revisiones silenciosas de la clave contra el servidor.
# Entre revisiones el sistema funciona 100% offline con la fecha guardada localmente.
REVALIDACION_DIAS = 7

# Servidor oficial de activación (bot en Render). El secreto maestro vive SOLO ahí.
LICENSE_SERVER_URL = os.environ.get(
    "MOBILDESK_LICENSE_SERVER",
    "https://mobildesk-keybot.onrender.com"
).rstrip("/")


# Cache del Machine ID: se detecta UNA vez por ejecucion de la app.
# Asi no se lanza PowerShell en cada cambio de modulo.
_MACHINE_ID_CACHE = None


def get_machine_id() -> str:
    """
    Obtiene un identificador único y determinista del hardware del equipo (Windows).
    Usa CIM/PowerShell (presente en todas las Windows modernas, incluida 11 24H2+)
    y conserva wmic como respaldo en equipos antiguos. Ambos leen el mismo UUID,
    por lo que los Machine IDs existentes no cambian.

    El resultado se cachea: el proceso externo corre solo la primera vez y con
    CREATE_NO_WINDOW para que nunca parpadee una ventana de consola.
    """
    global _MACHINE_ID_CACHE
    if _MACHINE_ID_CACHE:
        return _MACHINE_ID_CACHE

    raw_id = ""
    no_window = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

    def _uuid_valido(valor: str) -> bool:
        v = (valor or "").strip()
        return bool(v) and "0000" not in v and "FFFF" not in v

    if platform.system() == "Windows":
        # 1) PowerShell CIM (reemplazo oficial de wmic en Windows 11 24H2+)
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"],
                stderr=subprocess.DEVNULL,
                timeout=6,
                creationflags=no_window
            ).decode("utf-8", errors="ignore").strip()
            if _uuid_valido(out):
                raw_id = out
        except Exception:
            pass

        # 2) wmic como respaldo (Windows 10 / 11 anteriores a 24H2)
        if not _uuid_valido(raw_id):
            try:
                out = subprocess.check_output(
                    "wmic csproduct get uuid",
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    creationflags=no_window
                ).decode("utf-8", errors="ignore")
                lines = [line.strip() for line in out.splitlines() if line.strip() and "UUID" not in line]
                if lines and _uuid_valido(lines[0]):
                    raw_id = lines[0]
            except Exception:
                pass

    # Fallback final si nada funcionó
    if not _uuid_valido(raw_id):
        node = platform.node()
        processor = platform.processor()
        system = platform.system()
        raw_id = f"{node}-{processor}-{system}"

    # Generar hash corto y formateado (ej. KP-89FA-31BC-10D2)
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest().upper()
    _MACHINE_ID_CACHE = f"KP-{digest[:4]}-{digest[4:8]}-{digest[8:12]}"
    return _MACHINE_ID_CACHE


def validar_clave_en_servidor(machine_id: str, clave: str, timeout: int = 10) -> tuple:
    """
    Consulta al servidor oficial de activación (Render).
    Retorna (estado, mensaje, detalles) donde estado es:
      'valida'       -> clave legítima y vigente
      'invalida'     -> el servidor rechazó la clave
      'sin_conexion' -> no se pudo contactar al servidor (no confundir con inválida)
    """
    url = f"{LICENSE_SERVER_URL}/activar?" + urllib.parse.urlencode(
        {"machine_id": machine_id.strip().upper(), "clave": clave.strip().upper()}
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8", errors="replace"))
            if isinstance(body, dict) and body.get("ok") is False:
                return "invalida", body.get("error", "La clave ingresada no es válida."), {}
        except Exception:
            pass
        return "invalida", f"El servidor de licencias respondió con error ({error.code}).", {}
    except (urllib.error.URLError, OSError):
        return "sin_conexion", "No se pudo contactar al servidor de licencias.", {}
    except Exception as err:
        return "invalida", f"Error al validar la clave: {err}", {}

    if not isinstance(data, dict) or "ok" not in data:
        return "invalida", "Respuesta no reconocida del servidor de licencias.", {}
    if not data.get("ok"):
        return "invalida", data.get("error", "La clave ingresada no es válida."), {}

    detalles = {
        "plan_codigo": data.get("plan_codigo"),
        "plan_nombre": data.get("plan_nombre", "Plan Activo"),
        "fecha_expiracion": data.get("fecha_expiracion", ""),
        "fecha_expiracion_iso": data.get("fecha_expiracion_iso", ""),
        "dias_restantes": data.get("dias_restantes", 0)
    }
    return "valida", "Clave válida", detalles


def _revalidar_silenciosa(clave: str, machine_id: str):
    """
    Cada REVALIDACION_DIAS días, confirma la clave contra el servidor.
    Si no hay Internet, simplemente registra el intento y sigue funcionando normal.
    Nunca lanza excepciones ni interrumpe el arranque del sistema.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ultima_verificacion FROM system_license WHERE id = 1")
        row = cursor.fetchone()

        ultima = None
        if row and row["ultima_verificacion"]:
            try:
                ultima = datetime.fromisoformat(row["ultima_verificacion"])
            except Exception:
                ultima = None

        now = datetime.now()
        if ultima is not None and (now - ultima).days < REVALIDACION_DIAS:
            return

        estado, _msg, det = validar_clave_en_servidor(machine_id, clave, timeout=5)

        if estado == "valida":
            cursor.execute(
                """
                UPDATE system_license
                SET fecha_expiracion = ?, ultima_verificacion = ?
                WHERE id = 1
                """,
                (det.get("fecha_expiracion_iso") or "", now.isoformat())
            )
        else:
            # Sin conexión o rechazo puntual: solo registrar el intento.
            cursor.execute(
                "UPDATE system_license SET ultima_verificacion = ? WHERE id = 1",
                (now.isoformat(),)
            )
        conn.commit()
    except Exception:
        pass
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def init_or_get_license_info() -> dict:
    """
    Inicializa o recupera el estado de la licencia del sistema.
    """
    machine_id = get_machine_id()
    now_str = datetime.now().isoformat()
    today = datetime.now()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_license WHERE id = 1")
        row = cursor.fetchone()

        if not row:
            # Primera instalación: iniciar Demo de 7 días
            demo_expiry = today + timedelta(days=DEMO_DAYS)
            cursor.execute(
                """
                INSERT INTO system_license (
                    id, machine_id, fecha_instalacion, plan_activo,
                    clave_activacion, fecha_activacion, fecha_expiracion, ultima_verificacion
                ) VALUES (1, ?, ?, 'demo', NULL, NULL, ?, ?)
                """,
                (machine_id, now_str, demo_expiry.isoformat(), now_str)
            )
            conn.commit()
            _publicar_licencia_nube(conn, "demo", "demo", demo_expiry.isoformat())
            return {
                "estado": "demo",
                "plan_nombre": "Prueba Gratuita (Demo)",
                "dias_restantes": DEMO_DAYS,
                "fecha_expiracion": demo_expiry.strftime("%d/%m/%Y"),
                "machine_id": machine_id,
                "bloqueado": False
            }

        # Ya existe registro
        plan_activo = row["plan_activo"]
        fecha_exp_str = row["fecha_expiracion"]
        clave = row["clave_activacion"]

        if plan_activo == "vitalicio":
            return {
                "estado": "vitalicio",
                "plan_nombre": "Plan Vitalicio / Permanente",
                "dias_restantes": 99999,
                "fecha_expiracion": "Permanente",
                "machine_id": machine_id,
                "bloqueado": False
            }

        if plan_activo == "demo":
            fecha_exp = datetime.fromisoformat(fecha_exp_str)
            dias_restantes = max(0, (fecha_exp - today).days)
            bloqueado = today > fecha_exp
            return {
                "estado": "demo" if not bloqueado else "expirado",
                "plan_nombre": "Prueba Gratuita (Demo)" if not bloqueado else "Prueba Gratuita Expirada",
                "dias_restantes": dias_restantes if not bloqueado else 0,
                "fecha_expiracion": fecha_exp.strftime("%d/%m/%Y"),
                "machine_id": machine_id,
                "bloqueado": bloqueado
            }

        # Planes Mensual, Anual o Demo Extendida ya activados con clave.
        # La clave fue validada por el servidor oficial al momento de activarse;
        # aquí se confía en la fecha guardada localmente para operar sin Internet.
        if clave:
            fecha_exp = None
            if fecha_exp_str:
                try:
                    fecha_exp = datetime.fromisoformat(fecha_exp_str)
                except Exception:
                    fecha_exp = None

            plan_nombres_db = {
                "mensual": "Plan Mensual (30 Días)",
                "anual": "Plan Anual (365 Días)",
                "demo_extendida": "Demo Extendida"
            }
            plan_nombre = plan_nombres_db.get(plan_activo, "Plan Activo")

            if fecha_exp is None:
                info = {
                    "estado": "expirado",
                    "plan_nombre": "Sin Licencia Activa",
                    "dias_restantes": 0,
                    "fecha_expiracion": "No activado",
                    "machine_id": machine_id,
                    "bloqueado": True
                }
            else:
                bloqueado = today > fecha_exp
                dias_restantes = max(0, (fecha_exp - today).days)
                info = {
                    "estado": "activo" if not bloqueado else "expirado",
                    "plan_nombre": plan_nombre if not bloqueado else "Licencia Vencida",
                    "dias_restantes": dias_restantes if not bloqueado else 0,
                    "fecha_expiracion": fecha_exp.strftime("%d/%m/%Y"),
                    "machine_id": machine_id,
                    "bloqueado": bloqueado
                }

            # Revisión periódica silenciosa contra el servidor (no bloquea el uso).
            _revalidar_silenciosa(clave, machine_id)
            return info

        # Sin clave registrada
        return {
            "estado": "expirado",
            "plan_nombre": "Sin Licencia Activa",
            "dias_restantes": 0,
            "fecha_expiracion": "No activado",
            "machine_id": machine_id,
            "bloqueado": True
        }
    finally:
        conn.close()


def activate_system_license(key: str) -> tuple[bool, str]:
    """
    Aplica una clave de activación validándola contra el servidor oficial.
    La activación requiere Internet (es un proceso único); después de activar,
    el sistema funciona completamente offline.
    """
    machine_id = get_machine_id()

    estado, mensaje, det = validar_clave_en_servidor(machine_id, key, timeout=12)

    if estado == "sin_conexion":
        return False, (
            "No se pudo contactar al servidor de activación.\n\n"
            "Verifica tu conexión a Internet e inténtalo nuevamente en unos segundos."
        )
    if estado != "valida":
        return False, mensaje

    now_str = datetime.now().isoformat()
    plan_cod = det["plan_codigo"]

    if plan_cod == "V":
        plan_db = "vitalicio"
        exp_iso = "9999-12-31T23:59:59"
    else:
        plan_db = {"M": "mensual", "A": "anual"}.get(plan_cod, "demo_extendida")
        exp_iso = det["fecha_expiracion_iso"] or (
            datetime.now() + timedelta(days=det["dias_restantes"])
        ).isoformat()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE system_license
            SET plan_activo = ?,
                clave_activacion = ?,
                fecha_activacion = ?,
                fecha_expiracion = ?,
                ultima_verificacion = ?
            WHERE id = 1
            """,
            (plan_db, key.strip().upper(), now_str, exp_iso, now_str)
        )
        conn.commit()
        estado_nube = "vitalicio" if plan_db == "vitalicio" else "activo"
        _publicar_licencia_nube(conn, estado_nube, plan_db, exp_iso)
        return True, f"¡Licencia activada con éxito! ({det['plan_nombre']} activo hasta {det['fecha_expiracion']})"
    finally:
        conn.close()
