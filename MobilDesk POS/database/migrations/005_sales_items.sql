-- ============================================================
-- MiBodegaPOS
-- MIGRACIÓN 005
-- DETALLE DE VENTAS
-- ============================================================

CREATE TABLE IF NOT EXISTS sale_items (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    venta_id INTEGER NOT NULL,

    producto_id INTEGER NOT NULL,

    cantidad REAL NOT NULL,

    precio_usd REAL NOT NULL,

    subtotal_usd REAL NOT NULL,

    FOREIGN KEY (venta_id)
        REFERENCES sales(id),

    FOREIGN KEY (producto_id)
        REFERENCES products(id),

    CHECK (cantidad > 0),

    CHECK (precio_usd >= 0),

    CHECK (subtotal_usd >= 0)
);

-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sale_items_venta
ON sale_items(venta_id);

CREATE INDEX IF NOT EXISTS idx_sale_items_producto
ON sale_items(producto_id);