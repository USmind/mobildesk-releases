-- Migración 017: categoría + proveedor en productos (protocolo sync compartido, aditivo).
-- La tabla categories ya existe (001) y se reutiliza. La app vieja ignora los campos nuevos.
CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, activo INTEGER DEFAULT 1);
ALTER TABLE products ADD COLUMN proveedor_id INTEGER REFERENCES suppliers(id);
