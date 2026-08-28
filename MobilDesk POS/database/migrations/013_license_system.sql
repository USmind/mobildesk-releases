-- Migración 013: Sistema de Licencias y Activación
CREATE TABLE IF NOT EXISTS system_license (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    machine_id TEXT NOT NULL,
    fecha_instalacion TEXT NOT NULL,
    plan_activo TEXT NOT NULL DEFAULT 'demo',
    clave_activacion TEXT,
    fecha_activacion TEXT,
    fecha_expiracion TEXT,
    ultima_verificacion TEXT NOT NULL
);
