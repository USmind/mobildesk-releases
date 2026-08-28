import json
from database.connection import get_connection
from modules.configuracion.business_service import get_business_settings


def get_sale_ticket_data(sale_id_or_invoice):
    connection = get_connection()
    try:
        if isinstance(sale_id_or_invoice, int):
            sale = connection.execute(
                """
                SELECT s.*, u.nombre AS usuario_nombre,
                       c.nombre AS cliente_nombre, c.cedula AS cliente_cedula,
                       c.telefono AS cliente_telefono, c.direccion AS cliente_direccion,
                       d.saldo_bs AS deuda_saldo_bs
                FROM sales s
                LEFT JOIN users u ON s.usuario_id = u.id
                LEFT JOIN clients c ON s.cliente_id = c.id
                LEFT JOIN credit_debts d ON d.venta_id = s.id
                WHERE s.id = ?
                """,
                (sale_id_or_invoice,),
            ).fetchone()
        else:
            sale = connection.execute(
                """
                SELECT s.*, u.nombre AS usuario_nombre,
                       c.nombre AS cliente_nombre, c.cedula AS cliente_cedula,
                       c.telefono AS cliente_telefono, c.direccion AS cliente_direccion,
                       d.saldo_bs AS deuda_saldo_bs
                FROM sales s
                LEFT JOIN users u ON s.usuario_id = u.id
                LEFT JOIN clients c ON s.cliente_id = c.id
                LEFT JOIN credit_debts d ON d.venta_id = s.id
                WHERE s.numero_factura = ?
                """,
                (str(sale_id_or_invoice),),
            ).fetchone()

        if not sale:
            raise ValueError("Venta no encontrada.")

        sale = dict(sale)
        items = connection.execute(
            """
            SELECT si.*, p.codigo AS producto_codigo, p.nombre AS producto_nombre, p.unidad
            FROM sale_items si
            JOIN products p ON p.id = si.producto_id
            WHERE si.venta_id = ?
            ORDER BY si.id
            """,
            (sale["id"],),
        ).fetchall()

        sale["items"] = [dict(i) for i in items]
        sale["business"] = get_business_settings()
        return sale
    finally:
        connection.close()


def generate_sale_ticket_text(sale_id_or_invoice, width=42):
    data = get_sale_ticket_data(sale_id_or_invoice)
    biz = data["business"]
    line = "=" * width
    dline = "-" * width

    output = []
    # Header
    output.append(biz["nombre_negocio"].center(width))
    if biz.get("identificacion"):
        output.append(f"RIF/CI: {biz['identificacion']}".center(width))
    if biz.get("direccion"):
        output.append(biz["direccion"][:width].center(width))
    if biz.get("telefono"):
        output.append(f"Tel: {biz['telefono']}".center(width))

    output.append(line)
    output.append(f"FACTURA N°: {data['numero_factura']}".ljust(width))
    output.append(f"FECHA: {data['fecha']}".ljust(width))
    output.append(f"CAJERO: {data['usuario_nombre'] or 'General'}".ljust(width))

    if data.get("cliente_nombre"):
        output.append(f"CLIENTE: {data['cliente_nombre']}".ljust(width))
        if data.get("cliente_cedula"):
            output.append(f"CÉDULA: {data['cliente_cedula']}".ljust(width))

    output.append(dline)
    # Items
    output.append(f"{'CANT':<6}{'DESCRIPCION':<20}{'PRECIO':>8}{'TOTAL':>8}")
    output.append(dline)

    tasa = float(data["tasa_utilizada"] or 1)

    for item in data["items"]:
        qty = float(item["cantidad"])
        precio_bs = float(item["precio_usd"]) * tasa
        subtotal_bs = float(item["subtotal_usd"]) * tasa
        qty_str = f"{qty:g}"
        name = item["producto_nombre"][:18]
        output.append(f"{qty_str:<6}{name:<20}{precio_bs:>8.2f}{subtotal_bs:>8.2f}")

    output.append(dline)

    # Totals
    total_bs = float(data["total_bs"])
    total_usd = float(data["total_usd"])
    output.append(f"{'TOTAL BS:':<24}{total_bs:>18,.2f}")
    output.append(f"{'TOTAL USD:':<24}{f'${total_usd:,.2f}':>18}")
    output.append(f"{'TASA USD/BS:':<24}{f'{tasa:,.2f}':>18}")
    output.append(dline)

    if data.get("metodo_pago") == "mixto":
        output.append("MÉTODO DE PAGO: MIXTO / FRACCIONADO")
        det = {}
        if data.get("pagos_detalle"):
            try:
                det = json.loads(data["pagos_detalle"]) if isinstance(data["pagos_detalle"], str) else data["pagos_detalle"]
            except Exception:
                det = {}
        if det.get("divisas_usd"):
            usd_val = float(det["divisas_usd"])
            bs_eq = float(det.get("divisas_bs") or (usd_val * tasa))
            output.append(f"  - Divisas ($):  ${usd_val:,.2f} (Bs {bs_eq:,.2f})")
        if det.get("efectivo_bs"):
            output.append(f"  - Efectivo:     Bs {float(det['efectivo_bs']):,.2f}")
        if det.get("pago_movil_bs"):
            output.append(f"  - Pago Móvil:   Bs {float(det['pago_movil_bs']):,.2f}")
        if det.get("tarjeta_bs"):
            output.append(f"  - Tarjeta:      Bs {float(det['tarjeta_bs']):,.2f}")
        if det.get("fiado_bs"):
            output.append(f"  - Fiado:        Bs {float(det['fiado_bs']):,.2f}")
        vuelto = float(data.get("vuelto_bs") or det.get("vuelto_bs") or 0)
        vuelto_usd = float(data.get("vuelto_usd") or det.get("vuelto_usd") or 0)
        if vuelto > 0 or vuelto_usd > 0:
            if vuelto > 0:
                output.append(f"  VUELTO BS:      Bs {vuelto:,.2f}")
            if vuelto_usd > 0:
                output.append(f"  VUELTO USD:     ${vuelto_usd:,.2f}")
    elif data["es_fiada"]:
        saldo = float(data.get("deuda_saldo_bs") or total_bs)
        output.append(f"ESTADO: FIADO (Pendiente Bs {saldo:,.2f})")
    elif data["metodo_pago"] == "efectivo":
        recibido = float(data["monto_recibido_bs"] or total_bs)
        vuelto = float(data["vuelto_bs"] or 0)
        output.append(f"RECIBIDO BS: {recibido:>18,.2f}")
        output.append(f"VUELTO BS:   {vuelto:>18,.2f}")
    elif data["metodo_pago"] == "divisas":
        recibido_usd = float(data["monto_recibido_usd"] or total_usd)
        vuelto_usd = float(data["vuelto_usd"] or 0)
        output.append(f"RECIBIDO USD: ${recibido_usd:>17,.2f}")
        output.append(f"VUELTO USD:   ${vuelto_usd:>17,.2f}")
        if vuelto_usd > 0:
            output.append(f"VUELTO BS:    {vuelto_usd * tasa:>17,.2f}")
    else:
        metodo = data["metodo_pago"].replace("_", " ").title()
        output.append(f"MÉTODO DE PAGO: {metodo}")

    output.append(line)
    output.append((biz.get("mensaje_ticket") or "¡Gracias por su compra!").center(width))
    output.append("\n")

    return "\n".join(output)


def generate_ticket_html(sale_id_or_invoice):
    data = get_sale_ticket_data(sale_id_or_invoice)
    biz = data["business"]
    tasa = float(data["tasa_utilizada"] or 1)
    total_bs = float(data["total_bs"])
    total_usd = float(data["total_usd"])

    items_html = ""
    for item in data["items"]:
        qty = float(item["cantidad"])
        precio_bs = float(item["precio_usd"]) * tasa
        subtotal_bs = float(item["subtotal_usd"]) * tasa
        items_html += f"""
        <tr>
            <td style="text-align:left;">{item['producto_nombre']}<br><small style="color:#666;">{qty:g} {item['unidad']} x Bs {precio_bs:,.2f}</small></td>
            <td style="text-align:right; vertical-align:top; font-weight:600;">Bs {subtotal_bs:,.2f}</td>
        </tr>
        """

    if data.get("metodo_pago") == "mixto":
        pago_detalle = "<p><strong>Método:</strong> Pago Mixto / Fraccionado</p><ul style='margin:4px 0; padding-left:18px; font-size:12px;'>"
        det = {}
        if data.get("pagos_detalle"):
            try:
                det = json.loads(data["pagos_detalle"]) if isinstance(data["pagos_detalle"], str) else data["pagos_detalle"]
            except Exception:
                det = {}
        if det.get("divisas_usd"):
            usd_val = float(det["divisas_usd"])
            bs_eq = float(det.get("divisas_bs") or (usd_val * tasa))
            pago_detalle += f"<li>Divisas ($): ${usd_val:,.2f} (Bs {bs_eq:,.2f})</li>"
        if det.get("efectivo_bs"):
            pago_detalle += f"<li>Efectivo: Bs {float(det['efectivo_bs']):,.2f}</li>"
        if det.get("pago_movil_bs"):
            pago_detalle += f"<li>Pago Móvil: Bs {float(det['pago_movil_bs']):,.2f}</li>"
        if det.get("tarjeta_bs"):
            pago_detalle += f"<li>Tarjeta: Bs {float(det['tarjeta_bs']):,.2f}</li>"
        if det.get("fiado_bs"):
            pago_detalle += f"<li>Fiado: Bs {float(det['fiado_bs']):,.2f}</li>"
        pago_detalle += "</ul>"
        vuelto = float(data.get("vuelto_bs") or det.get("vuelto_bs") or 0)
        vuelto_usd = float(data.get("vuelto_usd") or det.get("vuelto_usd") or 0)
        if vuelto > 0 or vuelto_usd > 0:
            pago_detalle += f"<p><strong>Vuelto:</strong> Bs {vuelto:,.2f}" + (f" (${vuelto_usd:,.2f})" if vuelto_usd > 0 else "") + "</p>"
    elif data["es_fiada"]:
        pago_detalle = f"<p><strong>Método:</strong> Fiado</p><p style='color:#b91c1c;'><strong>Condición:</strong> FIADO (Pendiente)</p>"
    elif data["metodo_pago"] == "efectivo":
        recibido = float(data["monto_recibido_bs"] or total_bs)
        vuelto = float(data["vuelto_bs"] or 0)
        pago_detalle = f"<p><strong>Método:</strong> Efectivo</p><p>Recibido: Bs {recibido:,.2f} | Vuelto: Bs {vuelto:,.2f}</p>"
    elif data["metodo_pago"] == "divisas":
        recibido_usd = float(data["monto_recibido_usd"] or total_usd)
        vuelto_usd = float(data["vuelto_usd"] or 0)
        pago_detalle = f"<p><strong>Método:</strong> Divisas</p><p>Recibido: USD ${recibido_usd:,.2f} | Vuelto: USD ${vuelto_usd:,.2f} (Bs {vuelto_usd * tasa:,.2f})</p>"
    else:
        metodo_str = data["metodo_pago"].replace("_", " ").title()
        pago_detalle = f"<p><strong>Método:</strong> {metodo_str}</p>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Courier New', monospace; font-size: 13px; color: #111; margin: 0; padding: 10px; background: white; }}
  .ticket {{ max-width: 320px; margin: auto; padding: 12px; border: 1px dashed #ccc; }}
  .center {{ text-align: center; }}
  .bold {{ font-weight: bold; }}
  .divider {{ border-top: 1px dashed #999; margin: 8px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: 3px 0; font-size: 12px; }}
  .totals {{ font-size: 14px; font-weight: bold; }}
  p {{ margin: 3px 0; }}
</style>
</head>
<body>
<div class="ticket">
  <div class="center">
    <h2 style="margin:0 0 4px; font-size:18px;">{biz['nombre_negocio']}</h2>
    {f"<p>RIF/CI: {biz['identificacion']}</p>" if biz.get('identificacion') else ''}
    {f"<p>{biz['direccion']}</p>" if biz.get('direccion') else ''}
    {f"<p>Tel: {biz['telefono']}</p>" if biz.get('telefono') else ''}
  </div>
  <div class="divider"></div>
  <p><strong>Factura:</strong> {data['numero_factura']}</p>
  <p><strong>Fecha:</strong> {data['fecha']}</p>
  <p><strong>Cajero:</strong> {data['usuario_nombre'] or 'Principal'}</p>
  {f"<p><strong>Cliente:</strong> {data['cliente_nombre']}</p>" if data.get('cliente_nombre') else ''}
  <div class="divider"></div>
  <table>
    {items_html}
  </table>
  <div class="divider"></div>
  <table>
    <tr class="totals"><td>TOTAL BS:</td><td style="text-align:right;">Bs {total_bs:,.2f}</td></tr>
    <tr><td>TOTAL USD:</td><td style="text-align:right;">${total_usd:,.2f}</td></tr>
    <tr><td>Tasa:</td><td style="text-align:right;">Bs {tasa:,.2f}</td></tr>
  </table>
  <div class="divider"></div>
  {pago_detalle}
  <div class="divider"></div>
  <div class="center" style="margin-top:10px; font-style:italic;">
    <p>{biz.get('mensaje_ticket') or '¡Gracias por su compra!'}</p>
  </div>
</div>
</body>
</html>"""
    return html
