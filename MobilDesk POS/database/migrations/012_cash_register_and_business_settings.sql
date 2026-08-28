CREATE TABLE IF NOT EXISTS business_settings (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    nombre_negocio TEXT NOT NULL DEFAULT 'Kiosko',
    identificacion TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    mensaje_ticket TEXT DEFAULT '¡Gracias por su compra!'
);

INSERT OR IGNORE INTO business_settings (id, nombre_negocio, identificacion, telefono, direccion, mensaje_ticket)
VALUES (1, 'Kiosko', '', '', '', '¡Gracias por su compra!');

CREATE TABLE IF NOT EXISTS cash_registers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES users(id),
    monto_inicial_bs REAL NOT NULL DEFAULT 0,
    monto_inicial_usd REAL NOT NULL DEFAULT 0,
    monto_final_bs REAL DEFAULT NULL,
    monto_final_usd REAL DEFAULT NULL,
    diferencia_bs REAL DEFAULT 0,
    diferencia_usd REAL DEFAULT 0,
    fecha_apertura TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    fecha_cierre TEXT DEFAULT NULL,
    estado TEXT NOT NULL DEFAULT 'abierta',
    observaciones TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cash_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL REFERENCES cash_registers(id),
    usuario_id INTEGER NOT NULL REFERENCES users(id),
    tipo TEXT NOT NULL,
    moneda TEXT NOT NULL DEFAULT 'Bs',
    monto REAL NOT NULL,
    motivo TEXT NOT NULL,
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
