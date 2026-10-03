"""
Borrado total de datos del negocio.

Se usa desde 'Configurar Negocio' > 'Borrar todos los datos'. Borra ventas,
clientes, productos, inventario, caja, fiados y TODO el estado de sincronizacion
(incluido el codigo MOBIL-XXXX), de modo que al reiniciar el programa quede como
una instalacion nueva.

Por seguridad:
  1. Exige el rol admin.
  2. Hace una copia de respaldo (.bak) antes de tocar nada.
  3. Usa una transaccion: si algo falla, no se borra nada a medias.
  4. Las claves foraneas se desactivan durante el borrado y se restauran al final.
"""
import os
import shutil
import sqlite3
from datetime import datetime

from database.connection import DATABASE, get_connection

# Tablas que se vacian. El orden no importa porque se desactivan las FK, pero se
# mantiene agrupado por area para que sea legible.
TABLAS_NEGOCIO = [
    # Ventas y fiados
    "debt_payments",
    "credit_debts",
    "sale_items",
    "sales",
    # Caja
    "cash_movements",
    "cash_registers",
    # Inventario y catalogo
    "inventory_movements",
    "products",
    "categories",
    "suppliers",
    # Personas
    "clients",
    # Sincronizacion (incluye el codigo del negocio y la cola de eventos)
    "sync_applied_events",
    "sync_outbox",
]

# Tablas que se vacian del todo porque son configuracion de la maquina, no del
# negocio. Se borran solo si el usuario elige el borrado total.
TABLAS_SISTEMA = [
    "users",
    "system_license",
]

TABLAS_CONFIG = [
    "exchange_rates",
    "business_settings",
    "pricing_settings",
    "sync_settings",
]


def _tablas_existentes(connection):
    filas = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {f[0] for f in filas}


def contar_datos():
    """Devuelve un resumen de cuantas filas hay, para mostrarlo antes de borrar."""
    connection = get_connection()
    try:
        existentes = _tablas_existentes(connection)
        resumen = {}
        for tabla in TABLAS_NEGOCIO + TABLAS_SISTEMA + TABLAS_CONFIG:
            if tabla not in existentes:
                continue
            try:
                n = connection.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            except sqlite3.Error:
                continue
            if n:
                resumen[tabla] = int(n)
        return resumen
    finally:
        connection.close()


def crear_respaldo(destino=None):
    """Copia la base actual a un archivo .bak y devuelve su ruta."""
    if destino is None:
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        destino = str(DATABASE) + f".respaldo-{marca}.bak"
    origen = str(DATABASE)
    if not os.path.exists(origen):
        raise FileNotFoundError(f"No se encontro la base de datos en {origen}")
    # Cerrar conexiones sueltas: copiar un .db con WAL abierto puede dejar datos
    # sin copiar. Se compacta la copia para que sea un archivo autocontenido.
    origen_con = sqlite3.connect(origen)
    destino_con = sqlite3.connect(destino)
    try:
        origen_con.backup(destino_con)
    finally:
        origen_con.close()
        destino_con.close()
    return destino


def _avisar_celular_que_se_borro(negocio_id):
    """
    Avisa directamente a la nube para que el móvil borre también sus datos.

    No usa la cola de sync_outbox a propósito: esa cola se limpia durante el
    borrado y 'sync_now' puedemeter un snapshot que se cuelgue antes de enviar
    este aviso. Ir directo por HTTP garantiza que el móvil se entere.
    """
    if not negocio_id:
        return False
    try:
        from modules.sync.sync_service import (
            SUPABASE_URL, _request, _now, to_valid_uuid, derivar_llave,
        )
        import uuid as _uuid
        payload = {
            "id": str(_uuid.uuid4()),
            "negocio_id": to_valid_uuid(negocio_id),
            "dispositivo_id": to_valid_uuid("pc-borrado"),
            "tipo": "negocio_datos_borrados",
            "datos": {"motivo": "El administrador borró todos los datos desde la computadora"},
            "creado_en": _now(),
        }
        _request(
            SUPABASE_URL + "/rest/v1/mobildesk_eventos", "POST", payload, None,
            llave=derivar_llave(negocio_id),
        )
        return True
    except Exception:
        return False


def borrar_todos_los_datos(incluir_sistema=True, usuario_rol="admin"):
    """
    Borra todos los datos del negocio. Devuelve un resumen de lo eliminado.

    incluir_sistema=True ademas borra usuarios y licencia (el usuario quedara
    deslicenciado y sin usuarios: tendra que re-licenciar y crear de nuevo).
    """
    if usuario_rol != "admin":
        raise PermissionError("Solo un administrador puede borrar los datos del negocio.")

    # 1) Respaldo antes de tocar nada.
    respaldo = crear_respaldo()

    connection = get_connection()
    try:
        existentes = _tablas_existentes(connection)
        tablas = list(TABLAS_NEGOCIO)
        tablas += list(TABLAS_CONFIG)
        if incluir_sistema:
            tablas += list(TABLAS_SISTEMA)

        avisado = False
        try:
            fila = connection.execute(
                "SELECT valor FROM sync_settings WHERE clave='negocio_id'"
            ).fetchone()
            negocio_id = fila[0] if fila else None
            if negocio_id:
                avisado = _avisar_celular_que_se_borro(negocio_id)
        except sqlite3.Error:
            pass

        connection.execute("PRAGMA foreign_keys = OFF")
        eliminadas = {}
        for tabla in tablas:
            if tabla not in existentes:
                continue
            try:
                antes = connection.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                connection.execute(f"DELETE FROM {tabla}")
                if antes:
                    eliminadas[tabla] = int(antes)
            except sqlite3.Error as e:
                raise sqlite3.Error(f"No se pudo borrar la tabla '{tabla}': {e}")

        # NO se crea ningún usuario. El programa decide la pantalla de inicio
        # contando los usuarios reales: si no hay ninguno, muestra la pantalla
        # de Configuración Inicial para que el usuario elija su propia clave.
        # Antes se creaba un 'admin' con clave aleatoria y eso dejaba el programa
        # bloqueado en la pantalla de acceso con una contraseña desconocida.

        connection.execute("DELETE FROM sqlite_sequence WHERE name IN (" +
                          ",".join("?" * len(tablas)) + ")", tablas)
        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")
    except Exception:
        try:
            connection.rollback()
        finally:
            connection.close()
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass

    # El aviso se mandó por HTTP antes de limpiar; no hace falta tocar la cola.
    return {
        "respaldo": respaldo,
        "eliminadas": eliminadas,
        "credenciales": None,
        "movil_avisado": avisado,
    }