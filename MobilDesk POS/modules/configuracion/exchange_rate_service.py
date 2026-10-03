from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection


def get_current_exchange_rate():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT valor FROM exchange_rates ORDER BY id DESC LIMIT 1")
        resultado = cursor.fetchone()
        if resultado is None:
            return None
        return float(resultado["valor"])
    finally:
        connection.close()


def get_current_rate_value():
    return get_current_exchange_rate()


def get_profit_percentage():
    connection = get_connection()
    try:
        row = connection.execute("SELECT porcentaje_ganancia FROM pricing_settings WHERE id=1").fetchone()
        return float(row["porcentaje_ganancia"] if row else 0)
    finally:
        connection.close()


def sale_price_usd(precio_base_usd):
    return float(precio_base_usd) * (1 + get_profit_percentage() / 100)


def set_exchange_rate(valor, usuario_id=None):
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        raise ValueError("La tasa debe ser un número válido.")

    if valor <= 0:
        raise ValueError("La tasa debe ser mayor que cero.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        valid_user_id = None
        if usuario_id:
            row = cursor.execute("SELECT id FROM users WHERE id = ? AND activo = 1", (usuario_id,)).fetchone()
            if row:
                valid_user_id = row["id"]

        if not valid_user_id:
            row = cursor.execute("SELECT id FROM users WHERE activo = 1 ORDER BY id ASC LIMIT 1").fetchone()
            if row:
                valid_user_id = row["id"]

        cursor.execute(
            "INSERT INTO exchange_rates (valor, usuario_id) VALUES (?, ?)",
            (valor, valid_user_id),
        )
        queue_event_with_connection(
            connection,
            "tasa_cambio_actualizada",
            {"tasa": valor, "margen": get_profit_percentage()},
        )
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
