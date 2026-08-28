-- ============================================================
-- MIGRACIÓN 003
-- SISTEMA DE INVENTARIO
-- MiBodegaPOS
-- ============================================================

-- ------------------------------------------------------------
-- TABLA DE MOVIMIENTOS DE INVENTARIO
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    producto_id INTEGER NOT NULL,

    tipo TEXT NOT NULL
        CHECK (tipo IN ('entrada', 'salida', 'ajuste')),

    cantidad REAL NOT NULL,

    motivo TEXT,

    venta_id INTEGER,

    usuario_id INTEGER NOT NULL,

    fecha TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (producto_id)
        REFERENCES products(id),

    FOREIGN KEY (venta_id)
        REFERENCES sales(id),

    FOREIGN KEY (usuario_id)
        REFERENCES users(id)
);

-- ------------------------------------------------------------
-- ÍNDICES
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_inventory_product
ON inventory_movements(producto_id);

CREATE INDEX IF NOT EXISTS idx_inventory_date
ON inventory_movements(fecha);

CREATE INDEX IF NOT EXISTS idx_inventory_sale
ON inventory_movements(venta_id);

-- ------------------------------------------------------------
-- VISTA DEL STOCK ACTUAL
-- ------------------------------------------------------------

DROP VIEW IF EXISTS stock_actual;

CREATE VIEW stock_actual AS

SELECT
    p.id AS producto_id,
    p.codigo,
    p.nombre,
    p.unidad,
    p.stock_minimo,

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
    ) AS stock

FROM products p

LEFT JOIN inventory_movements im
    ON im.producto_id = p.id

GROUP BY
    p.id,
    p.codigo,
    p.nombre,
    p.unidad,
    p.stock_minimo;

-- ============================================================
-- FIN DE MIGRACIÓN 003
-- ============================================================