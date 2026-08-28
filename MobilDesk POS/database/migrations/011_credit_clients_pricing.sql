CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    telefono TEXT,
    direccion TEXT,
    cedula TEXT
);
CREATE TABLE IF NOT EXISTS credit_debts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL,
    total_bs REAL NOT NULL,
    saldo_bs REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY(venta_id) REFERENCES sales(id),
    FOREIGN KEY(cliente_id) REFERENCES clients(id)
);
CREATE TABLE IF NOT EXISTS debt_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deuda_id INTEGER NOT NULL,
    monto_bs REAL NOT NULL,
    fecha TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(deuda_id) REFERENCES credit_debts(id)
);
CREATE TABLE IF NOT EXISTS pricing_settings (
    id INTEGER PRIMARY KEY CHECK(id=1),
    porcentaje_ganancia REAL NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO pricing_settings(id, porcentaje_ganancia) VALUES(1, 0);
ALTER TABLE sales ADD COLUMN cliente_id INTEGER REFERENCES clients(id);
ALTER TABLE sales ADD COLUMN es_fiada INTEGER NOT NULL DEFAULT 0;
