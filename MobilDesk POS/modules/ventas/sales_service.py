import json
from database.connection import get_connection
from modules.configuracion.exchange_rate_service import get_current_rate_value
from modules.sync.sync_service import queue_event_with_connection


def get_next_invoice_number_with_connection(connection):
    row = connection.execute(
        "SELECT COALESCE(MAX(numero_factura), 0) + 1 FROM sales"
    ).fetchone()
    return int(row[0])


def get_next_invoice_number():
    connection = get_connection()
    try:
        return get_next_invoice_number_with_connection(connection)
    finally:
        connection.close()


def get_sale_products():
    connection = get_connection()
    try:
        return connection.execute(
            """
            SELECT p.id, p.codigo, p.codigo_barras, p.nombre, p.unidad, p.precio_usd
            FROM products p
            WHERE p.activo = 1
            ORDER BY p.nombre
            """
        ).fetchall()
    finally:
        connection.close()


def get_product_stock(producto_id):
    connection = get_connection()
    try:
        return _get_product_stock(connection, producto_id)
    finally:
        connection.close()


def _get_product_stock(connection, producto_id):
    row = connection.execute(
        """
        SELECT COALESCE(SUM(CASE
            WHEN tipo = 'entrada' THEN cantidad
            WHEN tipo = 'salida' THEN -cantidad
            WHEN tipo = 'ajuste' THEN cantidad
            ELSE 0 END), 0)
        FROM inventory_movements WHERE producto_id = ?
        """,
        (producto_id,),
    ).fetchone()
    return float(row[0] or 0)


def _normalize_items(items):
    normalized = {}
    for item in items:
        try:
            product_id = int(item["producto_id"])
            quantity = float(item["cantidad"])
            price = float(item["precio_usd"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("La venta contiene un producto no valido.") from error

        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        if price < 0:
            raise ValueError("El precio no puede ser negativo.")

        if product_id in normalized:
            normalized[product_id]["cantidad"] += quantity
        else:
            normalized[product_id] = {
                "producto_id": product_id,
                "cantidad": quantity,
                "precio_usd": price,
            }
    return list(normalized.values())


def create_sale(usuario_id, items, metodo_pago="efectivo", monto_recibido_bs=None,
                monto_recibido_usd=None, cliente=None, es_fiada=False, pagos_detalle=None):
    if not usuario_id:
        raise ValueError("No se encontro el usuario de la venta.")
    if not items:
        raise ValueError("La venta debe contener al menos un producto.")

    rate = get_current_rate_value()
    if rate is None:
        raise ValueError("No existe una tasa USD/Bs configurada.")
    rate = float(rate)
    items = _normalize_items(items)
    metodos_validos = {"efectivo", "tarjeta", "pago_movil", "divisas", "fiado", "mixto"}
    if metodo_pago not in metodos_validos:
        raise ValueError("El método de pago no es válido.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        total_usd = 0.0

        for item in items:
            product = cursor.execute(
                "SELECT id, nombre FROM products WHERE id = ? AND activo = 1",
                (item["producto_id"],),
            ).fetchone()
            if product is None:
                raise ValueError("El producto seleccionado no existe.")

            stock = _get_product_stock(connection, item["producto_id"])
            if item["cantidad"] > stock:
                raise ValueError(
                    f"Stock insuficiente para '{product['nombre']}'. Disponible: {stock:g}."
                )
            total_usd += item["cantidad"] * item["precio_usd"]

        invoice_number = get_next_invoice_number_with_connection(connection)
        total_bs = total_usd * rate
        vuelto_bs = 0.0
        vuelto_usd = 0.0
        es_fiada = bool(es_fiada or metodo_pago == "fiado")
        cliente_id = None
        if cliente and any(str(value or '').strip() for value in cliente.values()):
            cursor.execute("INSERT INTO clients(nombre, telefono, direccion, cedula) VALUES(?,?,?,?)",
                           (cliente.get("nombre", "").strip() or None, cliente.get("telefono", "").strip() or None,
                            cliente.get("direccion", "").strip() or None, cliente.get("cedula", "").strip() or None))
            cliente_id = cursor.lastrowid

        pagos_detalle_json = None
        if metodo_pago == "mixto":
            if not pagos_detalle or not isinstance(pagos_detalle, dict):
                raise ValueError("Debe indicar el desglose de pagos para una venta mixta.")
            pagos_detalle_json = json.dumps(pagos_detalle, ensure_ascii=False)
            monto_recibido_bs = float(pagos_detalle.get("efectivo_bs") or 0)
            monto_recibido_usd = float(pagos_detalle.get("divisas_usd") or 0)
            vuelto_bs = float(pagos_detalle.get("vuelto_bs") or 0)
            vuelto_usd = float(pagos_detalle.get("vuelto_usd") or 0)
            fiado_portion = float(pagos_detalle.get("fiado_bs") or 0)
            if fiado_portion > 0 and (cliente_id is None or not str(cliente.get("nombre", "")).strip()):
                raise ValueError("Para la porción de venta fiada debe indicar el nombre del cliente.")
        elif metodo_pago == "efectivo" and not es_fiada:
            if monto_recibido_bs is None:
                raise ValueError("Debe indicar el monto recibido en efectivo.")
            monto_recibido_bs = float(monto_recibido_bs)
            if monto_recibido_bs < total_bs:
                raise ValueError("El efectivo recibido no alcanza para cubrir el total.")
            vuelto_bs = monto_recibido_bs - total_bs
        elif metodo_pago == "divisas" and not es_fiada:
            if monto_recibido_usd is None:
                raise ValueError("Debe indicar el monto recibido en divisas.")
            monto_recibido_usd = float(monto_recibido_usd)
            if monto_recibido_usd < total_usd:
                raise ValueError("Las divisas recibidas no alcanzan para cubrir el total.")
            vuelto_usd = monto_recibido_usd - total_usd
            vuelto_bs = vuelto_usd * rate
        else:
            monto_recibido_bs = None
            monto_recibido_usd = None

        if es_fiada and (cliente_id is None or not str(cliente.get("nombre", "")).strip()):
            raise ValueError("Para una venta fiada debe indicar el nombre del cliente.")

        cursor.execute(
            """
            INSERT INTO sales
                (numero_factura, usuario_id, tasa_utilizada, total_usd, total_bs,
                 metodo_pago, monto_recibido_bs, vuelto_bs, monto_recibido_usd,
                 vuelto_usd, cliente_id, es_fiada, pagos_detalle)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (invoice_number, usuario_id, rate, total_usd, total_bs,
             metodo_pago, monto_recibido_bs, vuelto_bs, monto_recibido_usd,
             vuelto_usd, cliente_id, int(es_fiada), pagos_detalle_json),
        )
        sale_id = cursor.lastrowid
        if es_fiada:
            cursor.execute("INSERT INTO credit_debts(venta_id, cliente_id, total_bs, saldo_bs) VALUES(?,?,?,?)",
                           (sale_id, cliente_id, total_bs, total_bs))
        elif metodo_pago == "mixto" and pagos_detalle and float(pagos_detalle.get("fiado_bs") or 0) > 0:
            fiado_saldo = float(pagos_detalle["fiado_bs"])
            cursor.execute("INSERT INTO credit_debts(venta_id, cliente_id, total_bs, saldo_bs) VALUES(?,?,?,?)",
                           (sale_id, cliente_id, fiado_saldo, fiado_saldo))

        for item in items:
            subtotal = item["cantidad"] * item["precio_usd"]
            cursor.execute(
                """
                INSERT INTO sale_items
                    (venta_id, producto_id, cantidad, precio_usd, subtotal_usd)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sale_id, item["producto_id"], item["cantidad"], item["precio_usd"], subtotal),
            )
            cursor.execute(
                """
                INSERT INTO inventory_movements
                    (producto_id, tipo, cantidad, motivo, venta_id, usuario_id)
                VALUES (?, 'salida', ?, ?, ?, ?)
                """,
                (item["producto_id"], item["cantidad"], f"Venta #{invoice_number}", sale_id, usuario_id),
            )

        client_name = None
        if cliente_id:
            c_row = cursor.execute("SELECT nombre FROM clients WHERE id=?", (cliente_id,)).fetchone()
            if c_row: client_name = c_row["nombre"]

        queue_event_with_connection(connection, "venta_registrada", {
            "numero_factura": invoice_number, "tasa": rate, "total_usd": total_usd,
            "total_bs": total_bs, "metodo_pago": metodo_pago,
            "monto_recibido_bs": monto_recibido_bs, "monto_recibido_usd": monto_recibido_usd,
            "vuelto_bs": vuelto_bs, "vuelto_usd": vuelto_usd,
            "cliente_nombre": client_name,
            "es_fiada": bool(es_fiada),
            "saldo_pendiente": total_bs if es_fiada else (float(pagos_detalle.get("fiado_bs") or 0) if (metodo_pago == "mixto" and pagos_detalle) else 0),
            "pagos_detalle": pagos_detalle,
            "productos": [
                {"codigo": cursor.execute("SELECT codigo FROM products WHERE id=?", (item["producto_id"],)).fetchone()["codigo"],
                 "cantidad": item["cantidad"], "precio_usd": item["precio_usd"]}
                for item in items
            ],
        })
        connection.commit()
        return {
            "venta_id": sale_id,
            "numero_factura": invoice_number,
            "tasa": rate,
            "total_usd": total_usd,
            "total_bs": total_bs,
            "metodo_pago": metodo_pago,
            "vuelto_bs": vuelto_bs,
            "vuelto_usd": vuelto_usd,
            "pagos_detalle": pagos_detalle,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_sales_history():
    connection = get_connection()
    try:
        return connection.execute(
            """
            SELECT s.id, s.numero_factura, u.nombre AS usuario_nombre, c.nombre AS cliente_nombre,
                   s.tasa_utilizada, s.total_usd, s.total_bs, s.metodo_pago,
                   s.vuelto_bs, s.fecha, s.estado, s.es_fiada,
                   COALESCE(d.saldo_bs, 0) AS saldo_pendiente
            FROM sales s
            LEFT JOIN users u ON s.usuario_id = u.id
            LEFT JOIN clients c ON s.cliente_id = c.id
            LEFT JOIN credit_debts d ON d.venta_id = s.id
            ORDER BY s.id DESC
            """
        ).fetchall()
    finally:
        connection.close()


def get_credit_debts():
    connection = get_connection()
    try:
        return connection.execute("""SELECT d.id, c.nombre, c.telefono, s.numero_factura, d.total_bs, d.saldo_bs, d.estado, s.fecha
            FROM credit_debts d JOIN clients c ON c.id=d.cliente_id JOIN sales s ON s.id=d.venta_id ORDER BY d.id DESC""").fetchall()
    finally: connection.close()


def register_debt_payment(deuda_id, monto_bs):
    monto_bs = float(monto_bs)
    if monto_bs <= 0: raise ValueError("El pago debe ser mayor que cero.")
    connection = get_connection()
    try:
        debt = connection.execute(
            """SELECT d.id, d.saldo_bs, s.numero_factura, c.nombre AS cliente_nombre
               FROM credit_debts d
               JOIN sales s ON s.id = d.venta_id
               JOIN clients c ON c.id = d.cliente_id
               WHERE d.id = ?""",
            (deuda_id,)
        ).fetchone()
        if debt is None: raise ValueError("La deuda no existe.")
        if monto_bs > float(debt["saldo_bs"]): raise ValueError("El pago supera el saldo pendiente.")
        saldo = float(debt["saldo_bs"]) - monto_bs
        connection.execute("INSERT INTO debt_payments(deuda_id,monto_bs) VALUES(?,?)", (deuda_id, monto_bs))
        connection.execute("UPDATE credit_debts SET saldo_bs=?, estado=? WHERE id=?", (saldo, "pagada" if saldo == 0 else "pendiente", deuda_id))
        queue_event_with_connection(connection, "abono_deuda", {
            "numero_factura": str(debt["numero_factura"]),
            "cliente_nombre": str(debt["cliente_nombre"]),
            "monto_bs": monto_bs,
            "saldo_restante_bs": saldo,
        })
        connection.commit(); return saldo
    finally: connection.close()


def get_debt_payments(deuda_id):
    connection = get_connection()
    try: return connection.execute("SELECT monto_bs, fecha FROM debt_payments WHERE deuda_id=? ORDER BY id DESC", (deuda_id,)).fetchall()
    finally: connection.close()


def get_sales_summary(usuario_id=None):
    connection = get_connection()
    try:
        where = ["date(s.fecha, 'localtime') = date('now', 'localtime')", "s.estado = 'completada'"]
        parameters = []
        if usuario_id is not None:
            where.append("s.usuario_id = ?")
            parameters.append(usuario_id)
        return connection.execute(
            "SELECT COUNT(*) AS cantidad_ventas, COALESCE(SUM(total_usd), 0) AS total_usd, COALESCE(SUM(total_bs), 0) AS total_bs FROM sales s WHERE " + " AND ".join(where),
            parameters,
        ).fetchone()
    finally:
        connection.close()
