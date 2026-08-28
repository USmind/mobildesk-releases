import json
from database.connection import get_connection


def get_open_cash_register(usuario_id=None):
    connection = get_connection()
    try:
        if usuario_id is not None:
            row = connection.execute(
                """
                SELECT cr.*, u.nombre AS usuario_nombre
                FROM cash_registers cr
                JOIN users u ON u.id = cr.usuario_id
                WHERE cr.estado = 'abierta' AND cr.usuario_id = ?
                ORDER BY cr.id DESC LIMIT 1
                """,
                (usuario_id,),
            ).fetchone()
            if row:
                return dict(row)
        row = connection.execute(
            """
            SELECT cr.*, u.nombre AS usuario_nombre
            FROM cash_registers cr
            JOIN users u ON u.id = cr.usuario_id
            WHERE cr.estado = 'abierta'
            ORDER BY cr.id DESC LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def open_cash_register(usuario_id, monto_inicial_bs=0.0, monto_inicial_usd=0.0, observaciones=""):
    monto_inicial_bs = float(monto_inicial_bs or 0)
    monto_inicial_usd = float(monto_inicial_usd or 0)

    if monto_inicial_bs < 0 or monto_inicial_usd < 0:
        raise ValueError("Los montos iniciales no pueden ser negativos.")

    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT id FROM cash_registers WHERE estado = 'abierta' AND usuario_id = ?",
            (usuario_id,),
        ).fetchone()
        if existing:
            raise ValueError("Ya tienes una caja abierta. Debes cerrarla antes de abrir una nueva.")

        cursor = connection.execute(
            """
            INSERT INTO cash_registers (usuario_id, monto_inicial_bs, monto_inicial_usd, estado, observaciones)
            VALUES (?, ?, ?, 'abierta', ?)
            """,
            (usuario_id, monto_inicial_bs, monto_inicial_usd, observaciones.strip()),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def add_cash_movement(caja_id, usuario_id, tipo, moneda, monto, motivo):
    monto = float(monto or 0)
    if monto <= 0:
        raise ValueError("El monto del movimiento debe ser mayor a cero.")
    if tipo not in ("entrada", "salida", "gasto"):
        raise ValueError("El tipo de movimiento debe ser 'entrada', 'salida' o 'gasto'.")
    if moneda not in ("Bs", "USD"):
        raise ValueError("La moneda debe ser 'Bs' o 'USD'.")
    if not motivo or not motivo.strip():
        raise ValueError("Debe especificar el motivo del movimiento.")

    connection = get_connection()
    try:
        caja = connection.execute(
            "SELECT id, estado FROM cash_registers WHERE id = ?", (caja_id,)
        ).fetchone()
        if not caja:
            raise ValueError("La caja especificada no existe.")
        if caja["estado"] != "abierta":
            raise ValueError("No se pueden registrar movimientos en una caja cerrada.")

        cursor = connection.execute(
            """
            INSERT INTO cash_movements (caja_id, usuario_id, tipo, moneda, monto, motivo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (caja_id, usuario_id, tipo, moneda, monto, motivo.strip()),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_cash_movements(caja_id):
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT cm.*, u.nombre AS usuario_nombre
            FROM cash_movements cm
            JOIN users u ON u.id = cm.usuario_id
            WHERE cm.caja_id = ?
            ORDER BY cm.id DESC
            """,
            (caja_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()


def get_cash_register_summary(caja_id):
    connection = get_connection()
    try:
        caja = connection.execute(
            """
            SELECT cr.*, u.nombre AS usuario_nombre
            FROM cash_registers cr
            JOIN users u ON u.id = cr.usuario_id
            WHERE cr.id = ?
            """,
            (caja_id,),
        ).fetchone()
        if not caja:
            raise ValueError("Caja no encontrada.")

        caja = dict(caja)
        fecha_apertura = caja["fecha_apertura"]
        fecha_cierre = caja["fecha_cierre"]
        usuario_id = caja["usuario_id"]

        # Sales during cash register period
        if fecha_cierre:
            sales_rows = connection.execute(
                """
                SELECT metodo_pago, total_bs, total_usd, monto_recibido_bs, vuelto_bs, monto_recibido_usd, vuelto_usd, es_fiada, pagos_detalle
                FROM sales
                WHERE usuario_id = ? AND fecha >= ? AND fecha <= ? AND estado = 'completada'
                """,
                (usuario_id, fecha_apertura, fecha_cierre),
            ).fetchall()
        else:
            sales_rows = connection.execute(
                """
                SELECT metodo_pago, total_bs, total_usd, monto_recibido_bs, vuelto_bs, monto_recibido_usd, vuelto_usd, es_fiada, pagos_detalle
                FROM sales
                WHERE usuario_id = ? AND fecha >= ? AND estado = 'completada'
                """,
                (usuario_id, fecha_apertura),
            ).fetchall()

        ventas_por_metodo = {
            "efectivo": 0.0,
            "tarjeta": 0.0,
            "pago_movil": 0.0,
            "divisas_usd": 0.0,
            "divisas_bs": 0.0,
            "fiado": 0.0,
        }
        total_ventas_bs = 0.0
        total_ventas_usd = 0.0
        cantidad_ventas = len(sales_rows)

        for s in sales_rows:
            metodo = s["metodo_pago"]
            t_bs = float(s["total_bs"] or 0)
            t_usd = float(s["total_usd"] or 0)
            total_ventas_bs += t_bs
            total_ventas_usd += t_usd

            if metodo == "mixto" and s["pagos_detalle"]:
                try:
                    det = json.loads(s["pagos_detalle"]) if isinstance(s["pagos_detalle"], str) else s["pagos_detalle"]
                except Exception:
                    det = {}
                ventas_por_metodo["efectivo"] += float(det.get("efectivo_bs") or 0)
                ventas_por_metodo["tarjeta"] += float(det.get("tarjeta_bs") or 0)
                ventas_por_metodo["pago_movil"] += float(det.get("pago_movil_bs") or 0)
                usd_val = float(det.get("divisas_usd") or 0)
                bs_val = float(det.get("divisas_bs") or 0)
                ventas_por_metodo["divisas_usd"] += usd_val
                ventas_por_metodo["divisas_bs"] += bs_val
                ventas_por_metodo["fiado"] += float(det.get("fiado_bs") or 0)
            elif s["es_fiada"] or metodo == "fiado":
                ventas_por_metodo["fiado"] += t_bs
            elif metodo == "efectivo":
                ventas_por_metodo["efectivo"] += t_bs
            elif metodo == "tarjeta":
                ventas_por_metodo["tarjeta"] += t_bs
            elif metodo == "pago_movil":
                ventas_por_metodo["pago_movil"] += t_bs
            elif metodo == "divisas":
                ventas_por_metodo["divisas_usd"] += t_usd
                ventas_por_metodo["divisas_bs"] += t_bs

        # Movements
        movements = get_cash_movements(caja_id)
        entradas_bs = sum(m["monto"] for m in movements if m["tipo"] == "entrada" and m["moneda"] == "Bs")
        entradas_usd = sum(m["monto"] for m in movements if m["tipo"] == "entrada" and m["moneda"] == "USD")
        salidas_bs = sum(m["monto"] for m in movements if m["tipo"] in ("salida", "gasto") and m["moneda"] == "Bs")
        salidas_usd = sum(m["monto"] for m in movements if m["tipo"] in ("salida", "gasto") and m["moneda"] == "USD")

        monto_inicial_bs = float(caja["monto_inicial_bs"] or 0)
        monto_inicial_usd = float(caja["monto_inicial_usd"] or 0)

        # Expected in drawer
        esperado_bs = monto_inicial_bs + ventas_por_metodo["efectivo"] + entradas_bs - salidas_bs
        esperado_usd = monto_inicial_usd + ventas_por_metodo["divisas_usd"] + entradas_usd - salidas_usd

        return {
            "caja": caja,
            "cantidad_ventas": cantidad_ventas,
            "total_ventas_bs": total_ventas_bs,
            "total_ventas_usd": total_ventas_usd,
            "ventas_por_metodo": ventas_por_metodo,
            "entradas_bs": entradas_bs,
            "entradas_usd": entradas_usd,
            "salidas_bs": salidas_bs,
            "salidas_usd": salidas_usd,
            "esperado_bs": esperado_bs,
            "esperado_usd": esperado_usd,
            "movements": movements,
        }
    finally:
        connection.close()


def close_cash_register(caja_id, monto_final_bs, monto_final_usd, observaciones=""):
    monto_final_bs = float(monto_final_bs or 0)
    monto_final_usd = float(monto_final_usd or 0)

    if monto_final_bs < 0 or monto_final_usd < 0:
        raise ValueError("El monto contado no puede ser negativo.")

    summary = get_cash_register_summary(caja_id)
    esperado_bs = summary["esperado_bs"]
    esperado_usd = summary["esperado_usd"]

    diferencia_bs = monto_final_bs - esperado_bs
    diferencia_usd = monto_final_usd - esperado_usd

    connection = get_connection()
    try:
        connection.execute(
            """
            UPDATE cash_registers
            SET monto_final_bs = ?,
                monto_final_usd = ?,
                diferencia_bs = ?,
                diferencia_usd = ?,
                fecha_cierre = datetime('now', 'localtime'),
                estado = 'cerrada',
                observaciones = ?
            WHERE id = ? AND estado = 'abierta'
            """,
            (monto_final_bs, monto_final_usd, diferencia_bs, diferencia_usd, observaciones.strip(), caja_id),
        )
        connection.commit()
        return {
            "caja_id": caja_id,
            "monto_final_bs": monto_final_bs,
            "monto_final_usd": monto_final_usd,
            "esperado_bs": esperado_bs,
            "esperado_usd": esperado_usd,
            "diferencia_bs": diferencia_bs,
            "diferencia_usd": diferencia_usd,
        }
    finally:
        connection.close()


def get_cash_registers_history(limit=50):
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT cr.*, u.nombre AS usuario_nombre
            FROM cash_registers cr
            JOIN users u ON u.id = cr.usuario_id
            ORDER BY cr.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()
