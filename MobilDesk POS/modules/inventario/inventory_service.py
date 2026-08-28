from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection


# ============================================================
# OBTENER INVENTARIO
# ============================================================

def get_inventory():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                p.id,
                p.codigo,
                p.nombre,
                COALESCE(c.nombre, 'Sin categoría') AS categoria,
                p.unidad,
                p.stock_minimo,
                p.precio_usd,

                COALESCE(
                    SUM(
                        CASE
                            WHEN im.tipo = 'entrada'
                                THEN im.cantidad

                            WHEN im.tipo = 'salida'
                                THEN -im.cantidad

                            WHEN im.tipo = 'ajuste'
                                THEN im.cantidad

                            ELSE 0
                        END
                    ),
                    0
                ) AS stock_actual

            FROM products p

            LEFT JOIN categories c
                ON p.categoria_id = c.id

            LEFT JOIN inventory_movements im
                ON p.id = im.producto_id

            WHERE p.activo = 1

            GROUP BY
                p.id,
                p.codigo,
                p.nombre,
                c.nombre,
                p.unidad,
                p.stock_minimo,
                p.precio_usd

            ORDER BY p.nombre
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


# ============================================================
# OBTENER STOCK DE UN PRODUCTO
# ============================================================

def get_product_stock(producto_id):
    connection = get_connection()
    try:
        return get_product_stock_with_connection(connection, producto_id)
    finally:
        connection.close()


# ============================================================
# OBTENER STOCK USANDO UNA CONEXIÓN EXISTENTE
# ============================================================

def get_product_stock_with_connection(connection, producto_id):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN tipo = 'entrada'
                            THEN cantidad
                        WHEN tipo = 'salida'
                            THEN -cantidad
                        WHEN tipo = 'ajuste'
                            THEN cantidad
                        ELSE 0
                    END
                ),
                0
            )
        FROM inventory_movements
        WHERE producto_id = ?
        """,
        (producto_id,)
    )
    resultado = cursor.fetchone()
    return float(resultado[0] or 0)


# ============================================================
# REGISTRAR ENTRADA DE MERCANCÍA
# ============================================================

def add_inventory_entry(
    producto_id,
    cantidad,
    usuario_id,
    motivo="",
    costo_usd=0
):

    cantidad = float(cantidad)
    costo_usd = float(costo_usd)

    if cantidad <= 0:

        raise ValueError(
            "La cantidad debe ser mayor que cero."
        )

    if costo_usd < 0:
        raise ValueError("El costo por unidad no puede ser negativo.")

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Verificar que el producto existe y está activo
        cursor.execute(
            """
            SELECT id, nombre
            FROM products
            WHERE id = ?
              AND activo = 1
            """,
            (producto_id,)
        )

        producto = cursor.fetchone()

        if producto is None:

            raise ValueError(
                "El producto no existe o está inactivo."
            )

        cursor.execute(
            """
            INSERT INTO inventory_movements
            (
                producto_id,
                tipo,
                cantidad,
                costo_usd,
                motivo,
                venta_id,
                usuario_id
            )
            VALUES
            (
                ?,
                'entrada',
                ?,
                ?,
                ?,
                NULL,
                ?
            )
            """,
            (
                producto_id,
                cantidad,
                costo_usd,
                motivo.strip(),
                usuario_id
            )
        )

        codigo = cursor.execute("SELECT codigo FROM products WHERE id=?", (producto_id,)).fetchone()["codigo"]
        queue_event_with_connection(connection, "movimiento_inventario", {
            "producto_codigo": codigo, "tipo": "entrada", "cantidad": cantidad,
            "costo_usd": costo_usd, "motivo": motivo.strip(),
        })
        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# REGISTRAR AJUSTE DE INVENTARIO
#
# cantidad positiva  = aumenta stock
# cantidad negativa  = disminuye stock
# ============================================================

def add_inventory_adjustment(
    producto_id,
    cantidad,
    usuario_id,
    motivo=""
):

    cantidad = float(cantidad)

    if cantidad == 0:

        raise ValueError(
            "La cantidad del ajuste no puede ser cero."
        )

    if not motivo or not motivo.strip():

        raise ValueError(
            "Debes indicar el motivo del ajuste."
        )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Verificar producto
        cursor.execute(
            """
            SELECT id, nombre
            FROM products
            WHERE id = ?
              AND activo = 1
            """,
            (producto_id,)
        )

        producto = cursor.fetchone()

        if producto is None:

            raise ValueError(
                "El producto no existe o está inactivo."
            )

        # Obtener stock actual utilizando
        # la misma conexión de la transacción.
        stock_actual = get_product_stock_with_connection(
            connection,
            producto_id
        )

        nuevo_stock = stock_actual + cantidad

        if nuevo_stock < 0:

            raise ValueError(
                "El ajuste no puede dejar el stock negativo.\n\n"
                f"Stock actual: {stock_actual:g}\n"
                f"Ajuste: {cantidad:g}\n"
                f"Resultado: {nuevo_stock:g}"
            )

        cursor.execute(
            """
            INSERT INTO inventory_movements
            (
                producto_id,
                tipo,
                cantidad,
                motivo,
                venta_id,
                usuario_id
            )
            VALUES
            (
                ?,
                'ajuste',
                ?,
                ?,
                NULL,
                ?
            )
            """,
            (
                producto_id,
                cantidad,
                motivo.strip(),
                usuario_id
            )
        )

        codigo = cursor.execute("SELECT codigo FROM products WHERE id=?", (producto_id,)).fetchone()["codigo"]
        queue_event_with_connection(connection, "movimiento_inventario", {
            "producto_codigo": codigo, "tipo": "ajuste", "cantidad": cantidad,
            "costo_usd": None, "motivo": motivo.strip(),
        })
        connection.commit()

        return {
            "stock_anterior": stock_actual,
            "ajuste": cantidad,
            "stock_nuevo": nuevo_stock
        }

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# OBTENER HISTORIAL DE MOVIMIENTOS
# ============================================================

def get_inventory_movements(producto_id=None):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        if producto_id is None:

            cursor.execute(
                """
                SELECT
                    im.id,
                    p.codigo,
                    p.nombre,
                    im.tipo,
                    im.cantidad,
                    im.motivo,
                    u.nombre,
                    im.fecha

                FROM inventory_movements im

                INNER JOIN products p
                    ON im.producto_id = p.id

                INNER JOIN users u
                    ON im.usuario_id = u.id

                ORDER BY im.id DESC
                """
            )

        else:

            cursor.execute(
                """
                SELECT
                    im.id,
                    p.codigo,
                    p.nombre,
                    im.tipo,
                    im.cantidad,
                    im.motivo,
                    u.nombre,
                    im.fecha

                FROM inventory_movements im

                INNER JOIN products p
                    ON im.producto_id = p.id

                INNER JOIN users u
                    ON im.usuario_id = u.id

                WHERE im.producto_id = ?

                ORDER BY im.id DESC
                """,
                (producto_id,)
            )

        return cursor.fetchall()

    finally:

        connection.close()


# ============================================================
# OBTENER PRODUCTOS PARA LOS FORMULARIOS DE INVENTARIO
# ============================================================

def get_active_products():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                codigo,
                nombre,
                unidad

            FROM products

            WHERE activo = 1

            ORDER BY nombre
            """
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ============================================================
# OBTENER PRODUCTO POR ID
# ============================================================

def get_product(producto_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                p.id,
                p.codigo,
                p.nombre,
                p.unidad,
                p.stock_minimo

            FROM products p

            WHERE p.id = ?
              AND p.activo = 1
            """,
            (producto_id,)
        )

        return cursor.fetchone()

    finally:

        connection.close()


# ============================================================
# PRODUCTOS CON STOCK BAJO
# ============================================================

def get_low_stock_products():

    inventory = get_inventory()

    productos = []

    for producto in inventory:

        producto_id = producto[0]
        codigo = producto[1]
        nombre = producto[2]
        categoria = producto[3]
        unidad = producto[4]
        stock_minimo = float(producto[5] or 0)
        stock_actual = float(producto[6] or 0)

        if stock_actual <= stock_minimo:

            productos.append(
                (
                    producto_id,
                    codigo,
                    nombre,
                    categoria,
                    unidad,
                    stock_actual,
                    stock_minimo
                )
            )

    return productos


def update_inventory_movement_motivo(movimiento_id, motivo):
    connection = get_connection()
    try:
        row = connection.execute("SELECT venta_id FROM inventory_movements WHERE id = ?", (movimiento_id,)).fetchone()
        if row is None or row["venta_id"] is not None: raise ValueError("Los movimientos generados por una venta no se modifican.")
        connection.execute("UPDATE inventory_movements SET motivo = ? WHERE id = ?", (motivo.strip(), movimiento_id)); connection.commit()
    finally: connection.close()


def delete_inventory_movement(movimiento_id):
    connection = get_connection()
    try:
        row = connection.execute("SELECT venta_id FROM inventory_movements WHERE id = ?", (movimiento_id,)).fetchone()
        if row is None or row["venta_id"] is not None: raise ValueError("Los movimientos generados por una venta no se eliminan.")
        connection.execute("DELETE FROM inventory_movements WHERE id = ?", (movimiento_id,)); connection.commit()
    finally: connection.close()
