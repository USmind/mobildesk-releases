from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection


def get_products():
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT p.id, p.codigo, p.codigo_barras, p.nombre, p.marca, p.unidad,
                   p.precio_usd, p.stock_minimo, p.categoria_id,
                   COALESCE(c.nombre, 'Sin categoría') AS categoria,
                   COALESCE(
                       SUM(
                           CASE
                               WHEN im.tipo = 'entrada' THEN im.cantidad
                               WHEN im.tipo = 'salida' THEN -im.cantidad
                               WHEN im.tipo = 'ajuste' THEN im.cantidad
                               ELSE 0
                           END
                       ),
                       0
                   ) AS stock_actual
            FROM products p
            LEFT JOIN categories c ON c.id = p.categoria_id
            LEFT JOIN inventory_movements im ON im.producto_id = p.id
            WHERE p.activo = 1
            GROUP BY p.id, p.codigo, p.codigo_barras, p.nombre, p.marca, p.unidad, p.precio_usd, p.stock_minimo, p.categoria_id, c.nombre
            ORDER BY p.nombre
        """).fetchall()
    finally:
        connection.close()


def get_next_product_code():
    connection = get_connection()
    try:
        row = connection.execute("""SELECT codigo FROM products WHERE codigo GLOB 'P[0-9]*'
            ORDER BY CAST(SUBSTR(codigo, 2) AS INTEGER) DESC LIMIT 1""").fetchone()
        return f"P{(int(row['codigo'][1:]) + 1) if row else 1:06d}"
    finally: connection.close()


def get_categories():
    connection = get_connection()
    try: return connection.execute("SELECT id, nombre FROM categories WHERE activo=1 ORDER BY nombre").fetchall()
    finally: connection.close()


def create_category(nombre):
    connection = get_connection()
    try:
        connection.execute("INSERT OR IGNORE INTO categories(nombre, activo) VALUES(?,1)", (nombre.strip(),)); connection.commit()
        return connection.execute("SELECT id FROM categories WHERE nombre=?", (nombre.strip(),)).fetchone()["id"]
    finally: connection.close()


class ProductoYaExiste(Exception):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(f"El código {codigo} ya existe")


def create_product(codigo, nombre, unidad, precio_usd, stock_inicial=0, categoria_id=None, stock_minimo=0, codigo_barras=None):
    connection = get_connection()
    try:
        codigo = codigo.strip()
        if not codigo:
            raise ValueError("El código no puede estar vacío")
        existe = connection.execute("SELECT id FROM products WHERE codigo=?", (codigo,)).fetchone()
        if existe:
            raise ProductoYaExiste(codigo)
        if not codigo_barras:
            codigo_barras = codigo
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO products
            (codigo, codigo_barras, nombre, categoria_id, marca, unidad, costo_usd, precio_usd, stock_minimo, activo)
            VALUES (?, ?, ?, ?, '', ?, 0, ?, ?, 1)""",
            (codigo, codigo_barras, nombre.strip(), categoria_id, unidad, float(precio_usd), float(stock_minimo or 0)))
        prod_id = cursor.lastrowid

        stock_ini_float = float(stock_inicial or 0)
        if stock_ini_float > 0:
            user_row = cursor.execute("SELECT id FROM users WHERE activo = 1 ORDER BY id ASC LIMIT 1").fetchone()
            uid = user_row["id"] if user_row else None
            if uid is None:
                cursor.execute("INSERT OR IGNORE INTO users (nombre, username, password_hash, role, activo) VALUES ('Admin', 'admin', 'admin', 'admin', 1)")
                user_row = cursor.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
                uid = user_row["id"] if user_row else 1

            cursor.execute("""INSERT INTO inventory_movements
                (producto_id, tipo, cantidad, costo_usd, motivo, usuario_id)
                VALUES (?, 'entrada', ?, ?, 'Inventario Inicial', ?)""",
                (prod_id, stock_ini_float, float(precio_usd), uid))
            queue_event_with_connection(connection, "movimiento_inventario", {
                "producto_codigo": codigo,
                "tipo": "entrada",
                "cantidad": stock_ini_float,
                "costo_usd": float(precio_usd),
                "motivo": "Inventario Inicial",
                "fecha": None,
            })

        queue_event_with_connection(connection, "producto_guardado", {
            "codigo": codigo, "codigo_barras": codigo_barras, "nombre": nombre.strip(), "marca": "",
            "unidad": unidad, "precio_usd": float(precio_usd), "stock_minimo": float(stock_minimo or 0), "activo": 1,
        })
        connection.commit()
        return codigo
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_product(producto_id, nombre, unidad, precio_usd, stock_minimo=0, categoria_id=None, codigo_barras=None):
    connection = get_connection()
    try:
        if not codigo_barras:
            codigo_barras = connection.execute("SELECT codigo FROM products WHERE id=?", (producto_id,)).fetchone()["codigo"]
        connection.execute("""UPDATE products SET nombre=?, categoria_id=?, unidad=?,
            precio_usd=?, stock_minimo=?, codigo_barras=? WHERE id=? AND activo=1""",
            (nombre.strip(), categoria_id, unidad, float(precio_usd), float(stock_minimo or 0), codigo_barras, producto_id))
        codigo = connection.execute("SELECT codigo FROM products WHERE id=?", (producto_id,)).fetchone()["codigo"]
        queue_event_with_connection(connection, "producto_guardado", {
            "codigo": codigo, "codigo_barras": codigo_barras, "nombre": nombre.strip(), "marca": "",
            "unidad": unidad, "precio_usd": float(precio_usd), "stock_minimo": float(stock_minimo or 0), "activo": 1,
        })
        connection.commit()
    except Exception:
        connection.rollback(); raise
    finally: connection.close()


def delete_product(producto_id):
    connection = get_connection()
    try:
        row = connection.execute("SELECT codigo FROM products WHERE id=?", (producto_id,)).fetchone()
        connection.execute("UPDATE products SET activo=0 WHERE id=?", (producto_id,))
        if row:
            queue_event_with_connection(connection, "producto_eliminado", {"codigo": row["codigo"]})
        connection.commit()
    finally: connection.close()
