import bcrypt
from database.connection import get_connection

def _queue_user_sync(username, nombre, password_hash, role, activo):
    """Sincroniza un usuario a la nube para que la App pueda loguearse igual que en PC."""
    try:
        from modules.sync.sync_service import queue_event, get_business_id
        bid = get_business_id()
        if not bid:
            return
        queue_event("usuario_sincronizado", {
            "username": username.lower().strip(),
            "nombre": nombre.strip(),
            "password_hash": password_hash,
            "role": role,
            "activo": int(activo),
            "negocio_id": bid.strip(),
        })
    except Exception:
        pass

BOOTSTRAP_USERNAME = "__configuracion__"


def create_user(nombre, username, password, role):
    nombre, username = nombre.strip(), username.strip().lower()
    if not nombre or not username or not password:
        raise ValueError("Nombre, usuario y contrasena son obligatorios.")
    if role not in ("admin", "vendedor"):
        raise ValueError("El rol debe ser Administrador o Vendedor.")
    connection = get_connection()
    try:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor = connection.execute("INSERT INTO users (nombre, username, password_hash, role, activo) VALUES (?, ?, ?, ?, 1)", (nombre, username, password_hash, role))
        connection.commit()
        _queue_user_sync(username, nombre, password_hash, role, 1)
        return cursor.lastrowid
    except Exception:
        connection.rollback(); raise
    finally: connection.close()


def has_users():
    connection = get_connection()
    try: return connection.execute("SELECT 1 FROM users WHERE username != ? LIMIT 1", (BOOTSTRAP_USERNAME,)).fetchone() is not None
    finally: connection.close()


def ensure_bootstrap_user():
    """Technical administrator used only until the first real account is created."""
    connection = get_connection()
    try:
        user = connection.execute("SELECT * FROM users WHERE username = ?", (BOOTSTRAP_USERNAME,)).fetchone()
        if user is not None: return user
        password_hash = bcrypt.hashpw(b"bootstrap-disabled", bcrypt.gensalt()).decode("utf-8")
        connection.execute("INSERT INTO users (nombre, username, password_hash, role, activo) VALUES (?, ?, ?, 'admin', 1)", ("Configuracion inicial", BOOTSTRAP_USERNAME, password_hash))
        connection.commit()
        return connection.execute("SELECT * FROM users WHERE username = ?", (BOOTSTRAP_USERNAME,)).fetchone()
    finally: connection.close()


def authenticate(username, password):
    connection = get_connection()
    try: user = connection.execute("SELECT * FROM users WHERE username = ? AND activo = 1", (username.strip(),)).fetchone()
    finally: connection.close()
    return user if user and bcrypt.checkpw(password.encode("utf-8"), user[3].encode("utf-8")) else None


def get_users():
    connection = get_connection()
    try: return connection.execute("SELECT id, nombre, username, role, activo, fecha_creacion FROM users WHERE username != ? ORDER BY nombre", (BOOTSTRAP_USERNAME,)).fetchall()
    finally: connection.close()


def user_exists(username):
    connection = get_connection()
    try: return connection.execute("SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)).fetchone() is not None
    finally: connection.close()


def update_user(user_id, nombre, username, role, password=None):
    nombre, username = nombre.strip(), username.strip().lower()
    if not nombre or not username:
        raise ValueError("Nombre y usuario son obligatorios.")
    if role not in ("admin", "vendedor"):
        raise ValueError("El rol debe ser Administrador o Vendedor.")

    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND id != ?",
            (username, user_id)
        ).fetchone()
        if existing:
            raise ValueError(f"El nombre de usuario '{username}' ya está en uso por otra cuenta.")

        if role != "admin":
            current = connection.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
            if current and current["role"] == "admin":
                admins = connection.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND activo = 1 AND id != ?",
                    (user_id,)
                ).fetchone()[0]
                if admins == 0:
                    raise ValueError("No puede cambiar el rol de este usuario: debe quedar al menos un Administrador en el sistema.")

        if password and password.strip():
            password_hash = bcrypt.hashpw(password.strip().encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            connection.execute(
                "UPDATE users SET nombre = ?, username = ?, password_hash = ?, role = ? WHERE id = ?",
                (nombre, username, password_hash, role, user_id)
            )
        else:
            connection.execute(
                "UPDATE users SET nombre = ?, username = ?, role = ? WHERE id = ?",
                (nombre, username, role, user_id)
            )
            row = connection.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
            password_hash = row["password_hash"] if row else ""
        connection.commit()
        _queue_user_sync(username, nombre, password_hash, role, 1)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_user(user_id):
    connection = get_connection()
    try:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("Usuario no encontrado.")

        if user["role"] == "admin":
            admins = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND activo = 1 AND id != ?",
                (user_id,)
            ).fetchone()[0]
            if admins == 0:
                raise ValueError("No se puede eliminar el único Administrador del sistema.")

        # Guardar datos para sync antes de borrar
        _nombre = str(user["nombre"] or "")
        _username = str(user["username"] or "")
        _ph = str(user["password_hash"] or "")
        _role = str(user["role"] or "vendedor")
        connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
        connection.commit()
        _queue_user_sync(_username, _nombre, _ph, _role, 0)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def sync_all_users_to_cloud():
    """Sincroniza todos los usuarios existentes al iniciar, para que la App los vea."""
    try:
        users = get_users()
        for u in users:
            # get_users no trae password_hash, hay que leerlo
            conn = get_connection()
            try:
                row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (u["id"],)).fetchone()
                ph = str(row["password_hash"] or "") if row else ""
            finally:
                conn.close()
            _queue_user_sync(str(u["username"] or ""), str(u["nombre"] or ""), ph, str(u["role"] or "vendedor"), int(u["activo"] or 1))
    except Exception:
        pass
