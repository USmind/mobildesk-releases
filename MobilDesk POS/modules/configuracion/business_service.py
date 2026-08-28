from database.connection import get_connection
from modules.sync.sync_service import queue_event_with_connection


def get_business_settings():
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT nombre_negocio, identificacion, telefono, direccion, mensaje_ticket FROM business_settings WHERE id = 1"
        ).fetchone()
        if row:
            return dict(row)
        return {
            "nombre_negocio": "MobilDesk",
            "identificacion": "",
            "telefono": "",
            "direccion": "",
            "mensaje_ticket": "¡Gracias por su compra!",
        }
    finally:
        connection.close()


def save_business_settings(nombre_negocio, identificacion="", telefono="", direccion="", mensaje_ticket="¡Gracias por su compra!"):
    nombre_negocio = nombre_negocio.strip()
    if not nombre_negocio:
        raise ValueError("El nombre del negocio no puede estar vacío.")

    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO business_settings (id, nombre_negocio, identificacion, telefono, direccion, mensaje_ticket)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nombre_negocio = excluded.nombre_negocio,
                identificacion = excluded.identificacion,
                telefono = excluded.telefono,
                direccion = excluded.direccion,
                mensaje_ticket = excluded.mensaje_ticket
            """,
            (
                nombre_negocio,
                identificacion.strip(),
                telefono.strip(),
                direccion.strip(),
                mensaje_ticket.strip(),
            ),
        )
        queue_event_with_connection(
            connection,
            "negocio_config_actualizada",
            {
                "nombre_negocio": nombre_negocio,
                "identificacion": identificacion.strip(),
                "telefono": telefono.strip(),
                "direccion": direccion.strip(),
                "mensaje_ticket": mensaje_ticket.strip(),
            },
        )
        connection.commit()
        return get_business_settings()
    finally:
        connection.close()
