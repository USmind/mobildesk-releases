_current_user = None


def set_user(user):

    global _current_user

    if user is None:
        _current_user = None
        return

    # Si viene como diccionario
    if isinstance(user, dict):

        _current_user = {
            "id": user.get("id"),
            "nombre": user.get("nombre"),
            "username": user.get("username"),
            "role": user.get("role")
        }

        return

    # Si viene como sqlite3.Row
    try:

        _current_user = {
            "id": user["id"],
            "nombre": user["nombre"],
            "username": user["username"],
            "role": user["role"]
        }

        return

    except (KeyError, TypeError, IndexError):
        pass

    # Si viene como tupla
    _current_user = {
        "id": user[0],
        "nombre": user[1],
        "username": user[2] if len(user) > 2 else None,
        "role": user[3] if len(user) > 3 else None
    }


def get_user():

    return _current_user


def clear_user():

    global _current_user

    _current_user = None