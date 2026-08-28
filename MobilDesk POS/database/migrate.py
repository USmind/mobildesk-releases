import sqlite3
from pathlib import Path
from database.connection import DATABASE
from app_paths import resource_path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = DATABASE

MIGRATIONS_DIR = Path(resource_path("database/migrations"))


# ============================================================
# CONEXIÓN
# ============================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# TABLA DE MIGRACIONES
# ============================================================

def create_migrations_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            executed_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    connection.commit()


# ============================================================
# MIGRACIONES EXISTENTES
# ============================================================

def get_executed_migrations(connection):

    cursor = connection.execute("""
        SELECT filename
        FROM schema_migrations
        ORDER BY filename
    """)

    return {row[0] for row in cursor.fetchall()}


# ============================================================
# COMPROBAR SI UNA MIGRACIÓN YA ESTÁ APLICADA
# ============================================================

def migration_already_applied(connection, filename):

    # --------------------------------------------------------
    # 001
    # --------------------------------------------------------
    if filename == "001_init.sql":

        cursor = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'users'
        """)

        return cursor.fetchone() is not None

    # --------------------------------------------------------
    # 002
    # --------------------------------------------------------
    if filename == "002_products_update.sql":

        cursor = connection.execute("""
            PRAGMA table_info(products)
        """)

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        # La migración 002 agregó estas columnas.
        required_columns = {
            "codigo_barras",
            "descripcion",
            "marca",
            "unidad",
            "stock_minimo"
        }

        return required_columns.issubset(columns)

    # --------------------------------------------------------
    # Para futuras migraciones no asumimos nada.
    # --------------------------------------------------------

    return False


# ============================================================
# MARCAR MIGRACIÓN COMO EJECUTADA
# ============================================================

def mark_as_executed(connection, filename):

    connection.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (filename)
        VALUES (?)
        """,
        (filename,)
    )

    connection.commit()


# ============================================================
# EJECUTAR MIGRACIÓN
# ============================================================

def execute_migration(connection, migration_file):

    filename = migration_file.name

    print(
        f"Ejecutando "
        f"{migration_file.name}"
    )

    sql = migration_file.read_text(
        encoding="utf-8"
    )

    try:

        connection.executescript(sql)

        connection.execute(
            """
            INSERT OR IGNORE INTO schema_migrations
                (filename)
            VALUES
                (?)
            """,
            (filename,)
        )

        connection.commit()

        print("OK")

    except Exception as error:

        connection.rollback()

        print("ERROR")
        print(error)

        raise


# ============================================================
# EJECUTAR TODAS LAS MIGRACIONES
# ============================================================

def run_migrations():

    print("=" * 60)
    print("MobilDesk POS - SISTEMA DE MIGRACIONES")
    print("=" * 60)

    print()
    print("Base de datos:")
    print(DB_PATH)

    print()
    print("Carpeta de migraciones:")
    print(MIGRATIONS_DIR)

    MIGRATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = get_connection()

    try:

        create_migrations_table(connection)

        executed = get_executed_migrations(
            connection
        )

        migration_files = sorted(
            MIGRATIONS_DIR.glob("*.sql")
        )

        if not migration_files:

            print()
            print("No se encontraron archivos SQL.")

            return

        print()

        for migration_file in migration_files:

            filename = migration_file.name

            # ------------------------------------------------
            # Ya registrada
            # ------------------------------------------------

            if filename in executed:

                print(
                    f"Omitiendo {filename} "
                    f"(ya registrada)"
                )

                continue

            # ------------------------------------------------
            # Detectar migraciones antiguas que ya existen
            # ------------------------------------------------

            if migration_already_applied(
                connection,
                filename
            ):

                print(
                    f"Omitiendo {filename} "
                    f"(ya estaba aplicada)"
                )

                mark_as_executed(
                    connection,
                    filename
                )

                continue

            # ------------------------------------------------
            # Ejecutar migración nueva
            # ------------------------------------------------

            execute_migration(
                connection,
                migration_file
            )

        print()
        print("=" * 60)
        print("MIGRACIONES COMPLETADAS")
        print("=" * 60)

    finally:

        connection.close()


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    run_migrations()

