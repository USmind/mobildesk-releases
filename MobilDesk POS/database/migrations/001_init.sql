CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    username TEXT NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    role TEXT NOT NULL,

    activo INTEGER DEFAULT 1,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

);


CREATE TABLE IF NOT EXISTS categories (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL UNIQUE,

    activo INTEGER DEFAULT 1

);


CREATE TABLE IF NOT EXISTS products (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    codigo TEXT NOT NULL UNIQUE,

    nombre TEXT NOT NULL,

    categoria_id INTEGER,

    costo_usd REAL NOT NULL,

    precio_usd REAL NOT NULL,

    stock_minimo REAL DEFAULT 0,

    activo INTEGER DEFAULT 1,

    FOREIGN KEY(categoria_id)
    REFERENCES categories(id)

);


CREATE TABLE IF NOT EXISTS exchange_rates (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    valor REAL NOT NULL,

    usuario_id INTEGER,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(usuario_id)
    REFERENCES users(id)

);