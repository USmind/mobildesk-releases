"""Módulo de Sincronización en la Nube de Kiosko POS.

Sincronización integral y bidireccional (PC ↔ Teléfono Móvil) para:
- Tasa Oficial de Cambio USD / Bs y Margen de Ganancia.
- Nombre y Configuración del Comercio.
- Catálogo de Productos y Precios.
- Movimientos de Inventario y Ajustes de Stock.
- Ventas, Facturación y Comprobantes.
- Clientes, Fiados / Créditos y Abonos / Pagos de Deudas.
"""
import json
import uuid
import hashlib
import random
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from database.connection import get_connection

SUPABASE_URL = "https://atxeuhqhariymdqsbmpd.supabase.co"
SUPABASE_KEY = "sb_publishable_6a_o_Jv_XhqZE9TP7mO2EA_gOeak-mL"


def to_valid_uuid(text):
    """Convierte cualquier código de negocio o texto a un UUID válido determinista."""
    trimmed = str(text or "kiosko-default").strip().lower()
    try:
        return str(uuid.UUID(trimmed))
    except Exception:
        h = hashlib.md5(trimmed.encode("utf-8")).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _is_duplicate_key_error(detail):
    """Detecta el error 23505 de Postgres: el evento ya existe en la nube.

    Ocurre cuando el primer POST sí llegó al servidor pero la respuesta se
    perdió (timeout/red) y el reintento envía el mismo id. Es seguro tratarlo
    como éxito: el dato ya está guardado.
    """
    msg = str(detail).lower()
    return (
        "duplicate key" in msg
        or "23505" in msg
        or "kiosko_sync_events_pkey" in msg
        or "already exists" in msg
    )


def _translate_error(detail, status_code=None):
    """Traduce cualquier error técnico a un mensaje claro y amigable en español."""
    msg = str(detail).lower()
    if "permission denied" in msg or "42501" in msg or status_code == 401:
        return "El servidor de sincronización está actualizando permisos. Reintenta en unos segundos."
    if "email_not_confirmed" in msg:
        return "Verificación pendiente en el servidor."
    if "invalid_credentials" in msg or "invalid login" in msg:
        return "El código de negocio no es válido."
    if "over_request_rate_limit" in msg or "429" in msg or "too many" in msg:
        return "Conexión ocupada. Reintentando sincronización automáticamente..."
    return f"Aviso de sincronización: {detail}"


def _request(url, method="GET", data=None, token=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail)
            detail = payload.get("message") or payload.get("error_description") or detail
        except json.JSONDecodeError:
            pass
        translated = _translate_error(detail, error.code)
        raise ValueError(translated) from error
    except URLError as error:
        raise ConnectionError("Sin conexión a Internet. Todos los datos están seguros y guardados en tu equipo.") from error


def _setting(connection, key, default=None):
    row = connection.execute("SELECT valor FROM sync_settings WHERE clave=?", (key,)).fetchone()
    return row["valor"] if row else default


def _save_setting(connection, key, value):
    connection.execute(
        "INSERT INTO sync_settings(clave, valor) VALUES(?, ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (key, str(value)),
    )


def generate_new_business_code(business_name=""):
    """Genera un Código de Negocio limpio, profesional y fácil de recordar."""
    prefix = "".join(c for c in (business_name or "MOBILDESK").upper() if c.isalnum())[:6]
    if not prefix:
        prefix = "MOBILDESK"[:6]
    rand_num = random.randint(1000, 9999)
    return f"{prefix}-{rand_num}"


def get_business_id():
    """Retorna o genera un Código de Negocio único para este equipo."""
    connection = get_connection()
    try:
        bid = _setting(connection, "negocio_id")
        if not bid:
            bid = generate_new_business_code("MOBILDESK")
            _save_setting(connection, "negocio_id", bid)
            _save_setting(connection, "dispositivo_id", f"pc-{str(uuid.uuid4())[:8]}")
            connection.commit()
        return bid
    finally:
        connection.close()


def set_business_code(custom_code):
    """Permite enlazar directamente el PC usando un Código de Negocio."""
    custom_code = custom_code.strip()
    if not custom_code:
        raise ValueError("El código de negocio no puede estar vacío.")
    connection = get_connection()
    try:
        _save_setting(connection, "negocio_id", custom_code)
        _save_setting(connection, "email", f"codigo:{custom_code}")
        _save_setting(connection, "dispositivo_id", _setting(connection, "dispositivo_id", f"pc-{str(uuid.uuid4())[:8]}"))
        connection.execute("DELETE FROM sync_settings WHERE clave='snapshot_version'")
        _queue_initial_snapshot(connection)
        connection.commit()
    finally:
        connection.close()


def is_configured():
    connection = get_connection()
    try:
        return bool(_setting(connection, "negocio_id"))
    finally:
        connection.close()


def get_sync_status_info():
    """Retorna información clara y amigable del estado de sincronización."""
    connection = get_connection()
    try:
        business_id = _setting(connection, "negocio_id") or get_business_id()
        pending = int(connection.execute("SELECT COUNT(*) FROM sync_outbox WHERE enviado_en IS NULL").fetchone()[0])
        last_sync = _setting(connection, "ultimo_envio_exitoso", "Nunca")
        last_error = _setting(connection, "ultimo_error_global")
        return {
            "configured": bool(business_id),
            "business_id": business_id,
            "pending": pending,
            "last_sync": last_sync,
            "last_error": last_error,
        }
    finally:
        connection.close()


def queue_event_with_connection(connection, tipo, datos):
    """Agrega un cambio a la cola usando una transacción existente."""
    connection.execute(
        "INSERT INTO sync_outbox(id, tipo, datos) VALUES(?, ?, ?)",
        (str(uuid.uuid4()), tipo, json.dumps(datos, ensure_ascii=False)),
    )


def queue_event(tipo, datos):
    connection = get_connection()
    try:
        queue_event_with_connection(connection, tipo, datos)
        connection.commit()
    finally:
        connection.close()


def _queue_initial_snapshot(connection):
    """Coloca absolutamente todos los datos existentes en la cola para subirlos a la nube."""
    if _setting(connection, "snapshot_version") == "6":
        return

    # 1. Tasa y Margen Actuales
    row_tasa = connection.execute("SELECT valor FROM exchange_rates ORDER BY id DESC LIMIT 1").fetchone()
    row_gain = connection.execute("SELECT porcentaje_ganancia FROM pricing_settings WHERE id=1").fetchone()
    tasa_val = float(row_tasa["valor"]) if row_tasa else 0.0
    gain_val = float(row_gain["porcentaje_ganancia"]) if row_gain else 0.0
    queue_event_with_connection(connection, "tasa_cambio_actualizada", {"tasa": tasa_val, "margen": gain_val})

    # 2. Configuración del Negocio
    row_biz = connection.execute(
        "SELECT nombre_negocio, identificacion, telefono, direccion, mensaje_ticket FROM business_settings WHERE id=1"
    ).fetchone()
    if row_biz:
        queue_event_with_connection(connection, "negocio_config_actualizada", dict(row_biz))

    # 3. Catálogo de Productos
    products = connection.execute(
        "SELECT codigo, codigo_barras, nombre, marca, unidad, precio_usd, stock_minimo, activo FROM products"
    ).fetchall()
    for product in products:
        queue_event_with_connection(connection, "producto_guardado", dict(product))

    # 4. Movimientos de Inventario
    movements = connection.execute(
        """SELECT p.codigo AS producto_codigo, im.tipo, im.cantidad, im.costo_usd, im.motivo, im.fecha
           FROM inventory_movements im JOIN products p ON p.id=im.producto_id
           ORDER BY im.id"""
    ).fetchall()
    for movement in movements:
        queue_event_with_connection(connection, "movimiento_inventario", dict(movement))

    # 5. Ventas y Fiados
    sales = connection.execute(
        """SELECT s.numero_factura, s.tasa_utilizada AS tasa, s.total_usd, s.total_bs, s.metodo_pago,
                  s.monto_recibido_bs, s.monto_recibido_usd, s.vuelto_bs, s.vuelto_usd, s.es_fiada,
                  c.nombre AS cliente_nombre, COALESCE(d.saldo_bs, 0) AS saldo_pendiente
           FROM sales s
           LEFT JOIN clients c ON c.id=s.cliente_id
           LEFT JOIN credit_debts d ON d.venta_id=s.id"""
    ).fetchall()
    for sale in sales:
        items = connection.execute(
            """SELECT p.codigo, si.cantidad, si.precio_usd
               FROM sale_items si JOIN products p ON p.id=si.producto_id
               WHERE si.venta_id=(SELECT id FROM sales WHERE numero_factura=?)""",
            (sale["numero_factura"],),
        ).fetchall()
        data = dict(sale)
        data["productos"] = [dict(item) for item in items]
        queue_event_with_connection(connection, "venta_registrada", data)

    _save_setting(connection, "snapshot_version", "6")


def _user_id(connection):
    row = connection.execute("SELECT id FROM users WHERE username != ? ORDER BY id LIMIT 1", ("__configuracion__",)).fetchone()
    if row is not None:
        return row["id"]
    return connection.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()["id"]


def _apply_remote_event(connection, event):
    """Aplica un evento del móvil sin volver a colocarlo en la cola local."""
    already = connection.execute("SELECT 1 FROM sync_applied_events WHERE id=?", (event["id"],)).fetchone()
    if already:
        return False
    data, kind = event["datos"] or {}, event["tipo"]

    if kind == "tasa_cambio_actualizada":
        tasa = float(data.get("tasa") or 0)
        margen = float(data.get("margen") or 0)
        if tasa > 0:
            connection.execute(
                "INSERT INTO exchange_rates(valor, usuario_id) VALUES(?, ?)",
                (tasa, _user_id(connection)),
            )
        if margen >= 0:
            connection.execute(
                "UPDATE pricing_settings SET porcentaje_ganancia=? WHERE id=1",
                (margen,),
            )
    elif kind == "negocio_config_actualizada":
        nombre = data.get("nombre_negocio") or "MOBILDESK"
        connection.execute(
            """INSERT INTO business_settings (id, nombre_negocio, identificacion, telefono, direccion, mensaje_ticket)
               VALUES (1, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   nombre_negocio = excluded.nombre_negocio,
                   identificacion = excluded.identificacion,
                   telefono = excluded.telefono,
                   direccion = excluded.direccion,
                   mensaje_ticket = excluded.mensaje_ticket""",
            (
                nombre,
                data.get("identificacion", ""),
                data.get("telefono", ""),
                data.get("direccion", ""),
                data.get("mensaje_ticket", "¡Gracias por su compra!"),
            ),
        )
    elif kind == "producto_guardado":
        code = data.get("codigo")
        if not code:
            return False
        current = connection.execute("SELECT id FROM products WHERE codigo=?", (code,)).fetchone()
        codigo_barras = data.get("codigo_barras")
        values = (
            data.get("nombre", "Producto"),
            data.get("marca", ""),
            data.get("unidad", "Unidad"),
            float(data.get("precio_usd") or 0),
            float(data.get("stock_minimo") or 0),
            int(data.get("activo", 1)),
        )
        if current:
            connection.execute(
                "UPDATE products SET nombre=?, marca=?, unidad=?, precio_usd=?, stock_minimo=?, activo=?, codigo_barras=? WHERE id=?",
                (*values, codigo_barras, current["id"]),
            )
        else:
            connection.execute(
                "INSERT INTO products(codigo,codigo_barras,nombre,categoria_id,costo_usd,precio_usd,stock_minimo,activo,marca,unidad) VALUES(?, ?, ?, NULL, 0, ?, ?, ?, ?, ?)",
                (code, codigo_barras, values[0], values[3], values[4], values[5], values[1], values[2]),
            )
    elif kind == "producto_eliminado":
        connection.execute("UPDATE products SET activo=0 WHERE codigo=?", (data.get("codigo"),))
    elif kind == "movimiento_inventario":
        product = connection.execute("SELECT id FROM products WHERE codigo=?", (data.get("producto_codigo"),)).fetchone()
        if product:
            connection.execute(
                "INSERT INTO inventory_movements(producto_id,tipo,cantidad,costo_usd,motivo,venta_id,usuario_id,fecha) VALUES(?, ?, ?, ?, ?, NULL, ?, ?)",
                (
                    product["id"],
                    data.get("tipo", "ajuste"),
                    float(data.get("cantidad") or 0),
                    data.get("costo_usd"),
                    data.get("motivo", "Sincronizado desde móvil"),
                    _user_id(connection),
                    data.get("fecha") or _now(),
                ),
            )
    elif kind == "venta_registrada":
        invoice = str(data.get("numero_factura") or f"MOV-{event['id'][:8]}")
        exists = connection.execute("SELECT 1 FROM sales WHERE numero_factura=?", (invoice,)).fetchone()
        if not exists:
            es_fiada = bool(data.get("es_fiada") or data.get("metodo_pago") == "fiado")
            cliente_nombre = (data.get("cliente_nombre") or "").strip()
            cliente_id = None
            if cliente_nombre:
                c = connection.execute("SELECT id FROM clients WHERE LOWER(nombre)=LOWER(?)", (cliente_nombre,)).fetchone()
                if c:
                    cliente_id = c["id"]
                else:
                    cur_c = connection.execute("INSERT INTO clients(nombre,telefono,direccion,cedula) VALUES(?, '', '', '')", (cliente_nombre,))
                    cliente_id = cur_c.lastrowid

            cursor = connection.execute(
                """INSERT INTO sales(numero_factura,usuario_id,tasa_utilizada,total_usd,total_bs,metodo_pago,
                                     monto_recibido_bs,vuelto_bs,monto_recibido_usd,vuelto_usd,cliente_id,es_fiada)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    invoice,
                    _user_id(connection),
                    float(data.get("tasa") or 0),
                    float(data.get("total_usd") or 0),
                    float(data.get("total_bs") or 0),
                    data.get("metodo_pago", "efectivo"),
                    data.get("monto_recibido_bs"),
                    float(data.get("vuelto_bs") or 0),
                    data.get("monto_recibido_usd"),
                    float(data.get("vuelto_usd") or 0),
                    cliente_id,
                    int(es_fiada),
                ),
            )
            sale_id = cursor.lastrowid

            if es_fiada and cliente_id:
                saldo_bs = float(data.get("saldo_pendiente") or data.get("total_bs") or 0)
                connection.execute(
                    "INSERT INTO credit_debts(venta_id, cliente_id, total_bs, saldo_bs, estado) VALUES(?, ?, ?, ?, ?)",
                    (sale_id, cliente_id, float(data.get("total_bs") or 0), saldo_bs, "pagada" if saldo_bs <= 0 else "pendiente"),
                )

            for item in data.get("productos", []):
                product = connection.execute("SELECT id FROM products WHERE codigo=?", (item.get("codigo"),)).fetchone()
                if product:
                    quantity, price = float(item.get("cantidad") or 0), float(item.get("precio_usd") or 0)
                    connection.execute(
                        "INSERT INTO sale_items(venta_id,producto_id,cantidad,precio_usd,subtotal_usd) VALUES(?, ?, ?, ?, ?)",
                        (sale_id, product["id"], quantity, price, quantity * price),
                    )
                    connection.execute(
                        "INSERT INTO inventory_movements(producto_id,tipo,cantidad,motivo,venta_id,usuario_id) VALUES(?, 'salida', ?, ?, ?, ?)",
                        (product["id"], quantity, f"Venta sincronizada #{invoice}", sale_id, _user_id(connection)),
                    )
    elif kind == "abono_deuda":
        invoice = str(data.get("numero_factura") or "")
        monto_bs = float(data.get("monto_bs") or 0)
        if invoice and monto_bs > 0:
            sale = connection.execute("SELECT id FROM sales WHERE numero_factura=?", (invoice,)).fetchone()
            if sale:
                debt = connection.execute("SELECT id, saldo_bs FROM credit_debts WHERE venta_id=?", (sale["id"],)).fetchone()
                if debt:
                    new_saldo = max(0.0, float(debt["saldo_bs"]) - monto_bs)
                    connection.execute("INSERT INTO debt_payments(deuda_id, monto_bs) VALUES(?, ?)", (debt["id"], monto_bs))
                    connection.execute(
                        "UPDATE credit_debts SET saldo_bs=?, estado=? WHERE id=?",
                        (new_saldo, "pagada" if new_saldo <= 0 else "pendiente", debt["id"]),
                    )

    connection.execute("INSERT OR IGNORE INTO sync_applied_events(id) VALUES(?)", (event["id"],))
    return True


def sync_now():
    """Envía cambios pendientes y recibe los del móvil."""
    connection = get_connection()
    try:
        business_id = _setting(connection, "negocio_id") or get_business_id()
        valid_uuid = to_valid_uuid(business_id)
        device_id = _setting(connection, "dispositivo_id", f"pc-{str(uuid.uuid4())[:8]}")

        _queue_initial_snapshot(connection)
        connection.commit()

        rows = connection.execute("SELECT id, tipo, datos FROM sync_outbox WHERE enviado_en IS NULL ORDER BY creado_en").fetchall()
        sent = 0
        for row in rows:
            payload = {
                "id": to_valid_uuid(row["id"]),
                "negocio_id": valid_uuid,
                "dispositivo_id": to_valid_uuid(device_id),
                "tipo": row["tipo"],
                "datos": json.loads(row["datos"]),
                "creado_en": _now(),
            }
            try:
                _request(SUPABASE_URL + "/rest/v1/kiosko_sync_events", "POST", payload, None)
                connection.execute("UPDATE sync_outbox SET enviado_en=?, ultimo_error=NULL WHERE id=?", (_now(), row["id"]))
                connection.execute("INSERT OR IGNORE INTO sync_applied_events(id) VALUES(?)", (row["id"],))
                connection.commit()
                sent += 1
            except Exception as error:
                if _is_duplicate_key_error(error):
                    # El evento ya está en la nube: marcar como enviado y seguir.
                    connection.execute("UPDATE sync_outbox SET enviado_en=?, ultimo_error=NULL WHERE id=?", (_now(), row["id"]))
                    connection.execute("INSERT OR IGNORE INTO sync_applied_events(id) VALUES(?)", (row["id"],))
                    connection.commit()
                    sent += 1
                    continue
                connection.execute("UPDATE sync_outbox SET ultimo_error=? WHERE id=?", (str(error), row["id"]))
                _save_setting(connection, "ultimo_error_global", str(error))
                connection.commit()
                raise

        url = SUPABASE_URL + "/rest/v1/kiosko_sync_events?select=id,tipo,datos,creado_en&negocio_id=eq." + valid_uuid + "&order=creado_en.asc"
        remote_events = []
        try:
            remote_events = _request(url, token=None)
        except Exception:
            pass

        received = 0
        if isinstance(remote_events, list):
            for event in remote_events:
                if _apply_remote_event(connection, event):
                    received += 1

        _save_setting(connection, "ultimo_envio_exitoso", datetime.now().strftime("%I:%M %p"))
        _save_setting(connection, "ultimo_error_global", "")
        connection.commit()
        return {"sent": sent, "received": received}
    finally:
        connection.close()

