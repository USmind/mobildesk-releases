from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection


def get_products():
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT p.id, p.codigo, p.codigo_barras, p.nombre, p.marca, p.unidad,
                   p.precio_usd, p.stock_minimo, p.categoria_id, p.proveedor_id,
                   COALESCE(c.nombre, 'Sin categoría') AS categoria,
                   COALESCE(s.nombre, 'Sin proveedor') AS proveedor,
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
            LEFT JOIN suppliers s ON s.id = p.proveedor_id
            LEFT JOIN inventory_movements im ON im.producto_id = p.id
            WHERE p.activo = 1
            GROUP BY p.id, p.codigo, p.codigo_barras, p.nombre, p.marca, p.unidad, p.precio_usd, p.stock_minimo, p.categoria_id, p.proveedor_id, c.nombre, s.nombre
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


def get_suppliers():
    connection = get_connection()
    try: return connection.execute("SELECT id, nombre FROM suppliers WHERE activo=1 ORDER BY nombre").fetchall()
    finally: connection.close()


def create_supplier(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre del proveedor no puede estar vacío")
    connection = get_connection()
    try:
        existe = connection.execute("SELECT id FROM suppliers WHERE nombre=?", (nombre,)).fetchone()
        if existe:
            raise ValueError(f"El proveedor '{nombre}' ya existe")
        cursor = connection.execute("INSERT INTO suppliers(nombre, activo) VALUES(?,1)", (nombre,))
        connection.commit()
        return cursor.lastrowid
    finally: connection.close()


def get_or_create_category(nombre):
    nombre = (nombre or "").strip() if isinstance(nombre, str) else ""
    if not nombre:
        return None
    connection = get_connection()
    try:
        row = connection.execute("SELECT id FROM categories WHERE nombre=?", (nombre,)).fetchone()
        if row:
            return row["id"]
        connection.execute("INSERT OR IGNORE INTO categories(nombre, activo) VALUES(?,1)", (nombre,))
        connection.commit()
        row = connection.execute("SELECT id FROM categories WHERE nombre=?", (nombre,)).fetchone()
        return row["id"] if row else None
    finally: connection.close()


def get_or_create_supplier(nombre):
    nombre = (nombre or "").strip() if isinstance(nombre, str) else ""
    if not nombre:
        return None
    connection = get_connection()
    try:
        row = connection.execute("SELECT id FROM suppliers WHERE nombre=?", (nombre,)).fetchone()
        if row:
            return row["id"]
        connection.execute("INSERT OR IGNORE INTO suppliers(nombre, activo) VALUES(?,1)", (nombre,))
        connection.commit()
        row = connection.execute("SELECT id FROM suppliers WHERE nombre=?", (nombre,)).fetchone()
        return row["id"] if row else None
    finally: connection.close()


def _nombres_taxonomia(connection, categoria_id, proveedor_id):
    categoria = ""
    proveedor = ""
    if categoria_id:
        row = connection.execute("SELECT nombre FROM categories WHERE id=?", (categoria_id,)).fetchone()
        if row:
            categoria = row["nombre"] or ""
    if proveedor_id:
        try:
            row = connection.execute("SELECT nombre FROM suppliers WHERE id=?", (proveedor_id,)).fetchone()
            if row:
                proveedor = row["nombre"] or ""
        except Exception:
            proveedor = ""
    return categoria, proveedor


class ProductoYaExiste(Exception):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(f"El código {codigo} ya existe")


def create_product(codigo, nombre, unidad, precio_usd, stock_inicial=0, categoria_id=None, stock_minimo=0, codigo_barras=None, proveedor_id=None):
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
            (codigo, codigo_barras, nombre, categoria_id, proveedor_id, marca, unidad, costo_usd, precio_usd, stock_minimo, activo)
            VALUES (?, ?, ?, ?, ?, '', ?, 0, ?, ?, 1)""",
            (codigo, codigo_barras, nombre.strip(), categoria_id, proveedor_id, unidad, float(precio_usd), float(stock_minimo or 0)))
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

        categoria, proveedor = _nombres_taxonomia(connection, categoria_id, proveedor_id)
        queue_event_with_connection(connection, "producto_guardado", {
            "codigo": codigo, "codigo_barras": codigo_barras, "nombre": nombre.strip(), "marca": "",
            "unidad": unidad, "precio_usd": float(precio_usd), "stock_minimo": float(stock_minimo or 0), "activo": 1,
            "categoria": categoria, "proveedor": proveedor,
        })
        connection.commit()
        return codigo
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_product(producto_id, nombre, unidad, precio_usd, stock_minimo=0, categoria_id=None, codigo_barras=None, proveedor_id=None, codigo=None):
    connection = get_connection()
    try:
        actual = connection.execute("SELECT codigo, codigo_barras FROM products WHERE id=?", (producto_id,)).fetchone()
        if not actual:
            raise ValueError("El producto no existe")
        codigo_anterior = actual["codigo"]
        if codigo is None:
            codigo_nuevo = codigo_anterior
        else:
            codigo_nuevo = codigo.strip()
            if not codigo_nuevo:
                raise ValueError("El código no puede estar vacío")
        if not codigo_barras or not str(codigo_barras).strip():
            codigo_barras_nuevo = codigo_nuevo
        else:
            codigo_barras_nuevo = str(codigo_barras).strip()
        if codigo_nuevo != codigo_anterior:
            dup = connection.execute("SELECT id FROM products WHERE codigo=? AND id!=?", (codigo_nuevo, producto_id)).fetchone()
            if dup:
                raise ValueError("Ese código ya está en uso")
        if codigo_barras_nuevo != (actual["codigo_barras"] or ""):
            dup_cb = connection.execute("SELECT id FROM products WHERE codigo_barras=? AND id!=?", (codigo_barras_nuevo, producto_id)).fetchone()
            if dup_cb:
                raise ValueError("Ese código ya está en uso")
        connection.execute("""UPDATE products SET codigo=?, nombre=?, categoria_id=?, proveedor_id=?, unidad=?,
            precio_usd=?, stock_minimo=?, codigo_barras=? WHERE id=? AND activo=1""",
            (codigo_nuevo, nombre.strip(), categoria_id, proveedor_id, unidad, float(precio_usd), float(stock_minimo or 0), codigo_barras_nuevo, producto_id))
        categoria, proveedor = _nombres_taxonomia(connection, categoria_id, proveedor_id)
        producto_dict = {
            "codigo": codigo_nuevo, "codigo_barras": codigo_barras_nuevo, "nombre": nombre.strip(), "marca": "",
            "unidad": unidad, "precio_usd": float(precio_usd), "stock_minimo": float(stock_minimo or 0), "activo": 1,
            "categoria": categoria, "proveedor": proveedor,
        }
        queue_event_with_connection(connection, "producto_guardado", dict(producto_dict))
        if codigo_nuevo != codigo_anterior:
            queue_event_with_connection(connection, "producto_recodificado", {
                "codigo_anterior": codigo_anterior, "producto": dict(producto_dict),
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
