-- ============================================================
-- MiBodegaPOS
-- MIGRACIÓN 004
-- TABLA DE VENTAS
-- ============================================================

CREATE TABLE IF NOT EXISTS sales (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    numero_factura INTEGER NOT NULL UNIQUE,

    usuario_id INTEGER NOT NULL,

    tasa_utilizada REAL NOT NULL,

    total_usd REAL NOT NULL,

    total_bs REAL NOT NULL,

    fecha TEXT NOT NULL DEFAULT (datetime('now')),

    estado TEXT NOT NULL DEFAULT 'completada',

    FOREIGN KEY (usuario_id)
        REFERENCES users(id),

    CHECK (
        estado IN ('completada', 'anulada')
    )
);


-- ============================================================
-- ÍNDICE PARA CONSULTAS DE VENTAS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_usuario
ON sales(usuario_id);


CREATE INDEX IF NOT EXISTS idx_sales_fecha
ON sales(fecha);


CREATE INDEX IF NOT EXISTS idx_sales_estado
ON sales(estado);