import csv
from database.connection import get_connection


def get_sales_report(fecha_inicio=None, fecha_fin=None, usuario_id=None):
    connection = get_connection()
    try:
        where = ["s.estado = 'completada'"]
        params = []

        if fecha_inicio:
            where.append("date(s.fecha, 'localtime') >= date(?)")
            params.append(fecha_inicio)
        if fecha_fin:
            where.append("date(s.fecha, 'localtime') <= date(?)")
            params.append(fecha_fin)
        if usuario_id is not None:
            where.append("s.usuario_id = ?")
            params.append(usuario_id)

        sql = f"""
            SELECT s.id, s.numero_factura, s.fecha, u.nombre AS usuario_nombre,
                   c.nombre AS cliente_nombre, s.metodo_pago, s.tasa_utilizada,
                   s.total_usd, s.total_bs, s.vuelto_bs, s.vuelto_usd, s.es_fiada,
                   COALESCE(d.saldo_bs, 0) AS saldo_pendiente
            FROM sales s
            LEFT JOIN users u ON s.usuario_id = u.id
            LEFT JOIN clients c ON s.cliente_id = c.id
            LEFT JOIN credit_debts d ON d.venta_id = s.id
            WHERE {" AND ".join(where)}
            ORDER BY s.id DESC
        """
        rows = connection.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()


def get_financial_kpis(fecha_inicio=None, fecha_fin=None):
    connection = get_connection()
    try:
        where = ["s.estado = 'completada'"]
        params = []
        if fecha_inicio:
            where.append("date(s.fecha, 'localtime') >= date(?)")
            params.append(fecha_inicio)
        if fecha_fin:
            where.append("date(s.fecha, 'localtime') <= date(?)")
            params.append(fecha_fin)

        where_clause = " AND ".join(where)

        # Totals
        row_totals = connection.execute(
            f"""
            SELECT COUNT(*) AS total_transacciones,
                   COALESCE(SUM(s.total_bs), 0) AS total_ventas_bs,
                   COALESCE(SUM(s.total_usd), 0) AS total_ventas_usd
            FROM sales s
            WHERE {where_clause}
            """,
            params,
        ).fetchone()

        # Breakdown by payment method
        methods_rows = connection.execute(
            f"""
            SELECT s.metodo_pago, s.es_fiada,
                   COUNT(*) AS cantidad,
                   COALESCE(SUM(s.total_bs), 0) AS total_bs,
                   COALESCE(SUM(s.total_usd), 0) AS total_usd
            FROM sales s
            WHERE {where_clause}
            GROUP BY s.metodo_pago, s.es_fiada
            """,
            params,
        ).fetchall()

        metodos = {
            "efectivo": 0.0,
            "tarjeta": 0.0,
            "pago_movil": 0.0,
            "divisas_usd": 0.0,
            "divisas_bs": 0.0,
            "fiado": 0.0,
        }

        for m in methods_rows:
            metodo = m["metodo_pago"]
            t_bs = float(m["total_bs"] or 0)
            t_usd = float(m["total_usd"] or 0)
            if m["es_fiada"] or metodo == "fiado":
                metodos["fiado"] += t_bs
            elif metodo == "efectivo":
                metodos["efectivo"] += t_bs
            elif metodo == "tarjeta":
                metodos["tarjeta"] += t_bs
            elif metodo == "pago_movil":
                metodos["pago_movil"] += t_bs
            elif metodo == "divisas":
                metodos["divisas_usd"] += t_usd
                metodos["divisas_bs"] += t_bs

        # Cost and Profit Estimation
        cost_row = connection.execute(
            f"""
            SELECT COALESCE(SUM(si.cantidad * p.costo_usd), 0) AS costo_total_usd,
                   COALESCE(SUM(si.subtotal_usd), 0) AS venta_total_usd
            FROM sale_items si
            JOIN sales s ON s.id = si.venta_id
            JOIN products p ON p.id = si.producto_id
            WHERE {where_clause}
            """,
            params,
        ).fetchone()

        costo_total_usd = float(cost_row["costo_total_usd"] or 0)
        venta_items_usd = float(cost_row["venta_total_usd"] or 0)
        ganancia_bruta_usd = max(0, venta_items_usd - costo_total_usd) if costo_total_usd > 0 else venta_items_usd

        # Pending debts
        debts_row = connection.execute(
            "SELECT COALESCE(SUM(saldo_bs), 0) AS total_deudas_bs FROM credit_debts WHERE estado = 'pendiente'"
        ).fetchone()
        total_deudas_bs = float(debts_row["total_deudas_bs"] or 0)

        total_transacciones = int(row_totals["total_transacciones"] or 0)
        total_ventas_bs = float(row_totals["total_ventas_bs"] or 0)
        total_ventas_usd = float(row_totals["total_ventas_usd"] or 0)
        ticket_promedio_bs = total_ventas_bs / total_transacciones if total_transacciones > 0 else 0
        ticket_promedio_usd = total_ventas_usd / total_transacciones if total_transacciones > 0 else 0

        return {
            "total_transacciones": total_transacciones,
            "total_ventas_bs": total_ventas_bs,
            "total_ventas_usd": total_ventas_usd,
            "ticket_promedio_bs": ticket_promedio_bs,
            "ticket_promedio_usd": ticket_promedio_usd,
            "costo_total_usd": costo_total_usd,
            "ganancia_bruta_usd": ganancia_bruta_usd,
            "metodos_pago": metodos,
            "total_deudas_bs": total_deudas_bs,
        }
    finally:
        connection.close()


def get_top_selling_products(fecha_inicio=None, fecha_fin=None, limit=10):
    connection = get_connection()
    try:
        where = ["s.estado = 'completada'"]
        params = []
        if fecha_inicio:
            where.append("date(s.fecha, 'localtime') >= date(?)")
            params.append(fecha_inicio)
        if fecha_fin:
            where.append("date(s.fecha, 'localtime') <= date(?)")
            params.append(fecha_fin)

        params.append(limit)
        where_clause = " AND ".join(where)

        rows = connection.execute(
            f"""
            SELECT p.id, p.codigo, p.nombre, p.unidad,
                   COALESCE(SUM(si.cantidad), 0) AS unidades_vendidas,
                   COALESCE(SUM(si.subtotal_usd), 0) AS total_usd
            FROM sale_items si
            JOIN sales s ON s.id = si.venta_id
            JOIN products p ON p.id = si.producto_id
            WHERE {where_clause}
            GROUP BY p.id, p.codigo, p.nombre, p.unidad
            ORDER BY unidades_vendidas DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()


def get_critical_stock_report():
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT p.id, p.codigo, p.nombre, p.unidad, p.stock_minimo,
                   COALESCE(SUM(CASE
                       WHEN im.tipo = 'entrada' THEN im.cantidad
                       WHEN im.tipo = 'salida' THEN -im.cantidad
                       WHEN im.tipo = 'ajuste' THEN im.cantidad
                       ELSE 0 END), 0) AS stock_actual
            FROM products p
            LEFT JOIN inventory_movements im ON p.id = im.producto_id
            WHERE p.activo = 1
            GROUP BY p.id, p.codigo, p.nombre, p.unidad, p.stock_minimo
            HAVING stock_actual <= p.stock_minimo
            ORDER BY stock_actual ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()


def export_sales_to_csv(filepath, fecha_inicio=None, fecha_fin=None):
    sales = get_sales_report(fecha_inicio, fecha_fin)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Factura",
            "Fecha y Hora",
            "Vendedor",
            "Cliente",
            "Metodo de Pago",
            "Tasa USD/Bs",
            "Total USD",
            "Total Bs",
            "Es Fiada",
            "Saldo Pendiente Bs",
        ])
        for s in sales:
            writer.writerow([
                s["numero_factura"],
                s["fecha"],
                s["usuario_nombre"] or "",
                s["cliente_nombre"] or "Consumidor Final",
                s["metodo_pago"],
                f"{float(s['tasa_utilizada']):,.2f}",
                f"{float(s['total_usd']):,.2f}",
                f"{float(s['total_bs']):,.2f}",
                "Si" if s["es_fiada"] else "No",
                f"{float(s['saldo_pendiente']):,.2f}",
            ])
    return filepath
