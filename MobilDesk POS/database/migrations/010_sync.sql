CREATE TABLE IF NOT EXISTS sync_outbox (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    datos TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    enviado_en TEXT,
    ultimo_error TEXT
);

CREATE TABLE IF NOT EXISTS sync_applied_events (
    id TEXT PRIMARY KEY,
    aplicado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sync_settings (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
