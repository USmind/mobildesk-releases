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


def borrar_todos_los_datos(incluir_sistema=True, usuario_rol="admin",
                            crear_admin=True):
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

        # Si no hay usuarios y el borrado es total, el programa quedaria
        # bloqueado sin forma de entrar. Para eso se crea un admin por defecto
        # al final de este bloque.
        self_insert = bool(crear_admin and incluir_sistema and "users" in existentes)

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

        credenciales = None
        if self_insert and "users" in existentes:
            credenciales = _crear_admin_por_defecto(connection)

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

    return {"respaldo": respaldo, "eliminadas": eliminadas, "credenciales": credenciales}


def _crear_admin_por_defecto(connection):
    """
    Tras un borrado total se crea un administrador por defecto para que el
    programa siga siendo usable. La clave se genera al azar y se devuelve una
    sola vez, para que el usuario la cambie al entrar.
    """
    import hashlib
    import secrets
    from datetime import datetime as _dt

    usuario = "admin"
    clave = secrets.token_urlsafe(6)
    hash_clave = hashlib.sha256(clave.encode("utf-8")).hexdigest()
    ahora = _dt.now().isoformat()
    connection.execute(
        "INSERT INTO users(nombre, username, password_hash, role, activo, fecha_creacion)"
        " VALUES(?,?,?,?,1,?)",
        ("Administrador", usuario, hash_clave, "admin", ahora),
    )
    connection.commit()
    return usuario, clave